from decimal import Decimal

"""
成交明细 -- 合约 -- 
tb_trade_detail_futures
PRIMARY KEY (`trade_detail_id`)
"""


class TradeDetailFutures:

    def __init__(self, data=None):
        self.trade_detail_id: int = None

        self.account_id: int = None

        self.margin_changed: Decimal = None

        self.pnl: Decimal = None

        self.residual: Decimal = None

        self.index_price: Decimal = None

        self.bankruptcy_price: Decimal = None

        self.version: int = None

        self.extra_info: int = None
        if data:
            self.__dict__.update(data)
