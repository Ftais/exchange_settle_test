from decimal import Decimal


class RiskRateResult:
    riskRate: Decimal = None

    liqPrice_dict: dict[str, Decimal] = {}

    bankPrice_dict: dict[str, dict[str, Decimal]] = {}

    def __init__(self, data=None):
        if data:
            self.__dict__ = data
