import logging
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Dict

import yaml

from vmps.audio.track import AudioClip, AudioTrack
from vmps.video.track import VideoClip, VideoTrack
from vmps.subtitle.subtitle import Subtitle
from vmps.video.utils import has_audio_track

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S", level=logging.WARNING
)
logger = logging.getLogger("vmps")

class VMPSTask:
    def __init__(self, data_dir, config: Dict):
        self.workspace = Path(tempfile.TemporaryDirectory().name)
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.output = Path(data_dir) / config["output"]
        if "video" in config:
            self.video_track = VideoTrack(self.workspace / "video", data_dir, **config["video"]["meta"])
            self.video_track.add_clips_from_config(config["video"]["clips"])
        else:
            self.video_track = None

        if "audio" in config:
            self.audio_track = AudioTrack(self.workspace / "audio", data_dir, **config["audio"]["meta"])
            self.audio_track.add_clips_from_config(config["audio"]["clips"])
        else:
            self.audio_track = None

        if "subtitle" in config:
            self.subtitle = Subtitle(self.workspace / "subtitle")
            self.subtitle.add_clips_from_config(config["subtitle"]["clips"])
        else:
            self.subtitle = None


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
        if self.subtitle:
            self.subtitle.process()

        ffmpeg_cmd = ["ffmpeg", "-y", "-v", "warning"]
        if self.video_track:
            video_path = self.video_track.path.as_posix()
            ffmpeg_cmd.extend(["-i", video_path])
            if self.audio_track:
                ffmpeg_cmd.extend(["-i", self.audio_track.path.as_posix()])

                # 如果之前有音频，将两个音频混合
                if has_audio_track(video_path):
                    ffmpeg_cmd.extend(["-filter_complex", f"[1:a]apad,atrim=duration={self.video_track.duration}[aud];[0:a][aud]amix=inputs=2[amix]"])
                    ffmpeg_cmd.extend(["-map", "0:v"])
                    ffmpeg_cmd.extend(["-map", "[amix]"])
                else:
                    ffmpeg_cmd.extend(["-filter_complex", f"[1:a]apad,atrim=duration={self.video_track.duration}[aud]"])
                    ffmpeg_cmd.extend(["-map", "0:v"])
                    ffmpeg_cmd.extend(["-map", "[aud]"])

                ffmpeg_cmd.extend(["-c:v", "libx264"])
                ffmpeg_cmd.extend(["-c:a", "aac"])
            if self.subtitle:
                ffmpeg_cmd.extend(["-vf", f"subtitles={self.subtitle.path.as_posix()}"])
            ffmpeg_cmd.append(self.output.as_posix())
            logger.info(f"Excuting: {' '.join(ffmpeg_cmd)}")
            subprocess.run(ffmpeg_cmd, check=True)
        elif self.audio_track:
            shutil.move(self.audio_track.path, self.output)
        else:
            raise ValueError("No video or audio track found.")

    def clean(self):
        shutil.rmtree(self.workspace)


if __name__ == "__main__":
    with open("example/config.yaml") as f:
        config = yaml.safe_load(f)
    task = VMPSTask(config)
    task.process()
    task.clean()
