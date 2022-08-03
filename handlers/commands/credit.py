import asyncio
import json
import pyrogram

from utils.util_tg_operation import speak, get_user_credit, get_sender_id, get_chat_credit


async def credit(app: pyrogram.Client, message: pyrogram.types.Message, rtp: float):
    (reply_to_possibility, reply_to_msg_id) = (rtp, message.reply_to_message.id) \
        if message.reply_to_message else (-1, None)
    if reply_to_msg_id:
        target_msg = await app.get_messages(chat_id=message.chat.id, message_ids=reply_to_msg_id)
        target_id = get_sender_id(target_msg)

    else:
        target_id = get_sender_id(message)

    if target_id > 0:
        credit_info = await get_user_credit(target_id, message.chat.id)
    else:
        credit_info = await get_chat_credit(target_id, message.chat.id)
    debug_msg = (await speak(message.chat.id, json.dumps(credit_info.__dict__, indent=2, ensure_ascii=False)))[0]
    await asyncio.sleep(90)
    await app.delete_messages(message.chat.id, debug_msg.id)