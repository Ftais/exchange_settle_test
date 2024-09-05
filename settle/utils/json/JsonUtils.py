import json


class JsonUtils:

    @staticmethod
    def dict_to_json(obj: dict):
        return json.dumps(obj)

    @staticmethod
    def to_json(obj: object):
        return json.dumps(obj.__dict__)

    @staticmethod
    def list_to_json(obj: list):
        return json.dumps(obj)

    @staticmethod
    def from_json(body: str, clazz):
        return json.loads(body, object_hook=clazz)

    @staticmethod
    def of(body: str):
        return json.loads(body)
