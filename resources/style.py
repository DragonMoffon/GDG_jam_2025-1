from importlib.resources import path
from enum import IntEnum
from pathlib import Path
from typing import Any, Self
from dataclasses import dataclass, asdict
import tomllib
from arcade import load_font
from arcade.types import RGBA255
from pyglet.image import AbstractImage, load as load_texture

import resources.styles as styles

from .audio import Sound

__all__ = ("STYLE",)

@dataclass
class StyleTable:

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)
    
    @classmethod
    def create(cls, data: dict[str, Any], source: Path) -> Self:
        raise NotImplementedError()


@dataclass
class Colors(StyleTable):
    shadow: RGBA255
    base: RGBA255
    background: RGBA255
    dark: RGBA255
    accent: RGBA255
    bright: RGBA255
    highlight: RGBA255


@dataclass
class Format(StyleTable):
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
class Floating(StyleTable):
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
class Ambience(StyleTable):
    wind: Sound
    environment: Sound
    fan: Sound
    network: Sound
    machinery: Sound
    data: Sound
    navigation: Sound
    power: Sound

@dataclass
class Audio(StyleTable):
    slide_in: Sound
    slide_out: Sound
    connection: Sound
    block: Sound
    modal: Sound
    crash: Sound
    notification: Sound
    confirm: Sound
    drag: Sound
    drop: Sound
    stretch: Sound
    connect: Sound
    pickup: Sound
    disconnect: Sound
    ambience: Ambience


@dataclass
class Textures(StyleTable):
    logo_big: AbstractImage
    icon: AbstractImage


@dataclass
class Background(StyleTable):
    colour: tuple[int, int, int, int]
    base: Path
    base_offset: tuple[float, float]
    layers: tuple[Floating, ...]


@dataclass
class Menu(StyleTable):
    background: Background


@dataclass
class Panels(StyleTable):
    settings_tag: Path
    editor_tag: Path
    comms_tag: Path
    info_tag: Path
    panel_speed: float


@dataclass
class Editor(StyleTable):
    blink_speed: float
    background: Path

    puzzle_alert: AbstractImage

    node_inactive: AbstractImage
    node_active: AbstractImage
    branch_inactive: AbstractImage
    branch_active: AbstractImage
    variable: AbstractImage
    defintiion: AbstractImage
    dropdown: AbstractImage
    check_inactive: AbstractImage
    check_active: AbstractImage

    run_one: AbstractImage
    run_all: AbstractImage
    nav_p: AbstractImage
    nav_n: AbstractImage


@dataclass
class Game(StyleTable):
    background: Background
    panels: Panels
    editor: Editor


@dataclass
class TextFormat(StyleTable):
    name: str
    path: str
    size: float


@dataclass
class Text(StyleTable):
    normal: TextFormat
    header: TextFormat

@dataclass
class Style(StyleTable):
    source: Path
    name: str
    colors: Colors
    text: Text
    format: Format
    audio: Audio
    textures: Textures
    menu: Menu
    game: Game

    @classmethod
    def create(cls, data: dict[str, Any], source: Path) -> Self:

        text = Text(
            normal=TextFormat(**data["Text"]["Normal"]),
            header=TextFormat(**data["Text"]["Header"])
        )
        load_font(source / text.normal.path)
        load_font(source / text.header.path)

        audio_data = data["Audio"]
        ambience_data = audio_data.pop("Ambience")

        background_data = data["Menu"]["Background"]
        menu = Menu(
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

        background_data = data["Game"]["Background"]
        panel_data = data["Game"]["Panels"]
        editor_data = data["Game"]["Editor"]
        game = Game(
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

        return cls(
            source,
            data.get("name", "style"),
            Colors(**data["Colors"]),
            text,
            Format(**data["Format"]),
            Audio(
                **{name: Sound(source / pth) for name, pth in audio_data.items()},
                ambience=Ambience(
                    **{name: Sound(source / pth) for name, pth in ambience_data.items()}
                )
            ),
            Textures(
                logo_big=load_texture(source / data["Textures"]["logo_big"]),
                icon=load_texture(source / data["Textures"]["icon"])
            ),
            menu,
            game
        )


def get_style(name: str) -> Style:
    with path(styles, name) as pth:
        if pth.exists():
            cfg = pth / 'style.cfg'
            with open(cfg, 'rb') as fp:
                return Style.create(tomllib.load(fp), pth)
    raise FileNotFoundError(f"No style named {name} found")

STYLE = get_style("base")
