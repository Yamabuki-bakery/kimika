class GroupVerifyDao:

    def __init__(self, db):
        from . import KimikaDB
        self.__kimikaDB: KimikaDB.KimikaDB = db
        assert self.__kimikaDB is not None

    async def get_verify_scheme(self, chat_id: int) -> tuple[str | None, bool, bool, bool, bool] | None:
        cursor = await self.__kimikaDB.execute('SELECT * FROM group_verify WHERE chatid=:cid', {'cid': chat_id})
        row = await cursor.fetchone()
        if row:
            use_channel: str | None = row[1]
            use_photo: bool = row[2] == 1
            use_bio: bool = row[3] == 1
            use_username: bool = row[4] == 1
            use_new_account: bool = row[5] == 1
            return use_channel, use_photo, use_bio, use_username, use_new_account
        else:
            return None
