"""
{'status': 200, 'err': '', 'data': {'bitField0_': 0, 'bookOrders_': [{'orderId_': 1723241221554521600, 'price_': '85000.000000000000000000', 'quantity_': '120.000000000000000000', 'amount_': '10200000.000000000000000000', 'accountId_': 1710237525451354624, 'brokerUserId_': '', 'brokerId_': 9001, 'brokerName_': '', 'exchangeId_': 301, 'matchExchangeId_': 0, 'memoizedIsInitialized': 1, 'unknownFields': {'fields': {}}, 'memoizedSize': -1, 'memoizedHashCode': 0}], 'responseCode_': 0, 'memoizedIsInitialized': 1, 'unknownFields': {'fields': {}}, 'memoizedSize': -1, 'memoizedHashCode': 0}}
"""
from decimal import Decimal


class ExchangeOrder:

    def __init__(self, data=None):
        self.order_id = None
        self.price = None
        self.account_id = None
        self.quantity = None
        self.amount = None
        if data:
            self.__dict__.update(data)
            self.order_id = data['orderId_']
            self.price = Decimal(data['price_'])
            self.account_id = data['accountId_']
            self.quantity = Decimal(data['quantity_'])
            self.amount = Decimal(data['amount_'])
