from decimal import Decimal

"""
动账流水
tb_balance_flow
"""


class BalanceFlow:

    def __init__(self, data=None):
        self.id: int = None

        self.balanceFlowId: int = None

        self.balanceId: int = None

        self.businessSubject: int = None

        self.accountType: int = None

        self.accountId: int = None

        self.tokenId: str = None

        self.changed: Decimal = None

        self.total: Decimal = None

        self.tickedId: Decimal = None

        if data:
            self.__dict__.update(data)
