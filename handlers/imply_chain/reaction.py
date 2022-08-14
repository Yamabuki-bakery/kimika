from botConfig import *
from utils.util_tg_operation import get_sender_id, get_sender_name
import pyrogram, re, logging, asyncio
import pyrogram.errors


async def reaction(app: pyrogram.Client, message: pyrogram.types.Message) -> bool:
    (reply_to_possibility, reply_to_msg_id) = (1, message.reply_to_message.id) if message.reply_to_message else ( -1, None)
    # Check syntax
    message_text: str = message.text or message.caption or ""
    message_text = message_text.encode('UTF-8').decode('UTF-8')
    try:
        if message_text and message_text[-1] not in TG_REACTIONS:
            # Not ending with tg reaction emoji
            raise ValueError('')
        re_groups = re.search(build_regex(), message_text)
        if re_groups is None:
            raise ValueError('')

        start = re_groups.start()
        reaction_list: list[str] = []
        for i in range(start, len(message_text)):
            if message_text[i] != ' ':
                reaction_list.append(message_text[i])

        if len(reaction_list) > 100:
            reaction_list = reaction_list[0:100]
        logging.info(f'[reaction] The reaction_list is {reaction_list}, with len {len(reaction_list)}')
    except ValueError:
        # logging.info(f'[reaction] Checking 2nd syntax')
        re_groups = re.search(build_2nd_regex(), message_text)
        if re_groups is None:
            return False

        emoji = re_groups[1]
        try:
            times = int(re_groups[2])
            if times > 100:
                times = 100
        except (ValueError, TypeError):
            return False

        reaction_list = []
        for i in range(times):
            reaction_list.append(emoji)

        logging.info(f'[reaction] The reaction_list is {reaction_list}, with len {len(reaction_list)}')

    # get messages
    if reply_to_msg_id:
        start_from_msg_id = reply_to_msg_id
        target_id = get_sender_id(message.reply_to_message)
        target_name = get_sender_name(message.reply_to_message)
    else:
        start_from_msg_id = message.id
        target_id = get_sender_id(message)
        target_name = get_sender_name(message)
    logging.info(f'[reaction] Reaction to {target_id}, {target_name}')
    target_msg_list: list[pyrogram.types.Message] = []

    limit = len(reaction_list)
    async for message in app.search_messages(message.chat.id, from_user=target_id):
        if message.id <= start_from_msg_id:
            target_msg_list.append(message)
            limit -= 1
            if limit == 0:
                break

    count = len(reaction_list) if len(reaction_list) < len(target_msg_list) else len(target_msg_list)

    # run reaction
    for i in range(0, count):
        try:
            await target_msg_list[i].react(reaction_list[i], True)
            await asyncio.sleep(0.5)
        except pyrogram.errors.FloodWait:
            await asyncio.sleep(5)
        except pyrogram.errors.RPCError:
            continue

    return True


def build_regex() -> str:
    pattern = f'([{"".join(TG_REACTIONS)}][{"".join(TG_REACTIONS)} ]*)$'
    # print(pattern)
    return pattern


def build_2nd_regex() -> str:
    pattern = f'([{"".join(TG_REACTIONS)}]) *(\d+)$'
    # print(pattern)
    return pattern
