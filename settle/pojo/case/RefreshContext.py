class RefreshContext:

    def __init__(self, data=None):
        self.refresh_id: int

        self.refresh_balance_user_list: list[int] = None

        self.refresh_position_user_list: list[int] = None

        if data:
            self.__dict__.update(data)
