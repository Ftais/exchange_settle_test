import time

from settle.service.ExchangeService import ExchangeService


class ResetSymbolBiz:

    def __init__(self, exchange_service: ExchangeService):
        self.exchange_service = exchange_service

    def execute(self, symbol_id: str):
        pass
