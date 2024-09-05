from decimal import Decimal

from settle.service.DomainService import DomainService
from settle.service.MarkPriceService import MarkPriceService


class MarkPriceBiz:

    def __init__(self, domain_service: DomainService):
        self.domain_service = domain_service

    def get_mark_price(self, symbol_id: str) -> Decimal:
        return MarkPriceService.get_mark_price(self.domain_service.get_open_api_domain(), symbol_id)
