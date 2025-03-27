from pyglet.shapes import Batch
from arcade import Camera2D, Rect


class Element:
    def connect_renderer(self, batch: Batch): ...

    def disconnect_renderer(self):
        self.connect_renderer(None)

    def contains_point(self, point: tuple[float, float]):
        pass


class HoverPopup(Element):

    def __init__(self, text: str):
        pass


class ContextMenu(Element):

    def __init__(self, **actions):

        pass


class Gui:

    def __init__(self, viewport: Rect):
        self._batch = Batch
        self._camera = Camera2D(viewport=viewport)
        self._elements: list[Element] = []

    def draw(self):
        with self._camera.activate():
            self._batch.draw()

    def remove_element(self, element: Element):
        element.disconnect_renderer()
        self._elements.remove(element)
