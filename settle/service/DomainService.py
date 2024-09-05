from settle.pojo.type.ConfigType import ConfigType
from settle.utils.config.ConfigUtils import ConfigUtils
from settle.utils.json.JsonUtils import JsonUtils


class DomainService:

    def __init__(self):
        self.domain_dict: dict[str, str] = JsonUtils.of(ConfigUtils.get_config_content(ConfigType.DOMAIN))

    def get_open_api_domain(self):
        return self.domain_dict['open_api_domain']
