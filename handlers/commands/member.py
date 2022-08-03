import asyncio
import pyrogram
import pyrogram.errors

from utils.util_tg_operation import speak, get_sender_id, get_sender_name


async def member(app: pyrogram.Client, message: pyrogram.types.Message, rtp: float):
    (reply_to_possibility, reply_to_msg_id) = (rtp, message.reply_to_message.id) \
        if message.reply_to_message else (-1, None)
    if reply_to_msg_id:
        target_msg = await app.get_messages(chat_id=message.chat.id, message_ids=reply_to_msg_id)
        target_id = get_sender_id(target_msg)

    else:
        target_id = get_sender_id(message)
    try:
        member_info = await app.get_chat_member(chat_id=message.chat.id, user_id=target_id)
    except pyrogram.errors.UserNotParticipant:
        member_info = "Not a member of this group"

    debug_msg = (await speak(message.chat.id, str(member_info)))[0]
    await asyncio.sleep(90)
    await app.delete_messages(message.chat.id, debug_msg.id)