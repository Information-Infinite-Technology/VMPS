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
