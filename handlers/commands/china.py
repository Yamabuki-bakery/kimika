import pyrogram, random, global_var
from botConfig import *
from myTypes.LearningRecord import LearningRecord
from utils.util_tg_operation import speak


async def china(client: pyrogram.Client, message: pyrogram.types.Message, rtp: float):
    (reply_to_possibility, reply_to_msg_id) = (rtp, message.reply_to_message.id) \
        if message.reply_to_message else (-1, None)

    learningDao = global_var.db.learningDao
    china_records = await learningDao.get_answers(message.chat.id, 'china')

    if china_records:
        china_record: LearningRecord = random.choice(china_records)
        answer_msg = await client.get_messages(KIMIKACACHE, china_record.answer_msg_id)
        await answer_msg.copy(message.chat.id, reply_to_message_id=reply_to_msg_id if random.random() < reply_to_possibility else None)
    else:
        reply_list = CHINA_REPLY_LIST
        await speak(message.chat.id, random.choice(reply_list),
                    reply_to_msg_id if random.random() < reply_to_possibility else None)