from decimal import Decimal, ROUND_FLOOR


class ExchangePosition:

    def __init__(self, data=None):
        self.account_id = None
        self.margin = None
        self.open_value = None
        self.total = None
        self.locked = None
        self.avb = None

        if data:
            self.__dict__.update(data)
            if 'a' in data:
                self.account_id = data['a']
                self.margin = Decimal(data['m']).quantize(Decimal('0.000000000000000001'), rounding=ROUND_FLOOR)
                self.total = Decimal(data['t']).quantize(Decimal('0.000000000000000001'), rounding=ROUND_FLOOR)
                self.open_value = Decimal(data['o']).quantize(Decimal('0.000000000000000001'), rounding=ROUND_FLOOR)

    @staticmethod
    def format_key(account_id, symbol_id, direct):
        return f'{account_id}_{symbol_id}_{direct}'

    @staticmethod
    def is_long(key_str: str):
        (account_id, symbol_id, direct) = key_str.split('_')
        return direct == 'true'
