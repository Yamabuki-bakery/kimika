import logging, pyrogram.errors

import pyrogram, asyncio, global_var
from util_database import db_async, dbcommit_async
from util_tg_operation import get_user_credit
from botConfig import *


class JoinDenyFlags:
    not_chan_member = False
    no_photo = False
    no_bio = False
    no_username = False
    new_account = False

    def is_accept(self):
        return not (self.not_chan_member or self.no_photo or self.no_bio or self.no_username or self.new_account)


async def add2watch(message: pyrogram.types.Message):
    logging.info(
        f'🆕️ Message {message.id} is sent by service, {message.from_user.first_name} add to watching list')
    global_var.NEW_MEMBER_WATCHING_LIST.update({message.from_user.id: message.chat.id})
    await asyncio.sleep(6)
    global_var.NEW_MEMBER_WATCHING_LIST.pop(message.from_user.id)


async def verify_new_member(app: pyrogram.Client, message: pyrogram.types.Message):
    if message.service and message.service == pyrogram.enums.MessageServiceType.NEW_CHAT_MEMBERS:
        chatid = message.chat.id
        asyncio.create_task(add2watch(message))
        # logging.info(f'🆕️ Group {chatid} new member')
    else:
        # logging.info(f'not service message {message.text}')
        return
    DB = global_var.DB

    new_member = message.from_user
    cursor = await db_async(DB, 'SELECT * FROM group_verify WHERE chatid=:cid', {'cid': chatid})
    row = cursor.fetchone()

    if row:
        await message.delete()
        use_channel: str = row[1]
        use_photo: int = row[2]
        use_bio: int = row[3]
        use_username: int = row[4]
        use_new_account: int = row[5]
        verify_scheme = "" \
                        + ("channel " if use_channel is not None else "") \
                        + ("photo " if use_photo == 1 else "") \
                        + ("bio " if use_bio == 1 else "") \
                        + ("username " if use_username == 1 else "") \
                        + ("new account " if use_new_account == 1 else "")
        logging.info(f'🆕️ Group {chatid} verify new member, with {verify_scheme}')
    else:
        return

    # start checking credit here
    credit_task = asyncio.create_task(get_user_credit(new_member.id, chatid))

    deny_flags = JoinDenyFlags()

    if use_channel is not None:
        in_channel = False
        results = []
        try:
            async for m in app.get_chat_members(use_channel, query=new_member.first_name,
                                                filter=pyrogram.enums.ChatMembersFilter.SEARCH):
                results.append(m)
            for chan_member in results:
                if chan_member.user.id == new_member.id:
                    logging.info(f'✅🌐 User {new_member.id} {new_member.first_name} found in (API - search) channel')
                    in_channel = True
                    break
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
        if (credit.username is None) and use_username:
            deny_flags.no_username = True

    if deny_flags.is_accept():
        logging.info(f'[verify_new_member] New member {new_member.first_name} is accepted')
        await app.send_message(chat_id=chatid,
                               text=f"[@{new_member.first_name}](tg://user?id={new_member.id}) was accepted by quick verification.")
        rule_msg = await app.send_message(chat_id=chatid, text=GALGROUP_RULE)
        await asyncio.sleep(90)
        await rule_msg.delete()
        return
    else:
        logging.info(f'[verify_new_member] New member {new_member.first_name} is denied')
        prompt_channel = '' + (f' * 訂閱這個頻道 @{use_channel}\n' if deny_flags.not_chan_member else '')
        prompt_photo = '' + (' * 設置大頭貼 (並對所有人公開)\n' if deny_flags.no_photo else '')
        prompt_bio = '' + (' * 設置個人簡介\n' if deny_flags.no_bio else '')
        prompt_new_account = '' + (' * 使用你的 TG 大號\n' if deny_flags.new_account else '')
        prompt_username = '' + (f' * 設置用戶名\n' if deny_flags.no_username else '')
        text = f"""[@{new_member.first_name}](tg://user?id={new_member.id}) 你好，要加入本群你需要：
{prompt_channel + prompt_photo + prompt_bio + prompt_new_account + prompt_username}請滿足上述要求，然後在 20 秒後重新加群。
"""
        logging.info(text)
        restrict_task = asyncio.create_task(app.restrict_chat_member(
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
