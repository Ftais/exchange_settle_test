from decimal import Decimal

from settle.utils.http.HttpUtils import HttpUtils
from settle.utils.json.JsonUtils import JsonUtils


class TickerPriceService:
    url_path = '/quote/v1/ticker/price'

    @staticmethod
    def get_ticker_price(domain: str, symbol_id: str) -> Decimal:
        url = HttpUtils.http_protocol_format(domain, TickerPriceService.url_path)
        params = {'symbol': symbol_id}
        ret = JsonUtils.of(HttpUtils.get(url, params))
        return Decimal(ret[0]['p'])
