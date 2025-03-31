from uuid import UUID, uuid4
from typing import Callable

from pyglet.shapes import Batch, Group, RoundedRectangle
from arcade import get_window, Camera2D, Rect, Text

from resources import style

SHADOW = Group(0)
HIGHLIGHT = Group(1)
PRIMARY = Group(2)
OVERLAY_SHADOW = Group(3)
OVERLAY_HIGHTLIGHT = Group(4)
OVERLAY_PRIMARY = Group(5)


class Element:

    def __init__(self, uid: UUID | None = None):
        self.uid = uid or uuid4()
        self.gui: Gui | None = None

    def connect_renderer(self, batch: Batch | None): ...

    def disconnect_renderer(self):
        self.connect_renderer(None)

    def contains_point(self, point: tuple[float, float]) -> bool: ...
    def update_position(self, point: tuple[float, float]): ...


class Gui:

    def __init__(self, viewport: Rect):
        self._ctx = get_window().ctx
        self._batch = Batch()
        self._camera = Camera2D(viewport=viewport)
        self._elements: dict[UUID, Element] = {}

    def draw(self):
        with self._ctx.enabled(self._ctx.BLEND):
            with self._camera.activate():
                self._batch.draw()

    def add_element(self, element: Element):
        if element.uid in self._elements:
            return

        element.connect_renderer(self._batch)
        self._elements[element.uid] = element

        element.gui = self

    def remove_element(self, element: Element):
        if element.uid not in self._elements:
            return

        element.disconnect_renderer()
        self._elements.pop(element.uid)

        element.gui = None
