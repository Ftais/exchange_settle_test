from decimal import Decimal

"""
订单
tb_order
PRIMARY KEY (`order_id`),

"""


class TbOrder:

    def __init__(self, data=None):
        self.symbol_id: str = None

        self.order_id: int = None

        self.account_id: int = None

        self.order_type: int = None

        self.time_in_force: int = None

        self.price: Decimal = None

        self.quantity: Decimal = None

        self.amount: Decimal = None

        self.locked: Decimal = None

        self.side: int = None

        self.executed_quantity: Decimal = None

        self.executed_amount: Decimal = None

        self.stop_price: Decimal = None

        self.status: int = None

        self.security_type: int = None

        self.maker_fee_rate: Decimal = None

        self.taker_fee_rate: Decimal = None

        self.is_close: int = None

        self.leverage: Decimal = None

        self.margin_type: int = None

        self.is_liquidation_order: int = None

        self.cancel_reason: int = None

        self.extra_json: str = None

        self.type: str = None

        if data:
            self.__dict__.update(data)
