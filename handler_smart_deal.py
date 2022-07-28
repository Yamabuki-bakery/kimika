import global_var, logging, re, pyrogram.errors, asyncio
from botConfig import *
from util_tg_operation import get_sender_id, api_check_common_chat


async def smart_deal(client: pyrogram.Client, message: pyrogram.types.Message):
    app = client
    WAITING_REPLY = global_var.SMART_DEAL_WAITING_REPLY
    in_chat_id = message.chat.id
    sender_id = get_sender_id(message)
    if sender_id not in WAITING_REPLY:
        return

    ask_msg = WAITING_REPLY[sender_id]
    if message.id - ask_msg.id > 10 or in_chat_id != ask_msg.chat.id:
        return

    logging.info('[smart deal] 似乎是有效反饋')
    for flag in SMART_DEAL_FLAGS:
        if not message.text:
            return
        if flag in ask_msg.text:
            action = SMART_DEAL_FLAGS.index(flag)
            if action == 0:
                logging.info('[smart deal] 伸手黨處理 handler')
                if re.search(r"(?<!不)(([好行要y進进])|(ok)|(ao)|(可以)|(gkd)|(yes)|(快点)|(拉我))", message.text,
                             flags=re.IGNORECASE):
                    asyncio.create_task(deal_with_kick_to_rhine(ask_msg))
                    WAITING_REPLY.pop(sender_id)
                    try:
                        pass
                        # await app.delete_messages(chat_id=message.chat.id, message_ids=message.id)
                    except pyrogram.errors.RPCError:
                        logging.error('[smart deal] 消除消息失敗')
                    return
                if re.search(r"(不[好行要近用進])|(no?)|(不可以)|(不.ao)", message.text, flags=re.IGNORECASE):
                    await app.send_message(chat_id=message.chat.id, text='那你說你🐴呢', reply_to_message_id=message.id)
            break

    return


async def deal_with_kick_to_rhine(ask_msg):
    app = global_var.app
    target_msgid = ask_msg.reply_to_message.id
    target_userid = ask_msg.reply_to_message.from_user.id
    target_username = ask_msg.reply_to_message.from_user.first_name
    logging.info(f'[轉移伸手黨] user {target_userid} {target_username} 正在嘗試')
    try:
        if await api_check_common_chat(target_userid, RHINEGROUP):
            logging.warning(f'[轉移伸手黨] ERROR {target_userid} {target_username} 已經在萊茵圖書館。')
            error_msg = await app.send_message(chat_id=ask_msg.chat.id,
                                               text='麻煩懶狗親自造訪\n@RhineDiscussionRoom\n@RhineLibrary\n進行真人快打，3Q 謝謝')
            await asyncio.sleep(60)
            await app.delete_messages(chat_id=error_msg.chat.id, message_ids=[error_msg.id])
            return
    except pyrogram.errors.PeerIdInvalid:
        pass

    try:
        await app.add_chat_members(chat_id=RHINEGROUP, user_ids=target_userid)
        # await app.forward_messages(chat_id=RHINEGROUP, from_chat_id=GALGROUP, message_ids=[target_msgid])
        logging.info(f'[轉移伸手黨] user {target_userid} {target_username} 綁架到萊茵圖書館。')
    except pyrogram.errors.RPCError:
        logging.info(f'[轉移伸手黨] ERROR {target_userid} {target_username} 无法綁架到萊茵圖書館。')
        error_msg = await app.send_message(chat_id=ask_msg.chat.id,
                                           text='拉不動你，麻煩懶狗親自造訪\n@RhineDiscussionRoom\n@RhineLibrary\n進行真人快打，3Q 謝謝')
        await asyncio.sleep(60)
        await app.delete_messages(chat_id=error_msg.chat.id, message_ids=[error_msg.id])
