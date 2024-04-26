import requests
import json

class BAPI:
    BASE_URL = None
    def __init__(self, token, **header_kwargs):
        self.token = token
        self.headers = self._headers(header_kwargs)

    def _headers(self, header_kwargs):
        headers = {"Authorization": f"Bearer {self.token}"}
        headers.update(header_kwargs)
        return headers

    def _do_request(self, func, endpoint, **kwargs):
        if not self.BASE_URL:
            raise NotImplementedError(f"Class {self.__class__.__name__} "
                                      "missing BASE_URL attribute.")

        endpoint_url = f"{self.BASE_URL}/{endpoint}"
        headers = self.headers
        # log url, headers, kwargs
        resp = func(endpoint_url, headers=headers, **kwargs)
        if not resp.ok:
            raise RuntimeError(f"Error in API call for {endpoint_url}: "
                               f"{resp.content}")
        else:
            return resp.json()

    def post(self, endpoint, **kwargs):
        return self._do_request(
            func=requests.post,
            endpoint=endpoint,
            **kwargs
        )

    def get(self, endpoint, **kwargs):
        return self._do_request(
            func=requests.get,
            endpoint=endpoint,
            **kwargs
        )

