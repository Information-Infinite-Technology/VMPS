import ffmpeg
import logging

logger = logging.getLogger(__name__)


def get_video_codec(filepath):
    try:
        probe = ffmpeg.probe(filepath)
    except ffmpeg.Error as e:
        logger.error(e.stderr.decode("utf-8"))
        raise e

    video_stream = next((stream for stream in probe["streams"] if stream["codec_type"] == "video"), None)
    return video_stream["codec_name"] if video_stream else None


def has_audio_track(filepath):
    try:
        probe = ffmpeg.probe(filepath)
        streams = probe.get('streams', [])
        for stream in streams:
            if stream.get('codec_type') == 'audio':
                return True
        return False
    except ffmpeg.Error as e:
        logger.error(f"An error occurred when ffprobe {filepath}: {e.stderr.decode('utf-8')}")
        raise e
