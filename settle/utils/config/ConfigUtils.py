import os

from settle.pojo.type.ConfigType import ConfigType


class ConfigUtils:
    static_config_dir: str = None

    @staticmethod
    def get_env():
        return "stg"

    @staticmethod
    def get_config_dir() -> str:
        if ConfigUtils.static_config_dir is not None:
            return ConfigUtils.static_config_dir
        current_dir = os.path.abspath(os.path.dirname(__file__))
        current_dir = os.path.abspath(os.path.dirname(current_dir))
        current_dir = os.path.abspath(os.path.dirname(current_dir))
        ConfigUtils.static_config_dir = current_dir
        return current_dir

    @staticmethod
    def get_config_content(config_type: ConfigType) -> str:
        env = ConfigUtils.get_env()
        project_dir = ConfigUtils.get_config_dir()
        if config_type == ConfigType.EXCHANGE:
            return ConfigUtils.load(project_dir + ConfigType.EXCHANGE.value.format(env))
        if config_type == ConfigType.DOMAIN:
            return ConfigUtils.load(project_dir + ConfigType.DOMAIN.value.format(env))
        if config_type == ConfigType.CASE_GROUP_LIST:
            return ConfigUtils.load(project_dir + ConfigType.CASE_GROUP_LIST.value.format(env))
        if config_type == ConfigType.JDBC:
            return ConfigUtils.load(project_dir + ConfigType.JDBC.value.format(env))

    @staticmethod
    def get_case_group_users(group_id: str):
        env = ConfigUtils.get_env()
        project_dir = ConfigUtils.get_config_dir()
        return ConfigUtils.load(project_dir + ConfigType.USERS.value.format(env, group_id))

    @staticmethod
    def get_symbols(group_id: str):
        env = ConfigUtils.get_env()
        project_dir = ConfigUtils.get_config_dir()
        return ConfigUtils.load(project_dir + ConfigType.SYMBOLS.value.format(env, group_id))

    @staticmethod
    def get_case_group_case_run_list(group_id: str):
        env = ConfigUtils.get_env()
        project_dir = ConfigUtils.get_config_dir()
        return ConfigUtils.load(project_dir + ConfigType.CASE_RUN_LIST.value.format(env, group_id))

    @staticmethod
    def get_group_run_case(group_id: str, case_id: str):
        env = ConfigUtils.get_env()
        project_dir = ConfigUtils.get_config_dir()
        return ConfigUtils.load(project_dir + ConfigType.CASE.value.format(env, group_id, case_id))

    @staticmethod
    def load(file_path: str) -> str:
        with open(file_path, "r") as f:
            json_str = f.read()
            f.close()
            return json_str
