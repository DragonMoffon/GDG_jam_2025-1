from uuid import UUID
from pyglet.graphics import Group, Batch
from pyglet.text import Label
from pyglet.shapes import RoundedRectangle
from pyglet.sprite import Sprite

from resources import style

from jam.node.graph import Graph, Value, Block, Connection, BlockComputation, OperationValue

from .core import Element

formating = style.format
colors = style.colors


class ConnectionElement(Element): ...


class TextPanel(Element):

    def __init__(self, char_count: int = 6):
        self._text: Label = Label(
            "#" * char_count,
            0.0,
            0.0,
            0.0,
            anchor_y="bottom",
            font_name=style.text.normal.name,
            font_size=style.text.normal.size,
        )
        self._panel: RoundedRectangle = RoundedRectangle(
            0.0,
            0.0,
            self._text.content_width + 2 * formating.padding,
            self._text.content_height + 2 * formating.padding,
            formating.padding,
            4,
            colors.accent,
        )

    @property
    def width(self) -> float:
        return self._panel.width

    @property
    def height(self) -> float:
        return self._panel.height

    def update_position(self, point: tuple[float, float]) -> None:
        self._panel.position = point
        self._text.position = point[0] + formating.padding, point[1] + formating.padding, 0.0

    def connect_renderer(self, batch: Batch | None = None) -> None:
        self._panel.batch = batch
        self._text.batch = batch


class NestedImplementationElement(Element):

    def __init__(self, source: str):
        self._source: str = source
        self._sprite = Sprite(style.game.editor.defintiion, 0.0, 0.0, 0.0)
        self._sprite.width = formating.corner_radius
        self._sprite.height = formating.corner_radius

    def update_position(self, point: tuple[float, float]) -> None:
        self._sprite.position = point[0], point[1], 0.0

    def connect_renderer(self, batch: Batch | None) -> None:
        self._sprite.batch = batch # type: ignore

    # TODO: global ctx open graph


class ConnectionNodeElement(Element):

    def __init__(self):
        self._sprite = Sprite(style.game.editor.node_inactive, 0.0, 0.0, 0.0)
        self._sprite.width = 2 * formating.point_radius
        self._sprite.height = 2 * formating.point_radius

        self._active: bool = False
        self._branch: bool = False

    def update_position(self, point: tuple[float, float]) -> None:
        self._sprite.position = point[0], point[1], 0.0

    def connect_renderer(self, batch: Batch | None) -> None:
        self._sprite.batch = batch # type: ignore

    @property
    def active(self) -> bool:
        return self._active

    @active.setter
    def active(self, active: bool) -> None:
        self._active = active
        if active:
            if self._branch:
                self._sprite.image = style.game.editor.branch_active
            else:
                self._sprite.image = style.game.editor.node_active
        else:
            if self._branch:
                self._sprite.image = style.game.editor.branch_inactive
            else:
                self._sprite.image = style.game.editor.node_inactive

    @property
    def branch(self) -> bool:
        return self._branch

    @active.setter
    def active(self, branch: bool) -> None:
        self._branch = branch
        if branch:
            if self._active:
                self._sprite.image = style.game.editor.branch_active
            else:
                self._sprite.image = style.game.editor.branch_inactive
        else:
            if self._active:
                self._sprite.image = style.game.editor.node_active
            else:
                self._sprite.image = style.game.editor.node_inactive


class BlockElement(Element):
    
    def __init__(self, block: Block):
        super().__init__(block.uid)
        self._bottom_left = (0.0, 0.0)
        self._block = block

    @property
    def left(self) -> float:
        return self._bottom_left[0]

    @property
    def bottom(self) -> float:
        return self._bottom_left[1]

class TempValueElement(Element):

    def __init__(self, position: tuple[float, float], value: OperationValue):
        pass

class GraphElement(Element):
    pass