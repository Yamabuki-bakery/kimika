import pyrogram
import re

from utils.util_tg_operation import send_song


async def netease_link(client: pyrogram.Client, message: pyrogram.types.Message, rtp: float) -> bool:
    message_text: str = message.text or message.caption or ""
    results = re.search(r'song[A-Za-z?/=#]{0,9}(\d{1,12})', message_text)
    if results is not None:
        song_id = results[1]
    else:
        results = re.search(r'(\d{4,12})$', message_text)
        if results is not None:
            song_id = results[1]
        else:
            song_id = None

    if song_id:
        await send_song(int(song_id), message.chat.id)
        return True
    else:
        return False
