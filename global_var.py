import pyrogram

from database.KimikaDB import KimikaDB

app: pyrogram.Client
SMART_DEAL_WAITING_REPLY = {}
NEW_MEMBER_WATCHING_LIST = {}
ANTI_REPLAY_LIST: [int] = []

db: KimikaDB