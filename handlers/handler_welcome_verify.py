import asyncio
import logging
import re

import pyrogram
from utils.util_anti_replay import anti_replay
from botConfig import *
from utils.util_tg_operation import get_user_credit

@anti_replay
async def new_member_welcome(client: pyrogram.Client, message):
    app = client
    # DB = global_var.DB
    if message.chat.id != GALGROUP:
        return
    from_chat_id = message.chat.id
    # await app.forward_messages(chat_id=from_chat_id, from_chat_id=from_chat_id, message_ids=message.id)
    logging.info(f'[Welcome] {message.text}')
    this_user_id = message.entities[0].user.id
    this_user_name = message.entities[0].user.first_name
    bot_flags = "Flags: "

    bot_score = 0
    # check if 3-none account
    credit_result = await get_user_credit(this_user_id)
    if credit_result.photo:
        pass
    else:
        bot_flags += '無頭. '
        bot_score += 1

    if credit_result.username:
        pass
    else:
        bot_flags += '無@. '
        bot_score += 1

    if credit_result.bio:
        pass
    else:
        bot_flags += '無 Bio. '
        bot_score += 1

    if credit_result.new_account:
        bot_flags += '新創號'
        bot_score += 1

    if '超时未验证' in message.text:
        reply_text = f'[@{this_user_name}](tg://user?id={this_user_id}) 驗證超時\n'
        if bot_score > 0:
            reply_text += bot_flags + '\n'
        else:
            reply_text += 'Flags: (無)\n'

        classified = "鐵 bot" if bot_score == 4 else \
            (" bot" if bot_score == 3 else ("可疑" if bot_score == 2 else ("假人" if bot_score == 1 else "真人")))
        reply_text += f'鑑定爲{classified}，送走了'

        logging.info(f'[Welcome] {reply_text}')
        # await app.send_message(chat_id=from_chat_id, text=reply_text)
        return
    if '验证错误' in message.text:
        reply_text = f'[@{this_user_name}](tg://user?id={this_user_id}) 答題錯誤\n'
        if bot_score > 0:
            reply_text += bot_flags
        else:
            reply_text += 'Flags: (無)'

        await app.send_message(chat_id=from_chat_id, text=reply_text)
        return
    if '通过了验证' in message.text:
        used_time = int(re.search(r'通过了验证，用时 (\d+) 秒', message.text)[1])
        reply_text = f'居然有人通過了 ({used_time}) [@{this_user_name}](tg://user?id={this_user_id}) 你是哪道題？\n'
        if bot_score > 0:
            reply_text += bot_flags
        else:
            reply_text += 'Flags: (無)'

        if used_time < 30:
            reply_text += f'\n而且只用了 {used_time}[ ](tg://user?id={ESUONEGOV})秒，你肯定作弊了'

        await app.send_message(chat_id=from_chat_id, text=reply_text)

        rule_msg = await app.send_message(chat_id=from_chat_id, text=GALGROUP_RULE)
        await asyncio.sleep(90)
        await app.delete_messages(chat_id=rule_msg.chat.id, message_ids=rule_msg.id)
        return
