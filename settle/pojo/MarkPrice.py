from decimal import Decimal

"""
标记价格
"""


class MarkPrice:
    price: Decimal = None

    """
    发出时间
    """
    time: int = None

    def __init__(self, data=None):
        if data:
            self.__dict__ = data

