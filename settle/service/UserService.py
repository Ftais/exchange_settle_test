import json

from settle.pojo.user.User import User
from settle.utils.config.ConfigUtils import ConfigUtils
from settle.utils.json.JsonUtils import JsonUtils


class UserService:

    @staticmethod
    def load_user_config(group_id: int) -> dict[int, User]:
        array: list = json.loads(ConfigUtils.get_case_group_users(group_id))
        users: dict[int, User] = {}
        for body in array:
            users[body['uid']] = JsonUtils.from_json(JsonUtils.dict_to_json(body), User)
        return users
