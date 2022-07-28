import logging
import pyrogram
import eyed3
import asyncio
import time
import os
from datetime import datetime, timedelta
from pyrogram.raw import functions
import pyrogram.errors

from botConfig import *
import global_var
from util_database import db_async, dbcommit_async
from util_pyncmm import fetch_mp3_metadata, download_mp3

FILE_ID_CACHE = {}


async def speak(chat_id: int, msg_choices: (str, list), reply_to_msg_id: int = None):
    app = global_var.app
    DB = global_var.DB
    msgs_to_send = list(msg_choices) if not isinstance(msg_choices, str) else [msg_choices]
    returns = []
    for msg in msgs_to_send:
        try:
            if msg.startswith('kimika-message/'):
                message_id = int(msg.split('/')[1])
                target_msg = await app.get_messages(chat_id=KIMIKACACHE, message_ids=message_id)
                returns.append(await target_msg.forward(chat_id))
            if msg.startswith('kimika-sticker/'):
                cacheid = msg.split('/')[1]
                mediaid = FILE_ID_CACHE[cacheid].split('/')[1]
                returns.append(await app.send_sticker(chat_id, mediaid, reply_to_message_id=reply_to_msg_id))
            if msg.startswith('kimika-photo/'):
                cacheid = msg.split('/')[1]
                mediaid = FILE_ID_CACHE[cacheid].split('/')[1]
                returns.append(await app.send_photo(chat_id, mediaid, reply_to_message_id=reply_to_msg_id))
            if msg.startswith('kimika-video/'):
                cacheid = msg.split('/')[1]
                mediaid = FILE_ID_CACHE[cacheid].split('/')[1]
                returns.append(await app.send_video(chat_id, mediaid, reply_to_message_id=reply_to_msg_id))
            if msg.startswith('kimika-document/'):
                cacheid = msg.split('/')[1]
                mediaid = FILE_ID_CACHE[cacheid].split('/')[1]
                returns.append(await app.send_document(chat_id, mediaid, reply_to_message_id=reply_to_msg_id))
            if msg.startswith('kimika-animation/'):
                cacheid = msg.split('/')[1]
                mediaid = FILE_ID_CACHE[cacheid].split('/')[1]
                returns.append(await app.send_animation(chat_id, mediaid, reply_to_message_id=reply_to_msg_id))
            else:
                returns.append(await app.send_message(chat_id, msg, reply_to_message_id=reply_to_msg_id))
        except (KeyError, pyrogram.errors.FileReferenceExpired):
            logging.error(f'[Send Media] File reference invalid')
            mediaid = (await find_file_id(msg)).split('/')[1]
            if msg.startswith('kimika-sticker/'):
                returns.append(await app.send_sticker(chat_id, mediaid, reply_to_message_id=reply_to_msg_id))
            if msg.startswith('kimika-photo/'):
                returns.append(await app.send_photo(chat_id, mediaid, reply_to_message_id=reply_to_msg_id))
            if msg.startswith('kimika-video/'):
                returns.append(await app.send_video(chat_id, mediaid, reply_to_message_id=reply_to_msg_id))
            if msg.startswith('kimika-document/'):
                returns.append(await app.send_document(chat_id, mediaid, reply_to_message_id=reply_to_msg_id))
            if msg.startswith('kimika-animation/'):
                returns.append(await app.send_animation(chat_id, mediaid, reply_to_message_id=reply_to_msg_id))

    return returns


async def find_file_id(kimika_uri: str):
    app = global_var.app
    cache_message_id = int(kimika_uri.split('/')[1])
    cache_message = await app.get_messages(KIMIKACACHE, cache_message_id)
    if kimika_uri.startswith('kimika-sticker/'):
        result = 'sticker/' + cache_message.sticker.file_id
        FILE_ID_CACHE.update({cache_message_id: result})
        return result
    if kimika_uri.startswith('kimika-photo/'):
        result = 'photo/' + cache_message.photo.file_id
        FILE_ID_CACHE.update({cache_message_id: result})
        return result
    if kimika_uri.startswith('kimika-video/'):
        result = 'video/' + cache_message.video.file_id
        FILE_ID_CACHE.update({cache_message_id: result})
        return result
    if kimika_uri.startswith('kimika-document/'):
        result = 'document/' + cache_message.document.file_id
        FILE_ID_CACHE.update({cache_message_id: result})
        return result
    if kimika_uri.startswith('kimika-animation/'):
        result = 'animation/' + cache_message.animation.file_id
        FILE_ID_CACHE.update({cache_message_id: result})
        return result


class WorkingFlags:
    chat_action_chats = []


WORKING_FLAGS = WorkingFlags()


async def send_chat_action(action: pyrogram.enums.chat_action, chat_id: int):
    app = global_var.app
    DB = global_var.DB
    while 1:
        await app.send_chat_action(chat_id, action)
        await asyncio.sleep(5)
        if chat_id not in WORKING_FLAGS.chat_action_chats:
            logging.info(f"Chat action {action} at chat {chat_id} ended.")
            break


async def send_song(song_id: int, chat_id: int):
    global WORKING_FLAGS
    app = global_var.app
    DB = global_var.DB
    logging.info(f'🎵 Sending music, id: {song_id} to {chat_id}')
    if chat_id not in WORKING_FLAGS.chat_action_chats:
        WORKING_FLAGS.chat_action_chats.append(chat_id)
        asyncio.create_task(send_chat_action(pyrogram.enums.chat_action.ChatAction.UPLOAD_DOCUMENT, chat_id))
    # check cache

    cursor = await db_async(DB, 'SELECT * FROM music WHERE songid=:sid', {'sid': song_id})
    row = cursor.fetchone()
    if row:
        logging.info(f"🎵 Cache hit, song {row[1]}")
        cache_msg_id = row[2]
        try:
            cache_msg = await app.get_messages(chat_id=KIMIKACACHE, message_ids=cache_msg_id)
            if cache_msg is None:
                raise ValueError("Cache msg does not exist.")
            await cache_msg.forward(chat_id=chat_id)
            WORKING_FLAGS.chat_action_chats.remove(chat_id)
        except (pyrogram.errors.RPCError, ValueError, AttributeError) as err:
            logging.warning(f"🎵 Cache expired, song {row[1]}, try again.")
            await db_async(DB, 'DELETE FROM music WHERE songid=:sid', {'sid': song_id})
            await dbcommit_async(DB)
            await send_song(song_id, chat_id)
        return

    download_mp3_task = asyncio.create_task(download_mp3(song_id))
    metadata_task = asyncio.create_task(fetch_mp3_metadata(song_id))

    try:
        metadata = await metadata_task
    except Exception as err:
        logging.error(f'🎵[metadata_task] Something went wrong! {err}')
        await speak(chat_id=chat_id, msg_choices='kimika-sticker/5')  # http cat 404
        WORKING_FLAGS.chat_action_chats.remove(chat_id)
        return

    try:
        mp3 = await download_mp3_task
    except Exception as err:
        logging.error(f'🎵[download_mp3_task] Something went wrong! {err}')
        await speak(chat_id=chat_id, msg_choices='kimika-sticker/6')  # http cat 402 payment required
        WORKING_FLAGS.chat_action_chats.remove(chat_id)
        return

    # print(metadata)
    # print(f"Mp3 size {len(mp3.getvalue())}")
    mp3_temp = open("music.mp3", mode='w+b')
    mp3_temp.write(mp3.getvalue())
    mp3_temp.close()
    mp3_obj = eyed3.load("music.mp3")
    if mp3_obj.tag is None:
        mp3_obj.initTag()
    duration = int(mp3_obj.info.time_secs)
    mp3_obj.tag.album = metadata["album"]
    mp3_obj.tag.artist = metadata["artist"]
    mp3_obj.tag.title = metadata["name"]
    mp3_obj.tag.images.set(3, metadata["albumPicUrl"].read(), metadata["coverType"])
    mp3_obj.tag.save()

    sent = await app.send_audio(
        chat_id=chat_id,
        audio="music.mp3",
        duration=duration,
        performer=metadata["artist"],
        title=metadata["name"],
        thumb=metadata["albumPicUrl"],
        file_name=None,
        protect_content=False,
    )
    logging.info(f'🎵 Music sent! {chat_id}, {metadata["name"]}')
    WORKING_FLAGS.chat_action_chats.remove(chat_id)
    cache_msg = await sent.forward(KIMIKACACHE)
    await db_async(DB, 'INSERT INTO music(songid,cache_msg_id) VALUES (?,?)', (song_id, cache_msg.id))
    await dbcommit_async(DB)
    if os.path.exists("music.mp3"):
        os.remove("music.mp3")
    else:
        logging.error("music.mp3 does not exist")


class MemberCredit:
    valid: bool
    photo: bool
    new_account: bool
    username: str | None
    bio: str | None
    joined_time: int
    joined_time_readable: str
    msg_count_before_24h: int


async def get_user_credit(userid: int, chatid: int = None) -> MemberCredit:
    app = global_var.app
    DB = global_var.DB
    result = MemberCredit()
    result.valid = True
    user_info = await app.get_users(userid)

    result.photo = True if user_info.photo else False
    result.new_account = userid > 5000000000
    result.username = user_info.username if user_info.username else None

    if user_info.is_deleted:
        result.valid = False

    full_user_info = await app.invoke(functions.users.GetFullUser(id=await app.resolve_peer(userid)))
    # logging.info(full_user_info.full_user.about)
    result.bio = full_user_info.full_user.about if full_user_info.full_user.about else None

    if chatid and chatid < 0:
        try:  # in case the user is left or deleted
            chat_member_info = await app.get_chat_member(chat_id=chatid, user_id=userid)
            result.joined_time = int(chat_member_info.joined_date.timestamp())
            result.joined_time_readable = chat_member_info.joined_date.strftime('%d %b, %Y %H:%M')

        except pyrogram.errors.UserNotParticipant:
            logging.warning(f'[credit] the user {userid} is not in the group')
            result.joined_time = int(time.time()),
            result.joined_time_readable = 'Unknown'

        # A subroutine to find message count sent 1 day ago and older
        total_msg_count = await app.search_messages_count(chat_id=chatid, from_user=userid)
        # logging.info(f'Total msg count: {total_msg_count}')
        # limit = 50 if total_msg_count > 50 else total_msg_count
        counted = 0
        now = datetime.now()
        # logging.info(f'Start at limit {limit}')

        async for msg in app.search_messages(chat_id=chatid, from_user=userid):
            # msg: pyrogram.types.Message
            if now - msg.date < timedelta(days=1):
                counted += 1
            else:
                break

        msg_count_before_24h = total_msg_count - counted
        result.msg_count_before_24h = msg_count_before_24h
    else:
        result.joined_time = 0
        result.msg_count_before_24h = 0

    return result


async def api_check_common_chat(user_id: int, target_chat: int):
    app = global_var.app
    common = await app.get_common_chats(user_id)
    for chat in common:
        if chat.id == target_chat:
            logging.info(f'🌐 User {user_id} found in (API) common group {target_chat}')
            return True
    return False


def get_sender_id(message):
    if message.from_user:
        return message.from_user.id
    else:
        return message.sender_chat.id
