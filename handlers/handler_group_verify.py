from datetime import datetime
import logging
import pyrogram.errors

import asyncio
import global_var
import pyrogram
import time

import myTypes
from botConfig import *
from utils.util_anti_replay import anti_replay
from utils.util_tg_operation import get_sender_id, get_user_credit, speak


class JoinDenyFlags:
    not_chan_member = False
    no_photo = False
    no_bio = False
    no_username = False
    new_account = False

    def is_accept(self):
        return not (self.not_chan_member or self.no_photo or self.no_bio or self.no_username or self.new_account)


def add2watch(message: pyrogram.types.Message = None, user_id: int = None, chat_id: int = None):
    if message is not None:
        logging.info(
            f'[add2watch] 🆕️ Message {message.id} is sent by service, {message.from_user.first_name} add to watching list')
    else:
        logging.info(
            f'[add2watch] 🆕️ New member from update, {user_id} add to watching list for chat {chat_id}')
    global_var.NEW_MEMBER_WATCHING_LIST.update(
        {
            user_id or message.from_user.id: {
                'chat': chat_id or message.chat.id,
                'time': time.time()
            }
        }
    )
    asyncio.create_task(del_from_watch(message))


async def del_from_watch(message: pyrogram.types.Message):
    await asyncio.sleep(WATCHING_LIST_WAIT_SEC)
    global_var.NEW_MEMBER_WATCHING_LIST.pop(message.from_user.id)


async def new_member_update(app: pyrogram.Client, chat_member_updated: pyrogram.types.ChatMemberUpdated):
    logging.info(f'[new_member_update] update coming!')
    print(str(chat_member_updated))
    if chat_member_updated.new_chat_member.user is None:
        logging.info(f'[new_member_update] Something strange: the new chat member USER is none, may be a channel?!')
        return
    chatid = chat_member_updated.chat.id
    user_id = chat_member_updated.new_chat_member.user.id
    add2watch(None, user_id, chatid)
    asyncio.create_task(verify_new_member_task(app, chatid, user_id))


@anti_replay
async def verify_new_member(app: pyrogram.Client, message: pyrogram.types.Message):
    if message.service and message.service == pyrogram.enums.MessageServiceType.NEW_CHAT_MEMBERS:
        chatid = message.chat.id
        add2watch(message)
        # logging.info(f'🆕️ Group {chatid} new member')
        asyncio.create_task(verify_new_member_task(app, chatid, message.from_user.id, message))
    else:
        # logging.info(f'not service message {message.text}')
        return


async def verify_new_member_task(app: pyrogram.Client,
                                 chatid: int,
                                 joiner_id: int,
                                 joined_service_msg: pyrogram.types.Message = None):
    new_member = (await app.get_chat_member(chatid, joiner_id)).user
    groupVerifyDao = global_var.db.groupVerifyDao
    verify_scheme = await groupVerifyDao.get_verify_scheme(chatid)

    if verify_scheme is None:
        return

    check_permission_task = asyncio.create_task(get_current_permission(chatid, joiner_id))
    verifying_msg_task = asyncio.create_task(
        speak(chatid, f'🤔正在驗證：[@{new_member.first_name}](tg://user?id={new_member.id})，，，')
    )

    use_channel: str | None = verify_scheme[0]
    use_photo: int = verify_scheme[1]
    use_bio: int = verify_scheme[2]
    use_username: int = verify_scheme[3]
    use_new_account: int = verify_scheme[4]
    verify_scheme_str = "" \
                        + ("channel " if use_channel is not None else "") \
                        + ("photo " if use_photo else "") \
                        + ("bio " if use_bio else "") \
                        + ("username " if use_username else "") \
                        + ("new account " if use_new_account else "")
    logging.info(f'[verify_new_member] 🆕️ Group {chatid} verify new member, with {verify_scheme_str}')

    deny_flags = JoinDenyFlags()

    async def check_channel_member(channel_username: str, member: pyrogram.types.User) -> bool:
        results = []
        async for m in app.get_chat_members(channel_username, query=member.first_name,
                                            filter=pyrogram.enums.ChatMembersFilter.SEARCH):
            results.append(m)
        for chan_member in results:
            if chan_member.user.id == member.id:
                logging.info(
                    f'[verify_new_member] ✅🌐 User {member.id} {member.first_name} found in (API - search) channel')
                return True
        return False

    async def check_credit(member: pyrogram.types.User, chat_id: int) -> myTypes.MemberCredit:
        retry = 3
        while True:
            try:
                result = await get_user_credit(member, chat_id)
                return result
            except InterruptedError:
                logging.warning(f'[verify_new_member] Get credit failed, retrying: {retry}')
                retry -= 1
                await asyncio.sleep(2)
                if retry == 0:
                    result = await get_user_credit(member, chat_id, True)
                    return result

    if use_channel is not None:
        check_channel_task = asyncio.create_task(check_channel_member(use_channel, new_member))

    if use_bio or use_photo or use_username or use_new_account:
        credit_task = asyncio.create_task(check_credit(new_member, chatid))

    if use_channel is not None:
        try:
            in_channel = await check_channel_task
        except pyrogram.errors.RPCError as e:
            logging.error(f'[verify_new_member] Error when checking channel member.\n {e}')
            return

        if not in_channel:
            logging.info(f'[verify_new_member] This member does not belong to channel')
            deny_flags.not_chan_member = True

    if use_bio or use_photo or use_username or use_new_account:

        credit = await credit_task

        if (not credit.photo) and use_photo:
            deny_flags.no_photo = True
        if credit.bio is None and use_bio:
            deny_flags.no_bio = True
        if credit.new_account and use_new_account:
            deny_flags.new_account = True
        if credit.username is None and use_username:
            deny_flags.no_username = True

    verifying_msg: pyrogram.types.Message = (await verifying_msg_task)[0]
    if deny_flags.is_accept():
        logging.info(f'[verify_new_member] New member {new_member.first_name} is accepted')

        await verifying_msg.edit_text(f'✅驗證通過：[@{new_member.first_name}](tg://user?id={new_member.id})')
        #
        # await app.send_message(chat_id=chatid, text=f"[@{new_member.first_name}](tg://user?id={new_member.id}) was accepted by quick verification.")

        rule_msg = await app.send_message(chat_id=chatid, text=GALGROUP_RULE)
        await asyncio.sleep(90)
        await rule_msg.delete()
        return
    else:
        if joined_service_msg:
            asyncio.create_task(joined_service_msg.delete())
        asyncio.create_task(verifying_msg.delete())

        logging.info(f'[verify_new_member] New member {new_member.first_name} is denied')
        prompt_channel = '' + (f' * 訂閱這個頻道 @{use_channel}\n' if deny_flags.not_chan_member else '')
        prompt_photo = '' + (' * 設置大頭貼 (並對所有人公開)\n' if deny_flags.no_photo else '')
        prompt_bio = '' + (' * 設置個人簡介\n' if deny_flags.no_bio else '')
        prompt_new_account = '' + (' * 使用你的 TG 大號\n' if deny_flags.new_account else '')
        prompt_username = '' + (f' * 設置用戶名\n' if deny_flags.no_username else '')
        text = f"""[@{new_member.first_name}](tg://user?id={new_member.id}) 你好，要加入本群你需要：
{prompt_channel + prompt_photo + prompt_bio + prompt_new_account + prompt_username}請滿足上述要求，然後在 20 秒後重新加群。"""
        # logging.info(text)

        old_permissions, until_date = await check_permission_task

        _ = asyncio.create_task(app.restrict_chat_member(
            chat_id=chatid,
            user_id=new_member.id,
            permissions=pyrogram.types.ChatPermissions()
        ))
        msg = await app.send_message(chatid, text)
        await asyncio.sleep(20)
        await msg.delete()
        await app.ban_chat_member(chatid, new_member.id)
        logging.info(f'[verify_new_member] {new_member.first_name} kicked')
        await asyncio.sleep(5)
        await app.unban_chat_member(chatid, new_member.id)
        if old_permissions:
            await app.restrict_chat_member(chatid, joiner_id, old_permissions, until_date)


async def get_current_permission(chat_id: int, target_id: int) -> tuple[
    pyrogram.types.ChatPermissions | None, datetime | None]:
    try:
        chat_member = await global_var.app.get_chat_member(chat_id, target_id)
        if not chat_member:
            raise ValueError('ChatMember for {target_id} is null!')
        if chat_member.status != pyrogram.enums.chat_member_status.ChatMemberStatus.RESTRICTED:
            raise ValueError(f"The user {target_id} is not restricted!")
        current_permission = chat_member.permissions
        until_date = chat_member.until_date
        if not current_permission:
            raise ValueError(f'Current permission for {target_id} is null!')

        return current_permission, until_date

    except (pyrogram.errors.RPCError, ValueError) as err:
        logging.info(f'[get_current_permission] {err}, returning None.')
        chat_info = await global_var.app.get_chat(chat_id)
        return None, datetime.now()
