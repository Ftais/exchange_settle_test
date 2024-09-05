from settle.pojo.user.User import User
from settle.service.DomainService import DomainService
from settle.utils.http.ApiUtils import ApiUtils
from settle.utils.http.HttpUtils import HttpUtils
from settle.utils.json.JsonUtils import JsonUtils


class LeverageBiz:
    url = '/api/v1/futures/leverage'

    def __init__(self, domain_service: DomainService):
        self.domain_service = domain_service

    """
    [{"symbolId":"BTC-SWAP-USDT","leverage":"8","marginType":"CROSS"}]
    """

    def get_user_leverage(self, user: User, symbol_id) -> int:
        params = {'symbol': symbol_id}
        ret = JsonUtils.of(
            ApiUtils.get(HttpUtils.https_protocol_format(self.domain_service.get_open_api_domain(), self.url),
                         user.apiKey, user.secretKey, params))
        return int(ret[0]['leverage'])
