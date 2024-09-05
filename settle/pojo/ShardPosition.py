from decimal import Decimal

"""
仓位表
bb_shard_1.tb_balance_futures_position
bb_shard_2.tb_balance_futures_position
"""


class ShardPosition:
    """
    仓位id
    """
    positionId: int = None

    """
    合约账户
    """
    accountId: int = None

    """
    交易对id
    """
    tokenId: str = None

    """
    仓位开仓价值
    """
    openValue: Decimal = None

    """
    持仓张数
    """
    total: int = None

    """
    平仓挂单张数
    """
    locked: int = None

    """
    可用张数
    """
    available: int = None

    """
    仓位方向 1:多仓  0:空仓
    """
    isLong: int = None

    """
    开仓挂单张数
    """
    openOnBook: int = None

    """
    仓位保证金
    """
    margin: Decimal = None

    """
    开仓挂单冻结保证金
    """
    orderMargin: Decimal = None

    def __init__(self, data=None):
        if data:
            self.__dict__ = data

    """
    计算 数量 = 张数 * 合约乘数
    """

    def getTotalWithMultiplier(self, multiplier: Decimal) -> Decimal:
        return self.total * multiplier

    """
    持仓均价
    """

    def getAveragePriceByMultiplier(self, multiplier: Decimal) -> Decimal:
        return self.openValue / (self.total * multiplier)
