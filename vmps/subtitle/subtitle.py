import logging
from pathlib import Path
from typing import Dict, List, Tuple
from uuid import uuid4
import yaml

logger = logging.getLogger("vmps")


class Style:
    """
    Check http://www.tcax.org/docs/ass-specs.htm, section "5. Style Lines, [v4+ Styles] section" for details of the parameters
    Note that for bool parameters: -1 denotes true and 0 denotes false
    """

    def __init__(
        self,
        fontname: str = "Arial",
        fontsize: int = 20,
        primary_colour: str = "&H00FFFFFF",
        secondary_colour: str = "&H00FF0000",
        outline_colour: str = "&H00000000",
        back_colour: str = "&H80000000",
        bold: int = 0,
        italic: int = 0,
        underline: int = 0,
        strikeout: int = 0,
        scale_x: int = 100,
        scale_y: int = 100,
        spacing: int = 0,
        angle: int = 0,
        border_style: int = 1,
        outline: int = 2,
        shadow: int = 0,
        alignment: int = 2,
        margin_l: int = 10,
        margin_r: int = 10,
        margin_v: int = 10,
        encoding: int = 1,
    ):
        self.name = str(uuid4()).split("-")[0]
        self.fontname = fontname
        self.fontsize = fontsize
        self.primary_colour = primary_colour
        self.secondary_colour = secondary_colour
        self.outline_colour = outline_colour
        self.back_colour = back_colour
        self.bold = bold
        self.italic = italic
        self.underline = underline
        self.strikeout = strikeout
        self.scale_x = scale_x
        self.scale_y = scale_y
        self.spacing = spacing
        self.angle = angle
        self.border_style = border_style
        self.outline = outline
        self.shadow = shadow
        self.alignment = alignment
        self.margin_l = margin_l
        self.margin_r = margin_r
        self.margin_v = margin_v
        self.encoding = encoding

    def __str__(self):
        return f"Style: {self.name}, {self.fontname}, {self.fontsize}, {self.primary_colour}, {self.secondary_colour}, {self.outline_colour}, {self.back_colour}, {self.bold}, {self.italic}, {self.underline}, {self.strikeout}, {self.scale_x}, {self.scale_y}, {self.spacing}, {self.angle}, {self.border_style}, {self.outline}, {self.shadow}, {self.alignment}, {self.margin_l}, {self.margin_r}, {self.margin_v}, {self.encoding}"

    def __hash__(self):
        return hash(str(self).split(",", maxsplit=1)[1])

    def __eq__(self, other):
        return self.__hash__() == other.__hash__()


class Subtitle:
    def __init__(self, workspace: Path | str):
        self.workspace = Path(workspace)
        self.styles: List[Style] = []
        self.styles.append(Style())
        self.clips: List[str] = []
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.path = workspace / "subtitle.ass"

    def add_clip(
        self,
        uid: str,
        span: Tuple[str, str],
        text: str,
        layer: int = 0,
        **style_kwargs,
    ):
        """
        Add a clip to the subtitle
        Args:
            span (Tuple[str, str]): A tuple of two string timecodes representing the start and end of the clip
            text (str): The text to be displayed
            layer (str): Th layer of the subtitle
            style_kwargs (Dict): The style of the text, see Style class for details
        """
        try:
            style = Style(**style_kwargs)
        except:
            logger.fatal("Fail to make style for subtitle {uid}")
            raise

        if style not in self.styles:
            self.styles.append(style)
        else:
            style = next(s for s in self.styles if s == style)
        self.clips.append(f"Dialogue: {layer},{span[0]},{span[1]},{style.name},,0,0,0,,{text}")

    def add_clips_from_config(self, configs):
        for config in configs:
            self.add_clip(**config)

    def process(self):
        styles = "\n".join(str(style) for style in self.styles)
        clips = "\n".join(self.clips)
        content = f"""
[Script Info]
ScriptType: v4.00+

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
{styles}

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
{clips}
    """
        self.path.write_text(content)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    path_to_config = Path("./example/config.yaml").absolute()
    workspace = Path("./workspace/example/subtitle").absolute()
    workspace.mkdir(parents=True, exist_ok=True)
    with open(path_to_config) as f:
        config = yaml.safe_load(f)
    subtitle = Subtitle(workspace)
    subtitle.add_clips_from_config(config["subtitle"]["clips"])
    subtitle.process()
