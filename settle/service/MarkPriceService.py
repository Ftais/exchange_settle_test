from decimal import Decimal

from settle.utils.http.HttpUtils import HttpUtils
from settle.utils.json.JsonUtils import JsonUtils


class MarkPriceService:
    url_path = '/quote/v1/markPrice'

    @staticmethod
    def get_mark_price(domain: str, symbol_id: str) -> Decimal:
        url = HttpUtils.http_protocol_format(domain, MarkPriceService.url_path)
        params = {'symbol': symbol_id}
        ret = JsonUtils.of(HttpUtils.get(url, params))
        return Decimal(ret['price'])
