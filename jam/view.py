from arcade import View as ArcadeView
from .input import Button, Axis


class View(ArcadeView):

    def __init__(self) -> None:
        ArcadeView.__init__(self)

    def on_input(self, button: Button, modifiers: int, pressed: bool) -> None: ...
    def on_axis_change(self, axis: Axis, value_1: float, value_2: float) -> None: ...
    def on_cursor_motion(self, x: float, y: float, dx: float, dy: float) -> None: ...
    def on_cursor_scroll(
        self, x: float, y: float, scroll_x: float, scroll_y: float
    ) -> None: ...
