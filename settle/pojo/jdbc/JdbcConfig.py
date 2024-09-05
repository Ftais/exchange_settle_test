class JdbcConfig:

    def __init__(self, data=None):
        self.name: str = None

        self.host: str = None

        self.port: int = None

        self.user: str = None

        self.password: str = None

        self.schema: str = None

        if data:
            self.__dict__.update(data)
