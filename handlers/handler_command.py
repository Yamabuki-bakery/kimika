import logging
import re
import asyncio
import random

import pyrogram.errors

from utils.util_anti_replay import anti_replay
from . import commands
from . import imply_chain


@anti_replay
async def no_imply_at_command(client: pyrogram.Client, message: pyrogram.types.Message):
    await at_command(client, message, no_imply=True)


@anti_replay
async def at_command(
        client: pyrogram.Client,
        message: pyrogram.types.Message,
        again: int = 1,
        from_origin_chat: pyrogram.types.Chat = None,
        *args,
        **kwargs
):
    app = client
    if not from_origin_chat:
        from_origin_chat = message.chat

    _foreign_chat = from_origin_chat.id != message.chat.id
    (reply_to_possibility, reply_to_msg_id) = (0.75, message.reply_to_message.id) if message.reply_to_message else (
        -1, None)
    # return
    command_list = ['execute', 'learn', 'giveme', 'china',
                    'debug', 'member', 'lowCreditUsers', 'help',
                    'credit', 'wipe', 'kick', 'killer add',
                    'killer del', 'killer', 'ja', 'diss',
                    '\0\1\2\3', 'チャイナ', 'シナ', 'article']
    command_called = None
    logging.info(f'[command] Coming Message [{message.text or message.caption or ""}]')
    for command in command_list:
        # if command in (message.text or message.caption or ''):
        target = (message.text or message.caption or '')
        # print(command, target)
        if re.search(command, target, flags=re.IGNORECASE):
            command_called = command
            logging.info(f'[command] It is a {command_called} command')
            break

    if command_called:
        if not _foreign_chat:
            if command_list.index(command_called) == 15:  # diss
                await commands.diss(app, message, reply_to_possibility)

            if command_list.index(command_called) == 19:  # aritcle
                pass

            if command_list.index(command_called) == 2:  # giveme
                await commands.giveme(app, message, reply_to_possibility)

            if command_list.index(command_called) in [3, 17, 18]:  # china
                await commands.china(app, message, reply_to_possibility)

            if command_list.index(command_called) == 4:  # debug
                asyncio.create_task(commands.debug(message, reply_to_possibility))

            if command_list.index(command_called) == 5:  # member
                asyncio.create_task(commands.member(app, message, reply_to_possibility))

            if command_list.index(command_called) == 6:  # lowCreditUsers
                pass

            if command_list.index(command_called) == 7:  # help
                asyncio.create_task(commands.help(app, message, reply_to_possibility))

            if command_list.index(command_called) == 8:  # credit
                asyncio.create_task(commands.credit(app, message, reply_to_possibility))

            if command_list.index(command_called) == 9:  # wipe
                await commands.wipe(app, message, reply_to_possibility)

            if command_list.index(command_called) == 10:  # kick
                await commands.kick(app, message, reply_to_possibility)

            if command_list.index(command_called) == 11:  # killer add
                await commands.killer_add(app, message, reply_to_possibility)

            if command_list.index(command_called) == 12:  # killer del
                await commands.killer_del(app, message, reply_to_possibility)

            if command_list.index(command_called) == 13:  # killer
                await commands.killer_list(app, message)

            if command_list.index(command_called) == 14:  # ja
                await commands.ja(app, message, reply_to_possibility)

            if command_list.index(command_called) == 0:  # exec
                await commands.mt_exec(app, message, reply_to_possibility)

        if command_list.index(command_called) == 1:  # learn
            await commands.learn(app, message)

    else:
        if kwargs.get('no_imply'):
            return

        asyncio.create_task(imply_chain_func(
            client=client,
            message=message,
            reply_to_possibility=reply_to_possibility,
            reply_to_msg=message.reply_to_message,
            again=again,
            from_origin_chat=from_origin_chat,
        ))

        # message.stop_propagation()


@anti_replay
async def invoke_imply(
        client: pyrogram.Client,
        message: pyrogram.types.Message
):
    logging.info(f'[invoke_imply] comming [{message.text or message.caption or ""}]')
    asyncio.create_task(imply_chain_func(
        client=client,
        message=message,
        reply_to_possibility=1,
        reply_to_msg=message.reply_to_message,
        again=1,
        hash_sign=True
    ))


async def imply_chain_func(
        client: pyrogram.Client,
        message: pyrogram.types.Message,
        reply_to_possibility: float,
        again: int,
        reply_to_msg: pyrogram.types.Message = None,
        from_origin_chat: pyrogram.types.Chat = None,
        hash_sign: bool = False,
):
    app = client
    if not from_origin_chat:
        from_origin_chat = message.chat

    if await imply_chain.reaction(app, message):
        return

    if await imply_chain.netease_link(app, message, from_origin_chat):
        return

    if await imply_chain.forget(app, message):
        return

    if await imply_chain.learning(app, message, again == 0):
        return

    if hash_sign and again == 0:
        return

    if reply_to_msg is not None:
        logging.info(f'[at_command] No command found, try the replied message again')
        try:
            try_this = await app.get_messages(
                chat_id=reply_to_msg.chat.id,
                message_ids=reply_to_msg.id
            )
            asyncio.create_task(at_command(app, try_this, 0, from_origin_chat=from_origin_chat))
        except pyrogram.errors.exceptions.RPCError as e:
            logging.error(f'[at_command] {e}')
        finally:
            return

    if await imply_chain.random_reply(app, message, reply_to_possibility):
        return
