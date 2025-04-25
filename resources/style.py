from importlib.resources import path
from pathlib import Path
from dataclasses import dataclass
import tomllib
from arcade import load_font
from arcade.types import RGBA255
from pyglet.image import ImageData, load as load_texture

import resources.styles as styles


__all__ = ("STYLE",)


@dataclass
class Colors:
    shadow: RGBA255
    base: RGBA255
    background: RGBA255
    dark: RGBA255
    accent: RGBA255
    highlight: RGBA255


@dataclass
class Format:
    point_radius: float
    corner_radius: float
    select_radius: float
    header_size: float
    footer_size: float
    line_thickness: float
    padding: float
    drop_x: float
    drop_y: float


@dataclass
class Panels:
    settings_tag: Path
    editor_tag: Path
    comms_tag: Path
    info_tag: Path
    panel_speed: float


@dataclass
class Editor:
    background: Path

    node_inactive: ImageData
    node_active: ImageData
    branch_inactive: ImageData
    branch_active: ImageData
    variable: ImageData
    defintiion: ImageData
    dropdown: ImageData
    check_inactive: ImageData
    check_active: ImageData


@dataclass
class Game:
    background: Path
    panels: Panels
    editor: Editor


@dataclass
class TextFormat:
    name: str
    path: str
    size: float


@dataclass
class Text:
    normal: TextFormat
    header: TextFormat


class Style:

    def __init__(self, source: Path):
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

        self.format = Format(**self._raw["Format"])

        panel_data = self._raw["Game"]["Panels"]
        editor_data = self._raw["Game"]["Editor"]
        self.game = Game(
            source / self._raw["Game"]["background"],
            Panels(
                settings_tag=source / panel_data["settings_tag"],
                editor_tag=source / panel_data["editor_tag"],
                comms_tag=source / panel_data["comms_tag"],
                info_tag=source / panel_data["info_tag"],
                panel_speed=panel_data["panel_speed"],
            ),
            Editor(
                source / editor_data["background"],
                load_texture(source / editor_data["node_inactive"]),
                load_texture(source / editor_data["node_active"]),
                load_texture(source / editor_data["branch_inactive"]),
                load_texture(source / editor_data["branch_active"]),
                load_texture(source / editor_data["variable"]),
                load_texture(source / editor_data["definition"]),
                load_texture(source / editor_data["dropdown"]),
                load_texture(source / editor_data["check_inactive"]),
                load_texture(source / editor_data["check_active"]),
            ),
        )


with path(styles, "base") as pth:
    STYLE = Style(pth)
