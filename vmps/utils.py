from datetime import timedelta


def timecode2seconds(timecode):
    """Convert hh:mm:ss.sss timecode to seconds."""
    timecode = timecode.split(":")
    return int(timecode[0]) * 3600 + int(timecode[1]) * 60 + float(timecode[2])


def seconds2timecode(seconds):
    delta = timedelta(seconds=seconds)

    hours, remainder = divmod(delta.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    timecode = f"{hours:02}:{minutes:02}:{seconds:02}.{int(delta.microseconds / 1000):03}"
    return timecode
