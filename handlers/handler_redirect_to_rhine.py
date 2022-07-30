import logging, pyrogram, asyncio, global_var
from utils.util_tg_operation import get_sender_id
from utils.util_anti_replay import anti_replay


@anti_replay
async def redirect_to_rhine(client: pyrogram.Client, message: pyrogram.types.Message):
    app = client
    WAITING_REPLY = global_var.SMART_DEAL_WAITING_REPLY
    flag = '\U0001F440'
    resp2user = f'我知道有資源群和頻道，你要進嗎？我可以拉你進 {flag}'
    resp2channel = '伸手黨速爬'

    # ask_msg = None
    if message.from_user:
        # nonlocal ask_msg
        logging.info(f'[伸手黨] Message {message.id} is sent by user {message.from_user.id}, reply')
        ask_msg = await app.send_message(chat_id=message.chat.id, text=resp2user, reply_to_message_id=message.id)
        WAITING_REPLY.update({message.from_user.id: ask_msg})
        # print(WAITING_REPLY)
    else:
        logging.info(f'[伸手黨 - 頻道] Message {message.id} is sent by non-user {message.sender_chat.title}, reply')
        ask_msg = await app.send_message(chat_id=message.chat.id, text=resp2channel, reply_to_message_id=message.id)

    await asyncio.sleep(60)
    if (message.text and len(message.text) > 20) or message.caption:
        pass
    else:
        await app.delete_messages(chat_id=message.chat.id, message_ids=[ask_msg.id, message.id])
    try:
        WAITING_REPLY.pop(get_sender_id(message))
    except KeyError:
        pass
