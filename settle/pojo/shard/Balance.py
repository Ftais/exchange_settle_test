from decimal import Decimal

"""
资产、余额
tb_balance
"""


class Balance:

    def __init__(self, data=None):
        self.balance_id: int = None

        self.account_type: int = None

        self.account_id: int = None

        self.token_id: str = None

        self.broker_user_id: str = None

        self.total: Decimal = None

        self.locked: Decimal = None

        self.available: Decimal = None

        self.flow_id: int = None

        if data:
            self.__dict__.update(data)
