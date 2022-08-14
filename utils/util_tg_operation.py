import asyncio
import logging
import os
import time
from datetime import datetime, timedelta

import eyed3, mutagen
import pyrogram
import pyrogram.errors
from pyrogram.raw import functions

import global_var
import myTypes.MusicMetadata
from botConfig import *
from services.netease_music import fetch_mp3_metadata, download_mp3
from services import bili_music
from myTypes.MemberCredit import MemberCredit
from utils.util_str2filename import slugify

FILE_ID_CACHE = {}


async def speak(chat_id: int, msg_choices: (str, list), reply_to_msg_id: int = None):
    app = global_var.app
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
    chat_action_chats = {}

    def add(self, chat_id: int, action: pyrogram.enums.chat_action = None):
        if chat_id in self.chat_action_chats:
            self.chat_action_chats[chat_id] += 1
        else:
            self.chat_action_chats.update({
                chat_id: 1
            })
            asyncio.create_task(send_chat_action(action, chat_id))
        logging.info(f'[WorkingFlags] the {chat_id} has {self.chat_action_chats[chat_id]}')

    def remove(self, chat_id: int):
        logging.info(f'[WorkingFlags] the {chat_id} has {self.chat_action_chats[chat_id]}')
        if chat_id not in self.chat_action_chats:
            return
        else:
            if self.chat_action_chats[chat_id] == 1:
                self.chat_action_chats.pop(chat_id)
            else:
                self.chat_action_chats[chat_id] -= 1

    def check(self, chat_id: int):
        return chat_id in self.chat_action_chats


WORKING_FLAGS = WorkingFlags()


async def send_chat_action(action: pyrogram.enums.chat_action, chat_id: int):
    app = global_var.app
    while 1:
        await app.send_chat_action(chat_id, action)
        await asyncio.sleep(5)
        if not WORKING_FLAGS.check(chat_id):
            logging.info(f"[send_chat_action] Chat action {action} at chat {chat_id} ended.")
            break


async def send_song(song_id: int, chat_id: int):
    global WORKING_FLAGS
    app = global_var.app
    songDao = global_var.db.songDao
    logging.info(f'[send_song] 🎵 Sending music, id: {song_id} to {chat_id}')
    WORKING_FLAGS.add(chat_id, pyrogram.enums.chat_action.ChatAction.UPLOAD_DOCUMENT)
    # asyncio.create_task(send_chat_action(pyrogram.enums.chat_action.ChatAction.UPLOAD_DOCUMENT, chat_id))
    # check cache

    cached_id = await songDao.get_cached_song(song_id)
    if cached_id:
        logging.info(f"[send_song] 🎵 Cache hit, song {song_id}")
        cache_msg_id = cached_id
        try:
            cache_msg = await app.get_messages(chat_id=KIMIKACACHE, message_ids=cache_msg_id)
            if cache_msg is None:
                raise ValueError("[send_song] Cache msg does not exist.")
            await cache_msg.forward(chat_id=chat_id)
            WORKING_FLAGS.remove(chat_id)
        except (pyrogram.errors.RPCError, ValueError, AttributeError) as err:
            logging.warning(f"[send_song] 🎵 Cache expired, song {song_id}, try again.")
            await songDao.delete_song_cache(song_id)
            await send_song(song_id, chat_id)
        return

    download_mp3_task = asyncio.create_task(download_mp3(song_id))
    metadata_task = asyncio.create_task(fetch_mp3_metadata(song_id))

    try:
        n_metadata: myTypes.MusicMetadata.netease_metadata = await metadata_task
    except Exception as err:
        logging.error(f'🎵[metadata_task] Something went wrong! {err}')
        await speak(chat_id=chat_id, msg_choices='kimika-sticker/5')  # http cat 404
        WORKING_FLAGS.remove(chat_id)
        return

    try:
        audio_data = await download_mp3_task
        caption = ''
        filename = 'music.mp3'
    except Exception as err:
        logging.warning(f'🎵[download_mp3_task] Netease mp3 - something went wrong! {err} using bilibili instead!')

        # use bilibili instead
        bili_results = await bili_music.bili_search(f'{n_metadata.artist} - {n_metadata.name}')
        if bili_results is None:
            logging.error(f'🎵[bili_music_result] bili_results do not return anything!')
            await speak(chat_id=chat_id, msg_choices='kimika-sticker/6')  # http cat 402 payment required
            WORKING_FLAGS.remove(chat_id)
            return
        best_result = await bili_music.get_best(bili_results, n_metadata)
        try:
            audio_data = await bili_music.download_audio(best_result)
            caption = '🅱'
            filename = f'music.{best_result.format}'
        except Exception as err:
            logging.error(f'🎵[bili_music_download] Cannot download audio file! {err}')
            await speak(chat_id=chat_id, msg_choices='kimika-sticker/6')  # http cat 402 payment required
            WORKING_FLAGS.remove(chat_id)
            return

    # print(f"Mp3 size {len(mp3.getvalue())}")
    media_tempfile = open(filename, mode='w+b')
    media_tempfile.write(audio_data.getvalue())
    media_tempfile.close()
    # todo: mutagen 不幹了
    if filename.endswith('mp3'):
        mp3_obj = eyed3.load(filename)
        mp3_obj.initTag()
        # mp3_obj.tag.album = n_metadata.album
        # mp3_obj.tag.artist = n_metadata.artist
        # mp3_obj.tag.title = n_metadata.name
        # mp3_obj.tag.images.set(3, n_metadata.album_pic.read(), n_metadata.cover_type)
        # mp3_obj.tag.comments.set('Downloaded by Kimika')
        mp3_obj.tag.save()

    sent = await app.send_audio(
        chat_id=chat_id,
        audio=filename,
        duration=n_metadata.duration,
        performer=n_metadata.artist,
        title=n_metadata.name,
        thumb=n_metadata.album_pic,
        file_name=f'{slugify(n_metadata.artist)} - {slugify(n_metadata.name)}.mp3',
        protect_content=False,
        # caption=caption
    )
    logging.info(f'[send_song] 🎵 Music sent! {chat_id}, {n_metadata.name}')
    WORKING_FLAGS.remove(chat_id)
    cache_msg = await sent.forward(KIMIKACACHE)
    await songDao.save_song_cache(song_id, cache_msg.id)
    if os.path.exists(filename):
        os.remove(filename)
    else:
        logging.error(f"[send_song] {filename} does not exist")


async def get_user_credit(user: int | pyrogram.types.User, chatid: int = None, ignore_400=False) -> MemberCredit:
    app = global_var.app
    if isinstance(user, int) and not ignore_400:
        userid = user
    elif isinstance(user, pyrogram.types.User):
        userid = user.id
    else:
        raise ValueError('[get_user_credit] 請求過於惡俗！')

    result = MemberCredit()

    try:
        user_info = await app.get_users(userid)
        full_user_info = await app.invoke(functions.users.GetFullUser(id=await app.resolve_peer(userid)))

        result.photo = True if user_info.photo else False
        result.new_account = userid > 5000000000
        result.username = user_info.username if user_info.username else None
        result.bio = full_user_info.full_user.about if full_user_info.full_user.about else None
        if user_info.is_deleted:
            result.valid = False
    except pyrogram.errors.PeerIdInvalid:
        if ignore_400:
            logging.warning(f'[get_user_credit] Peer ID invalid for unknown reason! Ignoring, the bio is unavailable')
            result.bio = None
            result.photo = True if user.photo else False
            result.new_account = userid > 5000000000
            result.username = user.username if user.username else None
        else:
            logging.error('[get_user_credit] 過於惡俗！Peer ID invalid for unknown reason!')
            raise InterruptedError('[get_user_credit] Cannot ignoring 400!')

    # logging.info(full_user_info.full_user.about)

    if chatid and chatid < 0:
        try:  # in case the user is left or deleted
            chat_member_info = await app.get_chat_member(chat_id=chatid, user_id=userid)
            joined_date = chat_member_info.joined_date
            if joined_date:
                result.joined_time = int(chat_member_info.joined_date.timestamp())
                result.joined_time_readable = chat_member_info.joined_date.strftime('%d %b, %Y %H:%M')
            else:
                result.joined_time = 0
                result.joined_time_readable = '不明'

        except pyrogram.errors.UserNotParticipant:
            logging.warning(f'[credit] the user {userid} is not in the group')
            result.joined_time = int(time.time())
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


async def get_chat_credit(chat: int | pyrogram.types.Chat, chatid: int = None, ignore_400=False) -> MemberCredit:
    app = global_var.app
    if isinstance(chat, int) and not ignore_400:
        userid = chat
    elif isinstance(chat, pyrogram.types.Chat):
        userid = chat.id
    else:
        raise ValueError('[get_chat_creditv] 請求過於惡俗！')

    result = MemberCredit()

    try:
        chat_info = await app.get_chat(userid)

        result.photo = True if chat_info.photo else False
        result.new_account = True
        result.username = chat_info.username if chat_info.username else None
        result.bio = chat_info.description if chat_info.description else None

    except pyrogram.errors.PeerIdInvalid:
        if ignore_400:
            logging.warning(f'[get_chat_credit] Peer ID invalid for unknown reason! Ignoring, the bio is unavailable')
            result.bio = None
            result.photo = True if chat.photo else False
            result.new_account = userid > 5000000000
            result.username = chat.username if chat.username else None
        else:
            logging.error('[get_chat_credit] 過於惡俗！Peer ID invalid for unknown reason!')
            raise InterruptedError('[get_chat_credit] Cannot ignoring 400!')

    # logging.info(full_user_info.full_user.about)

    if chatid and chatid < 0:
        try:  # in case the user is left or deleted
            chat_member_info = await app.get_chat_member(chat_id=chatid, user_id=userid)
            joined_date = chat_member_info.joined_date
            if joined_date:
                result.joined_time = int(chat_member_info.joined_date.timestamp())
                result.joined_time_readable = chat_member_info.joined_date.strftime('%d %b, %Y %H:%M')
            else:
                result.joined_time = 0
                result.joined_time_readable = '不明'

        except pyrogram.errors.UserNotParticipant:
            logging.warning(f'[get_chat_credit] the chat {userid} is not in the group')
            result.joined_time = int(time.time())
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


def get_sender_id(message: pyrogram.types.Message):
    if message.from_user:
        return message.from_user.id
    else:
        return message.sender_chat.id


def get_sender_name(message: pyrogram.types.Message):
    if message.from_user:
        return message.from_user.first_name
    else:
        return message.sender_chat.title or message.sender_chat.first_name
