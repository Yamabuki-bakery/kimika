import asyncio, json, logging, time, aiosqlite, signal, sys, sqlite3
import pyrogram
from pyrogram.handlers import MessageHandler
from pyrogram import filters

config_fp = open('config.json')
CONFIG = json.load(config_fp)
config_fp.close()

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                    )

app = pyrogram.Client(
    "kimika",
    api_id=CONFIG["api_id"], api_hash=CONFIG["api_hash"],
    app_version=CONFIG["app_title"] + " 0.0.1",
    device_model="Xiaomi MI MIX 2S",
    ipv6=False
)

DB = None
DBFILE = 'members.db'


@app.on_message(filters.incoming & filters.chat(-1001131250808))
async def galgroup_msg(client, message):
    # logging.info(message)
    if message.reply_to_message:
        # see the msg replies to which another one as legal.
        logging.info(f'Message {message.id} replied to msg {message.reply_to_message_id}, ignoring')
        return

    if not message.from_user:
        # see the msg sent by non-user as legal
        logging.info(f'Message {message.id} is sent by non-user {message.sender_chat.title}, ignoring')
        return

    logging.info(f'Message {message.id} from {message.from_user.id} {message.from_user.first_name},'
                 f' looking for common chats.')

    if await check_common_chat(message.from_user.id, message.from_user.first_name, -1001131250808):
        logging.info(f'User {message.from_user.id} {message.from_user.first_name} is in the chat')
    else:
        logging.warning(f'User {message.from_user.id} {message.from_user.first_name} is NOT in the chat!')
        # kick


async def check_common_chat(user_id, first_name, target_chat):
    cursor = DB.execute('SELECT * FROM members WHERE userid=:target', {'target': user_id})
    row = cursor.fetchone()
    if row:
        assert row[0] == user_id
        logging.info(f'user id {user_id} {row[1]} found in db, time {row[2]}')
        if time.time() - row[2] < 86400:
            return True

    common = await app.get_common_chats(user_id)
    result = False
    for chat in common:
        if chat.id == target_chat:
            result = True
            logging.info(f'user id {user_id} {first_name} found in common group')
            DB.execute('REPLACE INTO members VALUES (?,?,?)', (user_id, first_name, int(time.time())))
            DB.commit()
            break
    return result


async def bot_init():
    logging.info('bot_init')
    await app.start()

    # msg_handler = MessageHandler(msg_handle_func)
    # app.add_handler(msg_handler)
    # logging.info(await app.get_me())
    # await app.send_message("me", str(int(time.time())))
    await pyrogram.idle()


async def main():
    # loop = asyncio.get_event_loop()
    await init_db()
    bot = asyncio.create_task(bot_init())
    await bot


async def init_db():
    global DB
    DB = sqlite3.connect(DBFILE)
    DB.execute('CREATE TABLE IF NOT EXISTS members (userid INTEGER PRIMARY KEY,'
                     ' firstName TEXT, lastCheck INTEGER)')
    DB.execute('CREATE UNIQUE INDEX IF NOT EXISTS userid_index ON members (userid)')
    DB.commit()



def signal_handler(sig, frame):
    print('You pressed Ctrl+C!')
    asyncio.create_task(quit_task())
    sys.exit(0)


if __name__ == '__main__':
    #signal.signal(signal.SIGINT, signal_handler)
    #signal.pause()
    asyncio.get_event_loop().run_until_complete(main())
    # asyncio.run(main())
