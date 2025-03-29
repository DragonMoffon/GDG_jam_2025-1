from importlib.resources import path
from dataclasses import dataclass
import tomllib
from arcade import load_font
from arcade.types import RGBA255

import resources.rust as rust


__all__ = ("STYLE",)


@dataclass
class Colors:
    base: RGBA255
    background: RGBA255
    dark: RGBA255
    accent: RGBA255
    highlight: RGBA255


@dataclass
class EditorColors:
    shadow: RGBA255
    block: RGBA255
    background: RGBA255
    accent: RGBA255
    connection: RGBA255
    select: RGBA255


@dataclass
class EditorBlock:
    radius: float
    header: float
    footer: float
    select: float


@dataclass
class Editor:
    point_radius: float
    line_thickness: float
    padding: float
    drop_x: int
    drop_y: int
    colors: EditorColors
    block: EditorBlock


@dataclass
class TextFormat:
    name: str
    path: str
    size: str


@dataclass
class Text:
    normal: TextFormat
    header: TextFormat


class Style:

    def __init__(self, source):
        with open(source / "style.toml", "rb") as fp:
            self._raw = tomllib.load(fp)

        self.name = self._raw["name"]

        self.colors = Colors(**self._raw["Colors"])

        self.text = Text(
            normal=TextFormat(**self._raw["Text"]["Normal"]),
            header=TextFormat(**self._raw["Text"]["Header"]),
        )
        load_font(source / self.text.normal.path)
        load_font(source / self.text.header.path)

        editor_raw = self._raw["Editor"]
        editor_colors = EditorColors(
            **{
                name: (
                    tuple(color)
                    if isinstance(color, list)
                    else tuple(self._raw["Colors"][color])
                )
                for name, color in editor_raw["Colors"].items()
            }
        )
        editor_block = EditorBlock(**editor_raw["Block"])

        self.editor = Editor(
            editor_raw["point_radius"],
            editor_raw["line_thickness"],
            editor_raw["padding"],
            editor_raw["drop_x"],
            editor_raw["drop_y"],
            editor_colors,
            editor_block,
        )


with path(rust) as pth:
    STYLE = Style(pth)
