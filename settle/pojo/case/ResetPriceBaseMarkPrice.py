from decimal import Decimal


class ResetPriceBaseMarkPrice:

    def __init__(self, data=None):
        self.symbol_tag: str = None

        self.price_mod: Decimal = None

        self.price_offset: Decimal = None

        self.taker_uid_tag: str = None

        self.maker_uid_tag: str = None
        if data:
            self.__dict__.update(data)
            self.price_mod = Decimal(data['price_mod'])
            self.price_offset = Decimal(data['price_offset'])
