class ResetSymbol:

    def __init__(self, data=None):
        self.symbol_id: str = None
        if data:
            self.__dict__.update(data)
