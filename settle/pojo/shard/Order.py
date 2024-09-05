from decimal import Decimal

"""
订单
tb_order
PRIMARY KEY (`order_id`),

"""


class Order:

    def __init__(self, data=None):
        self.orderId: int = None

        self.accountId: int = None

        self.orderType: int = None

        self.timeInForce: int = None

        self.price: Decimal = None

        self.quantity: Decimal = None

        self.amount: Decimal = None

        self.locked: Decimal = None

        self.side: int = None

        self.executedQuantity: Decimal = None

        self.executedQty: Decimal = None

        self.executedAmount: Decimal = None

        self.stopPrice: Decimal = None

        self.status: int = None

        self.securityType: int = None

        self.makerFeeRate: Decimal = None

        self.takerFeeRate: Decimal = None

        self.isClose: int = None

        self.leverage: Decimal = None

        self.marginType: int = None

        self.isLiquidationOrder: int = None

        self.cancelReason: int = None

        self.extraJson: str = None

        self.type: str = None

        if data:
            self.__dict__.update(data)
