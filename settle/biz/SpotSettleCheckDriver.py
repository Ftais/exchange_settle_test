import copy
import traceback
from decimal import Decimal, ROUND_FLOOR

from settle.biz.ShardRouteQueryBiz import ShardRouteQueryBiz
from settle.pojo.case.Case import Case
from settle.pojo.case.DecimalAccuracy import DecimalAccuracy
from settle.pojo.case.PlaceOrder import PlaceOrder
from settle.pojo.case.PredictTradeDetail import PredictTradeDetail
from settle.pojo.case.Symbol import Symbol
from settle.pojo.case.TotalTrade import TotalTrade
from settle.pojo.exchange.ExchangeOrder import ExchangeOrder
from settle.pojo.fee.FeeRate import FeeRate
from settle.pojo.shard.Balance import Balance
from settle.pojo.shard.TbOrder import TbOrder
from settle.pojo.shard.TradeDetail import TradeDetail
from settle.pojo.type.CaseActionType import CaseActionType
from settle.pojo.type.OrderStatusType import OrderStatusType
from settle.pojo.user.User import User
from settle.pojo.user.UserContext import UserContext
from settle.service.DomainService import DomainService
from settle.service.ExchangeService import ExchangeService
from settle.utils.retry.NeedRetryException import NeedRetryException
from settle.utils.retry.RetryDriver import RetryDriver


class SpotSettleCheckDriver:
    DecimalAccuracy

    def __init__(self, domain_service: DomainService, symbol_dict: dict[str, Symbol],
                 shard_route_query_biz: ShardRouteQueryBiz, exchange_service: ExchangeService,
                 ticker_price_dict: dict[str, Decimal]):
        self.domain_service = domain_service
        self.symbol_dict: dict[str, Symbol] = symbol_dict
        self.shard_route_query_biz: ShardRouteQueryBiz = shard_route_query_biz
        self.exchange_service = exchange_service
        self.ticker_price_dict = ticker_price_dict

    def check(self, predict_trade_details: list[PredictTradeDetail], case: Case,
              user_context_dict: dict[int, UserContext]):
        order_action_dict: dict[int, PlaceOrder] = self.mapping_order(case)
        RetryDriver.retry(
            lambda: self.retry_check_wrapper(predict_trade_details, case, user_context_dict, order_action_dict))

    def retry_check_wrapper(self, predict_trade_details: list[PredictTradeDetail], case: Case,
                            user_context_dict: dict[int, UserContext], order_action_dict: dict[int, PlaceOrder]):
        try:
            self.clear_user_cache(user_context_dict, order_action_dict)
            for predict_trade_detail in predict_trade_details:
                self.check_trade_detail(predict_trade_detail, case, user_context_dict, order_action_dict)
            self.update_order_all(case, user_context_dict)
            tb_order_list: list[TbOrder] = self.check_order_tail(user_context_dict, order_action_dict,
                                                                 predict_trade_details, case)
            self.check_trade_tail(case, user_context_dict)
            # self.compare_with_match_order(tb_order_list)
        except Exception as e:
            traceback.print_exc()
            raise NeedRetryException(e, "SpotSettleCheckDriver.retry_check_wrapper")

    # todo 检查盘口，看看还有没有单子挂的不对
    def compare_with_match_order(self, orders: list[TbOrder]):
        print("比对撮合orderBook")
        symbol_dict = set()
        for order in orders:
            symbol_dict.add(order.symbol_id)
        order_book_dict_1 = dict()
        order_book_dict_0 = dict()
        for symbol_id in symbol_dict:
            order_book: list = self.exchange_service.get_spot_orders_by_side(symbol_id, 1)
            order_book_dict = {}
            for order in order_book:
                order_book_dict[order.order_id] = order
            order_book_dict_1[symbol_id] = order_book_dict

            order_book: list = self.exchange_service.get_spot_orders_by_side(symbol_id, 0)
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
                assert order.quantity == exchange_order.quantity
                assert order.account_id == exchange_order.account_id
                assert order.price == exchange_order.price
            else:
                assert order.order_id not in order_book_dict, '完单 order_id={} 在撮合里面，不符合预期'

    # 对比资产
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
        print('比对最终资产和仓位情况 user_id ' + str(user_context.user.uid))
        after_spot_balance_dict = self.load_user_spot_balance(user_context)
        before_spot_balance_dict: dict[str, Balance] = copy.deepcopy(user_context.spot_balance_dict)

        token_set = set()

        user_total_spot_trade = user_context.user_total_spot_trade

        for key in user_total_spot_trade:
            token_set.add(key)

        for key in before_spot_balance_dict:
            token_set.add(key)

        for key in after_spot_balance_dict:
            token_set.add(key)

        for token_id in token_set:
            total_trade = self.get_total_trade_by_token_id(token_id, user_context)
            if token_id not in before_spot_balance_dict:
                before_spot_balance_dict[token_id] = Balance()
            before_spot_balance = before_spot_balance_dict[token_id]
            before_spot_balance.total = before_spot_balance.total + total_trade.balance_total_changed
            before_spot_balance.available = before_spot_balance.available + total_trade.balance_avb_changed
            before_spot_balance.locked = before_spot_balance.locked + total_trade.balance_locked_changed
            assert before_spot_balance.total == after_spot_balance_dict[token_id].total, '资产total不一致'
            assert before_spot_balance.available == after_spot_balance_dict[
                token_id].available, '资产available不一致 {} {}'.format(before_spot_balance.available,
                                                                        after_spot_balance_dict[token_id].available)
            assert before_spot_balance.locked == after_spot_balance_dict[
                token_id].locked, '资产locked不一致 {} {}'.format(before_spot_balance.locked,
                                                                  after_spot_balance_dict[token_id].locked)

    def check_order_tail(self, user_context_dict: dict[int, UserContext], order_action_dict: dict[int, PlaceOrder],
                         predict_trade_details: list[PredictTradeDetail], case: Case) -> list[TbOrder]:

        print('检查订单相关')

        # 清空成交数
        for related_id, order_action in order_action_dict.items():
            if order_action is not None and order_action.cancelId == -1:
                if order_action.type != 'MARKET' or order_action.side != 'BUY':
                    order_action.status = None
                order_action.trade_quantity = 0

        # 设置成交数
        for predict_trade_detail in predict_trade_details:
            taker_related_id = predict_trade_detail.taker_id
            maker_related_id = predict_trade_detail.maker_id
            quantity = predict_trade_detail.quantity
            order_action_dict[taker_related_id].trade_quantity = order_action_dict[
                                                                     taker_related_id].trade_quantity + quantity
            order_action_dict[maker_related_id].trade_quantity = order_action_dict[
                                                                     maker_related_id].trade_quantity + quantity
        uid_to_related_id_dict = {}

        # 计算订单状态
        for related_id, order_action in order_action_dict.items():
            if order_action is not None and order_action.cancelId == -1:
                if order_action.uid not in uid_to_related_id_dict:
                    uid_to_related_id_dict[order_action.uid] = []
                uid_to_related_id_dict[order_action.uid].append(order_action.id)
                if order_action.type == 'MARKET' and order_action.side == 'BUY':
                    assert order_action.quantity >= order_action.trade_amount, '成交数大于下单金额 {} {}'.format(
                        order_action.quantity, order_action.trade_amount)
                else:
                    assert order_action.quantity >= order_action.trade_quantity, '成交数大于下单数'
                if order_action.trade_quantity == Decimal(0):
                    if (order_action.type == 'LIMIT' or order_action.type == 'LIMIT_MAKER') and (
                            order_action.timeInForce is None or order_action.timeInForce == 'GTC'):
                        order_action.status = OrderStatusType.NEW.value
                    else:
                        order_action.status = OrderStatusType.CANCELED.value
                    continue
                if order_action.type == 'MARKET':
                    continue
                if order_action.quantity == order_action.trade_quantity:
                    order_action.status = OrderStatusType.FILLED.value
                    continue
                if order_action.timeInForce == 'IOC':
                    order_action.status = OrderStatusType.PARTIALLY_CANCELED.value
                    continue
                if order_action.timeInForce == 'FOK':
                    order_action.status = OrderStatusType.CANCELED.value
                else:
                    order_action.status = OrderStatusType.PARTIALLY_FILLED.value

        # 计算撤单，只修改状态
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

        # 和db对比
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
                assert order.status == order_action.status
                assert order.executed_quantity == order_action.trade_quantity
                if order_action.type != 'MARKET' or order_action.side != 'BUY':
                    assert order.quantity == order_action.quantity

                else:
                    assert order.executed_amount == order_action.trade_amount
                    assert order.amount == order_action.quantity
                if order_action.type != 'MARKET':
                    assert order.price == order_action.price
                # 撤单，解冻资产
                if OrderStatusType.is_canceled(order.status):
                    (base_total_trade, quote_total_trade) = self.get_total_trade(order_action.symbol, user_context)
                    if order.type != 'MARKET' or order.side != 0:
                        diff_quantity = order.quantity - order.executed_quantity
                        if order_action.side == 'BUY':
                            quote_total_trade.balance_avb_changed = quote_total_trade.balance_avb_changed + diff_quantity * order_action.price
                            quote_total_trade.balance_locked_changed = quote_total_trade.balance_locked_changed - diff_quantity * order_action.price
                        else:
                            base_total_trade.balance_avb_changed = base_total_trade.balance_avb_changed + diff_quantity
                            base_total_trade.balance_locked_changed = base_total_trade.balance_locked_changed - diff_quantity
                    else:
                        diff_amount = order.amount - order.executed_amount
                        quote_total_trade.balance_avb_changed = quote_total_trade.balance_avb_changed + diff_amount
                        quote_total_trade.balance_locked_changed = quote_total_trade.balance_locked_changed + diff_amount
                elif order_action.type == 'MARKET' and order_action.side == 'BUY' and order_action.status == OrderStatusType.FILLED.value:
                    (base_total_trade, quote_total_trade) = self.get_total_trade(order_action.symbol, user_context)
                    diff_amount = order.amount - order.executed_amount
                    quote_total_trade.balance_avb_changed = quote_total_trade.balance_avb_changed + diff_amount
                    quote_total_trade.balance_locked_changed = quote_total_trade.balance_locked_changed - diff_amount

        return order_action_mapping

    def clear_user_cache(self, user_context_dict: dict[int, UserContext], order_action_dict: dict[int, PlaceOrder]):
        for uid, user_context in user_context_dict.items():
            user_context.user_total_spot_trade.clear()
        for related_id, order_action in order_action_dict.items():
            order_action.status = OrderStatusType.PARTIALLY_FILLED.value
            order_action.trade_amount = Decimal(0)

    # todo 现货，市价单价格计算规则
    def market_order_price(self, taker_place_order: PlaceOrder, maker_place_order: PlaceOrder):
        if taker_place_order.priceType == 'MARKET' and taker_place_order.price is None:
            symbol = self.symbol_dict[taker_place_order.symbol]
            if taker_place_order.side == 'BUY_OPEN' or taker_place_order.side == 'BUY_CLOSE':
                taker_place_order.price = maker_place_order.price * (Decimal(1) + symbol.market_price_high_rate)
            else:
                taker_place_order.price = maker_place_order.price * (Decimal(1) - symbol.market_price_high_rate)

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
        self.update_trade(taker_place_order, predict_trade_detail, taker_trade_detail, user_context_dict[taker_uid])

        maker_shard_conn = self.shard_route_query_biz.route_shard_conn(maker_uid)
        maker_trade_detail: TradeDetail = TradeDetail(maker_shard_conn.getOne(
            'select * from tb_trade_detail where order_id = %s and match_order_id = %s',
            (maker_order.orderId, taker_order.orderId)))
        self.check_trade(maker_trade_detail, predict_trade_detail, 1)
        self.check_fee(maker_trade_detail, user_context_dict)
        self.update_trade(maker_place_order, predict_trade_detail, maker_trade_detail, user_context_dict[maker_uid])

    def check_trade(self, trade_detail: TradeDetail, predict_trade_detail: PredictTradeDetail, is_maker: int):
        print('校验成交明细 trade_detail trade_detail_id {}'.format(trade_detail.trade_detail_id))
        assert trade_detail is not None, '成交明细不存在，可能是清算延迟，也可能是盘口被人动了'
        assert trade_detail.status == 1, '成交清算动账未完成'
        assert trade_detail.is_maker == is_maker
        assert trade_detail.quantity == predict_trade_detail.quantity, '成交数量不一致'
        assert trade_detail.price == predict_trade_detail.price, '成交价格不一致'

    # 负maker是taker扣除了什么就得到什么吗
    def check_fee(self, trade_detail: TradeDetail, user_context_dict: dict[int, UserContext]):
        print('校验手续费 trade_detail trade_detail_id {}'.format(trade_detail.trade_detail_id))
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

        symbol: Symbol = self.symbol_dict[trade_detail.symbol_id]
        trade_fee = None
        if fee > Decimal(0):
            if trade_detail.side == 0:
                trade_fee = trade_detail.quantity * fee
                assert trade_detail.fee_token_id == symbol.base_token, "手续费token不一致"
            else:
                trade_fee = trade_detail.quantity * fee * trade_detail.price
                assert trade_detail.fee_token_id == symbol.quote_token, "手续费token不一致"
        trade_fee = trade_fee.quantize(Decimal('0.000000000000000001'), rounding=ROUND_FLOOR)
        assert trade_detail.token_fee == trade_fee, "手续费不一致"
        assert trade_detail.fee_rate == fee, "手续费率不一致"

    def update_trade(self, order_action: PlaceOrder, predict_trade_detail: PredictTradeDetail,
                     trade_detail: TradeDetail, user_context: UserContext):
        print('增量更新计算结果[资产] trade_detail trade_detail_id {}'.format(trade_detail.trade_detail_id))
        (base_total_trade, quote_total_trade) = self.get_total_trade(trade_detail.symbol_id, user_context)
        if trade_detail.side == 0:
            base_total_trade.balance_avb_changed = base_total_trade.balance_avb_changed + trade_detail.quantity - trade_detail.token_fee
            base_total_trade.balance_total_changed = base_total_trade.balance_total_changed + trade_detail.quantity - trade_detail.token_fee
            quote_total_trade.balance_locked_changed = quote_total_trade.balance_locked_changed - trade_detail.quantity * trade_detail.price
            quote_total_trade.balance_total_changed = quote_total_trade.balance_total_changed - trade_detail.quantity * trade_detail.price
        else:
            quote_total_trade.balance_avb_changed = quote_total_trade.balance_avb_changed + trade_detail.quantity * trade_detail.price - trade_detail.token_fee
            quote_total_trade.balance_total_changed = quote_total_trade.balance_total_changed + trade_detail.quantity * trade_detail.price - trade_detail.token_fee
            base_total_trade.balance_locked_changed = base_total_trade.balance_locked_changed - trade_detail.quantity
            base_total_trade.balance_total_changed = base_total_trade.balance_total_changed - trade_detail.quantity
        if order_action.type != 'MARKET' and trade_detail.is_maker == 0:
            diff_price = predict_trade_detail.taker_price - predict_trade_detail.price
            if trade_detail.side == 0:
                quote_total_trade.balance_avb_changed = quote_total_trade.balance_avb_changed + diff_price * trade_detail.quantity
                quote_total_trade.balance_locked_changed = quote_total_trade.balance_locked_changed - diff_price * trade_detail.quantity
        # 市价单，在这里更新成交金额，同时计算订单状态
        elif order_action.type == 'MARKET' and order_action.side == 'BUY':
            order_action.trade_amount = order_action.trade_amount + trade_detail.quantity * trade_detail.price
            diff_amount = order_action.quantity - order_action.trade_amount
            symbol = self.symbol_dict[order_action.symbol]
            order_action.status = None
            if diff_amount / trade_detail.price < symbol.min_qty:
                order_action.status = OrderStatusType.FILLED.value
            else:
                order_action.status = OrderStatusType.PARTIALLY_CANCELED.value

    def update_order_all(self, case: Case, user_context_dict: dict[int, UserContext]):
        print('计算更新订单相关')
        for case_action in case.case_actions:
            if case_action.case_action_type == CaseActionType.ORDER:
                order_action = case_action.order_action
                if order_action is not None and order_action.cancelId == -1:
                    self.update_order(order_action, user_context_dict[order_action.uid])

    def update_order(self, order_action: PlaceOrder, user_context: UserContext):
        (base_total_trade, quote_total_trade) = self.get_total_trade(order_action.symbol, user_context)
        if order_action.side == 'BUY':
            if order_action.type != 'MARKET':
                quote_total_trade.balance_avb_changed = quote_total_trade.balance_avb_changed - order_action.quantity * order_action.price
                quote_total_trade.balance_locked_changed = quote_total_trade.balance_locked_changed + order_action.quantity * order_action.price
            else:
                quote_total_trade.balance_avb_changed = quote_total_trade.balance_avb_changed - order_action.quantity
                quote_total_trade.balance_locked_changed = quote_total_trade.balance_locked_changed + order_action.quantity
        else:
            base_total_trade.balance_avb_changed = base_total_trade.balance_avb_changed - order_action.quantity
            base_total_trade.balance_locked_changed = base_total_trade.balance_locked_changed + order_action.quantity

    def get_total_trade_by_token_id(self, token_id, user_context: UserContext) -> TotalTrade:
        user_total_spot_trade = user_context.user_total_spot_trade
        if token_id not in user_total_spot_trade:
            total_trade = TotalTrade()
            user_total_spot_trade[token_id] = total_trade
        return user_total_spot_trade[token_id]

    def get_total_trade(self, symbol_id, user_context: UserContext) -> (TotalTrade, TotalTrade):
        user_total_spot_trade = user_context.user_total_spot_trade
        symbol: Symbol = self.symbol_dict[symbol_id]
        base_total_trade = None
        if symbol.base_token not in user_total_spot_trade:
            base_total_trade = TotalTrade()
            user_total_spot_trade[symbol.base_token] = base_total_trade
        base_total_trade = user_total_spot_trade[symbol.base_token]
        quote_total_trade = None
        if symbol.quote_token not in user_total_spot_trade:
            quote_total_trade = TotalTrade()
            user_total_spot_trade[symbol.quote_token] = quote_total_trade
        quote_total_trade = user_total_spot_trade[symbol.quote_token]
        return (base_total_trade, quote_total_trade)

    def load_user_order(self, user_context: UserContext, order_id_list: [int]) -> list[TbOrder]:
        user: User = user_context.user
        conn = self.shard_route_query_biz.route_shard_conn(user.uid)
        orders = conn.getAll('select * from tb_order where order_id in %s',
                             (order_id_list,))
        order_list = []
        for order in orders:
            order_list.append(TbOrder(order))
        return order_list

    def mapping_order(self, case: Case) -> dict[int, PlaceOrder]:
        order_action_dict: dict[int, PlaceOrder] = {}
        for case_action in case.case_actions:
            if case_action.order_action is not None and case_action.order_action.cancelId == -1:
                order_action_dict[case_action.order_action.id] = case_action.order_action
        return order_action_dict

    def load_user_spot_balance(self, user_context) -> dict[str, Balance]:
        user: User = user_context.user
        conn = self.shard_route_query_biz.route_shard_conn(user.uid)
        balances: list = conn.getAll('select * from tb_balance where account_id = %s', (user.spotAccountId))
        spot_balance_dict = {}
        for balance in balances:
            spot_balance_dict[balance['token_id']] = Balance(balance)
        return spot_balance_dict
