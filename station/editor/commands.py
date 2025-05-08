from station.gui.core import Element, Point

from .base import EditorCommand


class MoveELement(EditorCommand):
    def __init__(self, element: Element, point: Point) -> None:
        self._element: Element = element
        self._point: Point = point
        self._prev: Point = (0.0, 0.0)

    def execute(self):
        self._prev = (0.0, 0.0) # self._element.position -- If I required elements to have a position property which I might
        self._element.update_position(self._point)

    def undo(self):
        self._element.update_position(self._prev)