from time import sleep

from settle.utils.retry.NeedRetryException import NeedRetryException


class RetryDriver:
    """
    max_attempts为一共尝试的次数
    """

    @staticmethod
    def retry(func, max_attempts=3, interval_time_s=1):
        for i in range(max_attempts):
            try:
                return func()
            except NeedRetryException as e:
                sleep(interval_time_s)
                print(e.origin_exception)
                if (i + 1 < max_attempts):
                    extra_msg = ''
                    if e.extra_msg:
                        extra_msg = e.extra_msg
                    print(extra_msg + " 尝试重试")
                else:
                    extra_msg = ''
                    if e.extra_msg:
                        extra_msg = e.extra_msg
                    print(extra_msg + " 完全失败")
                    if e.origin_exception:
                        raise e.origin_exception
                    else:
                        raise e
                continue

    @staticmethod
    def trigger_retry():
        raise NeedRetryException
