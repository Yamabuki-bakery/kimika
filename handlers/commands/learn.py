import asyncio
import logging

import pyrogram, global_var, re

import botConfig
from myTypes.LearningRecord import LearningRecord
from utils.util_tg_operation import speak

LEARN_HELP = \
    '''學習如何回覆一個關鍵詞，用法：
回覆一個作爲答案的消息，然後

`kimika learn <keyword>`

keyword 字數限制 2~20 字
撤銷學習：使用 forget 回覆一條「我董力！」提示消息'''


async def learn(client: pyrogram.Client, message: pyrogram.types.Message):
    learningDao = global_var.db.learningDao
    (reply_to_possibility, reply_to_msg_id) = (1, message.reply_to_message.id) if message.reply_to_message else (
        -1, None)
    message_text: str = message.text or message.caption or ""
    message_text = message_text.encode('UTF-8').decode('UTF-8')

    try:
        if reply_to_msg_id is None:
            raise ValueError('沒有 reply 到一條 msg 上！')

        matches = re.search(r'learn (\S+)', message_text)

        if matches:
            keyword = matches[1]
        else:
            raise ValueError('沒有找到 keyword！')

        if len(keyword) < 2 or len(keyword) > 20:
            raise ValueError(f'keyword 長度 {len(keyword)} 過於惡俗！')

    except ValueError as err:
        logging.error(f'[learn] {err}')
        help_msg = await message.reply_text(LEARN_HELP, parse_mode=pyrogram.enums.ParseMode.MARKDOWN)
        asyncio.create_task(del_msg_after(help_msg, 10))
        return False

    # let's learn!
    try:
        answer_msg = await client.get_messages(chat_id=message.chat.id, message_ids=reply_to_msg_id)
        cached_msg = await answer_msg.forward(botConfig.KIMIKACACHE)

        learnt_resp_msg = await answer_msg.reply_text(f'{keyword}，\n我董力！ 😘')

        learning_record = LearningRecord()
        learning_record.answer_msg_id = cached_msg.id
        learning_record.keyword = keyword
        learning_record.caller_user_id = message.from_user.id if message.from_user else None
        learning_record.caller_chat_id = message.sender_chat.id if message.sender_chat else None
        learning_record.from_chat_id = message.chat.id
        learning_record.learnt_resp_msg_id = learnt_resp_msg.id
        learning_record.auto_trigger = False

        await learningDao.set_answer(learning_record)
        logging.info(f'[learn] 學會了 {keyword}!')

    except Exception as err:
        logging.error(f'[learn] error occurred when learning! {err}')
        await speak(message.chat.id, 'kimika-sticker/24')
        return False


async def del_msg_after(message: pyrogram.types.Message, after_sec: float):
    await asyncio.sleep(after_sec)
    await message.delete()
