import uuid
from decimal import Decimal
from time import sleep

from settle.biz.FuturesSettleCheckDriver import FuturesSettleCheckDriver
from settle.biz.LeverageBiz import LeverageBiz
from settle.biz.MarkPriceBiz import MarkPriceBiz
from settle.biz.PlaceOrderBiz import PlaceOrderBiz
from settle.biz.ResetPriceBaseMarkPriceBiz import ResetPriceBaseMarkPriceBiz
from settle.biz.ResetSymbolBiz import ResetSymbolBiz
from settle.biz.ShardRouteQueryBiz import ShardRouteQueryBiz
from settle.biz.SpotSettleCheckDriver import SpotSettleCheckDriver
from settle.builder.CaseBuilder import CaseBuilder
from settle.pojo.case.CancelUserOrders import CancelUserOrders
from settle.pojo.case.Case import Case
from settle.pojo.case.ClearPositions import ClearPositions
from settle.pojo.case.PlaceOrder import PlaceOrder
from settle.pojo.case.PredictTradeDetail import PredictTradeDetail
from settle.pojo.case.PriceBaseMarkPrice import PriceBaseMarkPrice
from settle.pojo.case.PriceBaseTickerPrice import PriceBaseTickerPrice
from settle.pojo.case.Symbol import Symbol
from settle.pojo.case.TotalTrade import TotalTrade
from settle.pojo.fee.FeeRate import FeeRate
from settle.pojo.shard.Balance import Balance
from settle.pojo.shard.BalanceFuturesPosition import BalanceFuturesPosition
from settle.pojo.shard.Order import Order
from settle.pojo.type.CaseActionType import CaseActionType
from settle.pojo.type.CaseType import CaseType
from settle.pojo.user.User import User
from settle.pojo.user.UserContext import UserContext
from settle.service.DomainService import DomainService
from settle.service.ExchangeService import ExchangeService
from settle.service.JdbcService import JdbcService
from settle.service.MarkPriceService import MarkPriceService
from settle.service.TickerPriceService import TickerPriceService
from settle.service.UserService import UserService
from settle.utils.retry.NeedRetryException import NeedRetryException
from settle.utils.retry.RetryDriver import RetryDriver


class SettleGroupDriver:

    def __init__(self, group_id: str):
        self.group_id = group_id

        self.case_list: list[Case] = {}

        self.user_context_dict: dict[int, UserContext] = {}

        self.user_tag_to_user_dict: dict[str, UserContext] = {}

        self.exchange_service: ExchangeService = None

        self.domain_service: DomainService = None

        self.symbol_dict: dict[str, Symbol] = {}

        self.symbol_tag_to_symbol_dict: dict[str, Symbol] = {}

        self.mark_price_biz: MarkPriceBiz = None

        self.reset_symbol_biz: ResetSymbolBiz = None

        self.reset_price_base_mark_price_biz: ResetPriceBaseMarkPriceBiz = None

        self.place_order_biz: PlaceOrderBiz = None

        self.market_biz = MarketBiz = None

        self.mark_price_dict: dict[str, Decimal] = {}

        self.ticker_price_dict: dict[str, Decimal] = {}

        self.leverage_biz: LeverageBiz = None

        self.jdbc_service: JdbcService = None

        self.shard_route_query_biz: ShardRouteQueryBiz = None

        self.case_type = None

    def start(self):
        self.init()
        self.run_cases()

    def run_cases(self):
        for case in self.case_list:
            print("\n<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
            print(
                "\nstart group={} case={} case_tag<<<{}>>> case_type={}".format(self.group_id, case.id, case.tag,
                                                                                case.type))
            self.case_type = case.type
            self.init_user_context()
            self.run_case(case)
            self.mark_price_dict.clear()
            self.user_context_dict.clear()
            print("\nend group={} case={} case_tag <<<{}>>> case_type={}".format(self.group_id, case.id, case.tag,
                                                                                 case.type))
            print("\n>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")

    def run_case(self, case: Case):
        for case_action in case.case_actions:
            if case_action.case_action_type == CaseActionType.ORDER:
                self.run_order_action(case_action.order_action)
            if case_action.case_action_type == CaseActionType.SETTLE_CHECK:
                if case.type == CaseType.FUTURES.value:
                    self.run_futures_settle_check(case_action.predict_trade_details, case)
                if case.type == CaseType.SPOT.value:
                    self.run_spot_settle_check(case_action.predict_trade_details, case)

            if case_action.case_action_type == CaseActionType.RESET_LAST_PRICE_TO_MARK_PRICE:
                self.reset_price_base_mark_price_biz.execute(case_action.reset_last_price_to_mark_price,
                                                             self.user_tag_to_user_dict, self.symbol_tag_to_symbol_dict)
            if case_action.case_action_type == CaseActionType.RESET_SYMBOL:
                self.reset_symbol_biz.execute(case_action.reset_symbol.symbol_id)
            if case_action.case_action_type == CaseActionType.WAIT_MOMENT:
                sleep(case_action.wait_moment.seconds)
            if case_action.case_action_type == CaseActionType.CANCEL_USER_ORDERS:
                self.futures_cancel_user_orders(case_action.cancel_user_orders)
            if case_action.case_action_type == CaseActionType.CLEAR_POSITION:
                self.clear_user_positions(case_action.clear_positions)

    def run_futures_settle_check(self, predict_trade_details: list[PredictTradeDetail], case: Case):
        settle_check_driver = FuturesSettleCheckDriver(self.domain_service, self.leverage_biz, self.symbol_dict,
                                                       self.shard_route_query_biz, self.exchange_service)
        settle_check_driver.check(predict_trade_details, case, self.user_context_dict)

    def run_spot_settle_check(self, predict_trade_details: list[PredictTradeDetail], case: Case):
        settle_check_driver = SpotSettleCheckDriver(self.domain_service, self.symbol_dict,
                                                    self.shard_route_query_biz, self.exchange_service,
                                                    self.ticker_price_dict)
        settle_check_driver.check(predict_trade_details, case, self.user_context_dict)

    def run_order_action(self, order_action: PlaceOrder):
        uid_tag = order_action.uidTag
        user_context: UserContext = self.pick_user_context(uid_tag)
        user: User = user_context.user
        order_action.uid = user.uid
        if order_action.cancelId == -1:
            symbol_tag = order_action.symbolTag
            symbol = self.symbol_tag_to_symbol_dict[symbol_tag]
            order_action.symbol = symbol.symbol_id
            if self.case_type == CaseType.FUTURES.value:
                if order_action.symbol not in self.mark_price_dict:
                    mark_price = MarkPriceService.get_mark_price(self.domain_service.get_open_api_domain(),
                                                                 order_action.symbol)
                    self.mark_price_dict[order_action.symbol] = mark_price

                if order_action.price_base_mark_price is not None:
                    price: Decimal = self.cal_order_price_by_mark_price(order_action.price_base_mark_price,
                                                                        self.mark_price_dict[order_action.symbol])
                    order_action.price = price

            else:
                if order_action.symbol not in self.ticker_price_dict:
                    ticker_price = TickerPriceService.get_ticker_price(self.domain_service.get_open_api_domain(),
                                                                       order_action.symbol)
                    self.ticker_price_dict[order_action.symbol] = ticker_price
                if order_action.price_base_ticker_price is not None:
                    price: Decimal = self.cal_order_price_by_ticker_price(order_action.price_base_ticker_price,
                                                                          self.ticker_price_dict[order_action.symbol])
                    order_action.price = price

            order_action.clientOrderId = uuid.uuid4()
            order: Order = RetryDriver.retry(
                lambda: self.retry_place_order(order_action, user))
            user_context.put_order_by_id(order_action.id, order)
        else:
            cancel_id = order_action.cancelId
            order = user_context.get_order_by_id(cancel_id)
            if self.case_type == CaseType.FUTURES.value:
                self.place_order_biz.futures_cancel(order, user)
            else:
                self.place_order_biz.spot_cancel(order, user)
            user_context.put_order_by_id(order_action.id, order)

    def retry_place_order(self, order_action, user) -> Order:
        order: Order = None
        if self.case_type == CaseType.FUTURES.value:
            order = self.place_order_biz.futures_place(order_action, user)
        if self.case_type == CaseType.SPOT.value:
            order = self.place_order_biz.spot_place(order_action, user)
        if order is None or order.orderId is None:
            raise NeedRetryException(None, "下单失败")
        return order

    def futures_cancel_user_orders(self, cancel_user_orders: CancelUserOrders):
        for uid_tag in cancel_user_orders.uid_tag_list:
            user_context = self.user_tag_to_user_dict[uid_tag]
            user = user_context.user
            for symbol_tag_id in cancel_user_orders.symbol_tag_list:
                symbol_id = self.symbol_tag_to_symbol_dict[symbol_tag_id].symbol_id
                self.place_order_biz.futures_cancel_orders(user, symbol_id, 'BUY')
                self.place_order_biz.futures_cancel_orders(user, symbol_id, 'SELL')

    def cal_order_price_by_mark_price(self, price_base_mark_price: PriceBaseMarkPrice, mark_price: Decimal) -> Decimal:
        return price_base_mark_price.cal_price(mark_price)

    def cal_order_price_by_ticker_price(self, price_base_ticker_price: PriceBaseTickerPrice,
                                        ticker_price: Decimal) -> Decimal:
        return price_base_ticker_price.cal_price(ticker_price)

    def pick_user_context(self, uid_tag: str) -> UserContext:
        return self.user_tag_to_user_dict[uid_tag]

    def init(self):
        self.init_cases()
        self.init_exchange_service()
        self.init_domain_service()
        self.init_jdbc_service()
        self.init_symbols()
        self.init_biz()

    def init_biz(self):
        self.mark_price_biz = MarkPriceBiz(self.domain_service)
        self.place_order_biz = PlaceOrderBiz(self.domain_service)
        self.reset_price_base_mark_price_biz = ResetPriceBaseMarkPriceBiz(self.place_order_biz, self.domain_service)
        self.market_biz = MarkPriceBiz(self.domain_service)
        self.leverage_biz = LeverageBiz(self.domain_service)
        self.reset_symbol_biz = ResetSymbolBiz(self.exchange_service)
        self.shard_route_query_biz = ShardRouteQueryBiz(self.jdbc_service)

    def init_symbols(self):
        symbol_list: list[Symbol] = CaseBuilder.get_symbols(self.group_id)
        for symbol in symbol_list:
            self.symbol_dict[symbol.symbol_id] = symbol
            self.symbol_dict[symbol.symbol_id].contract_multiplier = Decimal(symbol.contract_multiplier)
            self.symbol_dict[symbol.symbol_id].market_price_low_rate = Decimal(symbol.market_price_low_rate)
            self.symbol_dict[symbol.symbol_id].market_price_high_rate = Decimal(symbol.market_price_high_rate)
            self.symbol_tag_to_symbol_dict[symbol.symbol_tag] = symbol

    def init_cases(self):
        self.case_list = CaseBuilder.load_one_group_cases(self.group_id)

    def init_user_context(self):
        users = UserService.load_user_config(self.group_id)
        for uid, user in users.items():
            user_context = UserContext()
            user_context.user = user
            self.user_context_dict[uid] = user_context
            self.user_tag_to_user_dict[user.uidTag] = user_context
            fee_list: list = user.fee_list
            symbol_fee_dict = {}
            for ele in fee_list:
                fee_rate: FeeRate = FeeRate()
                fee_rate.symbolId = ele.symbol_id
                fee_rate.takerFee = Decimal(ele.taker_fee)
                fee_rate.makerFee = Decimal(ele.maker_fee)
                symbol_fee_dict[ele.symbol_id] = fee_rate
            user_context.symbol_fee_dict = symbol_fee_dict
            self.load_user_futures_balance(user_context)
            self.load_user_spot_balance(user_context)
            self.load_user_position(user_context)
        pass

    def load_user_spot_balance(self, user_context):
        user: User = user_context.user
        conn = self.shard_route_query_biz.route_shard_conn(user.uid)
        balances: list = conn.getAll('select * from tb_balance where account_id = %s', (user.spotAccountId))
        for balance in balances:
            user_context.spot_balance_dict[balance['token_id']] = Balance(balance)

    def load_user_futures_balance(self, user_context: UserContext):
        user: User = user_context.user
        conn = self.shard_route_query_biz.route_shard_conn(user.uid)
        balance = conn.getOne('select * from tb_balance where account_id = %s', (user.futuresAccountId))
        user_context.futures_balance = Balance(balance)

    def load_user_position(self, user_context: UserContext):
        user: User = user_context.user
        conn = self.shard_route_query_biz.route_shard_conn(user.uid)
        positions = conn.getAll('select * from tb_balance_futures_position where account_id = %s',
                                (user.futuresAccountId))
        origin_user_total_long_trade = user_context.origin_user_total_long_trade
        origin_user_total_short_trade = user_context.origin_user_total_short_trade
        for position in positions:
            total_trade = TotalTrade()
            total_trade.total = position['total']
            total_trade.margin = position['margin']
            total_trade.open_value = position['open_value']
            if position['is_long'] == 1:
                user_context.position_long_dict[position['token_id']] = BalanceFuturesPosition(position)
                origin_user_total_long_trade[position['token_id']] = total_trade
            else:
                user_context.position_short_dict[position['token_id']] = BalanceFuturesPosition(position)
                origin_user_total_short_trade[position['token_id']] = total_trade

    def init_exchange_service(self):
        self.exchange_service = ExchangeService()

    def init_domain_service(self):
        self.domain_service = DomainService()

    def init_jdbc_service(self):
        self.jdbc_service = JdbcService()

    def clear_user_positions(self, clear_positions: ClearPositions):
        long_position_dict = {}
        short_position_dict = {}
        symbol_tag_set = set(clear_positions.symbol_tag_list)
        for uid_tag in clear_positions.uid_tag_list:
            user_context = self.user_tag_to_user_dict[uid_tag]
            user = user_context.user
            conn = self.shard_route_query_biz.route_shard_conn(user.uid)
            positions = conn.getAll('select * from tb_balance_futures_position where account_id = %s',
                                    (user.futuresAccountId))
            for position in positions:
                symbol_id = position['token_id']
                if position['available'] is None or position['available'] == 0:
                    continue
                if symbol_tag_set.__contains__(symbol_id):
                    if position['is_long'] == 1:
                        if symbol_id not in long_position_dict:
                            long_position_list = []
                            long_position_dict[symbol_id] = long_position_list
                        long_position_dict[symbol_id].append(position)
                    else:
                        if symbol_id not in short_position_dict:
                            short_position_list = []
                            short_position_dict[symbol_id] = short_position_list
                        short_position_dict[symbol_id].append(position)

        if long_position_dict and short_position_dict:
            for symbol_id, long_positions in long_position_dict.items():
                mark_price = MarkPriceService.get_mark_price(self.domain_service.get_open_api_domain(),
                                                             symbol_id)
                mark_price = int(mark_price)
                if symbol_id in short_position_dict:
                    short_positions = list(reversed(short_position_dict[symbol_id]))
                    for long_position in long_positions:
                        user_context: UserContext = self.user_context_dict[int(long_position['broker_user_id'])]
                        order: PlaceOrder = PlaceOrder()
                        order.symbol = symbol_id
                        order.side = 'SELL_CLOSE'
                        order.type = 'LIMIT'
                        order.price = mark_price
                        order.quantity = long_position['available']
                        self.place_order_biz.futures_place(order, user_context.user)
                    for short_position in short_positions:
                        user_context: UserContext = self.user_context_dict[int(short_position['broker_user_id'])]
                        order: PlaceOrder = PlaceOrder()
                        order.symbol = symbol_id
                        order.side = 'BUY_CLOSE'
                        order.type = 'LIMIT'
                        order.price = mark_price
                        order.quantity = short_position['available']
                        self.place_order_biz.futures_place(order, user_context.user)
