import global_var
import logging
import pyrogram
import pyrogram.errors
import time

from botConfig import *
from utils.util_anti_replay import anti_replay


@anti_replay
async def galgroup_non_member_msg_abuse(client: pyrogram.Client, message: pyrogram.types.Message):
    app = client
    # logging.info(message)
    if message.reply_to_message:
        # see the msg replies to which another one as legal.
        # logging.info(f'💤 Message {message.id} replied to msg {message.reply_to_message_id}, ignoring')
        return

    if not message.from_user:
        # see the msg sent by non-user as legal
        # logging.info(f'💤 Message {message.id} is sent by non-user {message.sender_chat.title}, ignoring')
        return

    if message.service and message.service == pyrogram.enums.MessageServiceType.NEW_CHAT_MEMBERS:
        return

    if message.from_user.id in global_var.NEW_MEMBER_WATCHING_LIST and message.chat.id == \
            global_var.NEW_MEMBER_WATCHING_LIST[message.from_user.id]:
        logging.info(f'[galgroup_non_member] ⚠️ user {message.from_user.first_name} is in watching list, delete this message')
        await message.delete()
        return

        # logging.info(f'🔍 User {message.from_user.id} {message.from_user.first_name} sent message {message.id},'
    #            f' looking for common chats.')

    if await check_common_chat(message.from_user.id, message.from_user.first_name, GALGROUP, app):
        # logging.info(f'User {message.from_user.id} {message.from_user.first_name} is in the chat')
        pass
    else:
        logging.warning(f'[galgroup_non_member] ⚠️ User {message.from_user.id} {message.from_user.first_name} is NOT in the chat!')
        # await app.delete_user_history(GALGROUP, message.from_user.id)
        await message.forward(KIMIKACACHE)
        await app.delete_messages(GALGROUP, message.id)
        await app.ban_chat_member(GALGROUP, message.from_user.id)
        text = f'🛑 **New banned user**\n\n**ID**: {message.from_user.id}\n' \
               f'**Name**: [{message.from_user.first_name}](tg://user?id={message.from_user.id})\n' \
               f'**User**: {"@" + message.from_user.username if message.from_user.username else "None"}\n\n' \
               f'👋🏻 **Action**: Kicked\n' \
               f'🤔 **Reason**: Abuse Telegram bug'
        await app.send_message(GALGROUP, text)


async def check_common_chat(user_id, first_name, target_chat, app: pyrogram.Client):
    galMembersDao = global_var.db.galMembersDao
    # not querying api too much, check local db first
    # cursor = DB.execute('SELECT * FROM members WHERE userid=:target', {'target': user_id})
    name_in_db, last_check_time = await galMembersDao.check_member(user_id)
    if name_in_db is not None:
        logging.info(f'[check_common_chat] ✅📖 User {user_id} {name_in_db} found in db, time {last_check_time}')
        if time.time() - last_check_time < 86400:
            return True

    result = False
    try:
        common = await app.get_common_chats(user_id)
        for chat in common:
            if chat.id == target_chat:
                result = True
                logging.info(f'[check_common_chat] ✅🌐 User {user_id} {first_name} found in (API) common group')
                # DB.execute('REPLACE INTO members VALUES (?,?,?)', (user_id, first_name, int(time.time())))
                await galMembersDao.update_member(user_id, first_name, int(time.time()))
                break
    except pyrogram.errors.PeerIdInvalid:
        logging.error(f'[check_common_chat] ❌ Cannot get common group due to PEER INVALID, try get chat member instead.')
        # chat_member = await app.get_chat_member(target_chat, user_id)
        results = []
        async for m in app.get_chat_members(target_chat, query=first_name,
                                            filter=pyrogram.enums.ChatMembersFilter.SEARCH):
            results.append(m)
        for chat_member in results:
            if chat_member.user.id == user_id:
                logging.info(f'[check_common_chat] ✅🌐 User {user_id} {first_name} found in (API - search) common group')
                result = True
                break

    return result
