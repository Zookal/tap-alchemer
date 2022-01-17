import requests
from time import sleep
import singer
LOGGER = singer.get_logger()


class AlchemerAPI:
    api_token: str = None
    api_token_secret: str = None
    domain: str = None
    api_version: str = "5"

    def __init__(self, api_token: str, api_token_secret: str, domain: str):
        self.api_token = api_token
        self.api_token_secret = api_token_secret
        self.domain = domain

    def get_survey_list(self, params={}):
        return self._get_data(path=["survey"], params=params)

    def get_survey(self, survey_id):
        return self._get_data(path=["survey", survey_id])

    def get_questions(self, survey_id):
        return self._get_data(path=["survey", survey_id, "surveyquestion"])

    def get_question_option(self, survey_id, question_id):
        return self._get_data(path=["survey",survey_id, 'surveyquestion', question_id,'surveyoption'])


    def get_all_survey_options(self, survey_id, wait_sec=0):
        questions = self.get_questions(survey_id)
        options = []
        for question in questions:
            qid = question["id"]
            option = self.get_question_option(survey_id, qid)
            if option:
                opt_result = []
                for opt in option:
                    opt["question_id"] = qid
                    opt_result.append(opt)
                options += opt_result
            sleep(wait_sec)
        return options

    def get_survey_responses(self, survey_id, params=None):
        return self._multi_get_data(path=["survey", survey_id, 'surveyresponse'], params=params)

    def get_contact_lists(self):
        return self._get_data(path=['contactlist'])

    def get_contact_list(self, list_id):
        return self._get_data(path=['contactlist', list_id])

    def get_contacts(self, contact_list_id):
        return self._get_data(path=['contactlist', contact_list_id, 'contactlistcontact'])

    def get_contact(self, contact_list_id, contact_id):
        return self._get_data(path=['contactlist', contact_list_id, 'contactlistcontact', contact_id])

    def get_campaigns(self, survey_id):
        return self._get_data(path=["survey", survey_id, 'surveycampaign'])

    def get_campaign(self, survey_id, campaign_id):
        return self._get_data(path=["survey", survey_id, 'surveycampaign', campaign_id])

    def get_campaign_emails(self, survey_id, campaign_id):
        return self._get_data(path=["survey", survey_id, 'surveycampaign', campaign_id, 'emailmessage'])

    def get_campaign_email(self, survey_id, campaign_id, email_id):
        return self._get_data(path=["survey", survey_id, 'surveycampaign', campaign_id, 'emailmessage', email_id])

    def get_response_info(self, survey_id, campaign_id):
        return self._get_data(path=["survey", survey_id, 'surveycampaign', campaign_id, 'surveycontact'])

    def _get_data(self, path, attempts=10, wait_sec=3, just_data=True, params={}):
        url = self._make_url(path=path, params=params)
        attempt_count = 1
        for i in range(0, attempts):
            try:
                attempt_count += 1
                output = requests.get(url, verify=True)
                if output.ok:
                    output = output.json()
                    if just_data and "data" in output:
                        output = output["data"]

                    if not output:
                        output = {}

                    return output
            except Exception as e:
                if attempt_count >= attempts:
                    LOGGER.error("All attempts failed")
                    return
                LOGGER.warning(f"{e}\nTrying again in {wait_sec} second(s)...")
                sleep(wait_sec)

    def _multi_get_data(self, path, params={}):

        output = self._get_data(path=path, just_data=False, params=params)

        LOGGER.info(f">>> Total Pages {output['total_pages']}")
        if output["total_pages"] == 1:
            return output["data"]
        else:
            output_list = output["data"]
            for i in range(2, output["total_pages"] + 1):
                params.update({"page": i})
                output = self._get_data(path=path, just_data=False, params=params)
                output_list = output_list + output["data"]
            return output_list

    def _make_url(self, path=['survey'], params={}):
        base_url = f'https://{self.domain}/v{self.api_version}/'

        endpoints = ''
        for p in path:
            endpoints += ("/" if endpoints != "" and p else "") + str(p)

        url = f'{base_url}{endpoints}/?api_token={self.api_token}&api_token_secret={self.api_token_secret}'

        if "resultsperpage" not in params:
            params["resultsperpage"]: 500

        if "page" not in params:
            params.update({"page": 1})

        LOGGER.info(f">> endpoint: {endpoints} page: {params['page']}")

        params_list = []
        for key in params.keys():
            s = str(key) + '=' + str(params[key])
            params_list.append(s)
        param_str = '&'.join(params_list)
        param_str = '&' + param_str
        url = url + param_str
        return url

