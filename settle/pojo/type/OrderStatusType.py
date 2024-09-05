from enum import Enum


class OrderStatusType(Enum):
    PENDING_NEW = 10
    NEW = 0
    PARTIALLY_FILLED = 1
    FILLED = 2
    CANCELED = 4
    REJECTED = 8
    PARTIALLY_CANCELED = 5

    @staticmethod
    def is_canceled(status) -> bool:
        return status in [OrderStatusType.CANCELED.value, OrderStatusType.REJECTED.value,
                          OrderStatusType.PARTIALLY_CANCELED.value]

    @staticmethod
    def is_in_exchange(status) -> bool:
        return status in [OrderStatusType.NEW.value, OrderStatusType.PARTIALLY_FILLED.value]
