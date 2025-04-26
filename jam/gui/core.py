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

    def connect_renderer(self, batch: Batch | None) -> None: ...

    def disconnect_renderer(self) -> None:
        self.connect_renderer(None)

    # -- VALUE METHODS --

    def contains_point(self, point: tuple[float, float]) -> bool: ...
    def update_position(self, point: tuple[float, float]) -> None: ...

    # -- EVENT RESPONSES --

    def __gui_connected__(self, gui: Gui) -> None: ...
    def __gui_disconnected__(self) -> None: ...

    def __cursor_entered__(self) -> None: ...
    def __cursor_exited__(self) -> None: ...

    def __cursor_pressed__(self) -> None: ...


class Gui:

    def __init__(self, projector: Projector):
        self._ctx = get_window().ctx
        self._batch = Batch()
        self._elements: dict[UUID, Element] = {}

    @property
    def renderer(self) -> Batch:
        return self._batch

    def draw(self):
        self._batch.draw()

    def add_element(self, element: Element) -> None:
        if element.uid in self._elements:
            return

        element.connect_renderer(self._batch)
        self._elements[element.uid] = element

        element.gui = self
        element.__gui_connected__(self)

    def remove_element(self, element: Element) -> None:
        if element.uid not in self._elements:
            return

        element.disconnect_renderer()
        self._elements.pop(element.uid)

        element.__gui_disconnected__()
        element.gui = None


class Frame:

    def __init__(self) -> None:
        pass
