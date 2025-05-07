from importlib.resources import path
from enum import IntEnum
from pathlib import Path
from typing import Any, Self
from dataclasses import dataclass
import tomllib
from arcade import load_font
from arcade.types import RGBA255
from pyglet.image import ImageData, load as load_texture

import resources.styles as styles

from .audio import Sound

__all__ = ("STYLE",)


@dataclass
class Colors:
    shadow: RGBA255
    base: RGBA255
    background: RGBA255
    dark: RGBA255
    accent: RGBA255
    bright: RGBA255
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


class FloatMotionMode(IntEnum):
    CIRCLE = 0
    DIAGONAL = 1


@dataclass
class Floating:
    src: Path
    offset: tuple[float, float]
    foci: tuple[float, float]
    depth: float
    mode: FloatMotionMode
    scale: float
    sync: float
    rate: float

    @classmethod
    def create(cls, data: dict[str, Any], source: Path) -> Self:
        return cls(
            source / data["src"],
            data["offset"],
            data["foci"],
            data["depth"],
            FloatMotionMode(data["mode"]),
            data["scale"],
            data["sync"],
            data["rate"],
        )


@dataclass
class Audio:
    slide_in: Sound
    slide_out: Sound
    connection: Sound
    block: Sound
    modal: Sound
    ambient_wind: Sound
    crash: Sound

    ambience_environment: Sound
    ambience_fan: Sound
    ambience_network: Sound
    ambience_machinery: Sound
    ambience_data: Sound
    ambience_navigation: Sound

@dataclass
class Textures:
    logo_big: ImageData
    icon: ImageData


@dataclass
class Background:
    colour: tuple[int, int, int, int]
    base: Path
    base_offset: tuple[float, float]
    layers: tuple[Floating, ...]


@dataclass
class Menu:
    background: Background


@dataclass
class Panels:
    settings_tag: Path
    editor_tag: Path
    comms_tag: Path
    info_tag: Path
    panel_speed: float


@dataclass
class Editor:
    blink_speed: float
    background: Path

    puzzle_alert: ImageData

    node_inactive: ImageData
    node_active: ImageData
    branch_inactive: ImageData
    branch_active: ImageData
    variable: ImageData
    defintiion: ImageData
    dropdown: ImageData
    check_inactive: ImageData
    check_active: ImageData

    run_one: ImageData
    run_all: ImageData
    nav_p: ImageData
    nav_n: ImageData


@dataclass
class Game:
    background: Background
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
        self.source = source # save this for later
        with open(source / "style.cfg", "rb") as fp:
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

        audio_data = self._raw["Audio"]
        self.audio = Audio(
            **{name: Sound(source / pth) for name, pth in audio_data.items()}
        )

        image_data = self._raw["Textures"]
        self.textures = Textures(
            load_texture(source / image_data["logo_big"]),
            load_texture(source / image_data["icon"]),
        )

        background_data = self._raw["Menu"]["Background"]
        self.menu = Menu(
            Background(
                colour=tuple(background_data["color"]),
                base=source / background_data["base"],
                base_offset=background_data["base_offset"],
                layers=tuple(
                    Floating.create(data, source)
                    for data in background_data["Floating"]
                ),
            )
        )

        background_data = self._raw["Game"]["Background"]
        panel_data = self._raw["Game"]["Panels"]
        editor_data = self._raw["Game"]["Editor"]
        self.game = Game(
            Background(
                colour=tuple(background_data["color"]),
                base=source / background_data["base"],
                base_offset=background_data["base_offset"],
                layers=tuple(
                    Floating.create(data, source)
                    for data in background_data["Floating"]
                ),
            ),
            Panels(
                settings_tag=source / panel_data["settings_tag"],
                editor_tag=source / panel_data["editor_tag"],
                comms_tag=source / panel_data["comms_tag"],
                info_tag=source / panel_data["info_tag"],
                panel_speed=panel_data["panel_speed"],
            ),
            Editor(
                editor_data["blink_speed"],
                source / editor_data["background"],
                load_texture(source / editor_data["puzzle_alert"]),
                load_texture(source / editor_data["node_inactive"]),
                load_texture(source / editor_data["node_active"]),
                load_texture(source / editor_data["branch_inactive"]),
                load_texture(source / editor_data["branch_active"]),
                load_texture(source / editor_data["variable"]),
                load_texture(source / editor_data["definition"]),
                load_texture(source / editor_data["dropdown"]),
                load_texture(source / editor_data["check_inactive"]),
                load_texture(source / editor_data["check_active"]),
                load_texture(source / editor_data["run_one"]),
                load_texture(source / editor_data["run_all"]),
                load_texture(source / editor_data["nav_p"]),
                load_texture(source / editor_data["nav_n"]),
            ),
        )


with path(styles, "base") as pth:
    STYLE = Style(pth)
