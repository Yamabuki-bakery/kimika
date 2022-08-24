import botConfig
import global_var
import pyrogram


async def learning(client: pyrogram.Client, message: pyrogram.types.Message) -> bool:
    (reply_to_possibility, reply_to_msg_id) = (1, message.reply_to_message.id) if message.reply_to_message else (
    -1, None)
    message_text: str = message.text or message.caption or ""
    message_text = message_text.encode('UTF-8').decode('UTF-8')

    learningDao = global_var.db.learningDao

    learning_record = await learningDao.get_answers(message.chat.id, message_text)

    if learning_record is None:
        return False

    answer_msg = await client.get_messages(botConfig.KIMIKACACHE, learning_record.answer_msg_id)
    await answer_msg.copy(message.chat.id, reply_to_message_id=reply_to_msg_id)
    return True
