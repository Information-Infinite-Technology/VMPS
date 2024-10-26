import logging
import subprocess
from pathlib import Path
from typing import Optional, Tuple
from uuid import uuid4

import ffmpeg
import filetype
import yaml
from vmps.utils import timecode2seconds
from vmps.video.utils import get_video_codec


class VideoClip:
    def __init__(
        self,
        track,
        workspace: Path,
        path: Path,
        span: Tuple[str, str],
        clip: Optional[Tuple[str, str]] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        bitrate: Optional[str] = None,
        fps: Optional[int] = None,
        extension: str = "repeat_last",
        shrink: str = "trim_end",
        layer: int = 0,
        posX: int = 0,
        posY: int = 0,
    ):
        self.asset = Path(path)
        self.span = span
        self.clip = clip
        self.width = width if width else track.width
        self.height = height if height else track.height
        self.bitrate = bitrate if bitrate else track.bitrate
        self.fps = fps if fps else track.fps
        self.extension = extension
        self.shrink = shrink
        self.layer = layer
        self.posX = posX
        self.posY = posY
        self.codec = get_video_codec(self.asset)
        self.normalized = False
        self.path = (workspace / f"{uuid4().hex}").with_suffix(self.asset.suffix)
        workspace.mkdir(parents=True, exist_ok=True)

        self.track = track
        self.track.add_clip(self)

    def normalize(self):
        if self.normalized:
            return

        logging.info(f"Normalizing {self.asset} to {self.path}")

        expected_duration = timecode2seconds(self.span[1]) - timecode2seconds(self.span[0])
        if filetype.is_image(self.asset):
            ffmpeg_cmd = ["ffmpeg", "-y", "-v", "warning", "-i", self.asset.as_posix()]
            ffmpeg_cmd.extend(["-loop", "1"])
            ffmpeg_cmd.extend(["-t", str(expected_duration)])
            ffmpeg_cmd.extend(["-vf", f"scale={self.width}:{self.height}"])
            ffmpeg_cmd.extend(["-r", str(self.fps)])
            ffmpeg_cmd.extend(["-b:v", self.bitrate])
            ffmpeg_cmd.append(self.path.as_posix())
            try:
                subprocess.run(ffmpeg_cmd, check=True)
                self.normalized = True
            except subprocess.CalledProcessError as e:
                raise ValueError(f"Failed to generate normalized video: {e}")
            return

        assert filetype.is_video(self.asset), f"Unsupported file type: {self.asset}"

        ffmpeg_cmd = ["ffmpeg", "-y", "-v", "warning", "-i", self.asset.as_posix()]
        if self.clip:
            ffmpeg_cmd.extend(["-ss", self.clip[0], "-to", self.clip[1]])
            actual_duration = timecode2seconds(self.clip[1]) - timecode2seconds(self.clip[0])
        else:
            actual_duration = float(ffmpeg.probe(self.asset.as_posix())["streams"][0]["duration"])

        vf_filters = [f"scale={self.width}:{self.height}"]
        if actual_duration < expected_duration:
            extension_duration = expected_duration - actual_duration
            if self.extension == "repeat_first":
                vf_filters.append(f"tpad=start_duration={extension_duration}:start_mode=clone, fps={self.fps}")
            elif self.extension == "repeat_last":
                vf_filters.append(f"tpad=stop_duration={extension_duration}:stop_mode=clone, fps={self.fps}")
            else:
                raise NotImplementedError(f"Extension method '{self.extension}' is not implemented")

        elif actual_duration > expected_duration:
            if self.shrink == "trim_start":
                ffmpeg_cmd.extend(["-ss", str(actual_duration - expected_duration)])
            elif self.shrink == "trim_end":
                ffmpeg_cmd.extend(["-to", str(expected_duration)])
            else:
                raise NotImplementedError(f"Shrink method '{self.shrink}' is not implemented")

        if vf_filters:
            ffmpeg_cmd.extend(["-vf", ",".join(vf_filters)])
        ffmpeg_cmd.extend(["-r", str(self.fps)])
        ffmpeg_cmd.extend(["-b:v", self.bitrate])
        ffmpeg_cmd.extend(["-c:v", self.codec])
        ffmpeg_cmd.append(self.path.as_posix())

        try:
            logging.info(" ".join(ffmpeg_cmd))
            subprocess.run(ffmpeg_cmd, check=True)
            self.normalized = True
        except subprocess.CalledProcessError as e:
            raise ValueError(f"Failed to normalize video clip: {e}")


class VideoTrack:
    def __init__(self, workspace, width: int, height: int, bitrate: str, fps: int):
        self.workspace = workspace
        self.width = width
        self.height = height
        self.bitrate = bitrate
        self.fps = fps
        self.clips_base = []
        self.clips_overlay = []
        self.path = workspace / "output.mp4"

    def add_clip(self, clip):
        if clip.layer == 0:
            self.clips_base.append(clip)
        else:
            self.clips_overlay.append(clip)

    def sanity_check(self):
        for i in range(len(self.clips_base) - 1):
            if self.clips_base[i].span[1] != self.clips_base[i + 1].span[0]:
                raise ValueError(
                    "Layer 0 clips are not continuous: {self.clips_base[i].span[1]} != {self.clips_base[i + 1].span[0]}"
                )

        for clip in self.clips_overlay:
            if clip.span[1] > self.clips_base[-1].span[1]:
                raise ValueError(f"Clip {clip.asset} is out of range: {clip.span[1]} > {self.clips_base[-1].span[1]}")

    def process(self):
        self.clips_base.sort(key=lambda x: x.span[0])
        self.clips_overlay.sort(key=lambda x: x.layer)
        assert self.clips_base, "No base clips found"
        assert (
            timecode2seconds(self.clips_base[0].span[0]) == 0
        ), f"base clips should start at 00:00:00.000: {self.clips_base[0].span[0]}"
        self.duration = timecode2seconds(self.clips_base[-1].span[1])
        self.sanity_check()
        for clip in self.clips_base + self.clips_overlay:
            clip.normalize()

        # make base video
        base_video_path = self.workspace / "base.mp4"
        concat_demuxer = self.workspace / "base.demuxer"
        concat_demuxer.write_text("\n".join([f"file '{clip.path}'" for clip in self.clips_base]))
        ffmpeg_cmd = ["ffmpeg", "-y", "-v", "warning"]
        ffmpeg_cmd.extend(["-f", "concat"])
        ffmpeg_cmd.extend(["-safe", "0"])
        ffmpeg_cmd.extend(["-i", concat_demuxer.as_posix()])
        ffmpeg_cmd.extend(["-c", "copy"])
        ffmpeg_cmd.append(base_video_path.as_posix())
        try:
            subprocess.run(ffmpeg_cmd, check=True)
        except subprocess.CalledProcessError as e:
            raise ValueError(f"Failed to generate base video: {e}")

        if not self.clips_overlay:
            return

        input_files = [base_video_path.as_posix()] + [clip.path.as_posix() for clip in self.clips_overlay]
        filter_complex = []

        overlay_chain = ""
        overlay_video_stream = "[0:v]"
        for i, clip in enumerate(self.clips_overlay, start=1):
            start, end = timecode2seconds(clip.span[0]), timecode2seconds(clip.span[1])
            filter_complex.append(f"[{i}:v]setpts=PTS-STARTPTS+{start}/TB[fv{i}]")
            overlay_chain = f"{overlay_chain}{overlay_video_stream}[fv{i}]overlay=x={clip.posX}:y={clip.posY}:enable='between(t,{start},{end})'"
            overlay_video_stream = f"[ov{i}]"
            if i != len(self.clips_overlay):
                overlay_chain = f"{overlay_chain}{overlay_video_stream};"

        filter_complex_cmd = ";".join(filter_complex) + ";" + overlay_chain

        ffmpeg_cmd = ["ffmpeg", "-y", "-v", "warning"]
        for input_file in input_files:
            ffmpeg_cmd.extend(["-i", input_file])

        ffmpeg_cmd.extend(["-filter_complex", filter_complex_cmd])
        ffmpeg_cmd.extend(["-c:v", "libx264"])
        ffmpeg_cmd.append(self.path.as_posix())

        try:
            logging.info(" ".join(ffmpeg_cmd))
            subprocess.run(ffmpeg_cmd, check=True)
        except subprocess.CalledProcessError as e:
            raise ValueError(f"Failed to generate video track: {e}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    path_to_config = "/mnt/disk2/home/vv/workspace/VMPS/example/config.yaml"
    workspace = Path("./workspace/example/video").absolute()
    workspace.mkdir(parents=True, exist_ok=True)
    with open(path_to_config) as f:
        config = yaml.safe_load(f)
    video_track = VideoTrack(workspace, **config["video"]["meta"])
    for clip in config["video"]["clips"]:
        VideoClip(video_track, workspace / "clips", **clip)
    video_track.process()
