class WaitMoment:

    def __init__(self, data=None):
        self.seconds: int = None
        if data:
            self.__dict__.update(data)
