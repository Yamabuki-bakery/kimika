import pyrogram
from utils.util_anti_replay import anti_replay
from botConfig import *


@anti_replay
async def return_file_id(client: pyrogram.Client, message: pyrogram.types.Message):
    app = client
    media_uri = ''
    # need to save to cache
    if (message.media and message.media != pyrogram.enums.MessageMediaType.WEB_PAGE) or message.forward_date:
        saved = await app.forward_messages(chat_id=KIMIKACACHE, from_chat_id=message.chat.id, message_ids=message.id)
    if message.media == pyrogram.enums.MessageMediaType.STICKER:
        media_uri = 'kimika-sticker/' + str(saved.id)
    elif message.media == pyrogram.enums.MessageMediaType.PHOTO:
        media_uri = 'kimika-photo/' + str(saved.id)
    elif message.media == pyrogram.enums.MessageMediaType.VIDEO:
        media_uri = 'kimika-video/' + str(saved.id)
    elif message.media == pyrogram.enums.MessageMediaType.DOCUMENT:
        media_uri = 'kimika-document/' + str(saved.id)
    elif message.media == pyrogram.enums.MessageMediaType.ANIMATION:
        media_uri = 'kimika-animation/' + str(saved.id)
    elif message.forward_date:
        media_uri = 'kimika-message/' + str(saved.id)
    else:
        return

        # print(message)
    # print(media_uri)
    await app.send_message(chat_id=message.chat.id, text=media_uri)
