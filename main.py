import asyncio, json, logging, time, sqlite3
import pyrogram
# from pyrogram.handlers import MessageHandler
from pyrogram import filters
from pyrogram.errors import PeerIdInvalid

config_fp = open('config.json')
CONFIG = json.load(config_fp)
config_fp.close()

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s [%(levelname)s] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                    )
# https://docs.pyrogram.org/
app = pyrogram.Client(
    "kimika",
    api_id=CONFIG["api_id"], api_hash=CONFIG["api_hash"],
    app_version=CONFIG["app_title"] + " 0.0.1",
    device_model="Xiaomi MI MIX 2S",
    ipv6=False
)

DB = None
DBFILE = 'members.db'

GALGROUP = -1001131250808


@app.on_message(filters.incoming & filters.chat(GALGROUP))
async def galgroup_msg(client, message):
    # logging.info(message)
    if message.reply_to_message:
        # see the msg replies to which another one as legal.
        logging.info(f'💤 Message {message.id} replied to msg {message.reply_to_message_id}, ignoring')
        return

    if not message.from_user:
        # see the msg sent by non-user as legal
        logging.info(f'💤 Message {message.id} is sent by non-user {message.sender_chat.title}, ignoring')
        return

    logging.info(f'🔍 User {message.from_user.id} {message.from_user.first_name} sent message {message.id},'
                 f' looking for common chats.')

    if await check_common_chat(message.from_user.id, message.from_user.first_name, GALGROUP):
        # logging.info(f'User {message.from_user.id} {message.from_user.first_name} is in the chat')
        pass
    else:
        logging.warning(f'⚠️ User {message.from_user.id} {message.from_user.first_name} is NOT in the chat!')
        # await app.delete_user_history(GALGROUP, message.from_user.id)
        await app.delete_messages(GALGROUP, message.id)
        await app.ban_chat_member(GALGROUP, message.from_user.id)
        text = f'🛑 **New banned user**\n\n**ID**: {message.from_user.id}\n' \
               f'**Name**: {message.from_user.first_name}\n' \
               f'**User**: {"@" + message.from_user.username if message.from_user.username else "None"}\n\n' \
               f'👋🏻 **Action**: Kicked\n' \
               f'🤔 **Reason**: Abuse Telegram bug'
        await app.send_message(GALGROUP, text)


async def check_common_chat(user_id, first_name, target_chat):
    # not querying api too much, check local db first
    # cursor = DB.execute('SELECT * FROM members WHERE userid=:target', {'target': user_id})
    cursor = await db_async(DB, 'SELECT * FROM members WHERE userid=:target', {'target': user_id})
    row = cursor.fetchone()
    if row:
        assert row[0] == user_id
        logging.info(f'✅📖 User {user_id} {row[1]} found in db, time {row[2]}')
        if time.time() - row[2] < 86400:
            return True

    result = False
    try:
        common = await app.get_common_chats(user_id)
        for chat in common:
            if chat.id == target_chat:
                result = True
                logging.info(f'✅🌐 User {user_id} {first_name} found in (API) common group')
                # DB.execute('REPLACE INTO members VALUES (?,?,?)', (user_id, first_name, int(time.time())))
                await db_async(DB, 'REPLACE INTO members VALUES (?,?,?)', (user_id, first_name, int(time.time())))
                # DB.commit()
                await dbcommit_async(DB)
                break
    except PeerIdInvalid:
        logging.error(f'❌ Cannot get common group due to PEER INVALID, try get chat member instead.')
        #chat_member = await app.get_chat_member(target_chat, user_id)
        results = []
        async for m in app.get_chat_members(target_chat, query=first_name, filter=pyrogram.enums.ChatMembersFilter.SEARCH):
            results.append(m)
        for chat_member in results:
            if chat_member.user.id == user_id:
                result = True
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
    #bot = asyncio.create_task(bot_init())
    #await bot
    await asyncio.gather(bot_init())


async def db_async(conn, *query):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: conn.execute(query[0], query[1]))


async def dbcommit_async(conn):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: conn.commit())


async def init_db():
    global DB
    DB = sqlite3.connect(DBFILE, check_same_thread=False)
    DB.execute('CREATE TABLE IF NOT EXISTS members (userid INTEGER PRIMARY KEY,'
               ' firstName TEXT, lastCheck INTEGER)')
    DB.execute('CREATE UNIQUE INDEX IF NOT EXISTS userid_index ON members (userid)')
    DB.commit()


if __name__ == '__main__':
    # signal.signal(signal.SIGINT, signal_handler)
    # signal.pause()
    asyncio.get_event_loop().run_until_complete(main())
     #asyncio.run(main())
