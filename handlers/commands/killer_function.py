import asyncio

import pyrogram, global_var, logging
from datetime import datetime
import pyrogram.errors
from datetime import timedelta
from botConfig import *
from utils.util_tg_operation import speak, get_sender_id, get_sender_name, get_user_credit, get_chat_credit


class UniUser:
    type: int  # 0: user; 1: chat
    uid: int
    display_name: str
    username: str | None

    async def init(self, uid: int) -> None:
        self.uid = uid
        if uid > 0:
            self.type = 0
            try:
                info: pyrogram.types.User = await global_var.app.get_users(uid)
                self.display_name = info.first_name
                self.username = info.username
            except Exception:
                self.display_name = f'Unknown User ({uid})'
                self.username = None
        else:
            self.type = 1
            try:
                info: pyrogram.types.Chat = await global_var.app.get_chat(uid)
                self.display_name = info.title
                self.username = info.username
            except Exception:
                self.display_name = f'Unknown Chat ({uid})'
                self.username = None


async def killer_list(app: pyrogram.Client, message: pyrogram.types.Message):
    killerDao = global_var.db.killerDao
    killer_ids = await killerDao.get_killer_list(message.chat.id)
    resp_text = 'List of killers:\n'
    for killer_id in killer_ids:
        mUser = UniUser()
        await mUser.init(killer_id)
        resp_text += f'[{mUser.display_name}](tg://user?id={mUser.uid})\n'

    await app.send_message(chat_id=message.chat.id, text=resp_text)


async def killer_del(app: pyrogram.Client, message: pyrogram.types.Message, rtp: float):
    (reply_to_possibility, reply_to_msg_id) = (rtp, message.reply_to_message.id) \
        if message.reply_to_message else (-1, None)
    killerDao = global_var.db.killerDao
    # 檢查 reply 到人沒有
    # 檢查此人管理員權限
    try:
        if reply_to_msg_id is None:
            raise ValueError(f'[killer del] 沒有 reply 到人身上')

        caller_id = get_sender_id(message)
        caller_member = await app.get_chat_member(chat_id=message.chat.id, user_id=caller_id)
        target_msg = await app.get_messages(chat_id=message.chat.id, message_ids=reply_to_msg_id)
        target_id = get_sender_id(target_msg)

        if caller_member.status != pyrogram.enums.ChatMemberStatus.ADMINISTRATOR and \
                caller_member.status != pyrogram.enums.ChatMemberStatus.OWNER:
            raise ValueError(f'[killer del] 此人 {get_sender_name(message)} 不是管理員')

        target_user = UniUser()
        await target_user.init(target_id)
        caller_user = UniUser()
        await caller_user.init(caller_id)
        logging.info(f'[killer del] {caller_user.display_name} 要消除 killer {target_user.display_name}')

        if not await killerDao.check_killer(target_id, message.chat.id):
            raise ValueError(f'[killer del] 此人 {target_user.display_name} 不在 killer 數據庫')

        await killerDao.del_killer(target_id, message.chat.id)

        resp_text = f'🤔**Removed Killer**\n\n' \
                    f'**ID**: [{target_user.display_name}](tg://user?id={target_id})\n' \
                    f'**Username**: {"@" + target_user.username if target_user.username else "None"}\n\n' \
                    f'👋🏻 **Action**: Revoked\n' \
                    f'🤔 **Reason**: Invoked by admin [{get_sender_name(message)}](tg://user?id={caller_id})'

        await app.send_message(chat_id=message.chat.id, text=resp_text)

    except (pyrogram.errors.RPCError, ValueError) as e:
        logging.error(e)
        await speak(message.chat.id, 'kimika-sticker/3')  # 笑嘻了


async def killer_add(app: pyrogram.Client, message: pyrogram.types.Message, rtp: float):
    (reply_to_possibility, reply_to_msg_id) = (rtp, message.reply_to_message.id) \
        if message.reply_to_message else (-1, None)
    killerDao = global_var.db.killerDao
    # 檢查 reply 到人沒有
    # 檢查此人管理員權限
    try:
        if reply_to_msg_id is None:
            raise ValueError(f'[killer add] 沒有 reply 到人身上')

        caller_id = get_sender_id(message)
        caller_member = await app.get_chat_member(chat_id=message.chat.id, user_id=caller_id)
        target_msg = await app.get_messages(chat_id=message.chat.id, message_ids=reply_to_msg_id)
        target_id = get_sender_id(target_msg)

        if caller_member.status != pyrogram.enums.ChatMemberStatus.ADMINISTRATOR and \
                caller_member.status != pyrogram.enums.ChatMemberStatus.OWNER:
            raise ValueError(f'[killer add] 此人 {get_sender_name(message)} 不是管理員')

        target_user = UniUser()
        await target_user.init(target_id)
        caller_user = UniUser()
        await caller_user.init(caller_id)
        logging.info(f'[killer add] {caller_user.display_name} 要增加 killer {target_user.display_name}')

        if await killerDao.check_killer(target_id, message.chat.id):
            raise ValueError(f'[killer add] 此人 {target_user.display_name} 已在 killer 數據庫')

        await killerDao.add_killer(target_id, message.chat.id)

        resp_text = f'🤔**New Killer**\n\n' \
                    f'**ID**: [{target_user.display_name}](tg://user?id={target_id})\n' \
                    f'**Username**: {"@" + target_user.username if target_user.username else "None"}\n\n' \
                    f'👋🏻 **Action**: Granted\n' \
                    f'🤔 **Reason**: Invoked by admin [{get_sender_name(message)}](tg://user?id={caller_id})'

        await app.send_message(chat_id=message.chat.id, text=resp_text)

    except (pyrogram.errors.RPCError, ValueError) as e:
        logging.error(e)
        await speak(message.chat.id, 'kimika-sticker/3')  # 笑嘻了


async def wipe(app: pyrogram.Client, message: pyrogram.types.Message, rtp: float):
    (reply_to_possibility, reply_to_msg_id) = (rtp, message.reply_to_message.id) \
        if message.reply_to_message else (-1, None)
    killerDao = global_var.db.killerDao
    try:
        # 檢查自身權限
        my_membership = await app.get_chat_member(chat_id=message.chat.id, user_id='me')
        if my_membership.status != pyrogram.enums.ChatMemberStatus.ADMINISTRATOR and \
                my_membership.status != pyrogram.enums.ChatMemberStatus.OWNER:
            raise ValueError('[wipe] 俺不是管理員')
        else:
            if my_membership.privileges.can_delete_messages and my_membership.privileges.can_restrict_members:
                pass
            else:
                raise ValueError('[wipe] 權限不足')
        # 檢查調用人 killer 權限
        caller_id = get_sender_id(message)

        if not await killerDao.check_killer(caller_id, message.chat.id):
            raise ValueError(f'[wipe] 此人 {get_sender_name(message)} 不是 killer')
        # 檢查目標是否爲 空，kimika，管理員，調用人
        if reply_to_msg_id is None:
            raise ValueError(f'[wipe] 沒有 reply 到人身上')

        target_msg = await app.get_messages(chat_id=message.chat.id, message_ids=reply_to_msg_id)
        target_id = get_sender_id(target_msg)

        if caller_id == target_id:
            raise ValueError(f'[wipe] 此人 {get_sender_name(message)} 嘗試橄欖自己')

        try:
            target_member = await app.get_chat_member(chat_id=message.chat.id, user_id=target_id)
            if target_member.chat is not None:
                # in case of chat member banned
                raise pyrogram.errors.UserNotParticipant
            if target_member.user.is_self:
                raise ValueError(f'[wipe] 此人 {get_sender_name(message)} 嘗試橄欖 kimika')
        except pyrogram.errors.UserNotParticipant:
            logging.info('[wipe] UserNotParticipant，爲何不直接橄欖呢')
            target_member = None

        if target_member is not None and \
                (target_member.status == pyrogram.enums.ChatMemberStatus.ADMINISTRATOR or
                 target_member.status == pyrogram.enums.ChatMemberStatus.OWNER):
            raise ValueError(f'[wipe] 此人 {get_sender_name(message)} 嘗試橄欖管理員')

        # 檢查目標 credit message count 和 joined time
        if target_id > 0:
            target_credit = await get_user_credit(target_id, message.chat.id)
        else:
            target_credit = await get_chat_credit(target_id, message.chat.id)
        if target_credit.msg_count_before_24h > 10:
            await app.send_message(chat_id=message.chat.id, text='⛔️無法 Wipe：此人以前講過話，你可以嘗試 kick。')
            raise ValueError(f'[wipe] 此人 {get_sender_name(message)} 嘗試橄欖講過話的人')

        if datetime.now() - datetime.fromtimestamp(target_credit.joined_time) > timedelta(days=14):
            await app.send_message(chat_id=message.chat.id, text='⛔️無法 Wipe：此人屬於老群友，請聯絡管理員。')
            raise ValueError(f'[wipe] 此人 {get_sender_name(message)} 嘗試橄欖老群友')

        # 執行踢人
        asyncio.create_task(target_msg.forward(KIMIKADUSTBIN))
        await app.delete_user_history(chat_id=message.chat.id, user_id=target_id)
        await app.ban_chat_member(chat_id=message.chat.id, user_id=target_id)

        resp_text = f'[🛑](tg://user?id={ESUONEGOV}) **New banned user**\n\n' \
                    f'**ID**: [{target_id}](tg://user?id={target_id})\n' \
                    f'**Username**: {"@" + target_credit.username if target_credit.username else "None"}\n\n' \
                    f'👋🏻 **Action**: Kicked with history wiped\n' \
                    f'🤔 **Reason**: Invoked by [{get_sender_name(message)}](tg://user?id={caller_id})'

        await app.send_message(chat_id=message.chat.id, text=resp_text)

    except (pyrogram.errors.RPCError, ValueError) as e:
        logging.error(e)
        await speak(message.chat.id, 'kimika-sticker/3')  # 笑嘻了


async def kick(app: pyrogram.Client, message: pyrogram.types.Message, rtp: float):
    (reply_to_possibility, reply_to_msg_id) = (rtp, message.reply_to_message.id) \
        if message.reply_to_message else (-1, None)
    killerDao = global_var.db.killerDao
    try:
        # 檢查自身權限
        my_membership = await app.get_chat_member(chat_id=message.chat.id, user_id='me')
        if my_membership.status != pyrogram.enums.ChatMemberStatus.ADMINISTRATOR and \
                my_membership.status != pyrogram.enums.ChatMemberStatus.OWNER:
            raise ValueError('[kick] 俺不是管理員')
        else:
            if my_membership.privileges.can_restrict_members:
                pass
            else:
                raise ValueError('[kick] 權限不足')
        # 檢查調用人 killer 權限
        caller_id = get_sender_id(message)
        if not await killerDao.check_killer(caller_id, message.chat.id):
            raise ValueError(f'[kick] 此人 {get_sender_name(message)} 不是 killer')
        # 檢查目標是否爲 空，kimika，管理員，調用人
        if reply_to_msg_id is None:
            raise ValueError(f'[kick] 沒有 reply 到人身上')

        target_msg = await app.get_messages(chat_id=message.chat.id, message_ids=reply_to_msg_id)
        target_id = get_sender_id(target_msg)

        if caller_id == target_id:
            raise ValueError(f'[kick] 此人 {get_sender_name(message)} 嘗試橄欖自己')

        try:
            target_member = await app.get_chat_member(chat_id=message.chat.id, user_id=target_id)
            if target_member.chat is not None:
                # in case of chat member banned
                raise pyrogram.errors.UserNotParticipant
            if target_member.user.is_self:
                raise ValueError(f'[kick] 此人 {get_sender_name(message)} 嘗試橄欖 kimika')
        except pyrogram.errors.UserNotParticipant:
            logging.info('[kick] UserNotParticipant 爲何不直接橄欖呢？')
            target_member = None

        if target_member is not None and \
                (target_member.status == pyrogram.enums.ChatMemberStatus.ADMINISTRATOR or
                 target_member.status == pyrogram.enums.ChatMemberStatus.OWNER):
            raise ValueError(f'[kick] 此人 {get_sender_name(message)} 嘗試橄欖管理員')

        # 檢查目標 joined time
        if target_id > 0:
            target_credit = await get_user_credit(target_id, message.chat.id)
        else:
            target_credit = await get_chat_credit(target_id, message.chat.id)
        if datetime.now() - datetime.fromtimestamp(target_credit.joined_time) > timedelta(days=14):
            await app.send_message(chat_id=message.chat.id, text='⛔️無法 kick：此人屬於老群友，請聯絡管理員。')
            raise ValueError(f'[kick] 此人 {get_sender_name(message)} 嘗試橄欖老群友')

        # 執行踢人
        await app.ban_chat_member(chat_id=message.chat.id, user_id=target_id)

        resp_text = f'[🛑](tg://user?id={ESUONEGOV}) **New banned user**\n\n' \
                    f'**ID**: [{target_id}](tg://user?id={target_id})\n' \
                    f'**Username**: {"@" + target_credit.username if target_credit.username else "None"}\n\n' \
                    f'👋🏻 **Action**: Kicked\n' \
                    f'🤔 **Reason**: Invoked by [{get_sender_name(message)}](tg://user?id={caller_id})'

        await app.send_message(chat_id=message.chat.id, text=resp_text)

    except (pyrogram.errors.RPCError, ValueError) as e:
        logging.error(e)
        await speak(message.chat.id, 'kimika-sticker/3')  # 笑嘻了
