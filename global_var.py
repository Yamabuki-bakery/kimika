import pyrogram, sqlite3

app: pyrogram.Client
DB: sqlite3.Connection
SMART_DEAL_WAITING_REPLY = {}
NEW_MEMBER_WATCHING_LIST = {}