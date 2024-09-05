"""
保证金率
"""
from decimal import Decimal

from settle.pojo.FuturesRiskLimit import FuturesRiskLimit
from settle.pojo.MarkPrice import MarkPrice
from settle.pojo.RiskRateResult import RiskRateResult
from settle.pojo.ShardPosition import ShardPosition


class RiskRateService:
    """
    计算保证金率
    available == tb_balance.available

    position_dict        key = 交易对名称 value = list ShardPosition

    mark_price_dict      key = 交易对名称 value = MarkPrice

    risk_limit_list_dict key = 交易对名称 value = list FuturesRiskLimit 自行过滤白名单

    基于position_dict做驱动

    """

    @staticmethod
    def calculate(available: Decimal, position_dict: dict[str, list[ShardPosition]],
                  mark_price_dict: dict[str, MarkPrice],
                  risk_limit_list_dict: dict[str, list[FuturesRiskLimit]],
                  multiplier_dict: dict[str, Decimal]) -> RiskRateResult:
        maintain_margin: Decimal = Decimal(0)
        pnl: Decimal = Decimal(0)
        frozen_margin: Decimal = Decimal(0)
        pnl_dict = {}
        maintain_margin_rate_dict = {}
        for symbol_id, positions in position_dict:
            maintain_margin_call_tuple_temp = RiskRateService.maintain_margin_calculate(positions,
                                                                                        risk_limit_list_dict[
                                                                                            symbol_id])
            maintain_margin = maintain_margin + maintain_margin_call_tuple_temp[1]
            maintain_margin_rate_dict[symbol_id] = maintain_margin_call_tuple_temp[0]
            pnl_temp = RiskRateService.pnl_calculate(positions, mark_price_dict[symbol_id], multiplier_dict[symbol_id])
            pnl = pnl + pnl_temp
            pnl_dict[symbol_id] = pnl_temp
            frozen_margin = frozen_margin + RiskRateService.frozen_margin_calculate(positions)
        right = available + pnl + frozen_margin
        risk_rate: Decimal = Decimal(0)
        result: RiskRateResult = RiskRateResult()
        if right == Decimal(0):
            result.riskRate = risk_rate
        else:
            result.riskRate = maintain_margin / right
        for symbol_id, positions in position_dict:
            result.liqPrice_dict[symbol_id] = RiskRateService.liq_price_calculate(symbol_id, available, pnl_dict,
                                                                                  maintain_margin,
                                                                                  positions, multiplier_dict[symbol_id])

        return result

    """
    破产价
    """

    @staticmethod
    def bank_price_calculate(symbol_id: str, liq_price: Decimal, positions: list[ShardPosition],
                             maintain_margin_rate: Decimal, multiplier: Decimal) -> dict[str, Decimal]:
        long_bank_price = Decimal(0)
        short_bank_price = Decimal(0)
        for position in positions:
            if position.isLong:
                long_bank_price = liq_price - position.getAveragePriceByMultiplier(multiplier) * maintain_margin_rate
            else:
                long_bank_price = liq_price + position.getAveragePriceByMultiplier(multiplier) * maintain_margin_rate
        result = {}
        if long_bank_price != Decimal(0):
            result["long"] = long_bank_price
        if short_bank_price != Decimal(0):
            result["short"] = short_bank_price
        return result

    """
    爆仓价
    """

    @staticmethod
    def liq_price_calculate(symbol_id: str, available: Decimal, pnl_dict: dict[str, Decimal], maintain_margin: Decimal,
                            positions: list[ShardPosition], multiplier: Decimal) -> Decimal:
        other_pnl: Decimal = Decimal(0)
        for inner_symbol_id, pnl in pnl_dict:
            if symbol_id != inner_symbol_id:
                other_pnl = other_pnl + pnl
        long_open_value = Decimal(0)
        short_open_value = Decimal(0)
        long_amount = Decimal(0)
        short_amount = Decimal(0)
        for position in positions:
            if position.isLong == 1:
                long_open_value = position.openValue
                long_amount = position.total * multiplier
            else:
                short_open_value = position.openValue
                short_amount = position.total * multiplier
        return (available + other_pnl - maintain_margin - abs(long_open_value) + abs(short_open_value)) / (
                Decimal(-1) * abs(long_amount) + abs(short_amount))

    """
    计算冻结保证金
    """

    @staticmethod
    def frozen_margin_calculate(positions: list[ShardPosition]) -> Decimal:
        frozen_margin: Decimal = Decimal(0)
        for position in positions:
            frozen_margin = frozen_margin + position.orderMargin + position.margin
        return frozen_margin

    """
    计算pnl
    """

    @staticmethod
    def pnl_calculate(positions: list[ShardPosition], mark_price: MarkPrice, multiplier: Decimal) -> Decimal:
        pnl: Decimal = Decimal(0)
        for position in positions:
            if position.isLong == 1:
                pnl = pnl + position.openValue - mark_price.price * position.total * multiplier
        return pnl

    """
    计算维持保证金
    返回值是 (维持保证金率, 维持保证金)
    """

    @staticmethod
    def maintain_margin_calculate(positions: list[ShardPosition],
                                  risk_limit_list: list[FuturesRiskLimit]) -> tuple[Decimal, Decimal]:

        qty: int = 0
        total_open_value: Decimal = Decimal(0)
        for position in positions:
            qty = qty + position.total + position.openOnBook
            total_open_value = total_open_value + position.openValue
        risk_limit_list = sorted(risk_limit_list, key=RiskRateService.risk_limit_sort)
        target_risk_limit: FuturesRiskLimit = None
        for risk_limit in risk_limit_list:
            if risk_limit.riskLimitAmount >= qty:
                target_risk_limit = risk_limit
                break
        if target_risk_limit is None:
            target_risk_limit = risk_limit_list[len(risk_limit_list) - 1]
        return target_risk_limit.maintainMargin, total_open_value * target_risk_limit.maintainMargin

    @staticmethod
    def risk_limit_sort(x: FuturesRiskLimit):
        return x.riskLimitAmount
