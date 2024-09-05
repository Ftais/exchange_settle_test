from decimal import Decimal

from settle.pojo.fee.FeeRate import FeeRate


class User:

    def __init__(self, data=None):
        self.tag: str = None

        self.name: str = None

        self.uid: int = None

        self.uidTag: str = None

        self.masterUid: int = None

        self.spotAccountId: int = None

        self.futuresAccountId: int = None

        self.apiKey: str = None

        self.secretKey: str = None

        """
        trade_fee
        """
        self.fee: dict[str, FeeRate] = None

        self.user_fee_dict: dict[str, FeeRate] = {}

        """
        协议开通杠杆倍数
        """
        self.open_leverage: dict[str, Decimal] = None

        if data:
            self.__dict__.update(data)
