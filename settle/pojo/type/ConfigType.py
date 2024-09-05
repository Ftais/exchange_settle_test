from enum import Enum


class ConfigType(Enum):
    EXCHANGE = '/config/{}/exchange/exchange.json'
    USERS = '/config/{}/group/group{}/users/users.json'
    CASE_GROUP_LIST = '/config/{}/group/groups.json'
    CASE = '/config/{}/group/group{}/cases/case{}.json'
    CASE_RUN_LIST = '/config/{}/group/group{}/caseRunList.json'
    DOMAIN = '/config/{}/domain/domain.json'
    SYMBOLS = '/config/{}/group/group{}/symbols/symbols.json'
    JDBC = '/config/{}/jdbc/jdbc.json'


if __main__ == "__name__":