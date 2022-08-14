import aiohttp, json, io
from myTypes.MusicMetadata import netease_metadata


async def fetch_mp3_metadata(song_id: int) -> netease_metadata:
    async with aiohttp.ClientSession() as session:
        api_resp = await session.post("https://netease.esutg.workers.dev/api", data=str(song_id))
        if api_resp.ok:
            metadata = await api_resp.text()
            metadata = netease_metadata(metadata)
        else:
            raise ValueError("Metadata error!")

        cover_link: str = metadata.album_pic
        cover_img_resp = await session.get(cover_link)
        cover_img = io.BytesIO(await cover_img_resp.read())
        cover_img.seek(0)

        metadata.album_pic = cover_img
        metadata.cover_type = "image/png" if cover_link.endswith('.png') else "image/jpeg"
        return metadata


async def download_mp3(song_id: int) -> io.BytesIO:
    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=400)) as session:
        audio_api_resp = await session.post("https://netease.esutg.workers.dev/audioapi", data=str(song_id))
        try:
            audio_link = json.loads(await audio_api_resp.text())['mp3']
        except Exception:
            raise ValueError(f"[download_mp3] No mp3 for {song_id}")

        audio_resp = await session.get(audio_link)
        size = int(audio_resp.headers.get("Content-Length"))
        memfile = io.BytesIO()
        print('[download_mp3] Downloading...')
        loaded = 0
        async for chunk in audio_resp.content.iter_chunked(100000):
            loaded += len(chunk)
            print(f'\r[download_mp3] Progress: {loaded} / {size}', end='')
            memfile.write(chunk)
        print("\n[download_mp3] Complete!")
        memfile.seek(0)
        return memfile
