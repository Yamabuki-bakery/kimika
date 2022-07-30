import asyncio
import json
import logging
import pyrogram
from pyrogram import filters

import global_var
# from global_var import app, DB
from botConfig import *
from handlers.handler_command import at_command
from handlers.handler_galgroup_nonmember import galgroup_non_member_msg_abuse
from handlers.handler_redirect_to_rhine import redirect_to_rhine
from handlers.handler_return_fileid import return_file_id
from handlers.handler_welcome_verify import new_member_welcome
from handlers.handler_smart_deal import smart_deal
from handlers.handler_group_verify import verify_new_member
from utils.util_database import init_db

config_fp = open('config.json')
CONFIG = json.load(config_fp)
config_fp.close()

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s [%(levelname)s] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                    )


async def bot_init():
    logging.info('bot_init')

    # https://docs.pyrogram.org/
    global_var.app = pyrogram.Client(
        "kimika",
        api_id=CONFIG["api_id"], api_hash=CONFIG["api_hash"],
        app_version=CONFIG["app_title"] + " 0.0.1",
        device_model="Xiaomi MI MIX 2S",
        ipv6=False
    )

    await global_var.app.start()

    # kimika command
    global_var.app.add_handler(pyrogram.handlers.MessageHandler(
        at_command,
        filters.incoming & (filters.regex(r'(@?[kK]imika)|([きキｷ希][みミﾐ実][かカｶ香])') | filters.mentioned),
    ), group=-1)

    # 驗證通過 / 錯誤反饋
    global_var.app.add_handler(pyrogram.handlers.MessageHandler(
        new_member_welcome,
        filters.incoming & filters.user(1148507346) & filters.regex(r'((超时未验证)|(通过了验证)|(验证错误))')
    ), group=-1)

    # 返回文件 ID
    global_var.app.add_handler(pyrogram.handlers.MessageHandler(
        return_file_id,
        filters.incoming & pyrogram.filters.private & (pyrogram.filters.media | pyrogram.filters.forwarded)
    ), group=0)

    # 踢不加群就發言的人
    global_var.app.add_handler(pyrogram.handlers.MessageHandler(
        galgroup_non_member_msg_abuse,
        filters.incoming & filters.chat(GALGROUP)
    ), group=-2)

    # 拉伸手黨到萊茵圖書館
    global_var.app.add_handler(pyrogram.handlers.MessageHandler(
        redirect_to_rhine,
        filters.incoming &
        filters.chat(GALGROUP) &
        filters.regex(r'((有[沒木没]有)|([问問求])).*(([资資]源)|(下[载載])|([那這这一][个個])|(游戏)|(遊戲)|(合集))')
    ), group=3)

    # smart deal
    global_var.app.add_handler(pyrogram.handlers.MessageHandler(
        smart_deal,
        filters.incoming & filters.text
    ), group=2)

    global_var.app.add_handler(pyrogram.handlers.MessageHandler(
        verify_new_member,
        filters.incoming & filters.group & filters.new_chat_members
    ), group=1)

    await pyrogram.idle()


async def main():
    # loop = asyncio.get_event_loop()
    await init_db()
    # bot = asyncio.create_task(bot_init())
    # await bot
    await asyncio.gather(bot_init())


if __name__ == '__main__':
    # asyncio.get_event_loop().run_until_complete(main())
    asyncio.run(main())
