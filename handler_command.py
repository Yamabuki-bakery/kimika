import asyncio
import logging
import pyrogram
import random
import re

import global_var
from botConfig import *
from util_tg_operation import speak, send_song
import pyrogram.errors


async def at_command(client, message: pyrogram.types.Message):
    app = global_var.app
    DB = global_var.DB
    (reply_to_possibility, reply_to_msg_id) = (0.75, message.reply_to_message.id) if message.reply_to_message else (
        -1, None)
    # return
    command_list = ['execute', 'article', 'giveme', 'china',
                    'debug', 'member', 'lowCreditUsers', 'help',
                    'credit', 'wipe', 'kick', 'killer add',
                    'killer del', 'killer', 'ja', 'diss',
                    'ask', 'チャイナ', 'シナ']
    command_called = None
    logging.info(f'[command] Coming Message {message.text or message.caption or ""}')
    for command in command_list:
        # if command in (message.text or message.caption or ''):
        target = (message.text or message.caption or '')
        # print(command, target)
        if re.search(command, target, flags=re.IGNORECASE):
            command_called = command
            logging.info(f'[command] It is a {command_called} command')
            break

    if command_called:
        if command_list.index(command_called) == 15:  # diss
            reply_list = DISS_REPLY_LIST
            await speak(message.chat.id, random.choice(reply_list),
                        reply_to_msg_id if random.random() < reply_to_possibility else None)
        if command_list.index(command_called) == 1:  # aritcle
            pass
        if command_list.index(command_called) == 2:  # giveme
            (reply_to_possibility, reply_to_msg_id) = (
                2, message.reply_to_message.id) if message.reply_to_message else (
                -1, None)
            reply_list = GIVEME_REPLY_LIST
            await speak(message.chat.id, random.choice(reply_list),
                        reply_to_msg_id if random.random() < reply_to_possibility else None)  #
        if command_list.index(command_called) in [3, 17, 18]:  # china
            reply_list = CHINA_REPLY_LIST
            await speak(message.chat.id, random.choice(reply_list),
                        reply_to_msg_id if random.random() < reply_to_possibility else None)
        if command_list.index(command_called) == 4:  # debug
            if reply_to_msg_id:
                debug_msg = (await speak(message.chat.id, str(message.reply_to_message)))[0]
            else:
                debug_msg = (await speak(message.chat.id, str(message)))[0]
            await asyncio.sleep(90)
            await app.delete_messages(message.chat.id, debug_msg.id)
        if command_list.index(command_called) == 5:  # member
            if reply_to_msg_id:
                target_msg = await app.get_messages(chat_id=message.chat.id, message_ids=reply_to_msg_id)
                target_id = target_msg.from_user.id

            else:
                target_id = message.from_user.id
            try:
                member_info = await app.get_chat_member(chat_id=message.chat.id, user_id=target_id)
            except pyrogram.errors.UserNotParticipant:

                member_info = "Not a member of this group"
            debug_msg = (await speak(message.chat.id, str(member_info)))[0]
            await asyncio.sleep(90)
            await app.delete_messages(message.chat.id, debug_msg.id)
        if command_list.index(command_called) == 6:  # lowCreditUsers
            return
            reply = '插播一條通知，由於貫徹廣告動態清零政策一百年不動搖，以下的用戶\n'
            count = 0
            for suid in suspicious.split('\n'):
                uid = int(suid)
                reply += f'[{count}](tg://user?id={uid}) '
                await app.restrict_chat_member(chat_id=GALGROUP, user_id=uid,
                                               permissions=pyrogram.types.ChatPermissions(can_send_messages=True))
                count += 1

            reply += f'\n共 {count} 位，由於你們的帳號太新以及無大頭貼和用戶名，已被限制僅能發送文本，如需解除請手動退群重進或者和管理真人快打。'
            await app.send_message(chat_id=GALGROUP, text=reply)

            return
            ugt5b = []
            async for member in app.get_chat_members(message.chat.id):
                if member.user.id > 5000000000:
                    ugt5b.append(member)
            logging.info(f'[lowCreditUsers] There are {len(ugt5b)} users which id > 5b')

            userids = []
            for u in ugt5b:
                userids.append(u.user.id)
            ulist = await app.get_users(userids)

            uwophoto = []
            for u in ulist:
                if u.photo or u.username:
                    pass
                else:
                    uwophoto.append(u)
            logging.info(f'[lowCreditUsers] There are {len(uwophoto)} users which do not have photo')
            for u in uwophoto:
                print(u.id)
        if command_list.index(command_called) == 7:  # help
            help_text = KIMIKA_HELP
            help_msg = await app.send_message(chat_id=message.chat.id, text=help_text)
            await asyncio.sleep(60)
            try:
                await app.delete_messages(chat_id=help_msg.chat.id, message_ids=help_msg.id)
                await app.delete_messages(chat_id=help_msg.chat.id, message_ids=message.id)
            except pyrogram.errors.RPCError:
                pass
        if command_list.index(command_called) == 8:  # credit
            if reply_to_msg_id:
                target_msg = await app.get_messages(chat_id=message.chat.id, message_ids=reply_to_msg_id)
                target_id = target_msg.from_user.id

            else:
                target_id = message.from_user.id

            credit_info = await get_user_credit(target_id, message.chat.id)
            debug_msg = (await speak(message.chat.id,
                                     json.dumps(credit_info, indent=2, separators=(',', ': '), ensure_ascii=False)))[0]
            await asyncio.sleep(90)
            await app.delete_messages(message.chat.id, debug_msg.id)
        if command_list.index(command_called) == 9:  # wipe
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
                caller_id = message.from_user.id
                cursor = await db_async(DB, 'SELECT * FROM killer WHERE userid=:uid AND chatid=:cid',
                                        {'uid': caller_id, 'cid': message.chat.id})
                row = cursor.fetchone()
                if row:
                    pass
                else:
                    raise ValueError(f'[wipe] 此人 {message.from_user.first_name} 不是 killer')
                # 檢查目標是否爲 空，kimika，管理員，調用人
                if reply_to_msg_id is None:
                    raise ValueError(f'[wipe] 沒有 reply 到人身上')

                target_msg = await app.get_messages(chat_id=message.chat.id, message_ids=reply_to_msg_id)
                target_id = target_msg.from_user.id

                if caller_id == target_id:
                    raise ValueError(f'[wipe] 此人 {message.from_user.first_name} 嘗試橄欖自己')

                target_member = await app.get_chat_member(chat_id=message.chat.id, user_id=target_id)
                if target_member.user.is_self:
                    raise ValueError(f'[wipe] 此人 {message.from_user.first_name} 嘗試橄欖 kimika')

                if target_member.status == pyrogram.enums.ChatMemberStatus.ADMINISTRATOR or \
                        target_member.status == pyrogram.enums.ChatMemberStatus.OWNER:
                    raise ValueError(f'[wipe] 此人 {message.from_user.first_name} 嘗試橄欖管理員')

                # 檢查目標 credit message count 和 joined time
                target_credit = await get_user_credit(target_id, message.chat.id)
                if target_credit['msg_count_before_24h'] > 10:
                    await app.send_message(chat_id=message.chat.id, text='⛔️無法 Wipe：此人以前講過話，你可以嘗試 kick。')
                    raise ValueError(f'[wipe] 此人 {message.from_user.first_name} 嘗試橄欖講過話的人')

                if datetime.now() - datetime.fromtimestamp(target_credit['joined_time']) > timedelta(days=14):
                    await app.send_message(chat_id=message.chat.id, text='⛔️無法 Wipe：此人屬於老群友，請聯絡管理員。')
                    raise ValueError(f'[wipe] 此人 {message.from_user.first_name} 嘗試橄欖老群友')

                # 執行踢人
                await target_msg.forward(KIMIKACACHE)
                await app.delete_user_history(chat_id=message.chat.id, user_id=target_id)
                await app.ban_chat_member(chat_id=message.chat.id, user_id=target_id)

                resp_text = f'[🛑](tg://user?id={ESUONEGOV}) **New banned user**\n\n' \
                            f'**ID**: [{target_id}](tg://user?id={target_id})\n' \
                            f'**User**: {"@" + target_credit["username"] if target_credit["username"] else "None"}\n\n' \
                            f'👋🏻 **Action**: Kicked with history wiped\n' \
                            f'🤔 **Reason**: Invoked by [{message.from_user.first_name}](tg://user?id={caller_id})'

                await app.send_message(chat_id=message.chat.id, text=resp_text)

            except (pyrogram.errors.RPCError, ValueError) as e:
                logging.error(e)
                await speak(message.chat.id, 'kimika-sticker/3')  # 笑嘻了

        if command_list.index(command_called) == 10:  # kick
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
                caller_id = message.from_user.id
                cursor = await db_async(DB, 'SELECT * FROM killer WHERE userid=:uid AND chatid=:cid',
                                        {'uid': caller_id, 'cid': message.chat.id})
                row = cursor.fetchone()
                if row:
                    pass
                else:
                    raise ValueError(f'[kick] 此人 {message.from_user.first_name} 不是 killer')
                # 檢查目標是否爲 空，kimika，管理員，調用人
                if reply_to_msg_id is None:
                    raise ValueError(f'[kick] 沒有 reply 到人身上')

                target_msg = await app.get_messages(chat_id=message.chat.id, message_ids=reply_to_msg_id)
                target_id = target_msg.from_user.id

                if caller_id == target_id:
                    raise ValueError(f'[kick] 此人 {message.from_user.first_name} 嘗試橄欖自己')

                target_member = await app.get_chat_member(chat_id=message.chat.id, user_id=target_id)
                if target_member.user.is_self:
                    raise ValueError(f'[kick] 此人 {message.from_user.first_name} 嘗試橄欖 kimika')

                if target_member.status == pyrogram.enums.ChatMemberStatus.ADMINISTRATOR or \
                        target_member.status == pyrogram.enums.ChatMemberStatus.OWNER:
                    raise ValueError(f'[kick] 此人 {message.from_user.first_name} 嘗試橄欖管理員')

                # 檢查目標 joined time
                target_credit = await get_user_credit(target_id, message.chat.id)
                if datetime.now() - datetime.fromtimestamp(target_credit['joined_time']) > timedelta(days=14):
                    await app.send_message(chat_id=message.chat.id, text='⛔️無法 kick：此人屬於老群友，請聯絡管理員。')
                    raise ValueError(f'[kick] 此人 {message.from_user.first_name} 嘗試橄欖老群友')

                # 執行踢人
                await app.ban_chat_member(chat_id=message.chat.id, user_id=target_id)

                resp_text = f'[🛑](tg://user?id={ESUONEGOV}) **New banned user**\n\n' \
                            f'**ID**: [{target_id}](tg://user?id={target_id})\n' \
                            f'**User**: {"@" + target_credit["username"] if target_credit["username"] else "None"}\n\n' \
                            f'👋🏻 **Action**: Kicked\n' \
                            f'🤔 **Reason**: Invoked by [{message.from_user.first_name}](tg://user?id={caller_id})'

                await app.send_message(chat_id=message.chat.id, text=resp_text)

            except (pyrogram.errors.RPCError, ValueError) as e:
                logging.error(e)
                await speak(message.chat.id, 'kimika-sticker/3')  # 笑嘻了

        if command_list.index(command_called) == 11:  # killer add
            # 檢查 reply 到人沒有
            # 檢查此人管理員權限
            try:
                if reply_to_msg_id is None:
                    raise ValueError(f'[killer add] 沒有 reply 到人身上')

                caller_id = message.from_user.id
                caller_member = await app.get_chat_member(chat_id=message.chat.id, user_id=caller_id)
                target_msg = await app.get_messages(chat_id=message.chat.id, message_ids=reply_to_msg_id)
                target_id = target_msg.from_user.id

                if caller_member.status != pyrogram.enums.ChatMemberStatus.ADMINISTRATOR and \
                        caller_member.status != pyrogram.enums.ChatMemberStatus.OWNER:
                    raise ValueError(f'[killer add] 此人 {message.from_user.first_name} 不是管理員')

                target_user = await app.get_users(target_id)
                logging.info(f'[killer add] {caller_member.user.first_name} 要增加 killer {target_user.first_name}')

                cursor = await db_async(DB, 'SELECT * FROM killer WHERE userid=:uid AND chatid=:cid',
                                        {'uid': target_id, 'cid': message.chat.id})
                row = cursor.fetchone()
                if row:
                    raise ValueError(f'[killer add] 此人 {target_user.first_name} 已在 killer 數據庫')

                await db_async(DB, 'INSERT INTO killer(userid,chatid) VALUES (?,?)', (target_id, message.chat.id))
                await dbcommit_async(DB)

                resp_text = f'🤔**New Killer**\n\n' \
                            f'**ID**: [{target_user.first_name}](tg://user?id={target_id})\n' \
                            f'**User**: {"@" + target_user.username if target_user.username else "None"}\n\n' \
                            f'👋🏻 **Action**: Granted\n' \
                            f'🤔 **Reason**: Invoked by admin [{message.from_user.first_name}](tg://user?id={caller_id})'

                await app.send_message(chat_id=message.chat.id, text=resp_text)

            except (pyrogram.errors.RPCError, ValueError) as e:
                logging.error(e)
                await speak(message.chat.id, 'kimika-sticker/3')  # 笑嘻了

        if command_list.index(command_called) == 12:  # killer del
            # 檢查 reply 到人沒有
            # 檢查此人管理員權限
            try:
                if reply_to_msg_id is None:
                    raise ValueError(f'[killer del] 沒有 reply 到人身上')

                caller_id = message.from_user.id
                caller_member = await app.get_chat_member(chat_id=message.chat.id, user_id=caller_id)
                target_msg = await app.get_messages(chat_id=message.chat.id, message_ids=reply_to_msg_id)
                target_id = target_msg.from_user.id

                if caller_member.status != pyrogram.enums.ChatMemberStatus.ADMINISTRATOR and \
                        caller_member.status != pyrogram.enums.ChatMemberStatus.OWNER:
                    raise ValueError(f'[killer del] 此人 {message.from_user.first_name} 不是管理員')

                target_user = await app.get_users(target_id)
                logging.info(f'[killer del] {caller_member.user.first_name} 要消除 killer {target_user.first_name}')

                cursor = await db_async(DB, 'SELECT * FROM killer WHERE userid=:uid AND chatid=:cid',
                                        {'uid': target_id, 'cid': message.chat.id})
                row = cursor.fetchone()
                if row:
                    pass
                else:
                    raise ValueError(f'[killer del] 此人 {target_user.first_name} 不在 killer 數據庫')

                await db_async(DB, 'DELETE FROM killer WHERE userid=:uid AND chatid=:cid',
                               {'uid': target_id, 'cid': message.chat.id})
                await dbcommit_async(DB)

                resp_text = f'🤔**Removed Killer**\n\n' \
                            f'**ID**: [{target_user.first_name}](tg://user?id={target_id})\n' \
                            f'**User**: {"@" + target_user.username if target_user.username else "None"}\n\n' \
                            f'👋🏻 **Action**: Revoked\n' \
                            f'🤔 **Reason**: Invoked by admin [{message.from_user.first_name}](tg://user?id={caller_id})'

                await app.send_message(chat_id=message.chat.id, text=resp_text)

            except (pyrogram.errors.RPCError, ValueError) as e:
                logging.error(e)
                await speak(message.chat.id, 'kimika-sticker/3')  # 笑嘻了

        if command_list.index(command_called) == 13:  # killer
            cursor = await db_async(DB, 'SELECT * FROM killer WHERE chatid=:cid', {'cid': message.chat.id})
            rows = cursor.fetchall()
            resp_text = 'List of killers:\n'
            for row in rows:
                mUser = await app.get_users(row[1])
                resp_text += f'[{mUser.first_name}](tg://user?id={mUser.id})\n'

            await app.send_message(chat_id=message.chat.id, text=resp_text)

        if command_list.index(command_called) == 14:  # ja
            (reply_to_possibility, reply_to_msg_id) = (2, message.reply_to_message.id) \
                if message.reply_to_message else (-1, None)
            reply_list = JA_REPLY_LIST
            await speak(message.chat.id, random.choice(reply_list),
                        reply_to_msg_id if random.random() < reply_to_possibility else None)  #

        if command_list.index(command_called) == 0:  # exec
            if message.from_user.id != ESUONEGOV:
                logging.warning(f'[EXEC] Unauthorized exec from {message.from_user.id} {message.from_user.first_name}')
                reply = 'kimika-sticker/4'  # ......大丈夫？
                await speak(message.chat.id, reply,
                            reply_to_msg_id if random.random() < reply_to_possibility else None)
                return

            lines = message.text.splitlines()
            if len(lines) < 2:
                logging.error(f'[EXEC] Command only have {len(lines)} line.')
                reply = 'kimika-sticker/4'  # ......大丈夫？
                await speak(message.chat.id, reply,
                            reply_to_msg_id if random.random() < reply_to_possibility else None)
                return

            command = ''
            for i in range(1, len(lines)):
                command += lines[i] + '\n'

            logging.warning(f'[EXEC] the command is\n{command}')
            exec(command, {
                'tg': app,
                'run': asyncio.create_task,
                'ESUONEGOV': ESUONEGOV,
                'GALGROUP': GALGROUP,
                'RHINEGROUP': RHINEGROUP,
                # '__builtins__':None
            })

        if command_list.index(command_called) == 16:  # ask
            if message.chat.id != RHINEGROUP and message.chat.id != ESUONEGOV:
                logging.warning(f'[ask] Ask cmd not from rhine group.')
                return

            ask_art = ART_OF_ASKING

            sent = await app.send_message(chat_id=message.chat.id, text=ask_art, reply_to_message_id=reply_to_msg_id)
            # await asyncio.sleep(30)
            # await app.delete_messages(chat_id=sent.chat.id, message_ids=sent.id)

    else:
        results = re.search(r'song[A-Za-z?/=#]{0,9}(\d{1,12})', message.text)
        if results is not None:
            song_id = results[1]
        else:
            results = re.search(r'(\d{1,12})$', message.text)
            if results is not None:
                song_id = results[1]
            else:
                song_id = None

        if song_id:
            await send_song(int(song_id), message.chat.id)
            return

        await asyncio.sleep(random.random() * 4)
        reply_list = NOTHING_REPLY_LIST
        await speak(message.chat.id, random.choice(reply_list),
                    message.id if random.random() < reply_to_possibility else None)

    # message.stop_propagation()
