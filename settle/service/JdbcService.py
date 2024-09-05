from settle.pojo.jdbc.JdbcConfig import JdbcConfig
from settle.pojo.type.ConfigType import ConfigType
from settle.utils.config.ConfigUtils import ConfigUtils
from settle.utils.json.JsonUtils import JsonUtils
from utils.mysql_pool import Mysql


class JdbcService:
    schema_dict: dict[str, JdbcConfig] = {}

    conn_dict: dict[str, Mysql] = {}

    def __init__(self):
        jdbc_list: list[JdbcConfig] = JsonUtils.from_json(ConfigUtils.get_config_content(ConfigType.JDBC), JdbcConfig)
        for jdbc in jdbc_list:
            self.schema_dict[jdbc.schema] = jdbc
        conn_dict: dict[str, Mysql] = {}

    def conn(self, schema: str) -> Mysql:
        if schema in self.conn_dict:
            return self.conn_dict[schema]
        if schema in self.schema_dict:
            jdbc_config = self.schema_dict[schema]
            conn = Mysql(jdbc_config.host, jdbc_config.port, jdbc_config.user, jdbc_config.password, jdbc_config.schema)
            self.conn_dict[schema] = conn
            return conn
        raise ValueError("jdbc连接没有配置 schema : " + schema)
