#!/usr/bin/env python3
import pendulum
import singer
from singer import utils

from tap_alchemer.alchemer_api import AlchemerAPI

REQUIRED_CONFIG_KEYS = ["api_token", "api_token_secret", "domain"]
LOGGER = singer.get_logger()


class SchemaSurvey:
    stream: str = "survey"
    key: list = ["id"]
    schema: dict = {
        "properties": {
            "id": {'type': 'integer'},
            "team": {'type': 'integer'},
            "type": {'type': 'string'},
            "status": {'type': 'string'},
            "created_on": {'type': 'string', "format": "date-time", },
            "modified_on": {'type': 'string', "format": "date-time", },
            "title": {'type': 'string'},
            "statistics": {'type': 'object'},
            "links": {'type': 'object'},
        }
    }


class SchemaSurveyQuestion:
    stream: str = "survey_question"
    key: list = ["id"]
    schema: dict = {
        "properties": {
            "survey_id": {'type': 'integer'},
            "id": {'type': 'integer'},
            "type": {'type': 'string'},
            "title": {'type': 'object'},
            "base_type": {'type': 'string'},
            "shortname": {'type': 'string'},
            "varname": {'type': 'string'},
            "description": {'type': 'string'},
            "properties": {'type': 'object'},
            "options": {'type': 'object'},
            "comment": {'type': 'boolean'},
            "has_showhide_deps": {'type': 'boolean'},
        }
    }


class SchemaSurveyResponse:
    stream: str = "survey_response"
    key: list = ["response_id"]
    schema: dict = {
        "properties": {
            "response_id": {'type': 'string'},
            "survey_id": {'type': 'integer'},
            "id": {'type': 'integer'},
            "contact_id": {'type': 'string'},
            "status": {'type': 'string'},
            "is_test_data": {'type': 'integer'},
            "session_id": {'type': 'string'},
            "language": {'type': 'string'},
            "ip_address": {'type': 'string'},
            "url_variables": {'type': 'object'},
            "referer": {'type': 'string'},
            "user_agent": {'type': 'string'},
            "country": {'type': 'string'},
            "city": {'type': 'string'},
            "postal": {'type': 'string'},
            "region": {'type': 'string'},
            "utm_source": {'type': 'string'},
            "utm_medium": {'type': 'string'},
            "utm_campaign": {'type': 'string'},
            "link_id": {'type': 'integer'},
            "response_time": {'type': 'integer'},
            "dma": {'type': 'integer'},
            "data_quality": {'type': 'object'},
            "longitude": {'type': 'numeric'},
            "latitude": {'type': 'numeric'},
            "date_submitted": {'type': 'string', "format": "date-time"},
            "date_started": {'type': 'string', "format": "date-time"},
        }
    }


class SchemaSurveyData:
    stream: str = "survey_response_data"
    key: list = ["response_id"]
    schema: dict = {
        "properties": {
            "response_id": {'type': 'string'},
            "survey_id": {'type': 'integer'},
            "survey_response_id": {'type': 'integer'},
            "id": {'type': 'integer'},

            "answer_id": {'type': 'integer'},
            "section_id": {'type': 'integer'},

            "question": {'type': 'string'},
            "answer": {'type': 'string'},
            "type": {'type': 'string'},
            "shown": {'type': 'boolean'},
        }
    }


def initialize_client(config):
    api_token = config['api_token']
    api_token_secret = config['api_token_secret']
    domain = config['domain']
    return AlchemerAPI(api_token=api_token, api_token_secret=api_token_secret, domain=domain)


def convert_timezone_to_utc(dt: str):
    """
    Timezone in alchemr is in EST/EDT.
    EDT is not known as valid timezone for some target.
    This will convert the timezone to UTC
    :param dt:
    :return: dt UTC (string)
    """
    # append timezone
    if 'EDT' not in dt and 'EST' not in dt:
        dt = f"{dt} EST"

    # pendulum tzinfo database does not have EDT but has EST5EDT instead.
    dt_to_convert = dt.replace('EDT', 'EST5EDT')

    dt_conv = pendulum.from_format(dt_to_convert, 'YYYY-MM-DD HH:mm:ss z')
    return dt_conv.in_tz(tz='UTC').to_datetime_string()


def sync(config, state={}):
    alchemer = initialize_client(config)
    extraction_time = singer.utils.now()
    rows = {SchemaSurvey.stream: 0,
            SchemaSurveyQuestion.stream: 0,
            SchemaSurveyResponse.stream: 0,
            SchemaSurveyData.stream: 0}

    LOGGER.info('Syncing stream: survey')

    survey_state_modified = singer.get_bookmark(state, SchemaSurvey.stream, "modified_on", "")
    if survey_state_modified:
        params = {"filter[field][0]": "date_modified",
                  "filter[operator][0]": ">",
                  "filter[value][0]": survey_state_modified}
    else:
        params = {}

    surveys = alchemer.get_survey_list(params=params)
    if surveys:
        singer.write_schema(SchemaSurvey.stream, SchemaSurvey.schema, SchemaSurvey.key)
        singer.write_schema(SchemaSurveyQuestion.stream, SchemaSurveyQuestion.schema, SchemaSurveyQuestion.key)

        for survey in surveys:
            survey_id = survey.get("id")

            survey.update({"created_on": convert_timezone_to_utc(survey.get("created_on")),
                           "modified_on": convert_timezone_to_utc(survey.get("modified_on")),
                           })

            singer.write_record(stream_name=SchemaSurvey.stream, record=survey, time_extracted=extraction_time)

            if survey.get("modified_on") > survey_state_modified:
                survey_state_modified = survey.get("modified_on")
            rows[SchemaSurvey.stream] += 1

            data = alchemer.get_questions(survey_id=survey_id)
            for d in data:
                d.update({"survey_id": survey_id})
                singer.write_record(stream_name=SchemaSurveyQuestion.stream, record=d, time_extracted=extraction_time)
                rows[SchemaSurveyQuestion.stream] += 1

    state = singer.write_bookmark(state, SchemaSurvey.stream, "modified_on", survey_state_modified)
    singer.write_state(state)

    LOGGER.info('Syncing stream: survey_response')
    response_state_submitted = singer.get_bookmark(state, SchemaSurveyResponse.stream, "date_submitted", "")
    if response_state_submitted:
        params = {"filter[field][0]": "date_submitted",
                  "filter[operator][0]": ">",
                  "filter[value][0]": response_state_submitted}
    else:
        params = {}

    # get responses
    surveys = alchemer.get_survey_list()
    schema_output = False
    for survey in surveys:
        survey_id = survey.get("id")
        responses = alchemer.get_survey_responses(survey_id=survey_id, params=params)

        if responses and not schema_output:
            singer.write_schema(SchemaSurveyResponse.stream, SchemaSurveyResponse.schema, SchemaSurveyResponse.key)
            singer.write_schema(SchemaSurveyData.stream, SchemaSurveyData.schema, SchemaSurveyData.key)
            schema_output = True

        for resp in responses:
            resp.update({"survey_id": survey_id,
                         "response_id": f"{survey_id}_{resp.get('id')}"})
            if resp.get("url_variables"):
                resp.update({
                    "utm_source": resp.get("url_variables", {}).get("utm_source", {}).get("value", ""),
                    "utm_medium": resp.get("url_variables", {}).get("utm_medium", {}).get("value", ""),
                    "utm_campaign": resp.get("url_variables", {}).get("utm_campaign", {}).get("value", ""),
                })

            resp.update({"date_started": convert_timezone_to_utc(resp.get("date_started")),
                         "date_submitted": convert_timezone_to_utc(resp.get("date_submitted")),
                         })

            if resp.get("date_submitted") > response_state_submitted:
                response_state_submitted = resp.get("date_submitted")

            survey_data = resp["survey_data"]
            resp.pop("survey_data")

            singer.write_record(stream_name=SchemaSurveyResponse.stream, record=resp, time_extracted=extraction_time)
            rows[SchemaSurveyResponse.stream] += 1

            for k in survey_data:
                data = survey_data.get(k, {})
                data.update({"survey_id": survey_id,
                             "survey_response_id": resp.get("id", ""),
                             "response_id": f"{survey_id}_{resp.get('id')}"})
                singer.write_record(stream_name=SchemaSurveyData.stream, record=data, time_extracted=extraction_time)
                rows[SchemaSurveyData.stream] += 1

    state = singer.write_bookmark(state, SchemaSurveyResponse.stream, "date_submitted", response_state_submitted)
    singer.write_state(state)

    LOGGER.info('----------------------')
    for stream_id in rows:
        LOGGER.info('%s: %d', stream_id, rows.get(stream_id, 0))
    LOGGER.info('----------------------')


@utils.handle_top_exception(LOGGER)
def main():
    args = utils.parse_args(REQUIRED_CONFIG_KEYS)
    sync(args.config, args.state)


if __name__ == "__main__":
    main()
