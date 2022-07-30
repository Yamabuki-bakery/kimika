import asyncio
import pyrogram
import pyrogram.errors

from botConfig import *


async def help(app: pyrogram.Client, message: pyrogram.types.Message, rtp: float):
    (reply_to_possibility, reply_to_msg_id) = (rtp, message.reply_to_message.id) \
        if message.reply_to_message else (-1, None)
    help_text = KIMIKA_HELP
    help_msg = await app.send_message(chat_id=message.chat.id, text=help_text)
    await asyncio.sleep(60)
    try:
        await app.delete_messages(chat_id=help_msg.chat.id, message_ids=help_msg.id)
        await app.delete_messages(chat_id=help_msg.chat.id, message_ids=message.id)
    except pyrogram.errors.RPCError:
        pass
