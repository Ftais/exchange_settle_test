from settle.pojo.case.CancelUserOrders import CancelUserOrders
from settle.pojo.case.Case import Case
from settle.pojo.case.CaseAction import CaseAction
from settle.pojo.case.ClearPositions import ClearPositions
from settle.pojo.case.PlaceOrder import PlaceOrder
from settle.pojo.case.PredictTradeDetail import PredictTradeDetail
from settle.pojo.case.PriceBaseMarkPrice import PriceBaseMarkPrice
from settle.pojo.case.PriceBaseTickerPrice import PriceBaseTickerPrice
from settle.pojo.case.RefreshContext import RefreshContext
from settle.pojo.case.ResetPriceBaseMarkPrice import ResetPriceBaseMarkPrice
from settle.pojo.case.ResetSymbol import ResetSymbol
from settle.pojo.case.Symbol import Symbol
from settle.pojo.case.WaitMoment import WaitMoment
from settle.pojo.type.CaseActionType import CaseActionType
from settle.pojo.type.ConfigType import ConfigType
from settle.utils.config.ConfigUtils import ConfigUtils
from settle.utils.json.JsonUtils import JsonUtils


class CaseBuilder:

    @staticmethod
    def load_all_run_cases() -> dict[str, list[Case]]:
        group_dict = {}
        groups = CaseBuilder.get_groups()
        for group_id in groups:
            run_list: list = CaseBuilder.get_run_list(group_id)
            case_list: list = []
            for case_id in run_list:
                case_list.append(CaseBuilder.get_group_run_case(group_id, case_id))
            group_dict[group_id] = case_list
        return group_dict

    """
    加载单个组
    """

    @staticmethod
    def load_one_group_cases(group_id: str) -> list[Case]:
        run_list: list = CaseBuilder.get_run_list(group_id)
        case_list: list[Case] = []
        for case_id in run_list:
            case_list.append(CaseBuilder.get_group_run_case(group_id, case_id))
        return case_list

    @staticmethod
    def get_symbols(group_id: str) -> list[Symbol]:
        return JsonUtils.from_json(ConfigUtils.get_symbols(group_id), Symbol)

    @staticmethod
    def get_groups() -> list[str]:
        return JsonUtils.of(ConfigUtils.get_config_content(ConfigType.CASE_GROUP_LIST))

    @staticmethod
    def get_run_list(group_id: str) -> list[str]:
        return JsonUtils.of(ConfigUtils.get_case_group_case_run_list(group_id))

    @staticmethod
    def get_group_run_case(group_id: str, case_id: str) -> Case:
        c = Case()
        origin_str = ConfigUtils.get_group_run_case(group_id, case_id)
        origin_dict = JsonUtils.of(origin_str)
        c.id = origin_dict['id']
        c.tag = origin_dict['tag']
        c.type = origin_dict['type']
        case_actions_list: list = origin_dict['case_actions']
        c.case_actions = []
        for case_action in case_actions_list:
            action = CaseAction()
            action.case_action_type = CaseActionType.get_case_action_type(case_action['case_action_type'])
            if action.case_action_type == CaseActionType.RESET_LAST_PRICE_TO_MARK_PRICE:
                action.reset_last_price_to_mark_price = JsonUtils.from_json(
                    JsonUtils.dict_to_json(case_action['reset_last_price_to_mark_price']), ResetPriceBaseMarkPrice)
            if action.case_action_type == CaseActionType.ORDER:
                action.order_action = JsonUtils.from_json(JsonUtils.dict_to_json(case_action['order_action']),
                                                          PlaceOrder)
                if 'price_base_mark_price' in case_action['order_action']:
                    action.order_action.price_base_mark_price = JsonUtils.from_json(
                        JsonUtils.dict_to_json(case_action['order_action']['price_base_mark_price']),
                        PriceBaseMarkPrice)
                if 'price_base_ticker_price' in case_action['order_action']:
                    action.order_action.price_base_ticker_price = JsonUtils.from_json(
                        JsonUtils.dict_to_json(case_action['order_action']['price_base_ticker_price']),
                        PriceBaseTickerPrice)
            if action.case_action_type == CaseActionType.RESET_SYMBOL:
                action.reset_symbol = JsonUtils.from_json(
                    JsonUtils.dict_to_json(case_action['reset_symbol']), ResetSymbol)
            if action.case_action_type == CaseActionType.SETTLE_CHECK:
                action.predict_trade_details = JsonUtils.from_json(
                    JsonUtils.dict_to_json(case_action['predict_trade_details']), PredictTradeDetail)
            if action.case_action_type == CaseActionType.REFRESH_CONTEXT:
                action.refresh_context = JsonUtils.from_json(
                    JsonUtils.dict_to_json(case_action['refresh_context']), RefreshContext)
            if action.case_action_type == CaseActionType.CANCEL_USER_ORDERS:
                action.cancel_user_orders = CancelUserOrders(case_action)
            if action.case_action_type == CaseActionType.CLEAR_POSITION:
                action.clear_positions = ClearPositions(case_action)
            if action.case_action_type == CaseActionType.WAIT_MOMENT:
                action.wait_moment = WaitMoment(case_action)
            c.case_actions.append(action)
        return c
