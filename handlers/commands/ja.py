import pyrogram, random
from botConfig import *
from utils.util_tg_operation import speak


async def ja(client: pyrogram.Client, message: pyrogram.types.Message, rtp: float):
    (reply_to_possibility, reply_to_msg_id) = (2, message.reply_to_message.id) \
        if message.reply_to_message else (-1, None)
    reply_list = JA_REPLY_LIST
    await speak(message.chat.id, random.choice(reply_list),
                reply_to_msg_id if random.random() < reply_to_possibility else None)