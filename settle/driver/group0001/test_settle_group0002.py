from settle.driver.SettleGroupDriver import SettleGroupDriver
from settle.pojo.case.DecimalAccuracy import DecimalAccuracy


# def test_retry():
#     RetryDriver.retry(lambda: r('abcdefg'))
#
#
# def r(abc: str):
#     print(abc)
#     raise NeedRetryException

# def test_unit():
#     driver = SettleGroupDriver("0001")
#     driver.init()
#     print(1)

# def test_run():
#     DecimalAccuracy
#     driver = SettleGroupDriver("0001")
#     driver.start()

def test_run():
    DecimalAccuracy
    driver = SettleGroupDriver("0002")
    driver.start()
    print(1)

# def test_exchange():
#     svc = ExchangeService()
#     ret = svc.get_positions("BTCUSDT-PERPETUAL")
#     print(1)


# def test_t():
#     DecimalAccuracy
#     value = Decimal("44.6")
#     v = value.quantize(1, rounding=ROUND_UP)
#     print(v)
