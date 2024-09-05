from decimal import Decimal


class MarketInfo:

    def __init__(self):
        self.filterType: str = None
        self.minPrice: str = None
        self.maxPrice: str = None
        self.tickSize: str = None
        self.contractMultiplier: Decimal = None
