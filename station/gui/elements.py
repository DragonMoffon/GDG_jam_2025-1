from __future__ import annotations
from uuid import UUID

from pyglet.gl import GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA
from pyglet.graphics.shader import ShaderProgram
from pyglet.graphics import Batch, Group
from pyglet.text import Label as pyLabel
from pyglet.text.document import FormattedDocument, UnformattedDocument
from pyglet.text.layout import IncrementalTextLayout
from pyglet.text.caret import Caret
from pyglet.customtypes import AnchorX, AnchorY, HorizontalAlign
from pyglet.image import AbstractImage
from pyglet.image.animation import Animation
from pyglet import shapes, sprite

from station.graphics import format_label

from .core import Element, Point

__all__ = ("FLabel", "Label", "Line", "RoundedRectangle", "Sprite")


class FLabel(Element):

    def __init__(
        self,
        text: str = "",
        x: float = 0.0,
        y: float = 0.0,
        width: int | None = None,
        height: int | None = None,
        anchor_x: AnchorX = "left",
        anchor_y: AnchorY = "baseline",
        rotation: float = 0.0,
        multiline: bool = False,
        dpi: int | None = None,
        font_name: str | None = None,
        font_size: float | None = None,
        weight: str = "normal",
        italic: bool | str = False,
        stretch: bool | str = False,
        color: tuple[int, int, int] | tuple[int, int, int, int] = (255, 255, 255, 255),
        align: HorizontalAlign = "left",
        program: ShaderProgram | None = None,
        parent: Element | None = None,
        layer: Group | None = None,
        uid: UUID | None = None,
    ):
        self._label = format_label.FLabel(
            text,
            x,
            y,
            0.0,
            width,
            height,
            anchor_x,
            anchor_y,
            rotation,
            multiline,
            dpi,
            font_name,
            font_size,
            weight,
            italic,
            stretch,
            color,
            align,
            None,
            None,
            program,
        )
        Element.__init__(self, parent, layer, uid)
        self._label.group = self.layer

    @property
    def label(self) -> FLabel:
        return self._label

    def connect_renderer(self, batch: Batch | None) -> None:
        self._label.batch = batch

    def set_visible(self, visible: bool) -> None:
        self._label.visible = visible

    def contains_point(self, point: Point) -> bool:
        l, b = self._label.left, self._label.bottom
        w, h = self.get_size()
        return 0 <= point[0] - l <= w and 0 <= point[1] - b <= h

    def update_position(self, point: Point) -> None:
        self._label.position = point[0], point[1], 0.0

    def get_position(self) -> Point:
        return self._label.x, self._label.y

    def update_size(self, size: tuple[float, float]) -> None:
        self._label.width, self._label.height = size

    def get_size(self) -> tuple[float, float]:
        return self._label.content_width, self._label.content_height


class Label(Element):

    def __init__(
        self,
        text: str = "",
        x: float = 0.0,
        y: float = 0.0,
        width: int | None = None,
        height: int | None = None,
        anchor_x: AnchorX = "left",
        anchor_y: AnchorY = "baseline",
        rotation: float = 0.0,
        multiline: bool = False,
        dpi: int | None = None,
        font_name: str | None = None,
        font_size: float | None = None,
        weight: str = "normal",
        italic: bool | str = False,
        stretch: bool | str = False,
        color: tuple[int, int, int] | tuple[int, int, int, int] = (255, 255, 255, 255),
        align: HorizontalAlign = "left",
        program: ShaderProgram | None = None,
        parent: Element | None = None,
        layer: Group | None = None,
        uid: UUID | None = None,
    ):
        self._label = pyLabel(
            text,
            x,
            y,
            0.0,
            width,
            height,
            anchor_x,
            anchor_y,
            rotation,
            multiline,
            dpi,
            font_name,
            font_size,
            weight,
            italic,
            stretch,
            color,
            align,
            None,
            None,
            program,
        )
        Element.__init__(self, parent, layer, uid)
        self._label.group = self.layer

    @property
    def label(self) -> pyLabel:
        return self._label

    def connect_renderer(self, batch: Batch | None) -> None:
        self._label.batch = batch

    def set_visible(self, visible: bool) -> None:
        self._label.visible = visible

    def contains_point(self, point: Point) -> bool:
        l, b = self._label.left, self._label.bottom
        w, h = self.get_size()
        return 0 <= point[0] - l <= w and 0 <= point[1] - b <= h

    def update_position(self, point: Point) -> None:
        self._label.position = point[0], point[1], 0.0

    def get_position(self) -> Point:
        return self._label.x, self._label.y

    def update_size(self, size: tuple[float, float]) -> None:
        self._label.width, self._label.height = size

    def get_size(self) -> tuple[float, float]:
        return self._label.content_width, self._label.content_height


class Line(Element):

    def __init__(
        self,
        x: float,
        y: float,
        x2: float,
        y2: float,
        thickness: float = 1.0,
        color: tuple[int, int, int] | tuple[int, int, int, int] = (255, 255, 255, 255),
        blend_src: int = GL_SRC_ALPHA,
        blend_dest: int = GL_ONE_MINUS_SRC_ALPHA,
        program: ShaderProgram | None = None,
        parent: Element | None = None,
        layer: Group | None = None,
        uid: UUID | None = None,
    ):
        self._line = shapes.Line(
            x, y, x2, y2, thickness, color, blend_src, blend_dest, None, None, program
        )
        Element.__init__(self, parent, layer, uid)
        self._line.group = self.layer

    def _update_vertices(self) -> None:
        self._line._update_vertices()  # type: ignore -- W0212

    def connect_renderer(self, batch: Batch | None) -> None:
        self._line.batch = batch

    def set_visible(self, visible: bool) -> None:
        self._line.visible = visible

    @property
    def line(self) -> shapes.Line:
        return self._line

    @property
    def x2(self) -> float:
        return self._line.x2

    @property
    def y2(self) -> float:
        return self._line.y2

    def contains_point(self, point: Point) -> bool:
        x, y = self._line.position
        lx, ly = self._line.x2 - x, self._line.y2 - y
        length = (lx**2 + ly**2) ** 0.5

        dx, dy = lx / length, ly / length
        px, py = point[0] - x, point[1] - y

        dot = dx * px + dy * py
        if dot < 0.0 or length < dot:
            return False

        cx, cy = -dy, dx
        cross = cx * px + cy * py
        if self._line.thickness * 0.5 < abs(cross):
            return False

        return True

    def update_position(self, point: Point) -> None:
        if point == self._line.position:
            return
        p2 = self._line.x2, self._line.y2
        self._line.position = point
        self._line._x2, self._line._y2 = p2
        self._update_vertices()

    def get_position(self) -> Point:
        return self._line.position

    def update_position2(self, point: Point) -> None:
        self._line._x2, self._line._y2 = point
        self._update_vertices()

    def get_position2(self) -> Point:
        return self._line.x2, self._line.y2

    def update_positions(self, point1: Point, point2: Point) -> None:
        self._line.position = point1
        self._line._x2, self._line._y2 = point2
        self._update_vertices()


    def get_size(self) -> tuple[float, float]:
        return self._line.x2 - self._line.x, self._line.y2 - self._line.y


class RoundedRectangle(Element):

    def __init__(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        radius: float | tuple[float, float, float, float],
        segments: int | tuple[int, int, int, int] | None = None,
        color: tuple[int, int, int] | tuple[int, int, int, int] = (255, 255, 255, 255),
        blend_src: int = GL_SRC_ALPHA,
        blend_dest: int = GL_ONE_MINUS_SRC_ALPHA,
        program: ShaderProgram | None = None,
        parent: Element | None = None,
        layer: Group | None = None,
        uid: UUID | None = None,
    ):
        self._body: shapes.RoundedRectangle = shapes.RoundedRectangle(
            x,
            y,
            width,
            height,
            radius,
            segments,
            color,
            blend_src,
            blend_dest,
            None,
            None,
            program,
        )
        Element.__init__(self, parent, layer, uid)
        # We have to create everything for connect renderer before the __init__,
        # but we don't have the layer atp
        self._body.group = self.layer

    @property
    def rectangle(self) -> shapes.RoundedRectangle:
        return self._body

    def connect_renderer(self, batch: Batch | None) -> None:
        self._body.batch = batch

    def set_visible(self, visible: bool) -> None:
        self._body.visible = visible

    def contains_point(self, point: Point) -> bool:
        body = self._body
        l, b = body.position
        w, h = body.width, body.height
        return 0 <= point[0] - l <= w and 0 <= point[1] - b <= h

    def update_position(self, point: Point) -> None:
        self._body.position = point

    def get_position(self) -> Point:
        return self._body.position

    def update_size(self, size: tuple[float, float]) -> None:
        self._body.width, self._body.height = size

    def get_size(self) -> tuple[float, float]:
        return self._body.width, self._body.height


class Sprite(Element):

    def __init__(
        self,
        img: AbstractImage | Animation,
        x: float = 0,
        y: float = 0,
        z: float = 0,
        blend_src: int = GL_SRC_ALPHA,
        blend_dest: int = GL_ONE_MINUS_SRC_ALPHA,
        subpixel: bool = False,
        program: ShaderProgram | None = None,
        parent: Element | None = None,
        layer: Group | None = None,
        uid: UUID | None = None,
    ):
        self._sprite = sprite.Sprite(
            img, x, y, z, blend_src, blend_dest, None, None, subpixel, program
        )
        Element.__init__(self, parent, layer, uid)
        self._sprite.group = self.layer

    @property
    def sprite(self) -> sprite.Sprite:
        return self._sprite

    def connect_renderer(self, batch: Batch | None) -> None:
        self._sprite.batch = batch  # type: ignore -- None

    def set_visible(self, visible: bool) -> None:
        self._sprite.visible = visible

    def contains_point(self, point: Point) -> bool:
        l, b, d = self._sprite.position
        w, h = self._sprite.width, self._sprite.height
        return 0 <= point[0] - l <= w and 0 <= point[1] - b <= h

    def update_position(self, point: Point) -> None:
        self._sprite.position = point

    def get_position(self) -> Point:
        return self._sprite.position

    def update_size(self, size: tuple[float, float]) -> None:
        self._sprite.width, self._sprite.height = size

    def get_size(self) -> tuple[float, float]:
        return self._sprite.height, self._sprite.width


class TextInput(Element):

    def __init__(
        self,
        text: str,
        x: float,
        y: float,
        width: int,
        height: int,
        font_name: str,
        font_size: int,
        color: tuple[int, int, int] | tuple[int, int, int, int] = (255, 255, 255, 255),
        anchor_x: AnchorX = "left",
        anchor_y: AnchorY = "bottom",
        multiline: bool = False,
        dpi: float | None = None,
        program: ShaderProgram | None = None,
        wrap_lines: bool = False,
        formatted: bool = False,
        caret: bool = True,
        parent: Element | None = None,
        layer: Group | None = None,
        uid: UUID | None = None,
    ):
        Element.__init__(self, parent, layer, uid)
        if formatted:
            self._document = FormattedDocument(text)
        else:
            self._document = UnformattedDocument(text)
        self._document.set_style(
            0,
            len(text),
            {"font_name": font_name, "font_size": font_size, "color": color},
        )

        self._layout = IncrementalTextLayout(
            self._document,
            x,
            y,
            0.0,
            width,
            height,
            anchor_x,
            anchor_y,
            0,
            multiline,
            dpi,
            program=program,
            group=self.layer,
            wrap_lines=wrap_lines,
        )

        if caret:
            self._caret = Caret(self._layout, color=color)
        else:
            self._caret = None

    def connect_renderer(self, batch: Batch | None) -> None:
        self._layout.batch = batch
        self._caret.batch = batch

    def set_visible(self, visible: bool) -> None:
        self._layout.visible = visible
        self._caret.visible = visible

    def update_position(self, point: Point) -> None:
        self._layout.position = point

    def get_position(self) -> Point:
        return self._layout.position

    def get_size(self) -> tuple[float, float]:
        return (self._layout.width, self._layout.height)
