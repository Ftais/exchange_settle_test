import copy
import traceback
from decimal import Decimal, ROUND_FLOOR, ROUND_UP, ROUND_DOWN

from settle.biz.LeverageBiz import LeverageBiz
from settle.biz.ShardRouteQueryBiz import ShardRouteQueryBiz
from settle.pojo.case.Case import Case
from settle.pojo.case.DecimalAccuracy import DecimalAccuracy
# from settle.pojo.case.DecimalAccuracy import DecimalAccuracy
from settle.pojo.case.PlaceOrder import PlaceOrder
from settle.pojo.case.PredictTradeDetail import PredictTradeDetail
from settle.pojo.case.Symbol import Symbol
from settle.pojo.case.TotalTrade import TotalTrade
from settle.pojo.exchange.ExchangeOrder import ExchangeOrder
from settle.pojo.exchange.ExchangePosition import ExchangePosition
from settle.pojo.fee.FeeRate import FeeRate
from settle.pojo.shard.Balance import Balance
from settle.pojo.shard.BalanceFuturesPosition import BalanceFuturesPosition
from settle.pojo.shard.TbOrder import TbOrder
from settle.pojo.shard.TradeDetail import TradeDetail
from settle.pojo.shard.TradeDetailFutures import TradeDetailFutures
from settle.pojo.type.CaseActionType import CaseActionType
from settle.pojo.type.OrderStatusType import OrderStatusType
from settle.pojo.user.User import User
from settle.pojo.user.UserContext import UserContext
from settle.service.DomainService import DomainService
from settle.service.ExchangeService import ExchangeService
from settle.utils.retry.NeedRetryException import NeedRetryException
from settle.utils.retry.RetryDriver import RetryDriver


class FuturesSettleCheckDriver:
    domain_service: DomainService = None

    leverage_biz: LeverageBiz = None

    symbol_dict: dict[str, Symbol] = None

    shard_route_query_biz: ShardRouteQueryBiz = None

    exchange_service: ExchangeService = None

    DecimalAccuracy

    def __init__(self, domain_service: DomainService, leverage_biz: LeverageBiz, symbol_dict: dict[str, Symbol],
                 shard_route_query_biz: ShardRouteQueryBiz, exchange_service: ExchangeService):
        self.domain_service = domain_service
        self.leverage_biz: LeverageBiz = leverage_biz
        self.symbol_dict: dict[str, Symbol] = symbol_dict
        self.shard_route_query_biz: ShardRouteQueryBiz = shard_route_query_biz
        self.exchange_service = exchange_service

    def check(self, predict_trade_details: list[PredictTradeDetail], case: Case,
              user_context_dict: dict[int, UserContext]):
        self.load_user_info(user_context_dict)
        order_action_dict: dict[int, PlaceOrder] = self.mapping_order(case)
        RetryDriver.retry(
            lambda: self.retry_check_wrapper(predict_trade_details, case, user_context_dict, order_action_dict))

    def retry_check_wrapper(self, predict_trade_details: list[PredictTradeDetail], case: Case,
                            user_context_dict: dict[int, UserContext], order_action_dict: dict[int, PlaceOrder]):
        try:
            self.clear_user_trade(user_context_dict)
            for predict_trade_detail in predict_trade_details:
                self.check_trade_detail(predict_trade_detail, case, user_context_dict, order_action_dict)
            self.update_user_total_order(user_context_dict, order_action_dict)
            tb_orders: list[TbOrder] = self.check_order_tail(user_context_dict, order_action_dict,
                                                             predict_trade_details, case)
            self.check_trade_tail(case, user_context_dict)
            self.compare_with_match_position(user_context_dict)
            self.compare_with_match_order(tb_orders)
        except Exception as e:
            traceback.print_exc()
            raise NeedRetryException(e, "FuturesSettleCheckDriver.retry_check_wrapper")

    """
    查全
    但是返回值是个b'' 转成dict之后，字段变成了float，精度丢失
    """

    def compare_with_match_order(self, orders: list[TbOrder]):
        print('比对撮合订单')
        symbol_dict = set()
        for order in orders:
            symbol_dict.add(order.symbol_id)
        order_book_dict_1 = dict()
        order_book_dict_0 = dict()
        for symbol_id in symbol_dict:
            order_book: list = self.exchange_service.get_futures_orders_by_side(symbol_id, 1)
            order_book_dict = {}
            for order in order_book:
                order_book_dict[order.order_id] = order
            order_book_dict_1[symbol_id] = order_book_dict

            order_book: list = self.exchange_service.get_futures_orders_by_side(symbol_id, 0)
            order_book_dict = {}
            for order in order_book:
                order_book_dict[order.order_id] = order
            order_book_dict_0[symbol_id] = order_book_dict

        for order in orders:
            order_book_dict: dict = None
            if order.side == 0:
                order_book_dict: dict = order_book_dict_0[order.symbol_id]
            else:
                order_book_dict: dict = order_book_dict_1[order.symbol_id]
            if OrderStatusType.is_in_exchange(order.status):
                assert order.order_id in order_book_dict, '非完单 order_id={} 不在撮合里面，不符合预期'
                exchange_order: ExchangeOrder = order_book_dict[order.order_id]
                assert (order.quantity - order.executed_quantity) == exchange_order.quantity, '{} {}'.format(
                    order.quantity,
                    exchange_order.quantity)
                assert order.account_id == exchange_order.account_id
                assert order.price == exchange_order.price
            else:
                assert order.order_id not in order_book_dict, '完单 order_id={} 在撮合里面，不符合预期'

    def compare_with_match_position(self, user_context_dict: dict[int, UserContext]):
        print('比对撮合仓位')
        in_exchange_dict = {}
        for symbol_id, symbol in self.symbol_dict.items():
            ret = self.exchange_service.get_positions(symbol_id)
            data = ret.data
            in_exchange_dict[symbol_id] = data
        for uid, user_context in user_context_dict.items():
            for symbol_id, position in user_context.after_position_long_dict.items():
                if symbol_id not in self.symbol_dict:
                    continue
                # 撮合，就算为0，应该也是没有释放
                key = ExchangePosition.format_key(user_context.user.futuresAccountId, symbol_id, "true")
                in_exchange: dict = in_exchange_dict[symbol_id].__dict__
                if key not in in_exchange and position.total == Decimal(0):
                    continue
                assert key in in_exchange, '撮合里面不存在该仓位 {}'.format(key)
                data = in_exchange[key]
                assert data.total == position.total, '撮合比对total不一致 {} {} {}'.format(key, data.total,
                                                                                           position.total)
                assert data.open_value.quantize(Decimal('0.001'), ROUND_UP) == position.open_value.quantize(
                    Decimal('0.001'), ROUND_UP), '撮合比对open_value不一致 {} {} {}'.format(key,
                                                                                            data.open_value.quantize(
                                                                                                Decimal('0.0001'),
                                                                                                ROUND_UP),
                                                                                            position.open_value.quantize(
                                                                                                Decimal('0.0001'),
                                                                                                ROUND_UP))
                assert data.margin.quantize(Decimal('0.001'), ROUND_FLOOR) == position.margin.quantize(
                    Decimal('0.001'),
                    ROUND_FLOOR), '撮合比对margin不一致'
            for symbol_id, position in user_context.after_position_short_dict.items():
                if symbol_id not in self.symbol_dict:
                    continue
                # 撮合，就算为0，应该也是没有释放
                key = ExchangePosition.format_key(user_context.user.futuresAccountId, symbol_id, "false")
                in_exchange: dict = in_exchange_dict[symbol_id].__dict__
                if key not in in_exchange and position.total == Decimal(0):
                    continue
                assert key in in_exchange, '撮合里面不存在该仓位 {}'.format(key)
                data = in_exchange[key]
                assert data.total == position.total, '撮合比对total不一致 {} {}'.format(data.total, position.total)
                assert data.open_value.quantize(Decimal('0.001'), ROUND_UP) == position.open_value.quantize(
                    Decimal('0.001'), ROUND_UP), '撮合比对open_value不一致 {} {}'.format(
                    data.open_value.quantize(Decimal('0.001'), ROUND_UP), position.open_value.quantize(
                        Decimal('0.001'), ROUND_UP))
                assert data.margin.quantize(Decimal('0.001'), ROUND_FLOOR) == position.margin.quantize(
                    Decimal('0.001'),
                    ROUND_FLOOR), '撮合比对margin不一致'

    def check_order_tail(self, user_context_dict: dict[int, UserContext], order_action_dict: dict[int, PlaceOrder],
                         predict_trade_details: list[PredictTradeDetail], case: Case) -> list[TbOrder]:

        print('检查订单相关')

        for related_id, order_action in order_action_dict.items():
            if order_action is not None and order_action.cancelId == -1:
                order_action.trade_quantity = 0
                order_action.status = None

        for predict_trade_detail in predict_trade_details:
            taker_related_id = predict_trade_detail.taker_id
            maker_related_id = predict_trade_detail.maker_id
            quantity = predict_trade_detail.quantity
            order_action_dict[taker_related_id].trade_quantity = order_action_dict[
                                                                     taker_related_id].trade_quantity + quantity
            order_action_dict[maker_related_id].trade_quantity = order_action_dict[
                                                                     maker_related_id].trade_quantity + quantity

        uid_to_related_id_dict = {}

        for related_id, order_action in order_action_dict.items():
            if order_action is not None and order_action.cancelId == -1:
                if order_action.uid not in uid_to_related_id_dict:
                    uid_to_related_id_dict[order_action.uid] = []
                uid_to_related_id_dict[order_action.uid].append(order_action.id)
                assert order_action.quantity >= order_action.trade_quantity, '成交数大于下单数'
                if order_action.trade_quantity == Decimal(0):
                    if order_action.type == 'LIMIT' and (
                            order_action.timeInForce is None or order_action.timeInForce == 'GTC' or order_action.timeInForce == 'LIMIT_MAKER'):
                        order_action.status = OrderStatusType.NEW.value
                    else:
                        order_action.status = OrderStatusType.CANCELED.value
                    continue
                if order_action.quantity == order_action.trade_quantity:
                    order_action.status = OrderStatusType.FILLED.value
                    continue
                if order_action.priceType == 'MARKET':
                    order_action.status = OrderStatusType.PARTIALLY_CANCELED.value
                    continue
                if order_action.timeInForce == 'IOC':
                    order_action.status = OrderStatusType.PARTIALLY_CANCELED.value
                    continue
                if order_action.timeInForce == 'FOK':
                    order_action.status = OrderStatusType.CANCELED.value
                else:
                    order_action.status = OrderStatusType.PARTIALLY_FILLED.value

        # 撤单识别
        for case_action in case.case_actions:
            if case_action.case_action_type == CaseActionType.ORDER:
                order_action = case_action.order_action
                if order_action is not None and order_action.cancelId != -1:
                    place_order_action = order_action_dict[order_action.cancelId]
                    if place_order_action.trade_quantity != Decimal(0):
                        place_order_action.status = OrderStatusType.PARTIALLY_CANCELED.value
                    else:
                        place_order_action.status = OrderStatusType.CANCELED.value

        order_action_mapping = []

        for uid, related_id_list in uid_to_related_id_dict.items():
            user_context = user_context_dict[uid]
            order_id_list = []
            order_dict = {}
            for related_id in related_id_list:
                order_id_list.append(user_context.get_order_by_id(related_id).orderId)
                order_dict[user_context.get_order_by_id(related_id).orderId] = related_id
            order_list = self.load_user_order(user_context, order_id_list)
            for order in order_list:
                order_action_mapping.append(order)
                order_action = order_action_dict[order_dict[order.order_id]]
                assert order.status == order_action.status, '{} {}'.format(order.status, order_action.status)
                assert order.executed_quantity == order_action.trade_quantity
                assert order.quantity == order_action.quantity
                assert order.price == order_action.price
                assert order.account_id == user_context.user.futuresAccountId
                if order_action.priceType != 'MARKET' or order.is_close != 1:
                    assert order.price == order_action.price
                if OrderStatusType.is_canceled(order.status):
                    diff_quantity = order.quantity - order.executed_quantity
                    price = order.price
                    if order.is_close == 0:
                        total_trade = None
                        if order.side == 0:
                            if order.symbol_id not in user_context.user_total_long_trade:
                                total_trade = TotalTrade()
                                user_context.user_total_long_trade[order.symbol_id] = total_trade
                            total_trade = user_context.user_total_long_trade[order.symbol_id]
                        else:
                            if order.symbol_id not in user_context.user_total_short_trade:
                                total_trade = TotalTrade()
                                user_context.user_total_short_trade[order.symbol_id] = total_trade
                            total_trade = user_context.user_total_short_trade[order.symbol_id]
                        contract_multiplier: Decimal = self.get_contract_multiplier(order.symbol_id)
                        leverage: Decimal = Decimal(user_context.symbol_leverage_dict[order.symbol_id])
                        margin_changed = self.cal_margin_changed_for_open(leverage, price, contract_multiplier,
                                                                          diff_quantity, order_action)
                        total_trade.balance_avb_changed = total_trade.balance_avb_changed + margin_changed
                        total_trade.balance_locked_changed = total_trade.balance_locked_changed - margin_changed
                    else:
                        if order.side == 1:
                            if order.symbol_id not in user_context.user_total_long_trade:
                                total_trade = TotalTrade()
                                user_context.user_total_long_trade[order.symbol_id] = total_trade
                            total_trade = user_context.user_total_long_trade[order.symbol_id]
                        else:
                            if order.symbol_id not in user_context.user_total_short_trade:
                                total_trade = TotalTrade()
                                user_context.user_total_short_trade[order.symbol_id] = total_trade
                            total_trade = user_context.user_total_short_trade[order.symbol_id]
                        total_trade.position_locked_changed = total_trade.position_locked_changed - diff_quantity
                        total_trade.position_avb_changed = total_trade.position_avb_changed + diff_quantity
        return order_action_mapping

    def check_trade_tail(self, case: Case, user_context_dict: dict[int, UserContext]):
        print('比对最终资产和仓位情况')
        s = set()
        for case_action in case.case_actions:
            if case_action.order_action is not None and case_action.order_action.cancelId == -1:
                s.add(case_action.order_action.uid)
        for uid in s:
            user_context = user_context_dict[uid]
            self.check_user_tail(user_context)

    def check_user_tail(self, user_context: UserContext):
        after_futures_balance = self.load_user_futures_balance(user_context)
        (after_position_long_dict, after_position_short_dict) = self.load_user_position(user_context)
        before_futures_balance: Balance = copy.deepcopy(user_context.futures_balance)
        before_position_long_dict = copy.deepcopy(user_context.position_long_dict)
        before_position_short_dict = copy.deepcopy(user_context.position_short_dict)

        symbol_set = set()

        for symbol_id, total_trade, in user_context.user_total_long_trade.items():
            self.chase_balance(total_trade, before_futures_balance)
            if symbol_id not in before_position_long_dict:
                before_position_long = self.init_position()
                before_position_long_dict[symbol_id] = before_position_long
            self.chase_position(total_trade, before_position_long_dict[symbol_id])
            symbol_set.add(symbol_id)

        for symbol_id, total_trade, in user_context.user_total_short_trade.items():
            self.chase_balance(total_trade, before_futures_balance)
            if symbol_id not in before_position_short_dict:
                before_position_short = self.init_position()
                before_position_short_dict[symbol_id] = before_position_short
            self.chase_position(total_trade, before_position_short_dict[symbol_id])
            symbol_set.add(symbol_id)

        self.check_user_balance_tail(before_futures_balance, after_futures_balance, user_context)
        self.check_user_position_tail(symbol_set, before_position_long_dict, after_position_long_dict, user_context)
        self.check_user_position_tail(symbol_set, before_position_short_dict, after_position_short_dict, user_context)
        user_context.after_position_long_dict = after_position_long_dict
        user_context.after_position_short_dict = after_position_short_dict

    def check_user_balance_tail(self, before_futures_balance: Balance, after_futures_balance: Balance,
                                user_context: UserContext):
        assert before_futures_balance.total == after_futures_balance.total, 'balance.total不一致'
        assert before_futures_balance.locked == after_futures_balance.locked, 'balance.locked不一致 {} {}'.format(
            before_futures_balance.locked, after_futures_balance.locked)
        assert before_futures_balance.available == after_futures_balance.available, 'balance.available不一致'

    def check_user_position_tail(self, symbol_set: set, before_position_dict: dict[str, BalanceFuturesPosition],
                                 after_position_dict: dict[str, BalanceFuturesPosition],
                                 user_context: UserContext):
        for symbl_id in symbol_set:
            if symbl_id not in before_position_dict:
                continue
            before_position = before_position_dict[symbl_id]
            after_position = after_position_dict[symbl_id]
            assert before_position.available == after_position.available, 'position.available不一致'
            assert before_position.total == after_position.total, 'position.total不一致'
            assert before_position.locked == after_position.locked, 'position.locked不一致'
            assert before_position.margin == after_position.margin, 'position.margin不一致'

    def init_position(self) -> BalanceFuturesPosition:
        before_position = BalanceFuturesPosition()
        before_position.available = Decimal(0)
        before_position.locked = Decimal(0)
        before_position.total = Decimal(0)
        before_position.margin = Decimal(0)
        return before_position

    def chase_balance(self, total_trade: TotalTrade, before_futures_balance: Balance):
        before_futures_balance.available = before_futures_balance.available + total_trade.balance_avb_changed
        before_futures_balance.locked = before_futures_balance.locked + total_trade.balance_locked_changed
        before_futures_balance.total = before_futures_balance.total + total_trade.balance_total_changed

    def chase_position(self, total_trade: TotalTrade, before_position: BalanceFuturesPosition):
        before_position.total = before_position.total + total_trade.position_total_changed
        before_position.locked = before_position.locked + total_trade.position_locked_changed
        before_position.available = before_position.available + total_trade.position_avb_changed
        before_position.margin = before_position.margin + total_trade.position_margin_changed

    def update_user_total_order(self, user_context_dict: dict[int, UserContext],
                                order_action_dict: dict[int, PlaceOrder]):
        print('计算订单相关')
        for uid, user_context in user_context_dict.items():
            for related_id, order_action in order_action_dict.items():
                if uid != order_action.uid:
                    continue
                total_trade: TotalTrade = None
                contract_multiplier: Decimal = self.get_contract_multiplier(order_action.symbol)
                leverage: Decimal = Decimal(user_context.symbol_leverage_dict[order_action.symbol])
                if order_action.side == 'BUY_OPEN':
                    if order_action.symbol in user_context.user_total_long_trade:
                        total_trade = user_context.user_total_long_trade[order_action.symbol]
                    else:
                        total_trade = TotalTrade()
                        user_context.user_total_long_trade[order_action.symbol] = total_trade
                    leverage_ratio = Decimal(1) / leverage
                    leverage_ratio = leverage_ratio.quantize(Decimal('0.000000000000000001'), rounding=ROUND_UP)
                    order_margin_locked = order_action.price * contract_multiplier * order_action.quantity * leverage_ratio
                    order_margin_locked = order_margin_locked.quantize(Decimal('0.000000000000000001'),
                                                                       rounding=ROUND_UP)
                    total_trade.balance_avb_changed = total_trade.balance_avb_changed - order_margin_locked
                    total_trade.balance_locked_changed = total_trade.balance_locked_changed + order_margin_locked
                if order_action.side == 'SELL_OPEN':
                    if order_action.symbol in user_context.user_total_short_trade:
                        total_trade = user_context.user_total_short_trade[order_action.symbol]
                    else:
                        total_trade = TotalTrade()
                        user_context.user_total_short_trade[order_action.symbol] = total_trade
                    leverage_ratio = Decimal(1) / leverage
                    leverage_ratio = leverage_ratio.quantize(Decimal('0.000000000000000001'), rounding=ROUND_UP)
                    order_margin_locked = order_action.price * contract_multiplier * order_action.quantity * leverage_ratio
                    order_margin_locked = order_margin_locked.quantize(Decimal('0.000000000000000001'),
                                                                       rounding=ROUND_UP)
                    total_trade.balance_avb_changed = total_trade.balance_avb_changed - order_margin_locked
                    total_trade.balance_locked_changed = total_trade.balance_locked_changed + order_margin_locked
                if order_action.side == 'SELL_CLOSE':
                    if order_action.symbol in user_context.user_total_long_trade:
                        total_trade = user_context.user_total_long_trade[order_action.symbol]
                    else:
                        total_trade = TotalTrade()
                        user_context.user_total_long_trade[order_action.symbol] = total_trade
                    total_trade.position_avb_changed = total_trade.position_avb_changed - order_action.quantity
                    total_trade.position_locked_changed = total_trade.position_locked_changed + order_action.quantity
                if order_action.side == 'BUY_CLOSE':
                    if order_action.symbol in user_context.user_total_short_trade:
                        total_trade = user_context.user_total_short_trade[order_action.symbol]
                    else:
                        total_trade = TotalTrade()
                        user_context.user_total_short_trade[order_action.symbol] = total_trade
                    total_trade.position_avb_changed = total_trade.position_avb_changed - order_action.quantity
                    total_trade.position_locked_changed = total_trade.position_locked_changed + order_action.quantity

    def clear_user_trade(self, user_context_dict: dict[int, UserContext]):
        for uid, user_context in user_context_dict.items():
            user_context.user_total_long_trade.clear()
            user_context.user_total_short_trade.clear()
            user_context.user_total_long_trade = copy.deepcopy(user_context.origin_user_total_long_trade)
            user_context.user_total_short_trade = copy.deepcopy(user_context.origin_user_total_short_trade)

    def check_trade_detail(self, predict_trade_detail: PredictTradeDetail, case: Case,
                           user_context_dict: dict[int, UserContext], order_action_dict: dict[int, PlaceOrder]):

        taker_id = predict_trade_detail.taker_id
        maker_id = predict_trade_detail.maker_id
        taker_place_order = order_action_dict[taker_id]
        maker_place_order = order_action_dict[maker_id]
        taker_uid = taker_place_order.uid
        maker_uid = maker_place_order.uid
        taker_order = user_context_dict[taker_uid].get_order_by_id(taker_id)
        maker_order = user_context_dict[maker_uid].get_order_by_id(maker_id)

        self.market_order_price(taker_place_order, maker_place_order)

        predict_trade_detail.price = order_action_dict[maker_id].price
        predict_trade_detail.taker_price = order_action_dict[taker_id].price

        taker_shard_conn = self.shard_route_query_biz.route_shard_conn(taker_uid)
        taker_trade_detail: TradeDetail = TradeDetail(
            taker_shard_conn.getOne('select * from tb_trade_detail where order_id = %s and match_order_id = %s',
                                    (taker_order.orderId, maker_order.orderId)))

        self.check_trade(taker_trade_detail, predict_trade_detail, 0)
        self.check_fee(taker_trade_detail, user_context_dict)

        taker_trade_detail_id = taker_trade_detail.trade_detail_id
        taker_trade_detail_futures: TradeDetailFutures = TradeDetailFutures(taker_shard_conn.getOne(
            'select * from tb_trade_detail_futures where trade_detail_id = %s',
            (taker_trade_detail_id)))
        self.check_futures_trade(user_context_dict[taker_uid], taker_trade_detail,
                                 taker_trade_detail_futures, taker_place_order)

        self.update_user_total_trade(user_context_dict[taker_uid], taker_trade_detail, taker_trade_detail_futures,
                                     predict_trade_detail)

        maker_shard_conn = self.shard_route_query_biz.route_shard_conn(maker_uid)
        maker_trade_detail: TradeDetail = TradeDetail(maker_shard_conn.getOne(
            'select * from tb_trade_detail where order_id = %s and match_order_id = %s',
            (maker_order.orderId, taker_order.orderId)))
        self.check_trade(maker_trade_detail, predict_trade_detail, 1)
        self.check_fee(maker_trade_detail, user_context_dict)

        maker_trade_detail_id = maker_trade_detail.trade_detail_id
        maker_trade_detail_futures: TradeDetailFutures = TradeDetailFutures(maker_shard_conn.getOne(
            'select * from tb_trade_detail_futures where trade_detail_id = %s',
            (maker_trade_detail_id)))
        self.check_futures_trade(user_context_dict[maker_uid], maker_trade_detail,
                                 maker_trade_detail_futures, maker_place_order)

        self.update_user_total_trade(user_context_dict[maker_uid], maker_trade_detail, maker_trade_detail_futures,
                                     predict_trade_detail)

    def market_order_price(self, taker_place_order: PlaceOrder, maker_place_order: PlaceOrder):
        if taker_place_order.priceType == 'MARKET' and taker_place_order.price is None:
            symbol = self.symbol_dict[taker_place_order.symbol]
            if taker_place_order.side == 'BUY_OPEN' or taker_place_order.side == 'BUY_CLOSE':
                taker_place_order.price = maker_place_order.price * (Decimal(1) + symbol.market_price_high_rate)
            else:
                taker_place_order.price = maker_place_order.price * (Decimal(1) - symbol.market_price_high_rate)

    def update_user_total_trade(self, user_context: UserContext, trade_detail: TradeDetail,
                                trade_detail_futures: TradeDetailFutures, predict_trade_detail: PredictTradeDetail):
        print('增量更新计算结果[资产、仓位] trade_detail trade_detail_id {}'.format(trade_detail.trade_detail_id))
        total_trade: TotalTrade = None
        if trade_detail.is_close == 0:
            if trade_detail.side == 0:
                user_total_long_trade = user_context.user_total_long_trade
                if trade_detail.symbol_id in user_total_long_trade:
                    total_trade = user_total_long_trade[trade_detail.symbol_id]
                else:
                    total_trade = TotalTrade()
                    user_total_long_trade[trade_detail.symbol_id] = total_trade
            else:
                user_total_short_trade = user_context.user_total_short_trade
                if trade_detail.symbol_id in user_total_short_trade:
                    total_trade = user_total_short_trade[trade_detail.symbol_id]
                else:
                    total_trade = TotalTrade()
                    user_total_short_trade[trade_detail.symbol_id] = total_trade

        if trade_detail.is_close == 1:
            if trade_detail.side == 1:
                user_total_long_trade = user_context.user_total_long_trade
                if trade_detail.symbol_id in user_total_long_trade:
                    total_trade = user_total_long_trade[trade_detail.symbol_id]
                else:
                    total_trade = TotalTrade()
                    user_total_long_trade[trade_detail.symbol_id] = total_trade
            else:
                user_total_short_trade = user_context.user_total_short_trade
                if trade_detail.symbol_id in user_total_short_trade:
                    total_trade = user_total_short_trade[trade_detail.symbol_id]
                else:
                    total_trade = TotalTrade()
                    user_total_short_trade[trade_detail.symbol_id] = total_trade
        if trade_detail.is_close == 0:
            self.update_user_total_trade_for_open(total_trade, trade_detail, trade_detail_futures, predict_trade_detail,
                                                  user_context)
        else:
            self.update_user_total_trade_for_close(total_trade, trade_detail, trade_detail_futures,
                                                   predict_trade_detail, user_context)

    def update_user_total_trade_for_open(self, total_trade: TotalTrade, trade_detail: TradeDetail,
                                         trade_detail_futures: TradeDetailFutures,
                                         predict_trade_detail: PredictTradeDetail, user_context: UserContext):

        total_trade.balance_total_changed = total_trade.balance_total_changed - trade_detail.token_fee
        if trade_detail.token_fee > 0:
            total_trade.balance_locked_changed = total_trade.balance_locked_changed - trade_detail.token_fee
        else:
            total_trade.balance_avb_changed = total_trade.balance_avb_changed - trade_detail.token_fee
        total_trade.position_total_changed = total_trade.position_total_changed + trade_detail.quantity
        total_trade.position_avb_changed = total_trade.position_avb_changed + trade_detail.quantity
        total_trade.position_margin_changed = total_trade.position_margin_changed + trade_detail_futures.margin_changed
        total_trade.total = total_trade.total + trade_detail.quantity
        total_trade.margin = total_trade.margin + trade_detail_futures.margin_changed
        contract_multiplier: Decimal = self.get_contract_multiplier(trade_detail.symbol_id)
        total_trade.open_value = total_trade.open_value + trade_detail.price * trade_detail.quantity * contract_multiplier

    def update_user_total_trade_for_close(self, total_trade: TotalTrade, trade_detail: TradeDetail,
                                          trade_detail_futures: TradeDetailFutures,
                                          predict_trade_detail: PredictTradeDetail, user_context: UserContext):
        total_trade.balance_total_changed = total_trade.balance_total_changed - trade_detail.token_fee
        if trade_detail.token_fee > 0:
            total_trade.balance_locked_changed = total_trade.balance_locked_changed - trade_detail.token_fee
            total_trade.position_margin_changed = total_trade.position_margin_changed - trade_detail_futures.margin_changed - trade_detail.token_fee
        else:
            total_trade.balance_avb_changed = total_trade.balance_avb_changed - trade_detail.token_fee
            total_trade.position_margin_changed = total_trade.position_margin_changed - trade_detail_futures.margin_changed
        total_trade.position_locked_changed = total_trade.position_locked_changed - trade_detail.quantity
        total_trade.position_total_changed = total_trade.position_total_changed - trade_detail.quantity

        total_trade.balance_total_changed = total_trade.balance_total_changed + trade_detail_futures.pnl
        total_trade.balance_locked_changed = total_trade.balance_locked_changed - trade_detail_futures.margin_changed
        total_trade.balance_avb_changed = total_trade.balance_avb_changed + trade_detail_futures.pnl + trade_detail_futures.margin_changed
        pass

    def check_futures_trade(self, user_context: UserContext, trade_detail: TradeDetail,
                            detail_futures: TradeDetailFutures, place_order: PlaceOrder):
        print('检查合约成交明细 trade_detail trade_detail_id {}'.format(trade_detail.trade_detail_id))
        if trade_detail.is_close == 0:
            self.check_futures_trade_for_open(user_context, trade_detail, detail_futures, place_order)
        else:
            self.check_futures_trade_for_close(user_context, trade_detail, detail_futures, place_order)

    def check_futures_trade_for_open(self, user_context: UserContext, trade_detail: TradeDetail,
                                     taker_trade_detail_futures: TradeDetailFutures, place_order: PlaceOrder):
        contract_multiplier: Decimal = self.get_contract_multiplier(trade_detail.symbol_id)
        leverage: Decimal = Decimal(user_context.symbol_leverage_dict[trade_detail.symbol_id])

        """
        保证金用自己的价格去算
        """
        price = place_order.price

        """
        BigDecimal leverageRatio = BigDecimal.ONE.divide(leverage, ProtoConstants.PRECISION, BigDecimal.ROUND_UP);
        return amount.multiply(contractMultiplier).multiply(leverageRatio).setScale(ProtoConstants.PRECISION, BigDecimal.ROUND_UP);
        """
        order_margin_locked = self.cal_margin_changed_for_open(leverage, price, contract_multiplier,
                                                               trade_detail.quantity, place_order)

        margin: Decimal = order_margin_locked
        if trade_detail.token_fee > 0:
            margin_changed = margin - trade_detail.token_fee
            assert margin_changed == taker_trade_detail_futures.margin_changed, '{} {}'.format(margin_changed,
                                                                                               taker_trade_detail_futures.margin_changed)
        else:
            margin_changed = margin
            assert margin_changed == taker_trade_detail_futures.margin_changed
        assert Decimal(0) == taker_trade_detail_futures.pnl
        assert Decimal(0) == taker_trade_detail_futures.residual

    def check_futures_trade_for_close(self, user_context: UserContext, trade_detail: TradeDetail,
                                      trade_detail_futures: TradeDetailFutures, place_order: PlaceOrder):

        symbol_id = trade_detail.symbol_id

        contract_multiplier: Decimal = self.get_contract_multiplier(symbol_id)
        leverage: Decimal = Decimal(user_context.symbol_leverage_dict[symbol_id])

        # 平仓一定有记录
        origin_position_long_dict: dict[str, BalanceFuturesPosition] = user_context.position_long_dict

        origin_position_short_dict: dict[str, BalanceFuturesPosition] = user_context.position_short_dict

        origin_position = None
        side = place_order.side
        if side == 'SELL_CLOSE':
            origin_position = origin_position_long_dict[symbol_id]
        else:
            origin_position = origin_position_short_dict[symbol_id]

        user_total_trade = None
        if side == 'SELL_CLOSE':
            user_total_trade = user_context.user_total_long_trade
        else:
            user_total_trade = user_context.user_total_short_trade

        # trade_total = None
        # if symbol_id not in user_total_trade:
        #     trade_total = TotalTrade()
        #     trade_total.open_value = origin_position.open_value
        #     trade_total.margin = origin_position.margin
        #     trade_total.total = origin_position.total
        #     user_total_trade[symbol_id] = trade_total
        trade_total = user_total_trade[symbol_id]

        trade_price = trade_detail.price

        open_value_changed = trade_total.open_value * trade_detail.quantity / trade_total.total

        open_value_changed = open_value_changed.quantize(Decimal('0.000000000000000001'), rounding=ROUND_FLOOR)

        pnl = None
        if side == 'SELL_CLOSE':
            pnl = trade_price * trade_detail.quantity * contract_multiplier - open_value_changed
        else:
            pnl = open_value_changed - trade_price * trade_detail.quantity * contract_multiplier

        ### (trade_price - open_price) * quantity * contract_multiplier
        ### trade_price * quantity * contract_multiplier - (open_value / total_) * quantity * contract_multiplier
        pnl = pnl.quantize(Decimal('0.000000000000000001'), rounding=ROUND_FLOOR)

        trade_total.open_value = trade_total.open_value - open_value_changed

        margin_changed = trade_total.margin * trade_detail.quantity / trade_total.total

        margin_changed = margin_changed.quantize(Decimal('0.000000000000000001'), rounding=ROUND_FLOOR)

        trade_total.margin = trade_total.margin - margin_changed

        trade_total.total = trade_total.total - trade_detail.quantity

        """
        保证金用自己的价格去算
        """

        if trade_detail.token_fee > 0:
            margin_changed = margin_changed - trade_detail.token_fee
            assert margin_changed == trade_detail_futures.margin_changed
        else:
            margin_changed = margin_changed
            assert margin_changed == trade_detail_futures.margin_changed
        assert pnl == trade_detail_futures.pnl
        assert Decimal(0) == trade_detail_futures.residual

        pass

    def check_trade(self, trade_detail: TradeDetail, predict_trade_detail: PredictTradeDetail, is_maker: int):
        print('校验成交明细 trade_detail trade_detail_id {}'.format(trade_detail.trade_detail_id))
        assert trade_detail is not None, '成交明细不存在，可能是清算延迟，也可能是盘口被人动了'
        assert trade_detail.status == 1, '成交清算动账未完成 {}'.format(trade_detail.trade_detail_id)
        assert trade_detail.is_maker == is_maker
        assert trade_detail.quantity == predict_trade_detail.quantity, '成交张数不一致'
        assert trade_detail.price == predict_trade_detail.price, '成交价格不一致'

    def check_fee(self, trade_detail: TradeDetail, user_context_dict: dict[int, UserContext]):
        print('校验手续费 trade_detail trade_detail_id {}'.format(trade_detail.trade_detail_id))
        contract_multiplier: Decimal = self.get_contract_multiplier(trade_detail.symbol_id)
        open_value: Decimal = trade_detail.price * trade_detail.quantity * contract_multiplier
        open_value = open_value.quantize(Decimal('0.000000000000000001'), rounding=ROUND_DOWN)
        """
                BigDecimal matchValue = matchQty.multiply(matchPrice).multiply(multiplier)
                .setScale(ProtoConstants.PRECISION, BigDecimal.ROUND_DOWN);
        """
        symbol_fee_dict: dict[str, FeeRate] = user_context_dict[trade_detail.broker_user_id].symbol_fee_dict
        fee_rate = symbol_fee_dict[trade_detail.symbol_id]
        fee: Decimal = None
        if trade_detail.is_maker == 1:
            fee = fee_rate.makerFee
            if fee < Decimal(0):
                taker_user_fee: Decimal = user_context_dict[trade_detail.match_broker_user_id].symbol_fee_dict[
                    trade_detail.symbol_id].takerFee
                if abs(fee) > taker_user_fee:
                    fee = taker_user_fee * Decimal(-1)
        else:
            fee = fee_rate.takerFee
        trade_fee: Decimal = open_value * fee
        trade_fee = trade_fee.quantize(Decimal('0.000000000000000001'), rounding=ROUND_UP)
        assert trade_detail.token_fee == trade_fee, "手续费不一致"
        assert trade_detail.fee_rate == fee, "手续费率不一致"

    def get_contract_multiplier(self, symbol_id: str) -> Decimal:
        return self.symbol_dict[symbol_id].contract_multiplier

    def mapping_order(self, case: Case) -> dict[int, PlaceOrder]:
        order_action_dict: dict[int, PlaceOrder] = {}
        for case_action in case.case_actions:
            if case_action.order_action is not None and case_action.order_action.cancelId == -1:
                order_action_dict[case_action.order_action.id] = case_action.order_action
        return order_action_dict

    def load_user_info(self, user_context_dict: dict[int, UserContext]):
        for uid, user_context in user_context_dict.items():
            user: User = user_context.user
            leverage_dict: dict[str, int] = {}
            for symbol_id in self.symbol_dict:
                leverage_dict[symbol_id] = self.leverage_biz.get_user_leverage(user, symbol_id)
            user_context.symbol_leverage_dict = leverage_dict

    def load_user_futures_balance(self, user_context: UserContext) -> Balance:
        user: User = user_context.user
        conn = self.shard_route_query_biz.route_shard_conn(user.uid)
        balance = conn.getOne('select * from tb_balance where account_id = %s', (user.futuresAccountId))
        return Balance(balance)

    def load_user_position(self, user_context: UserContext):
        user: User = user_context.user
        conn = self.shard_route_query_biz.route_shard_conn(user.uid)
        positions = conn.getAll('select * from tb_balance_futures_position where account_id = %s',
                                (user.futuresAccountId))
        after_position_long_dict = {}
        after_position_short_dict = {}
        for position in positions:
            if position['is_long'] == 1:
                after_position_long_dict[position['token_id']] = BalanceFuturesPosition(position)
            else:
                after_position_short_dict[position['token_id']] = BalanceFuturesPosition(position)
        return (after_position_long_dict, after_position_short_dict)

    def load_user_order(self, user_context: UserContext, order_id_list: [int]) -> list[TbOrder]:
        user: User = user_context.user
        conn = self.shard_route_query_biz.route_shard_conn(user.uid)
        orders = conn.getAll('select * from tb_order where order_id in %s',
                             (order_id_list,))
        order_list = []
        for order in orders:
            order_list.append(TbOrder(order))
        return order_list

    def cal_margin_changed_for_open(self, leverage: Decimal, price: Decimal, contract_multiplier: Decimal,
                                    quantity: Decimal, order_action: PlaceOrder) -> Decimal:
        leverage_ratio = Decimal(1) / leverage
        leverage_ratio = leverage_ratio.quantize(Decimal('0.000000000000000001'), rounding=ROUND_UP)
        order_margin_locked = price * contract_multiplier * order_action.quantity * leverage_ratio
        order_margin_locked = order_margin_locked.quantize(Decimal('0.000000000000000001'), rounding=ROUND_UP)
        margin_changed = order_margin_locked * quantity / order_action.quantity
        margin_changed = margin_changed.quantize(Decimal('0.000000000000000001'), rounding=ROUND_DOWN)
        return margin_changed
