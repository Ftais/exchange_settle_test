from decimal import Decimal


class Symbol:

    def __init__(self, data=None):
        self.symbol_id: str = None
        self.contract_multiplier: Decimal = Decimal(0)
        self.market_price_low_rate: Decimal = None
        self.market_price_high_rate: Decimal = None
        self.base_token: str = None
        self.quote_token: str = None
        self.min_qty: Decimal = None
        self.symbol_tag: str = None
        if data:
            self.__dict__.update(data)
            if 'market_price_low_rate' in data:
                self.market_price_low_rate = Decimal(data['market_price_low_rate'])
            if 'market_price_high_rate' in data:
                self.market_price_high_rate = Decimal(data['market_price_high_rate'])
            if 'min_qty' in data:
                self.min_qty = Decimal(data['min_qty'])
