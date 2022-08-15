import mutagen, logging
import io
from mutagen.id3 import ID3, APIC, COMM, TALB, TIT2, TPE1, TPE2, ID3NoHeaderError
from myTypes.MusicMetadata import netease_metadata, bili_metadata


# Not completed, 嚶嚶
def apply_metadata(metadata: netease_metadata | bili_metadata, filename: str):
    def write_keys(song):
        # Writing metadata
        # Due to different capabilites of containers, only
        # ones that can actually be stored will be written.
        complete_metadata = {
            "title": [metadata.title],
            "artist": [metadata.artist],
            "albumartist": [metadata.artist],
            "album": [metadata.album if isinstance(metadata, netease_metadata) else ""],
            "copyright": ['Downloaded by kimika'],
        }
        for k, v in complete_metadata.items():
            try:
                song[k] = v
            except Exception as err:
                logging.error(f'[apply_metadata][write_keys] {err}')
        song.save()

    def mp4():
        from mutagen import easymp4
        from mutagen.mp4 import MP4, MP4Cover

        song = easymp4.EasyMP4(filename)
        write_keys(song)
        if isinstance(metadata, netease_metadata):
            song = MP4(filename)
            song["covr"] = [MP4Cover(metadata.album_pic.getvalue())]
            song.save()

    def mp3():
        from mutagen.mp3 import EasyMP3
        from mutagen.id3 import ID3, APIC

        song = EasyMP3(filename)
        write_keys(song)
        if isinstance(metadata, netease_metadata):
            song = ID3(filename)
            song.update_to_v23()  # better compatibility over v2.4
            song.add(
                APIC(
                    encoding=3,
                    mime=metadata.cover_type,
                    type=3,
                    desc="",
                    data=metadata.album_pic.getvalue(),
                )
            )
            song.save(v2_version=3)

    def flac():
        from mutagen.flac import FLAC, Picture

        song = FLAC(filename)
        write_keys(song)
        if isinstance(metadata, netease_metadata):
            pic = Picture()
            pic.data = metadata.album_pic.getvalue()
            pic.mime = metadata.cover_type
            song.add_picture(pic)
            song.save()

    def ogg():
        import base64
        from mutagen.flac import Picture
        from mutagen.oggvorbis import OggVorbis

        song = OggVorbis(filename)
        write_keys(song)
        if isinstance(metadata, netease_metadata):
            pic = Picture()
            pic.data = metadata.album_pic.getvalue()
            pic.mime = metadata.cover_type
            song["metadata_block_picture"] = [
                base64.b64encode(pic.write()).decode("ascii")
            ]
            song.save()

    format = filename.split(".")[-1].upper()
    logging.info(f'[apply_metadata] Writing tag: {format}')
    for ext, method in [
        ({"M4A", "M4B", "M4P", "MP4"}, mp4),
        ({"MP3"}, mp3),
        ({"FLAC"}, flac),
        ({"OGG", "OGV"}, ogg),
    ]:
        if format in ext:
            method()

