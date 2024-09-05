"""
一笔成交对应一个对象
"""
from decimal import Decimal


class PredictTradeDetail:

    def __init__(self, data=None):
        self.taker_id: int = None

        self.maker_id: int = None

        """
        取maker的价格
        """
        self.price: Decimal = None

        self.taker_price: Decimal = None

        self.quantity: Decimal = None

        # self.margin_changed: Decimal = None
        #
        # self.pnl: Decimal = None

        if data:
            self.__dict__.update(data)
            self.quantity = Decimal(data['quantity'])
