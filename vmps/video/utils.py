import ffmpeg


def get_video_codec(filepath):
    probe = ffmpeg.probe(filepath)
    video_stream = next((stream for stream in probe["streams"] if stream["codec_type"] == "video"), None)
    return video_stream["codec_name"] if video_stream else None
