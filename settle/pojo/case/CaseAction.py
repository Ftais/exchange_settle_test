from settle.pojo.case.CancelUserOrders import CancelUserOrders
from settle.pojo.case.ClearPositions import ClearPositions
from settle.pojo.case.PlaceOrder import PlaceOrder
from settle.pojo.case.PredictTradeDetail import PredictTradeDetail
from settle.pojo.case.RefreshContext import RefreshContext
from settle.pojo.case.ResetPriceBaseMarkPrice import ResetPriceBaseMarkPrice
from settle.pojo.case.ResetSymbol import ResetSymbol
from settle.pojo.case.WaitMoment import WaitMoment
from settle.pojo.type.CaseActionType import CaseActionType


class CaseAction:
    def __init__(self, data=None):
        self.case_action_type: CaseActionType = None
        self.reset_last_price_to_mark_price: ResetPriceBaseMarkPrice = None
        self.order_action: PlaceOrder = None
        self.reset_symbol: ResetSymbol = None
        self.predict_trade_details: list[PredictTradeDetail] = None
        self.refresh_context: RefreshContext = None
        self.cancel_user_orders: CancelUserOrders = None
        self.wait_moment: WaitMoment = None
        self.clear_positions: ClearPositions = None
        if data:
            self.__dict__.update(data)
