class KillerDao:
    # table killer
    # col userid
    # col chatid

    def __init__(self, db):
        from . import KimikaDB
        self.__kimikaDB: KimikaDB.KimikaDB = db
        assert self.__kimikaDB is not None

    async def check_killer(self, user_id: int, chat_id: int) -> bool:
        cursor = await self.__kimikaDB.execute('SELECT * FROM killer WHERE userid=:uid AND chatid=:cid',
                                               {'uid': user_id, 'cid': chat_id})
        row = await cursor.fetchone()
        if row:
            return True
        else:
            return False

    async def add_killer(self, user_id: int, chat_id: int):
        await self.__kimikaDB.execute('INSERT INTO killer(userid,chatid) VALUES (?,?)', (user_id, chat_id))
        await self.__kimikaDB.commit()

    async def del_killer(self, user_id: int, chat_id: int):
        await self.__kimikaDB.execute('DELETE FROM killer WHERE userid=:uid AND chatid=:cid', {'uid': user_id, 'cid': chat_id})
        await self.__kimikaDB.commit()

    async def get_killer_list(self, chat_id: int) -> list[int]:
        cursor = await self.__kimikaDB.execute('SELECT * FROM killer WHERE chatid=:cid', {'cid': chat_id})
        rows = await cursor.fetchall()
        result: [int] = []
        for row in rows:
            result.append(row[1])

        return result
