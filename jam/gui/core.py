from __future__ import annotations
from uuid import UUID, uuid4


from pyglet.graphics import Batch, Group
from arcade import get_window
from arcade.camera import Projector

from jam.input import Button, Axis

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

    def connect_gui(self, gui: Gui):
        self.gui = gui
        self.connect_renderer(gui.renderer)

    def disconnect_gui(self):
        self.gui = None
        self.disconnect_renderer()

    def contains_point(self, point: tuple[float, float]) -> bool: ...
    def update_position(self, point: tuple[float, float]): ...


class Gui:

    def __init__(self, projector: Projector):
        self._ctx = get_window().ctx
        self._batch = Batch()
        self._camera = projector
        self._elements: dict[UUID, Element] = {}

    @property
    def renderer(self) -> Batch:
        return self._batch

    def draw(self):
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