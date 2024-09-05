import uuid

from settle.pojo.case.PlaceOrder import PlaceOrder
from settle.pojo.shard.Order import Order
from settle.pojo.user.User import User
from settle.service.DomainService import DomainService
from settle.utils.http.ApiUtils import ApiUtils
from settle.utils.http.HttpUtils import HttpUtils
from settle.utils.json.JsonUtils import JsonUtils


class PlaceOrderBiz:
    futures_order_url = "/api/v1/futures/order"
    futures_open_order_url = '/api/v1/futures/openOrders'
    futures_cancel_side_order_url = '/api/v1/futures/batchOrders'
    spot_order_url = "/api/v1/spot/order"

    def __init__(self, domain_service: DomainService):
        self.domain_service = domain_service

    def spot_place(self, order: PlaceOrder, user: User) -> Order:
        params = self.spot_build_params(order)
        place_params = {k: v for k, v in params.items() if v is not None}
        print("下单请求 {}".format(place_params))
        ret = ApiUtils.post(
            HttpUtils.https_protocol_format(self.domain_service.get_open_api_domain(), self.spot_order_url),
            user.apiKey,
            user.secretKey,
            place_params,
            {}
        )
        print("下单结果 {}".format(ret))
        placed_order: Order = JsonUtils.from_json(ret, Order)
        placed_order.orderId = int(placed_order.orderId)
        return placed_order

    def futures_place(self, order: PlaceOrder, user: User) -> Order:
        params = self.futures_build_params(order)
        place_params = {k: v for k, v in params.items() if v is not None}
        print("下单请求 {}".format(place_params))
        ret = ApiUtils.post(
            HttpUtils.https_protocol_format(self.domain_service.get_open_api_domain(), self.futures_order_url),
            user.apiKey,
            user.secretKey,
            place_params,
            {}
        )
        print("下单结果 {}".format(ret))
        placed_order: Order = JsonUtils.from_json(ret, Order)
        if placed_order.orderId is not None:
            placed_order.orderId = int(placed_order.orderId)
        return placed_order

    def spot_build_params(self, order: PlaceOrder) -> dict:
        client_order_id = uuid.uuid4()
        if order.clientOrderId is not None:
            client_order_id = order.clientOrderId
        params = {'symbol': order.symbol, 'side': order.side, 'type': order.type, 'price': str(order.price),
                  'quantity': str(order.quantity),
                  'timestamp': 0, 'clientOrderId': client_order_id}
        if order.priceType == 'MARKET' or order.type == 'MARKET':
            params['price'] = None
        order.clientOrderId = params['clientOrderId']
        return params

    def futures_build_params(self, order: PlaceOrder) -> dict:
        client_order_id = uuid.uuid4()
        if order.clientOrderId is not None:
            client_order_id = order.clientOrderId
        params = {'symbol': order.symbol, 'side': order.side, 'type': order.type, 'price': str(order.price),
                  'quantity': str(order.quantity),
                  'timestamp': 0, 'timeInForce': order.timeInForce, 'priceType': order.priceType,
                  'clientOrderId': client_order_id}
        if order.priceType == 'MARKET':
            params['price'] = None
        order.clientOrderId = params['clientOrderId']
        return params

    def futures_cancel(self, order: Order, user: User) -> Order:
        params = {'orderId': order.orderId, "type": order.type}
        print("撤单请求 {}".format(params))
        ret = ApiUtils.delete(
            HttpUtils.https_protocol_format(self.domain_service.get_open_api_domain(), self.futures_order_url),
            user.apiKey,
            user.secretKey,
            params,
            {}
        )
        print("撤单结果 {}".format(ret))
        cancel_order: Order = JsonUtils.from_json(ret, Order)
        return cancel_order

    def spot_cancel(self, order: Order, user: User) -> Order:
        params = {'orderId': order.orderId, "type": order.type}
        print("撤单请求 {}".format(params))
        ret = ApiUtils.delete(
            HttpUtils.https_protocol_format(self.domain_service.get_open_api_domain(), self.spot_order_url),
            user.apiKey,
            user.secretKey,
            params,
            {}
        )
        print("撤单结果 {}".format(ret))
        cancel_order: Order = JsonUtils.from_json(ret, Order)
        return cancel_order

    def futures_open_orders(self, symbol_id, user: User) -> list[Order]:
        params = {'symbol': symbol_id, "type": 'LIMIT'}
        ret = ApiUtils.get(
            HttpUtils.https_protocol_format(self.domain_service.get_open_api_domain(), self.futures_open_order_url),
            user.apiKey,
            user.secretKey,
            params,
            {}
        )
        print(ret)
        return JsonUtils.from_json(ret, Order)

    def futures_cancel_orders(self, user: User, symbol_id: str, side: str):
        params = {'symbol': symbol_id, "side": side}
        print("批量撤单请求 {}".format(params))
        ret = ApiUtils.delete(
            HttpUtils.https_protocol_format(self.domain_service.get_open_api_domain(),
                                            self.futures_cancel_side_order_url),
            user.apiKey,
            user.secretKey,
            params,
            {}
        )
        print("批量撤单结果 {}".format(ret))

    def spot_cancel_orders(self, user: User, symbol_id: str, side: str):
        params = {'symbol': symbol_id, "side": side}
        print("批量撤单请求 {}".format(params))
        ret = ApiUtils.delete(
            HttpUtils.https_protocol_format(self.domain_service.get_open_api_domain(),
                                            self.futures_cancel_side_order_url),
            user.apiKey,
            user.secretKey,
            params,
            {}
        )
        print("批量撤单结果 {}".format(ret))
