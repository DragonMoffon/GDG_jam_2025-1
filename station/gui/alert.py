from uuid import UUID

from pyglet.graphics import Group

from resources import style
from station.puzzle import Puzzle, AlertOrientation
from .core import Element, Point
from .elements import Line, RoundedRectangle, Sprite

__all__ = ("AlertElement", "AlertOrientation")


class AlertElement(Element):

    def __init__(
        self,
        puzzle: Puzzle,
        parent: Element | None = None,
        layer: Group | None = None,
        uid: UUID | None = None,
    ):
        Element.__init__(self, parent, layer, uid)
        self._pin = puzzle.alert.pin
        self._pin_orientation = puzzle.alert.pin_orientation
        self._loc = puzzle.alert.loc
        self._loc_orientation = puzzle.alert.loc_orientation

        self._pin_offset = (0.0, 0.0)
        self._puzzle = puzzle

        self._icon = Sprite(
            style.game.editor.puzzle_alert,
            self._loc[0],
            self._loc[1],
            parent=self,
            layer=self.BODY(2),
        )
        self._icon.color = style.colors.highlight
        self._body = RoundedRectangle(
            self._icon.x,
            self._icon.y,
            self._icon.width,
            self._icon.height,
            style.format.padding,
            color=style.colors.base,
            parent=self,
            layer=self.BODY(1),
        )
        self._select = RoundedRectangle(
            self._icon.x - style.format.select_radius,
            self._icon.y - style.format.select_radius,
            self._icon.width + 2 * style.format.select_radius,
            self._icon.height + 2 * style.format.select_radius,
            style.format.padding + style.format.select_radius,
            color=style.colors.highlight,
            parent=self,
            layer=self.SPACING(),
        )
        self._select.visible = False

        self._lines: tuple[Line, Line, Line] = (
            Line(
                0.0,
                0.0,
                1.0,
                1.0,
                style.format.line_thickness,
                style.colors.highlight,
                parent=self,
                layer=self.BODY(),
            ),
            Line(
                0.0,
                0.0,
                1.0,
                1.0,
                style.format.line_thickness,
                style.colors.highlight,
                parent=self,
                layer=self.BODY(),
            ),
            Line(
                0.0,
                0.0,
                1.0,
                1.0,
                style.format.line_thickness,
                style.colors.highlight,
                parent=self,
                layer=self.BODY(),
            ),
        )
        self._place_lines()

    @property
    def puzzle(self) -> Puzzle:
        return self._puzzle

    def contains_point(self, point: Point) -> bool:
        l, b, *_ = self._icon.position
        w, h = self._icon.width, self._icon.height
        return 0 <= point[0] - l <= w and 0 <= point[1] - b <= h

    def update_position(self, point: Point) -> None:
        self._icon.position = point[0], point[1], 0
        self._select.position = (
            point[0] - style.format.select_radius,
            point[1] - style.format.select_radius,
        )
        self._place_lines()

    def get_position(self) -> Point:
        return self._icon.position

    def update_size(self, size: tuple[float, float]) -> None:
        self._icon.width, self._icon.height = size
        self._body.width, self._body.height = size
        self._select.width = size[0] + 2 * style.format.select_radius
        self._select.height = size[1] + 2 * style.format.select_radius

        self._place_lines()

    def get_size(self) -> tuple[float, float]:
        return self._icon.width, self._icon.height

    def update_offset(self, offset: tuple[float, float]) -> None:
        self._pin_offset = offset
        self._place_lines()

    def _place_lines(self) -> None:
        pin = self._pin[0] + self._pin_offset[0], self._pin[1] + self._pin_offset[1]
        loc = self._loc

        match self._pin_orientation:
            case AlertOrientation.LEFT:
                px = pin[0] - style.format.corner_radius
                py = pin[1]
            case AlertOrientation.TOP:
                px = pin[0]
                py = pin[1] + style.format.corner_radius
            case AlertOrientation.RIGHT:
                px = pin[0] + style.format.corner_radius
                py = pin[1]
            case AlertOrientation.BOTTOM:
                px = pin[0]
                py = pin[1] - style.format.corner_radius

        match self._loc_orientation:
            case AlertOrientation.LEFT:
                lx = loc[0]
                ly = loc[1] + self._icon.height / 2.0

                lx2 = lx - style.format.corner_radius
                ly2 = ly
            case AlertOrientation.TOP:
                lx = loc[0] + self._icon.width / 2.0
                ly = loc[1] + self._icon.height

                lx2 = lx
                ly2 = ly + style.format.corner_radius
            case AlertOrientation.RIGHT:
                lx = loc[0] + self._icon.width
                ly = loc[1] + self._icon.height / 2.0

                lx2 = lx + style.format.corner_radius
                ly2 = ly
            case AlertOrientation.BOTTOM:
                lx = loc[0] + self._icon.width / 2.0
                ly = loc[1]

                lx2 = lx
                ly2 = ly - style.format.corner_radius

        l1, l2, l3 = self._lines
        l1.position = pin
        l1.x2, l1.y2 = px, py
        l2.position = px, py
        l2.x2, l2.y2 = lx2, ly2
        l3.position = lx2, ly2
        l3.x2, l3.y2 = lx, ly

    def highlight(self) -> None:
        self._select.visible = True

    def deselect(self) -> None:
        self._select.visible = False
