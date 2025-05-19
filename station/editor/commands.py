from station.gui.core import Element, Point
from station.gui.graph import ConnectionElement

from .base import EditorCommand


class MoveElement(EditorCommand):
    def __init__(self, element: Element, point: Point):
        self._element: Element = element
        self._point: Point = point
        self._prev: Point = (0.0, 0.0)

    def execute(self) -> None:
        self._prev = self._element.get_position()
        self._element.update_position(self._point)

    def undo(self) -> None:
        self._element.update_position(self._prev)


class MoveConnectionLink(EditorCommand):
    def __init__(self, element: ConnectionElement, link: int, point: Point):
        self._element: ConnectionElement = element
        self._link: int = link
        self._point: Point = point
        self._prev: Point = (0.0, 0.0)

    def execute(self) -> None:
        self._prev = self._element.get_link(self._link)
        self._element.update_link(self._link, self._point)

    def undo(self) -> None:
        self._element.update_position(self._prev)


class InsertConnectionLink(EditorCommand):

    def __init__(
        self,
        element: ConnectionElement,
        point: Point,
        idx: int | None = None,
    ):
        if idx is None:
            idx, _ = element.get_closest_line(point)
        self.element: ConnectionElement = element
        self.point: Point = point
        self.idx: int = idx

    def execute(self) -> None:
        self.element.insert_link(self.idx, self.point)

    def undo(self) -> None:
        self.element.remove_link(self.idx)


class RemoveConnectionLink(EditorCommand):

    def __init__(self, element: ConnectionElement, idx: int):
        self.element = element
        self.idx = idx
        self._prev: Point = element.get_link(idx)

    def execute(self) -> None:
        self._prev = self.element.get_link(self.idx)
        self.element.remove_link(self.idx)

    def undo(self) -> None:
        self.element.insert_link(self.idx, self._prev)
