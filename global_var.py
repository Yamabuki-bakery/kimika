import pyrogram

from database.KimikaDB import KimikaDB

app: pyrogram.Client
SMART_DEAL_WAITING_REPLY = {}
NEW_MEMBER_WATCHING_LIST = {}
# {
#     uid: {
#         chatid: chatid,
#         time: time
#     }
# }
ANTI_REPLAY_LIST: list[int] = []

db: KimikaDB