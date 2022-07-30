import asyncio
import pyrogram

from utils.util_tg_operation import speak


async def debug(message: pyrogram.types.Message, rtp: float):
    (reply_to_possibility, reply_to_msg_id) = (rtp, message.reply_to_message.id) \
        if message.reply_to_message else (-1, None)
    if reply_to_msg_id:
        debug_msg = (await speak(message.chat.id, str(message.reply_to_message)))[0]
    else:
        debug_msg = (await speak(message.chat.id, str(message)))[0]
    await asyncio.sleep(90)
    await debug_msg.delete()