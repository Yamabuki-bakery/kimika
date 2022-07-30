class SongDao:

    def __init__(self, db):
        from . import KimikaDB
        self.__kimikaDB: KimikaDB.KimikaDB = db
        assert self.__kimikaDB is not None

    async def get_cached_song(self, song_id: int) -> int | None:
        cursor = await self.__kimikaDB.execute('SELECT cache_msg_id FROM music WHERE songid=:sid', {'sid': song_id})
        row = await cursor.fetchone()
        if row:
            return int(row[0])
        else:
            return None

    async def delete_song_cache(self, song_id: int):
        await self.__kimikaDB.execute('DELETE FROM music WHERE songid=:sid', {'sid': song_id})
        await self.__kimikaDB.commit()

    async def save_song_cache(self, song_id: int, cache_msg_id: int):
        await self.__kimikaDB.execute('INSERT INTO music(songid, cache_msg_id) VALUES (?,?)', (song_id, cache_msg_id))
        await self.__kimikaDB.commit()
