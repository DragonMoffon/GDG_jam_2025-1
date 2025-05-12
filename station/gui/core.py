from __future__ import annotations
from uuid import UUID, uuid4

from arcade import get_window
from arcade.camera import Projector
from pyglet.graphics import Batch, Group

__all__ = (
    "GUI",
    "Element",
    "Point",
    "ProjectorGroup",
)

Point = tuple[float, float]


class ProjectorGroup(Group):

    def __init__(self, projector: Projector, order: int = 0) -> None:
        super().__init__(order)
        self.projector: Projector = projector
        self._previous_projector: Projector | None = None

    def set_state(self) -> None:
        self._previous_projector = get_window().current_camera
        self.projector.use()

    def unset_state(self) -> None:
        if self._previous_projector is None:
            return
        self._previous_projector.use()
        self._previous_projector = None


class Element:

    def __init__(
        self,
        parent: Element | None = None,
        layer: Group | None = None,
        uid: UUID | None = None,
    ):
        self.parent: Element | None = None
        self.children: dict[UUID, Element] = {}
        self.layer: Group | None = layer
        self.uid: UUID = uid or uuid4()
        self.gui: GUI | None = None

        if parent is not None:
            parent.add_child(self)
            if self.layer is None:
                self.layer = parent.layer

    # -- GROUP METHODS --

    def SHADOW(self) -> Group:
        if self.layer is None:
            return Group(0)
        return Group(0, self.layer)

    def SPACING(self) -> Group:
        return Group(1, self.layer)

    def BODY(self, order: int = 0) -> Group:
        if order < 0 or 7 < order:
            print("WARNING: body layer overlapping with other batch layer")
        return Group(2 + order, self.layer)

    def NEXT(self, order: int = 0) -> Group:
        if self.layer is None:
            return Group(3 + order, None)
        return Group(self.layer.order + 1 + order, self.layer.parent)

    def PREV(self, order: int = 0) -> Group:
        if self.layer is None:
            return Group(1 + order)
        return Group(self.layer.order - 1 + order, self.layer.parent)

    def HIGHLIGHT(self, order: int = 0) -> Group:
        return Group(10 + order, self.layer.highlight)

    # -- TREE METHODS --

    def __hash__(self) -> int:
        return hash(self.uid)

    def __eq__(self, other: Element) -> bool:
        return self.uid == other.uid

    def add_child(self, child: Element) -> None:
        if child.uid in self.children:
            return
        child.parent = self
        self.children[child.uid] = child
        if self.gui is not None:
            self.gui.add_element(child)

    def remove_child(self, child: Element) -> None:
        if child.uid not in self.children:
            return
        self.children.pop(child.uid)
        child.parent = None
        if self.gui is not None:
            self.gui.remove_element(child)

    def connect_renderer(self, batch: Batch | None) -> None:
        pass

    def disconnect_renderer(self) -> None:
        self.connect_renderer(None)

    # -- VALUE PROPERTIES --
    @property
    def width(self) -> float:
        return self.get_size()[0]

    @property
    def height(self) -> float:
        return self.get_size()[1]

    @property
    def x(self) -> float:
        return self.get_position()[0]

    @property
    def y(self) -> float:
        return self.get_position()[1]

    # -- VALUE METHODS --

    def contains_point(self, point: Point) -> bool:
        return False

    # Still responsible for update position because layouting adds a lot of
    # opinionated complexity
    def update_position(self, point: Point) -> None:
        raise NotImplementedError

    def get_position(self) -> Point:
        raise NotImplementedError

    def update_size(self, size: tuple[float, float]) -> None:
        raise NotImplementedError

    def get_size(self) -> tuple[float, float]:
        raise NotImplementedError


class GUI:

    def __init__(self):
        self._ctx = get_window().ctx
        self._batch = Batch()
        self._elements: dict[UUID, Element] = {}

    @property
    def renderer(self) -> Batch:
        return self._batch

    def draw(self) -> None:
        self._batch.draw()

    def add_element(self, element: Element) -> None:
        if element.uid in self._elements:
            return

        element.connect_renderer(self._batch)
        self._elements[element.uid] = element

        element.gui = self
        for element in element.children.values():
            self.add_element(element)

    def remove_element(self, element: Element) -> None:
        if element.uid not in self._elements:
            return
        for child in element.children.values():
            self.remove_element(child)

        element.disconnect_renderer()
        self._elements.pop(element.uid)

        element.gui = None
