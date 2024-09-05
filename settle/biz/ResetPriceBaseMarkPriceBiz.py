from decimal import Decimal

from settle.biz.PlaceOrderBiz import PlaceOrderBiz
from settle.pojo.case.PlaceOrder import PlaceOrder
from settle.pojo.case.ResetPriceBaseMarkPrice import ResetPriceBaseMarkPrice
from settle.pojo.case.Symbol import Symbol
from settle.pojo.user.UserContext import UserContext
from settle.service.DomainService import DomainService
from settle.service.MarkPriceService import MarkPriceService


class ResetPriceBaseMarkPriceBiz:

    def __init__(self, place_order_biz: PlaceOrderBiz, domain_service: DomainService):
        self.place_order_biz = place_order_biz
        self.domain_service = domain_service

    def execute(self, action: ResetPriceBaseMarkPrice, user_tag_to_user_dict: dict[str, UserContext],
                symbol_tag_to_symbol_dict: dict[str, Symbol]):
        symbol_id = symbol_tag_to_symbol_dict[action.symbol_tag].symbol_id
        mark_price = MarkPriceService.get_mark_price(self.domain_service.get_open_api_domain(),
                                                     symbol_id)
        price = Decimal(int(mark_price / action.price_mod)) * action.price_mod + action.price_offset
        order: PlaceOrder = PlaceOrder()
        order.symbol = symbol_id
        order.side = 'BUY_OPEN'
        order.type = 'LIMIT'
        order.price = price
        order.quantity = 1
        self.place_order_biz.futures_place(order, user_tag_to_user_dict[action.maker_uid_tag].user)
        order: PlaceOrder = PlaceOrder()
        order.symbol = symbol_id
        order.side = 'SELL_OPEN'
        order.type = 'LIMIT'
        order.price = price
        order.quantity = 1
        self.place_order_biz.futures_place(order, user_tag_to_user_dict[action.taker_uid_tag].user)
