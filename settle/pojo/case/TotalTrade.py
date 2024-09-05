from decimal import Decimal


class TotalTrade:

    def __init__(self):
        self.symbol_id: str = None

        self.is_long: int = None

        self.open_value: Decimal = Decimal(0)

        self.margin: Decimal = Decimal(0)

        self.total: Decimal = Decimal(0)

        self.balance_total_changed: Decimal = Decimal(0)

        self.balance_avb_changed: Decimal = Decimal(0)

        self.balance_locked_changed: Decimal = Decimal(0)

        self.position_total_changed: Decimal = Decimal(0)

        self.position_avb_changed: Decimal = Decimal(0)

        self.position_locked_changed: Decimal = Decimal(0)

        self.position_margin_changed: Decimal = Decimal(0)
