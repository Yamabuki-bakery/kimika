class GalMembersDao:

    def __init__(self, db):
        from . import KimikaDB
        self.__kimikaDB: KimikaDB.KimikaDB = db
        assert self.__kimikaDB is not None

    async def check_member(self, user_id: int) -> tuple[str | None, int | None]:
        cursor = await self.__kimikaDB.execute('SELECT * FROM members WHERE userid=:target', {'target': user_id})
        row = await cursor.fetchone()
        if row:
            assert row[0] == user_id
            first_name = row[1]
            last_check_time = row[2]
            return first_name, last_check_time
        else:
            return None, None

    async def update_member(self, user_id: int, first_name: str, timestamp: int):
        await self.__kimikaDB.execute('REPLACE INTO members VALUES (?,?,?)', (user_id, first_name, timestamp))
        # DB.commit()
        await self.__kimikaDB.commit()
