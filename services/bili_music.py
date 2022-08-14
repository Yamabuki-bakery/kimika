import json, io, asyncio, aiohttp, logging
from myTypes.MusicMetadata import bili_metadata, netease_metadata


async def bili_search(keyword: str) -> list[bili_metadata] | None:
    logging.info(f'[bili_search] Searching for [{keyword}]')
    async with aiohttp.ClientSession() as session:
        api_resp = await session.get(
            f'https://api.bilibili.com/audio/music-service-c/s?search_type=music&page=1&pagesize=30&keyword={keyword}')
        if api_resp.ok:
            data = await api_resp.text(encoding='UTF-8')
        else:
            logging.error(f'[bili_search] [{keyword}] API resp not ok! ')
            return None

        try:
            data = json.loads(data)
        except json.JSONDecodeError as err:
            logging.error(f'[bili_search] [{keyword}] JSON error! {err}')
            return None

        if data['data']['result']:
            results: list = data['data']['result']
        else:
            logging.error(f'[bili_search] [{keyword}] searching did not return any result!')
            return None

        bili_results: list[bili_metadata] = []
        for record in results:
            metadata = bili_metadata(record)
            bili_results.append(metadata)

        return bili_results


async def get_best(bili_results: list[bili_metadata], origin_metadata: netease_metadata) -> bili_metadata:
    # scoring scheme: lower is better
    duration_tasks = []
    for bili_result in bili_results:
        duration_tasks.append(asyncio.create_task(get_duration_task(bili_result)))
    for no in range(len(duration_tasks)):
        duration: int = await duration_tasks[no]
        bili_results[no].duration = duration

    scores: list[int] = []
    for bili_result in bili_results:
        score = 0
        score += levenshtein_distance(bili_result.title, origin_metadata.name)
        score += levenshtein_distance(bili_result.author, origin_metadata.artist)
        score += abs(bili_result.duration - origin_metadata.duration)
        scores.append(score)

    best_score = min(scores)
    return bili_results[scores.index(best_score)]


async def get_duration_task(mdata: bili_metadata) -> int:
    async with aiohttp.ClientSession() as session:
        api_resp = await session.get(f'https://www.bilibili.com/audio/music-service-c/web/song/info?sid={mdata.sid}')
        retry = 3
        while retry:
            if api_resp.ok:
                data = await api_resp.text(encoding='UTF-8')
                break
            else:
                retry -= 1
                if retry:
                    logging.warning(f'[get_duration_task] Retrying [{mdata.sid}]')
                    await asyncio.sleep(2)
                    continue
                logging.error(f'[get_duration_task] [{mdata.sid}] API resp not ok! ')
                return 0

        try:
            data = json.loads(data)
        except json.JSONDecodeError as err:
            logging.error(f'[get_duration_task] [{mdata.sid}] JSON error! {err}')
            return 0

        if 'data' in data:
            if 'duration' in data['data']:
                return data['data']['duration']

        return 0





def levenshtein_distance(s: str, t: str) -> int:
    # for all i and j, d[i,j] will hold the Levenshtein distance between
    # the first i characters of s and the first j characters of t
    s = '/' + s
    t = '/' + t
    m = len(s)
    n = len(t)

    d = [[0] * n for _ in range(m)]

    # source prefixes can be transformed into empty string by
    # dropping all characters
    for i in range(1, m):
        d[i][0] = i

    # target prefixes can be reached from empty source prefix
    # by inserting every character
    for j in range(1, n):
        d[0][j] = j

    for j in range(1, n):
        for i in range(1, m):
            if s[i] == t[j]:
                substitution_cost = 0
            else:
                substitution_cost = 1

            d[i][j] = min(d[i - 1][j] + 1,  # deletion
                          d[i][j - 1] + 1,  # insertion
                          d[i - 1][j - 1] + substitution_cost)  # substitution

    return d[m - 1][n - 1]


async def download_audio(metadata: bili_metadata) -> io.BytesIO:
    bili_headers = {
        'referer': 'https://www.bilibili.com/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0'
    }
    async with aiohttp.ClientSession(headers=bili_headers, connector=aiohttp.TCPConnector(limit=400)) as session:
        if metadata.audio_url:
            audio_resp = await session.get(metadata.audio_url)
        else:
            raise ValueError(f'[bili_download_audio] Missing audio link for {metadata.title}!')

        size = int(audio_resp.headers.get("Content-Length"))
        memfile = io.BytesIO()
        print('[bili_download_audio] Downloading...')
        loaded = 0
        async for chunk in audio_resp.content.iter_chunked(10000):
            loaded += len(chunk)
            print(f'\r[bili_download_audio] Progress: {loaded} / {size}', end='')
            memfile.write(chunk)
        print("\n[bili_download_audio] Complete!")
        memfile.seek(0)
        return memfile


async def test():
    from services.netease_music import fetch_mp3_metadata
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s [%(levelname)s] %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S'
                        )
    target = 442316000
    origin_meta = await fetch_mp3_metadata(target)
    bili_results = await bili_search(f'{origin_meta.artist} - {origin_meta.name}')
    best_result = await get_best(bili_results, origin_meta)
    print(json.dumps(best_result.__dict__, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    asyncio.run(test())

