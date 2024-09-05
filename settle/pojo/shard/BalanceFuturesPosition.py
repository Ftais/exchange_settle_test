from decimal import Decimal

"""
仓位
tb_balance_futures_position
"""


class BalanceFuturesPosition:

    def __init__(self, data=None):
        self.position_id: int = None

        self.account_id: int = None

        self.token_id: str = None

        self.broker_user_id: str = None

        self.total: int = None

        self.locked: int = None

        self.available: int = None

        self.margin: Decimal = None

        self.order_margin: Decimal = None

        self.leverage: Decimal = None

        self.margin_type: int = None

        self.open_value: Decimal = None

        self.realised_pnl: Decimal = None

        self.liquidation_price: Decimal = None

        self.bankruptcy_price: Decimal = None

        self.is_Long: int = None

        self.open_on_book: int = None

        self.version: int = None

        if data:
            self.__dict__.update(data)
