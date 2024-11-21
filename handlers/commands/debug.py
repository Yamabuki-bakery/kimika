import asyncio
import pyrogram
import pyrogram.errors
import logging

from utils.util_tg_operation import speak


async def debug(message: pyrogram.types.Message, rtp: float):
    (reply_to_possibility, reply_to_msg_id) = (rtp, message.reply_to_message.id) \
        if message.reply_to_message else (-1, None)
    if reply_to_msg_id:
        message_to_send = str(message.reply_to_message)
    else:
        message_to_send = str(message)

    message_to_send = f"```json\n{message_to_send}\n```"
    try:
        debug_msg = (await speak(message.chat.id, message_to_send))[0]
        await asyncio.sleep(90)
        await debug_msg.delete()
    except pyrogram.errors.RPCError as e:
        logging.error(f'[debug] {e}')
        print(message_to_send)