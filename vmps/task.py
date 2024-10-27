import logging
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Dict

import yaml

from vmps.audio.track import AudioClip, AudioTrack
from vmps.video.track import VideoClip, VideoTrack


class VMPSTask:
    def __init__(self, config: Dict):
        workspace = Path(tempfile.TemporaryDirectory().name)
        workspace.mkdir(parents=True, exist_ok=True)
        self.output = Path(config["output"])
        if "video" in config:
            self.video_track = VideoTrack(workspace / "video", **config["video"]["meta"])
            self.video_track.add_clips_from_config(config["video"]["clips"])
        else:
            self.video_track = None

        if "audio" in config:
            self.audio_track = AudioTrack(workspace / "audio", **config["audio"]["meta"])
            self.audio_track.add_clips_from_config(config["audio"]["clips"])
        else:
            self.audio_track = None

    def sanity_check(self):
        if self.video_track and self.audio_track:
            assert (
                self.video_track.duration >= self.audio_track.duration
            ), "Video duration must not be shorter than audio duration."

    def process(self):
        self.sanity_check()
        if self.video_track:
            self.video_track.process()
        if self.audio_track:
            self.audio_track.process()

        if self.video_track and self.audio_track:
            ffmpeg_cmd = ["ffmpeg", "-y", "-v", "warning"]
            ffmpeg_cmd.extend(["-i", self.video_track.path.as_posix()])
            ffmpeg_cmd.extend(["-i", self.audio_track.path.as_posix()])
            ffmpeg_cmd.extend(["-filter_complex", f"[1:a]apad,atrim=duration={self.video_track.duration}[aud]"])
            ffmpeg_cmd.extend(["-map", "0:v"])
            ffmpeg_cmd.extend(["-map", "[aud]"])
            ffmpeg_cmd.extend(["-c:v", "copy"])
            ffmpeg_cmd.extend(["-c:a", "aac"])
            ffmpeg_cmd.append(self.output.as_posix())
            try:
                logging.info(ffmpeg_cmd)
                subprocess.run(ffmpeg_cmd, check=True)
            except subprocess.CalledProcessError as e:
                raise ValueError(f"Failed to merge video and audio: {e}")
        elif self.video_track:
            shutil.move(self.video_track.path, self.output)
        elif self.audio_track:
            shutil.move(self.audio_track.path, self.output)
        else:
            raise ValueError("No video or audio track found.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    with open("example/config.yaml") as f:
        config = yaml.safe_load(f)
    task = VMPSTask(config)
    task.process()
