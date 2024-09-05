from decimal import Decimal

from settle.pojo.case.PriceBaseMarkPrice import PriceBaseMarkPrice
from settle.pojo.case.PriceBaseTickerPrice import PriceBaseTickerPrice

"""
包含下撤单
"""


class PlaceOrder:

    def __init__(self, data=None):
        """
        唯一标识，case级别
        """
        self.id: int = None

        """
        如果这个有值，说明这个action是个撤单 这个cancelId就对应当时下单的id
        """
        self.cancelId: int = -1

        """
        用来关联用户
        """
        self.uid: int = None

        self.uidTag: str = None

        self.symbol: str = None

        self.symbolTag: str = None

        self.side: str = None

        self.type: str = None

        self.price: Decimal = None

        self.price_base_mark_price: PriceBaseMarkPrice = None

        self.price_base_ticker_price: PriceBaseTickerPrice = None

        """
        api:张数
        """
        self.quantity: Decimal = None

        self.timestamp: int = 0

        self.leverage: int = None

        """
        GTC、IOC、FOK、LIMIT_MAKER
        """
        self.timeInForce: str = None

        """
        MARKET
        """
        self.priceType: str = None

        self.clientOrderId: str = None

        self.is_taker: bool = False

        self.status: int = None

        """
        已成交的张数
        """
        self.trade_quantity: Decimal = 0

        self.trade_amount: Decimal = 0

        if data:
            self.__dict__.update(data)
            if 'quantity' in data:
                self.quantity = Decimal(data['quantity'])
            if 'price' in data:
                self.price = Decimal(data['price'])
