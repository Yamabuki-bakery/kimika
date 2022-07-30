import asyncio, aiohttp, io, eyed3, re, json, os

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


async def fetch_mp3_metadata(song_id: int):
    async with aiohttp.ClientSession() as session:
        api_resp = await session.post("https://netease.esutg.workers.dev/api", data=str(song_id))
        if api_resp.ok:
            metadata = await api_resp.text()
            metadata = json.loads(metadata)
        else:
            raise ValueError("Metadata error!")

        cover_link: str = metadata["albumPicUrl"]
        cover_img_resp = await session.get(cover_link)
        cover_img = io.BytesIO(await cover_img_resp.read())
        cover_img.seek(0)

        metadata.update({"albumPicUrl": cover_img})
        metadata.update({"coverType": "image/png" if cover_link.endswith('.png') else "image/jpeg"})
        return metadata


async def download_mp3(song_id: int) -> io.BytesIO:
    async with aiohttp.ClientSession() as session:
        audio_api_resp = await session.post("https://netease.esutg.workers.dev/audioapi", data=str(song_id))
        try:
            audio_link = json.loads(await audio_api_resp.text())['mp3']
        except:
            raise ValueError(f"[download_mp3] No mp3 for {song_id}")
        audio_resp = await session.get(audio_link)
        size = int(audio_resp.headers.get("Content-Length"))
        memfile = io.BytesIO()
        print('[download_mp3] Downloading...')
        loaded = 0
        async for chunk in audio_resp.content.iter_chunked(10000):
            loaded += len(chunk)
            print(f'\r[download_mp3] Progress: {loaded} / {size}', end='')
            memfile.write(chunk)
        print("\n[download_mp3] Complete!")
        memfile.seek(0)
        return memfile


if __name__ == '__main__':
    asyncio.run(main())
