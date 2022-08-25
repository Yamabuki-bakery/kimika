import pyrogram, random, global_var, asyncio
from botConfig import *
from myTypes.LearningRecord import LearningRecord
from utils.util_tg_operation import speak


async def random_reply(client: pyrogram.Client, message: pyrogram.types.Message, rtp: float) -> bool:
    (reply_to_possibility, reply_to_msg_id) = (rtp, message.reply_to_message.id) if message.reply_to_message else (
    -1, None)
    await asyncio.sleep(random.random() * 4)

    learningDao = global_var.db.learningDao
    random_records = await learningDao.get_answers(message.chat.id, 'random')

    if random_records:
        random_record: LearningRecord = random.choice(random_records)
        answer_msg = await client.get_messages(KIMIKACACHE, random_record.answer_msg_id)
        if reply_to_msg_id:
            await answer_msg.copy(message.chat.id, reply_to_message_id=reply_to_msg_id)
        else:
            await answer_msg.copy(message.chat.id,
                                  reply_to_message_id=message.id if random.random() < reply_to_possibility else None)

    else:
        reply_list = NOTHING_REPLY_LIST
        if reply_to_msg_id:
            await speak(message.chat.id, random.choice(reply_list), reply_to_msg_id)
        else:
            await speak(message.chat.id, random.choice(reply_list),
                        message.id if random.random() < reply_to_possibility else None)

    return True
