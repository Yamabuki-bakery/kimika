import logging

import botConfig
import global_var
import pyrogram


async def learning(client: pyrogram.Client, message: pyrogram.types.Message, twice=False) -> bool:
    (reply_to_possibility, reply_to_msg_id) = (1, message.reply_to_message.id) if message.reply_to_message else (
        -1, None)
    if twice:
        reply_to_msg_id = message.id

    message_text: str = message.text or message.caption or ""
    message_text = message_text.encode('UTF-8').decode('UTF-8')

    learningDao = global_var.db.learningDao

    learning_record = await learningDao.get_answers(message.chat.id, message_text)

    if learning_record is None:
        return False

    answer_msg = await client.get_messages(botConfig.KIMIKACACHE, learning_record.answer_msg_id)
    await answer_msg.copy(message.chat.id, reply_to_message_id=reply_to_msg_id)
    return True


async def forget(client: pyrogram.Client, message: pyrogram.types.Message) -> bool:
    (reply_to_possibility, reply_to_msg_id) = (1, message.reply_to_message.id) if message.reply_to_message else (
    -1, None)
    learningDao = global_var.db.learningDao
    message_text: str = message.text or message.caption or ""
    message_text = message_text.encode('UTF-8').decode('UTF-8')

    if reply_to_msg_id is None:
        return False

    if 'forget' not in message_text.lower():
        return False

    target_msg = await client.get_messages(message.chat.id, reply_to_msg_id)
    target_message_text: str = target_msg.text or target_msg.caption or ""
    target_message_text = target_message_text.encode('UTF-8').decode('UTF-8')

    if '😘' not in target_message_text:
        return False

    result = await learningDao.del_answer(message.chat.id, target_msg.id)
    if result:
        logging.info(f'[forget] {target_message_text} forgot!!')
        await target_msg.delete()
        return True
    else:
        return False