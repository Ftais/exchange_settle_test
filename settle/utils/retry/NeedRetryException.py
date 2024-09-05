class NeedRetryException(Exception):

    def __init__(self, origin_exception: Exception = None, extra_msg: str = None):
        self.origin_exception = origin_exception
        self.extra_msg = extra_msg
