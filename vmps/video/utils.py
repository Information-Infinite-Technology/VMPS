import ffmpeg


def get_video_codec(filepath):
    # Probe the input file to get codec information
    probe = ffmpeg.probe(filepath)
    # Find the video stream and extract the codec name
    video_stream = next((stream for stream in probe["streams"] if stream["codec_type"] == "video"), None)
    return video_stream["codec_name"] if video_stream else None
