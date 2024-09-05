from decimal import Decimal

"""
风险限额
档位阶梯
"""


class FuturesRiskLimit:
    riskLimitId: int = None

    symbolId: str = None

    """
    阶梯限额
    """
    riskLimitAmount: Decimal = None

    """
    维持保证金率
    """
    maintainMargin: Decimal = None

    initialMargin: Decimal = None

    """
    是否是白名单阶梯
    """
    isWhite: int = None

    def __init__(self, data=None):
        if data:
            self.__dict__ = data
