from ecoinfra.apis import BAPI

import logging
_logger = logging.getLogger(__name__)

class OpenAI(BAPI):
    BASE_URL = "https://api.openai.com/v1"
    def _headers(self, header_kwargs):
        headers = {"Content-Type": "application/json"}
        headers.update(super()._headers(header_kwargs))
        return headers


class Chat:
    def __init__(self, api, system_prompt, model="gpt-4-turbo"):
        self.api = api
        self.model = model
        self.messages = [{'role': 'system', 'content': system_prompt}]

    def _post_raw(self, message, role, **kwargs):
        msg = {"role": role, "content": message}
        messages = self.messages + [msg]
        json_data = {
            "model": self.model,
            "messages": messages,
            **kwargs
        }
        result = self.api.post("chat/completions", json=json_data)
        return result

    def post(self, message, role="user", **kwargs):
        result = self._post_raw(message, role, **kwargs)
        _logger.info(result['usage'])
        return result['choices'][0]['message']['content']
