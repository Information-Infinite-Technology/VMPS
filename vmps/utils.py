def timecode2seconds(timecode):
    """Convert hh:mm:ss.sss timecode to seconds."""
    timecode = timecode.split(":")
    return int(timecode[0]) * 3600 + int(timecode[1]) * 60 + float(timecode[2])


def is_image(path):
    from PIL import Image

    try:
        im = Image.open(filename)
        return True
    except IOError:
        return False
