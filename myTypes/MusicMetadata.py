import io, json, re


class netease_metadata:
    title: str
    artist: str
    album: str
    year: int
    album_pic: str | io.BytesIO
    vip: int
    lyric: str | None
    duration: int
    cover_type: str

    def __init__(self, metadata_json: str):
        data = json.loads(metadata_json)
        self.title = data['name']
        self.artist = data['artist']
        self.album = data['album']
        self.year = data['year']
        self.album_pic = data['albumPicUrl']
        self.vip = data['vip']
        self.duration = data['duration']
        self.lyric = data['lyric']


class bili_metadata:
    sid: int
    pubdate: int
    title: str
    artist: str  # the [author] attribute in bili api
    audio_url: str | None
    quality: str | None
    duration: int | None
    format: str
    score: int  # matching score, lower is better

    def __init__(self, result_record: dict):
        self.sid = result_record['id']
        self.pubdate = result_record['pubdate']
        self.title = result_record['title']
        self.artist = result_record['author']
        self.duration = None
        self.format = 'm4a'
        self.get_audio_url(result_record)
        self.score = 999

    def get_audio_url(self, result_record: dict):
        best_quality = {
            "quality": "000kbps",
            "url": ""
        }
        play_url_list = result_record['play_url_list']
        for record in play_url_list:
            if record['url'] and record['quality'] and record['quality'] > best_quality['quality']:
                best_quality = record
            elif record['url'] and record['quality'] and record['quality'] == best_quality['quality']:
                groups = re.search(r'https://(.*)\?', record['url'])
                if groups and groups[1].endswith('m4a'):
                    best_quality = record
        if best_quality['url'] is None:
            self.quality = None
            self.audio_url = None
        else:
            self.quality = best_quality['quality']
            self.audio_url = best_quality['url']
            groups = re.search(r'https://.*\.(.{3,5})\?', self.audio_url)
            if groups:
                self.format = groups[1]
