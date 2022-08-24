import pyrogram, asyncio, random
from botConfig import *
from utils.util_tg_operation import speak


async def random_reply(client: pyrogram.Client, message: pyrogram.types.Message, rtp: float) -> bool:
    (reply_to_possibility, reply_to_msg_id) = (rtp, message.reply_to_message.id) if message.reply_to_message else (-1, None)
    await asyncio.sleep(random.random() * 4)
    reply_list = NOTHING_REPLY_LIST
    if reply_to_msg_id:
        await speak(message.chat.id, random.choice(reply_list), reply_to_msg_id)
    else:
        await speak(message.chat.id, random.choice(reply_list), message.id if random.random() < reply_to_possibility else None)

    return True