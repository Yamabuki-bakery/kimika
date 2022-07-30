import asyncio
import json
import pyrogram

from utils.util_tg_operation import speak, get_user_credit


async def credit(app: pyrogram.Client, message: pyrogram.types.Message, rtp: float):
    (reply_to_possibility, reply_to_msg_id) = (rtp, message.reply_to_message.id) \
        if message.reply_to_message else (-1, None)
    if reply_to_msg_id:
        target_msg = await app.get_messages(chat_id=message.chat.id, message_ids=reply_to_msg_id)
        target_id = target_msg.from_user.id

    else:
        target_id = message.from_user.id

    credit_info = await get_user_credit(target_id, message.chat.id)
    debug_msg = (await speak(message.chat.id, json.dumps(credit_info.__dict__, indent=2, ensure_ascii=False)))[0]
    await asyncio.sleep(90)
    await app.delete_messages(message.chat.id, debug_msg.id)