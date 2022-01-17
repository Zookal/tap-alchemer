# tap-alchemer

Previously known as SurgyGizmo, the rebranded survey company are most used for NPS data.

Alchemer dates are on EDT, this tap converts them to UTC.

# Streams

Just a few entities had being included in this tap.

| entity | description |
| ------ | ----------- |
| survey | Survey attributes and setup  |
| survey_question | Questions used in the survey |
| survey_response | Attributes for the Response of the survey |
| survey_response_data | Response for each question |

Some data had being flattened to simplify reporting.

There is no discover catalog, as the catalog is simple and stream are not configurable in this release.

## Incremental Load (state)

`survey` and `survey_response` are incremental loaded.

## Installation

```bash
# download this package locally
pip install .

#or 
pip install https://github.com/Zookal/tap-alchemer/archives/master.zip
```

## Configuration

This tap requires a `config.json` with the token for Alchemer. See [sample_config.json](sample_config.json) for an example.

Domain configuration are dependant of you account creation from Alchemer, see more details [API domain](https://apihelp.alchemer.com/help/us-eu-or-ca-api)

```json
{
  "api_token": "",
  "api_token_secret": "",,
  "domain":  "api.alchemer.com" 
}
```

To run `tap-alchmer` with the configuration file, use this command:

```bash
tap-alchemer -c config.json -s state.json
```

### Quick shortcuts for local development
```bash
export PYTHONPATH=$(pwd):$PYTHONPATH
python tap_alchemer/__init__.py -c config.json -s state.json
```
### TODO
* publish on PIP
* add other streams like campaign and contact  
