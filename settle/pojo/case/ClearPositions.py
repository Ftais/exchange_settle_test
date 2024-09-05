class ClearPositions:
    def __init__(self, data=None):
        self.uid_tag_list = []
        self.symbol_tag_list = []

        if data:
            self.__dict__.update(data)
