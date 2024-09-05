import json

from settle.pojo.exchange.ExchangeOrder import ExchangeOrder
from settle.pojo.exchange.ExchangePosition import ExchangePosition
from settle.pojo.type.ConfigType import ConfigType
from settle.utils.config.ConfigUtils import ConfigUtils
from settle.utils.http.HttpUtils import HttpUtils
from settle.utils.json.JsonUtils import JsonUtils


class ExchangeService:
    body: dict = None

    spot_addresses: list = None

    futures_addresses: list = None

    url_info = "/v1/engine/status"

    url_ca = "/v1/engine/market/ca"

    url_positions = "/v1/engine/position/info"

    url_insure_fund = "/v1/engine/futures/fund"

    url_orders = "/v1/engine/bos"

    def __init__(self):
        self.body = json.loads(ConfigUtils.get_config_content(ConfigType.EXCHANGE))
        if 'spot' in self.body:
            self.spot_addresses = self.body['spot']['address']
        if 'futures' in self.body:
            self.futures_addresses = self.body['futures']['address']

    def get_master_node(self, type: str) -> str:
        if type == 'spot':
            for address in self.spot_addresses:
                ret = json.loads(HttpUtils.get(HttpUtils.http_protocol_format(address, self.url_info)))
                if ret['data']:
                    return address
        if type == 'futures':
            for address in self.futures_addresses:
                ret = json.loads(HttpUtils.get(HttpUtils.http_protocol_format(address, self.url_info)))
                if ret['data']:
                    return address

    """
    一次最多撤200单
    """

    def cancel_all_order_in_exchange(self, symbol_id: str, type: str):
        address = self.get_master_node(type)
        body = {'symbol_id': symbol_id, 'exchange_id': 301}
        return HttpUtils.post(HttpUtils.http_protocol_format(address, self.url_ca), None, body)

    def get_positions(self, symbol_id: str):
        address = self.get_master_node('futures')
        body = {'symbol_id': symbol_id, 'exchange_id': 301, 'is_reverse': False, 'dump_scale': 18}
        return JsonUtils.from_json(
            HttpUtils.post(HttpUtils.http_protocol_format(address, self.url_positions), None, body), ExchangePosition)

    def get_insure_fund(self):
        address = self.get_master_node('futures')
        return json.loads(HttpUtils.post(HttpUtils.http_protocol_format(address, self.url_insure_fund), None, None))

    """
    buy:0 sell:1
    {"status":200, "err":"", "data":{"bitField0_":0,"bookOrders_":[{"orderId_":1723241221554521600,"price_":"85000.000000000000000000","quantity_":"120.000000000000000000","amount_":"10200000.000000000000000000","accountId_":1710237525451354624,"brokerUserId_":"","brokerId_":9001,"brokerName_":"","exchangeId_":301,"matchExchangeId_":0,"memoizedIsInitialized":1,"unknownFields":{"fields":{}},"memoizedSize":-1,"memoizedHashCode":0}],"responseCode_":0,"memoizedIsInitialized":1,"unknownFields":{"fields":{}},"memoizedSize":-1,"memoizedHashCode":0}}
    """

    def get_futures_orders_by_side(self, symbol_id: str, side: int) -> list[ExchangeOrder]:
        address = self.get_master_node('futures')
        body = {'symbol_id': symbol_id, 'exchange_id': 301, 'side': side}
        ret: dict = json.loads(HttpUtils.post(HttpUtils.http_protocol_format(address, self.url_orders), None, body))
        ret: list = ret['data']['bookOrders_']
        order_book: list = []
        for e in ret:
            order_book.append(ExchangeOrder(e))
        return order_book

    def get_spot_orders_by_side(self, symbol_id: str, side: int) -> list[ExchangeOrder]:
        address = self.get_master_node('spot')
        body = {'symbol_id': symbol_id, 'exchange_id': 301, 'side': side}
        ret: dict = json.loads(HttpUtils.post(HttpUtils.http_protocol_format(address, self.url_orders), None, body))
        ret: list = ret['data']['bookOrders_']
        order_book: list = []
        for e in ret:
            order_book.append(ExchangeOrder(e))
        return order_book
