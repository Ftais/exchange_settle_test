from settle.service.JdbcService import JdbcService


class ShardRouteQueryBiz:

    def __init__(self, jdbc_service: JdbcService):
        self.jdbc_service: JdbcService = jdbc_service
        self.uid_shard_cache: dict[int, int] = {}

    def route_shard_no(self, uid: str) -> int:
        if uid in self.uid_shard_cache:
            return self.uid_shard_cache[uid]
        conn = self.jdbc_service.conn("bb_server")
        row = conn.getOne('select shard_id from tb_account where broker_user_id = %s limit 1', (uid))
        return int(row.get('shard_id')) % 1000

    def route_shard_conn(self, uid: str):
        shard_no: int = self.route_shard_no(uid)
        return self.jdbc_service.conn("bb_shard_" + str(shard_no))
