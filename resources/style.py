from importlib.resources import path
from enum import IntEnum
from pathlib import Path
from zipfile import Path as ZipPath
import zipfile
from typing import Any, Self
from dataclasses import dataclass, fields
import tomllib
from arcade.types import RGBA255
from pyglet.font import add_file
from pyglet.image import AbstractImage, ImageData, load as _load_texture

import styles

from .audio import Sound

__all__ = ("STYLE",)

StylePath = Path | ZipPath

def load_font(pth: StylePath) -> None:
    with pth.open('rb') as fp:
        add_file(fp) # type: ignore -- IO[bytes] works as Binary

def load_texture(pth: StylePath) -> AbstractImage:
    with pth.open('rb') as fp:
        return _load_texture(str(pth), fp) # type: ignore -- IO[bytes] works as Binary

@dataclass
class StyleTable:

    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)

    @classmethod
    def create(cls, data: dict[str, Any], source: StylePath) -> Self:
        for field in fields(cls):
            if isinstance(field.type, type) and issubclass(field.type, StyleTable):
                data[field.name] = field.type.create(data.get(field.name, {}), source)
        return cls(**data)

@dataclass
class Application(StyleTable):
    window_width: int
    window_height: int
    min_width: int
    min_height: int

    window_name: str
    window_icon: ImageData

    @classmethod
    def create(cls, data: dict[str, Any], source: StylePath) -> Self:
        icon = load_texture(source / data.pop('window_icon'))
        return cls(
            **data,
            window_icon=icon
        )

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
    texture: AbstractImage
    offset: tuple[float, float]
    foci: tuple[float, float]
    depth: float
    mode: FloatMotionMode
    scale: float
    sync: float
    rate: float

    @classmethod
    def create(cls, data: dict[str, Any], source: StylePath) -> Self:
        return cls(
            load_texture(source / data["texture"]),
            data["offset"],
            data["foci"],
            data["depth"],
            FloatMotionMode(data["mode"]),
            data["scale"],
            data["sync"],
            data["rate"],
        )


@dataclass
class Background(StyleTable):
    color: tuple[int, int, int, int]
    base: AbstractImage
    base_offset: tuple[float, float]
    layers: tuple[Floating, ...]

    @classmethod
    def create(cls, data: dict[str, Any], source: StylePath) -> Self:
        return cls(
            tuple(data["color"]),
            load_texture(source / data["base"]),
            tuple(data["base_offset"]),
            tuple(
                Floating.create(floating, source)
                for floating in data.get("floating", ())
            ),
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

    @classmethod
    def create(cls, data: dict[str, str], source: StylePath) -> Self:
        return cls(**{name: Sound(source / pth) for name, pth in data.items()})


@dataclass
class Audio(StyleTable):
    slide_in: Sound
    slide_out: Sound
    connection: Sound
    block: Sound
    modal: Sound
    crash: Sound
    boot: Sound
    notification: Sound
    incoming_comm: Sound
    confirm: Sound
    drop: Sound
    connect: Sound
    pickup: Sound
    disconnect: Sound
    ambience: Ambience

    @classmethod
    def create(cls, data: dict[str, Any], source: StylePath) -> Self:
        ambience = Ambience.create(data.pop("ambience"), source)
        return cls(
            ambience=ambience,
            **{name: Sound(source / pth) for name, pth in data.items()},
        )


@dataclass
class Textures(StyleTable):
    credits_logo: ImageData
    logo_big: ImageData

    @classmethod
    def create(cls, data: dict[str, str], source: StylePath) -> Self:
        return cls(**{name: load_texture(source / pth) for name, pth in data.items()})


@dataclass
class Menu(StyleTable):
    new_fade: float
    new_transition: float
    new_logo: float
    continue_fade: float
    continue_transition: float
    continue_logo: float
    background: Background


@dataclass
class Panels(StyleTable):
    settings_tag: Path
    editor_tag: Path
    comms_tag: Path
    info_tag: Path
    panel_speed: float

    @classmethod
    def create(cls, data: dict[str, Any], source: StylePath) -> Self:
        return cls(
            panel_speed=data.pop("panel_speed"),
            **{name: source / pth for name, pth in data.items()},
        )


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
    definition: AbstractImage
    dropdown: AbstractImage
    check_inactive: AbstractImage
    check_active: AbstractImage

    run_one: AbstractImage
    run_all: AbstractImage
    nav_p: AbstractImage
    nav_n: AbstractImage

    @classmethod
    def create(cls, data: dict[str, Any], source: StylePath) -> Self:
        return cls(
            blink_speed=data.pop("blink_speed"),
            background=source / data.pop("background"),
            **{name: load_texture(source / pth) for name, pth in data.items()},
        )


@dataclass
class Game(StyleTable):
    background: Background
    panels: Panels
    editor: Editor


@dataclass
class Font(StyleTable):
    default: Path
    bold: Path
    bold_italic: Path
    light: Path
    light_italic: Path
    italic: Path

    @classmethod
    def create(cls, data: dict[str, Any], source: StylePath) -> Self:
        for pth in data.values():
            load_font(source / pth)

        default = data["default"]
        return cls(
            source / default,
            source / data.get("bold", default),
            source / data.get("bold_italic", default),
            source / data.get("light", default),
            source / data.get("light_italic", default),
            source / data.get("italic", default),
        )


@dataclass
class Fonts(StyleTable):
    monospace: Font
    regular: Font


@dataclass
class TextSizes(StyleTable):
    header: int
    header_1: int
    header_2: int
    header_3: int
    header_4: int
    header_5: int
    header_6: int
    normal: int
    subtitle: int

    @classmethod
    def create(cls, data: dict[str, int], source: StylePath) -> Self:
        header = data["header"]
        normal = data["normal"]
        return cls(
            header,
            data.get("header_1", header * 6),
            data.get("header_2", header * 5),
            data.get("header_3", header * 4),
            data.get("header_4", header * 3),
            data.get("header_5", header * 2),
            data.get("header_6", header * 1),
            normal,
            data.get("subtitle", normal),
        )


@dataclass
class TextNames(StyleTable):
    monospace: str
    regular: str


@dataclass
class Text(StyleTable):
    fonts: Fonts
    names: TextNames
    sizes: TextSizes


@dataclass
class Style(StyleTable):
    source: StylePath
    name: str
    application: Application
    colors: Colors
    text: Text
    format: Format
    audio: Audio
    textures: Textures
    menu: Menu
    game: Game

    @classmethod
    def create(cls, data: dict[str, Any], source: StylePath) -> Self:
        return cls(
            source,
            data["name"],
            Application.create(data['application'], source),
            Colors.create(data["colors"], source),
            Text.create(data["text"], source),
            Format.create(data["format"], source),
            Audio.create(data["audio"], source),
            Textures.create(data["textures"], source),
            Menu.create(data["menu"], source),
            Game.create(data["game"], source),
        )


def get_style(name: str) -> Style:
    with path(styles, name) as pth:
        if pth.exists():
            cfg = pth / "style.cfg"
            with open(cfg, "rb") as fp:
                return Style.create(tomllib.load(fp), pth)
    with path(styles, f"{name}.syl") as pth:
        if pth.exists():
            zip = ZipPath(pth)
            cfg = zip / "style.cfg"
            with cfg.open('rb') as fp:
                return Style.create(tomllib.load(fp), zip)
    raise FileNotFoundError(f"No style named {name} found")


STYLE = get_style("base")
