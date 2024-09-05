from settle.pojo.case.TotalTrade import TotalTrade
from settle.pojo.fee.FeeRate import FeeRate
from settle.pojo.shard.Balance import Balance
from settle.pojo.shard.BalanceFuturesPosition import BalanceFuturesPosition
from settle.pojo.shard.Order import Order
from settle.pojo.user import User


class UserContext:

    def get_order_by_id(self, id: int) -> Order:
        return self.order_dict[id]

    def put_order_by_id(self, id: int, order: Order):
        self.order_dict[id] = order

    def __init__(self, data=None):
        self.user: User = None

        self.spot_balance_dict: dict[str, Balance] = {}

        self.futures_balance: Balance = None

        self.position_long_dict: dict[str, BalanceFuturesPosition] = {}

        self.position_short_dict: dict[str, BalanceFuturesPosition] = {}

        self.user_total_long_trade: dict[str, TotalTrade] = {}

        self.user_total_short_trade: dict[str, TotalTrade] = {}

        self.origin_user_total_long_trade: dict[str, TotalTrade] = {}

        self.origin_user_total_short_trade: dict[str, TotalTrade] = {}

        self.user_total_spot_trade: dict[str, TotalTrade] = {}

        """
        订单, key是关联PlaceOrder.id
        """
        self.order_dict: dict[int, Order] = {}

        self.symbol_leverage_dict: dict[str, int] = {}

        self.symbol_fee_dict: dict[str, FeeRate] = {}

        # self.after_futures_balance: Balance = None
        #
        self.after_position_long_dict: dict[str, BalanceFuturesPosition] = {}

        self.after_position_short_dict: dict[str, BalanceFuturesPosition] = {}

        if data:
            self.__dict__.update(data)
