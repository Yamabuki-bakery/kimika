import pyrogram, random, logging, asyncio
from botConfig import *
from utils.util_tg_operation import speak


async def mt_exec(app: pyrogram.Client, message: pyrogram.types.Message, rtp: float):
    (reply_to_possibility, reply_to_msg_id) = (rtp, message.reply_to_message.id) \
        if message.reply_to_message else (-1, None)
    if message.from_user.id != ESUONEGOV:
        logging.warning(f'[EXEC] Unauthorized exec from {message.from_user.id} {message.from_user.first_name}')
        reply = 'kimika-sticker/4'  # ......大丈夫？
        await speak(message.chat.id, reply, reply_to_msg_id if random.random() < reply_to_possibility else None)
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