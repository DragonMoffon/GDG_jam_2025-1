from uuid import UUID, uuid4

from pyglet.graphics import Batch, Group
from arcade import get_window, Camera2D, Rect

SHADOW_GROUP = Group(0)
SPACING_GROUP = Group(1)
PRIMARY_GROUP = Group(2)
HIGHLIGHT_GROUP = Group(3)

OVERLAY_SHADOW_GROUP = Group(4)
OVERLAY_SPACING_GROUP = Group(5)
OVERLAY_PRIMARY_GROUP = Group(6)
OVERLAY_HIGHLIGHT_GROUP = Group(7)


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


class Frame:

    def __init__(self) -> None:
        pass