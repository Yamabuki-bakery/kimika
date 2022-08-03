import aiosqlite

from botConfig import *
from .GalMembersDao import GalMembersDao
from .GroupVerifyDao import GroupVerifyDao
from .KillerDao import KillerDao
from .SongDao import SongDao
from .LearningDao import LearningDao


class KimikaDB:
    DB: aiosqlite.Connection
    songDao: SongDao
    groupVerifyDao: GroupVerifyDao
    galMembersDao: GalMembersDao
    killerDao: KillerDao
    learningDao: LearningDao

    async def init(self):
        await self.init_db()
        self.init_dao()

    def init_dao(self):
        self.songDao = SongDao(self)
        self.groupVerifyDao = GroupVerifyDao(self)
        self.galMembersDao = GalMembersDao(self)
        self.killerDao = KillerDao(self)
        self.learningDao = LearningDao(self)

    async def init_db(self):
        self.DB = await aiosqlite.connect(DBFILE)
        await self.DB.execute('CREATE TABLE IF NOT EXISTS members ('
                              'userid INTEGER PRIMARY KEY, '
                              'firstName TEXT, '
                              'lastCheck INTEGER'
                              ')')
        await self.DB.execute('CREATE UNIQUE INDEX IF NOT EXISTS userid_index ON members (userid)')

        await self.DB.execute('CREATE TABLE IF NOT EXISTS killer ('
                              'count INTEGER PRIMARY KEY, '
                              'userid INTEGER, '
                              'chatid INTEGER'
                              ')')

        await self.DB.execute('CREATE TABLE IF NOT EXISTS music ('
                              'count INTEGER PRIMARY KEY, '
                              'songid INTEGER, '
                              'cache_msg_id INTEGER'
                              ')')

        await self.DB.execute('CREATE TABLE IF NOT EXISTS group_verify ('
                              'chatid INTEGER PRIMARY KEY, '
                              'useChannel TEXT, '
                              'usePhoto INTEGER, '
                              'useBio INTEGER, '
                              'useUsername INTEGER, '
                              'useNewAccount INTEGER'
                              ')')

        await self.DB.execute('CREATE TABLE IF NOT EXISTS learning ('
                              'recordid INTEGER PRIMARY KEY, '
                              'fromChatId INTEGER, '
                              'callerUserId INTEGER, '
                              'callerChatId INTEGER, '
                              'answerMsgId INTEGER, '
                              'keyword TEXT,'
                              'learntRespMsgId INTEGER,'
                              'autoTrigger INTEGER'
                              ')')
        await self.DB.commit()

    async def execute(self, *query) -> aiosqlite.Cursor:
        return await self.DB.execute(*query)

    async def commit(self):
        await self.DB.commit()

    async def close(self):
        await self.DB.close()

