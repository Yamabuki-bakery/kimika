import asyncio, sqlite3
import global_var

from botConfig import *


async def db_async(conn: sqlite3.Connection, *query) -> sqlite3.Cursor:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: conn.execute(query[0], query[1]))


async def dbcommit_async(conn: sqlite3.Connection) -> None:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: conn.commit())


async def init_db():
    global_var.DB = sqlite3.connect(DBFILE, check_same_thread=False)
    global_var.DB.execute('CREATE TABLE IF NOT EXISTS members ('
                              'userid INTEGER PRIMARY KEY, '
                              'firstName TEXT, '
                              'lastCheck INTEGER'
                          ')')
    global_var.DB.execute('CREATE UNIQUE INDEX IF NOT EXISTS userid_index ON members (userid)')

    global_var.DB.execute('CREATE TABLE IF NOT EXISTS killer ('
                              'count INTEGER PRIMARY KEY, '
                              'userid INTEGER, '
                              'chatid INTEGER'
                          ')')

    global_var.DB.execute('CREATE TABLE IF NOT EXISTS music ('
                              'count INTEGER PRIMARY KEY, '
                              'songid INTEGER, '
                              'cache_msg_id INTEGER'
                          ')')

    global_var.DB.execute('CREATE TABLE IF NOT EXISTS group_verify ('
                              'chatid INTEGER PRIMARY KEY, '
                              'useChannel TEXT, '
                              'usePhoto INTEGER, '
                              'useBio INTEGER, '
                              'useUsername INTEGER, '
                              'useNewAccount INTEGER'
                          ')')
    global_var.DB.commit()
