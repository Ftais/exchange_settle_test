from enum import Enum


class CaseActionType(Enum):
    RESET_LAST_PRICE_TO_MARK_PRICE = "RESET_LAST_PRICE_TO_MARK_PRICE"
    ORDER = "ORDER"
    RESET_SYMBOL = "RESET_SYMBOL"
    SETTLE_CHECK = "SETTLE_CHECK"
    REFRESH_CONTEXT = "REFRESH_CONTEXT"
    CANCEL_USER_ORDERS = "CANCEL_USER_ORDERS"
    WAIT_MOMENT = "WAIT_MOMENT"
    CLEAR_POSITION = "CLEAR_POSITION"

    @staticmethod
    def get_case_action_type(value):
        if value == CaseActionType.RESET_LAST_PRICE_TO_MARK_PRICE.value:
            return CaseActionType.RESET_LAST_PRICE_TO_MARK_PRICE
        if value == CaseActionType.ORDER.value:
            return CaseActionType.ORDER
        if value == CaseActionType.RESET_SYMBOL.value:
            return CaseActionType.RESET_SYMBOL
        if value == CaseActionType.SETTLE_CHECK.value:
            return CaseActionType.SETTLE_CHECK
        if value == CaseActionType.REFRESH_CONTEXT.value:
            return CaseActionType.REFRESH_CONTEXT
        if value == CaseActionType.CANCEL_USER_ORDERS.value:
            return CaseActionType.CANCEL_USER_ORDERS
        if value == CaseActionType.WAIT_MOMENT.value:
            return CaseActionType.WAIT_MOMENT
        if value == CaseActionType.CLEAR_POSITION.value:
            return CaseActionType.CLEAR_POSITION
