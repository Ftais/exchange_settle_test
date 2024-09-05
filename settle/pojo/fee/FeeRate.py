from decimal import Decimal


class FeeRate:

    def __init__(self, data=None):
        self.symbolId: str = None

        self.makerFee: Decimal = None

        self.takerFee: Decimal = None

        self.fee_type: str = None
        if data:
            self.__dict__.update(data)
