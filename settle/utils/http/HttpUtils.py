import requests


class HttpUtils:

    @staticmethod
    def https_protocol_format(host: str, path: str) -> str:
        return "https://{}{}".format(host, path)

    @staticmethod
    def http_protocol_format(host: str, path: str) -> str:
        return "http://{}{}".format(host, path)

    @staticmethod
    def get(url: str, params=None, headers=None) -> str:
        if params is None:
            params = {}
        return requests.get(url, params, headers=headers).content

    @staticmethod
    def delete(url: str, params=None, headers=None) -> str:
        if params is None:
            params = {}
        return requests.delete(url, params=params, headers=headers).content

    @staticmethod
    def post(url: str, params=None, body=None, headers=None) -> str:
        if params is None:
            params = {}
        if body is None:
            body = {}
        return requests.post(url, data=params, json=body, headers=headers).content
