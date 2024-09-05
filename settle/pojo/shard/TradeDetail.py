from decimal import Decimal

"""
成交明细 -- 现货合约通用部分 
tb_trade_detail

KEY `IDX_ACCOUNT_ID` (`account_id`),
KEY `idx_account_id_order_id` (`account_id`,`order_id`),


"""


class TradeDetail:

    def __init__(self, data=None):
        self.trade_detail_id: int = None

        self.account_id: int = None

        self.ticked_td: int = None

        self.broker_user_id: int = None

        self.order_id: int = None

        self.match_order_id: int = None

        self.match_account_id: int = None

        self.match_broker_user_id: int = None

        self.symbol_id: str = None

        self.side: int = None

        self.quantity: Decimal = None

        self.amount: Decimal = None

        self.price: Decimal = None

        self.token_fee: Decimal = None

        self.fee_rate: Decimal = None

        self.status: int = None

        self.is_maker: int = None

        self.is_close: int = None

        self.fee_token_id: str = None

        self.extra_info: int = None

        if data:
            self.__dict__.update(data)
            self.broker_user_id = int(data.get("broker_user_id"))
            self.match_broker_user_id = int(data.get("match_broker_user_id"))
