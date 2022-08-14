import mutagen
import io
from mutagen.id3 import ID3, APIC, COMM, TALB, TIT2, TPE1, TPE2, ID3NoHeaderError

# Not completed, 嚶嚶
def mp3_id3(
        mp3_filename: str,
        title: str = None,
        album: str = None,
        artist: str = None,
        comments: str = None,
        cover=None,
        cover_type='image/jpg'):
    print(mp3_filename)
    try:
        tags = ID3(mp3_filename)
        tags.delete()
    except ID3NoHeaderError:
        print("Adding ID3 header")
        tags = ID3()

    if title:
        tags.add(TIT2(encoding=3, text=title))

    if comments:
        print('writing comments')
        tags.add(COMM(encoding=3, desc=comments, text='test'))

    if cover:
        tags.add(APIC(encoding=0, mime=cover_type, type=0, desc="Kimika cover", data=cover.read()))

    tags.save(mp3_filename)

    # tags["TIT2"] = TIT2(encoding=3, text=title)
    # tags["TALB"] = TALB(encoding=3, text=u'mutagen Album Name')
    # tags["TPE2"] = TPE2(encoding=3, text=u'mutagen Band')
    # tags["COMM"] = COMM(encoding=3, lang=u'eng', desc='desc', text=u'mutagen comment')
    # tags["TPE1"] = TPE1(encoding=3, text=u'mutagen Artist')
    # tags["TCOM"] = TCOM(encoding=3, text=u'mutagen Composer')
    # tags["TCON"] = TCON(encoding=3, text=u'mutagen Genre')
    # tags["TDRC"] = TDRC(encoding=3, text=u'2010')
    # tags["TRCK"] = TRCK(encoding=3, text=u'track_number')
