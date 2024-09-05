from decimal import Decimal

from settle.pojo.trade.MarketInfo import MarketInfo
from settle.service.DomainService import DomainService
from settle.utils.http.HttpUtils import HttpUtils
from settle.utils.json.JsonUtils import JsonUtils


class MarketBiz:
    url = '/api/v1/exchangeInfo'

    def __init__(self, domain_service: DomainService):
        self.domain_service = domain_service

    def get_market_filter(self, symbol_id) -> MarketInfo:
        exchange_info = JsonUtils.of(
            HttpUtils.get(HttpUtils.http_protocol_format(self.domain_service.get_open_api_domain(), self.url)))
        market_info = MarketInfo()
        for contract in exchange_info['contracts']:
            if contract['symbol'] == symbol_id:
                filters: list = contract['filters']
                for filter in filters:
                    if 'minPrice' in filter:
                        market_info.minPrice = filter['minPrice']
                    if 'tickSize' in filter:
                        market_info.tickSize = filter['tickSize']
                market_info.contractMultiplier = Decimal(contract['contractMultiplier'])
        return market_info
