from decimal import Decimal

"""
基于标记价格、计算下单价格
"""


class PriceBaseMarkPrice:

    def __init__(self, data=None):
        self.price_mod: Decimal = None

        self.price_offset: Decimal = None
        if data:
            self.__dict__.update(data)
            self.price_mod = Decimal(data['price_mod'])
            self.price_offset = Decimal(data['price_offset'])

    def cal_price(self, mark_price: Decimal) -> Decimal:
        return Decimal(int(mark_price / self.price_mod)) * self.price_mod + self.price_offset
