from pyglet.graphics import Batch
from pyglet.shapes import RoundedRectangle, Line
from pyglet.sprite import Sprite

from resources import style

from .core import Element, BASE_PRIMARY, BASE_SPACING
from station.puzzle import Puzzle, AlertOrientation


class AlertElement(Element):

    def __init__(self, puzzle: Puzzle):
        Element.__init__(self)
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
            group=BASE_PRIMARY,
        )
        self._icon.color = style.colors.highlight
        self._body = RoundedRectangle(
            self._icon.x,
            self._icon.y,
            self._icon.width,
            self._icon.height,
            style.format.padding,
            color=style.colors.base,
            group=BASE_PRIMARY,
        )
        self._select = RoundedRectangle(
            self._icon.x - style.format.select_radius,
            self._icon.y - style.format.select_radius,
            self._icon.width + 2 * style.format.select_radius,
            self._icon.height + 2 * style.format.select_radius,
            style.format.padding + style.format.select_radius,
            color=style.colors.highlight,
            group=BASE_SPACING,
        )
        self._select.visible = False

        self._lines: tuple[Line, Line, Line] = (
            Line(
                0.0, 0.0, 1.0, 1.0, style.format.line_thickness, style.colors.highlight
            ),
            Line(
                0.0, 0.0, 1.0, 1.0, style.format.line_thickness, style.colors.highlight
            ),
            Line(
                0.0, 0.0, 1.0, 1.0, style.format.line_thickness, style.colors.highlight
            ),
        )
        self._place_lines()

    @property
    def puzzle(self) -> Puzzle:
        return self._puzzle

    def connect_renderer(self, batch: Batch | None) -> None:
        self._body.batch = batch
        self._select.batch = batch
        self._icon.batch = batch
        for line in self._lines:
            line.batch = batch

    def contains_point(self, point: tuple[float, float]) -> bool:
        l, b, *_ = self._icon.position
        w, h = self._icon.width, self._icon.height
        return 0 <= point[0] - l <= w and 0 <= point[1] - b <= h

    def update_position(self, point: tuple[float, float]) -> None:
        self._icon.position = point[0], point[1], 0
        self._select.position = (
            point[0] - style.format.select_radius,
            point[1] - style.format.select_radius,
        )
        self._place_lines()

    def update_offset(self, offset: tuple[float, float]):
        self._pin_offset = offset
        self._place_lines()

    def _place_lines(self):
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

    def highlight(self):
        self._select.visible = True

    def deselect(self):
        self._select.visible = False
