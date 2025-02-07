from __future__ import annotations

import logging
import subprocess
from pathlib import Path
from typing import Optional, Tuple
from uuid import uuid4

import ffmpeg
import filetype
import yaml
from vmps.utils import timecode2seconds

logger = logging.getLogger("vmps")


class AudioClip:
    def __init__(
        self,
        track: AudioTrack,
        workspace: Path | str,
        data_dir: Path | str,
        uid: str,
        path: Path | str,
        span: Tuple[str, str],
        clip: Optional[Tuple[str, str]] = None,
        channel: int = 0,
        volume: Optional[float] = None,
        loop: bool = False,
        sample_rate: Optional[int] = 44100,
    ):
        """
        Args:
            uid: Unique identifier of the audio clip
            track: AudioTrack object
            workspace: Path to workspace directory
            path: Path to audio or video file (audio track will be extracted)
            span: Tuple of start and end timecodes
            clip: Optional tuple of start and end timecodes to clip the audio
            channel: Channel number of the audio clip, defaults to 0
            volume: Volume of the audio clip, defaults to None (e.g. 0 means mute, 2 means double; or use Decibel values like 10dB, -5dB, see https://trac.ffmpeg.org/wiki/AudioVolume)
            loop: if True, clip will be looped to match the required duration
            sample_rate: Sample rate of the audio clip, defaults to 44100 Hz
        """
        self.workspace = Path(workspace)
        self.asset = data_dir / Path(path)
        self.uid = uid
        self.track = track
        self.channel = channel
        self.sample_rate = sample_rate if sample_rate else track.sample_rate
        self.span = span
        self.clip = clip
        self.path = self.workspace / f"{uuid4().hex}.wav"
        self.track = track
        self.volume = volume
        self.loop = loop
        self.track.add_clip(self)

        self.workspace.mkdir(parents=True, exist_ok=True)

        self.normalized = False

    @property
    def duration(self):
        return timecode2seconds(self.span[1]) - timecode2seconds(self.span[0])

    def normalize(self):
        if self.normalized:
            return

        ffmpeg_cmd = ["ffmpeg", "-y", "-v", "warning"]
        try:
            actual_duration = float(ffmpeg.probe(self.asset.as_posix())["streams"][0]["duration"])
        except ffmpeg.Error as e:
            logger.error(e.stderr.decode("utf-8"))
            raise e
        if self.clip:
            if self.clip[1]:
                ffmpeg_cmd.extend(["-to", self.clip[1]])
                actual_duration = timecode2seconds(self.clip[1])
            if self.clip[0]:
                ffmpeg_cmd.extend(["-ss", self.clip[0]])
                actual_duration -= timecode2seconds(self.clip[0])

        expected_duration = timecode2seconds(self.span[1]) - timecode2seconds(self.span[0])
        if actual_duration > expected_duration:
            raise ValueError(
                f"Actual duration {actual_duration} > expected duration {expected_duration}"
            )
        elif actual_duration < expected_duration and not self.loop:
            raise ValueError(
                f"Actual duration {actual_duration} < expected duration {expected_duration}, set loop=True to loop the clip"
            )

        filter_complex = []
        if self.loop and actual_duration < expected_duration:
            loop_count = int(expected_duration // actual_duration) + 1
            filter_complex.append(
                f"aloop=loop={loop_count}:size={int(self.sample_rate * actual_duration)},"
                f"atrim=duration={expected_duration}"
            )

        if self.volume is not None:
            filter_complex.append(f"volume={self.volume}")

        ffmpeg_cmd.extend(["-i", self.asset.as_posix()])
        if filter_complex:
            ffmpeg_cmd.extend(["-filter_complex", ",".join(filter_complex)])
        ffmpeg_cmd.extend(["-ar", str(self.sample_rate)])
        ffmpeg_cmd.extend(["-ac", "1"])
        ffmpeg_cmd.append(self.path.as_posix())

        try:
            logger.info(f"Normalizing {self.uid}: {' '.join(ffmpeg_cmd)}")
            subprocess.run(ffmpeg_cmd, check=True)
            self.normalized = True
        except subprocess.CalledProcessError as e:
            logger.fatal(f"Failed to normalize {self.asset}: {e}")
            raise e


class AudioTrack:
    def __init__(self, workspace: Path | str, data_dir: Path | str, sample_rate: int):
        self.workspace = workspace
        self.data_dir = data_dir
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.sample_rate = sample_rate
        self.clips = []
        self.path = self.workspace / "audio.wav"

    def add_clip(self, clip: AudioClip):
        self.clips.append(clip)

    def add_clips_from_config(self, configs):
        for config in configs:
            AudioClip(self, self.workspace / "clips", self.data_dir, **config)

    def sanity_check(self):
        # channel numbers are contiguous starting from 0
        channels = set([clip.channel for clip in self.clips])
        assert max(channels) == len(channels) - 1, "Channels must be contiguous starting from 0"

        # clips within same channel do not overlap
        for channel in channels:
            clips = sorted(
                [clip for clip in self.clips if clip.channel == channel], key=lambda x: x.span[0]
            )
            for prev_clip, clip in zip(clips[:-1], clips[1:]):
                prev_end = timecode2seconds(prev_clip.span[1])
                cur_start = timecode2seconds(clip.span[0])
                assert (
                    cur_start >= prev_end
                ), f"Clips {prev_clip.span} and {clip.span} must not overlap"

    @property
    def duration(self):
        return max([timecode2seconds(clip.span[1]) for clip in self.clips])

    def process(self):
        self.sanity_check()
        audio_channel_paths = []
        for channel in set([clip.channel for clip in self.clips]):
            audio_channel_path = self.workspace / f"ch_{channel}.wav"
            self.process_one_channel(channel, audio_channel_path)
            audio_channel_paths.append(audio_channel_path)

        channels = set([clip.channel for clip in self.clips])
        channels_with_max_duration = set(
            [clip.channel for clip in self.clips if timecode2seconds(clip.span[1]) == self.duration]
        )

        ffmpeg_cmd = ["ffmpeg", "-y", "-v", "warning"]
        for audio_channel_path in audio_channel_paths:
            ffmpeg_cmd.extend(["-i", audio_channel_path.as_posix()])

        filter_complex = "".join(
            f"[{c}:a]anull[a{c}];" if c in channels_with_max_duration else f"[{c}:a]apad[a{c}];"
            for c in channels
        )

        num_channels = len(audio_channel_paths)
        filter_complex += (
            "".join(
                f"[a{i}]"
                for i in list(channels - channels_with_max_duration)
                + list(channels_with_max_duration)
            )
            + f"join=inputs={num_channels}:channel_layout={num_channels}c[out]"
        )

        ffmpeg_cmd.extend(["-filter_complex", filter_complex])
        ffmpeg_cmd.extend(["-map", "[out]"])  # Set output to match number of channels
        ffmpeg_cmd.extend(["-ar", str(self.sample_rate)])  # Set sample rate
        ffmpeg_cmd.append(self.path.as_posix())

        try:
            logger.info(f"Processing audio track: {' '.join(ffmpeg_cmd)}")
            subprocess.run(ffmpeg_cmd, check=True)
        except subprocess.CalledProcessError as e:
            raise ValueError(f"Failed to process audio track: {e}")

    def process_one_channel(self, channel: int, audio_channel_path: Path):
        clips = [clip for clip in self.clips if clip.channel == channel]
        for clip in clips:
            try:
                clip.normalize()
            except:
                logger.fatal(f"Failed to normalize clip {clip.uid}")
                raise

        inputs = []
        filters = []
        for i, clip in enumerate(clips):
            start_time = int(1000 * timecode2seconds(clip.span[0]))
            inputs += ["-i", clip.path.as_posix()]
            delay_filter = f"[{i}:a]adelay={start_time}|{start_time}[a{i}]"
            filters.append(delay_filter)

        filter_complex = (
            "; ".join(filters)
            + f"; {''.join(f'[a{i}]' for i in range(len(clips)))}amix=inputs={len(clips)}:normalize=0"
        )

        ffmpeg_cmd = ["ffmpeg", "-y", "-v", "warning"]
        ffmpeg_cmd.extend(inputs)
        ffmpeg_cmd.extend(["-filter_complex", filter_complex])
        ffmpeg_cmd.extend(["-ar", str(self.sample_rate)])
        ffmpeg_cmd.append(audio_channel_path.as_posix())

        try:
            logger.info(ffmpeg_cmd)
            subprocess.run(ffmpeg_cmd, check=True)
        except subprocess.CalledProcessError as e:
            raise ValueError(f"Failed to process channel {channel} of audio track: {e}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    path_to_config = Path("./example/config.yaml").absolute()
    workspace = Path("./workspace/example/audio").absolute()
    workspace.mkdir(parents=True, exist_ok=True)
    with open(path_to_config) as f:
        config = yaml.safe_load(f)
    audio_track = AudioTrack(workspace, **config["audio"]["meta"])
    for clip in config["audio"]["clips"]:
        AudioClip(audio_track, workspace / "clips", **clip)

    audio_channel_path = workspace / "ch_0.wav"
    audio_track.process()
