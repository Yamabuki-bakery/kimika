import asyncio
import eyed3
import os
import re
from services.netease_music import download_mp3, fetch_mp3_metadata

target = 206276


async def main():
    text = input('Enter netease song:\n')
    results = re.search(r'song[A-Za-z?/=#]{0,9}(\d{1,12})', text)
    if results is not None:
        song_id = results[1]
    else:
        try:
            song_id = str(int(text))
        except ValueError:
            print(f"ID {text} illegal.")
            return
    # TODO: check cache
    download_mp3_task = asyncio.create_task(download_mp3(song_id))
    metadata_task = asyncio.create_task(fetch_mp3_metadata(song_id))
    mp3 = await download_mp3_task
    metadata = await metadata_task
    # print(metadata)
    # print(f"Mp3 size {len(mp3.getvalue())}")
    mp3_temp = open("temp.mp3", mode='w+b')
    mp3_temp.write(mp3.getvalue())
    mp3_temp.close()
    input("Press enter to continue")
    mp3_obj = eyed3.load("temp.mp3")
    if mp3_obj.tag is None:
        mp3_obj.initTag()
    mp3_obj.tag.album = metadata["album"]
    mp3_obj.tag.artist = metadata["artist"]
    mp3_obj.tag.title = metadata["name"]
    mp3_obj.tag.images.set(3, metadata["albumPicUrl"].read(), metadata["coverType"])
    mp3_obj.tag.save()

    os.startfile("temp.mp3")


if __name__ == '__main__':
    asyncio.run(main())
