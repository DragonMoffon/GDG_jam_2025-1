from .mode import EditorMode
from station.input import Button, Axis

class Editor:

    def __init__(self) -> None:
        pass

    def on_input(self, button: Button, modifiers: int, pressed: bool) -> None:
        pass

    def on_axis_changed(self, axis: Axis, input_1: float, input_2: float) -> None:
        pass

    def on_cursor_motion(self, x: float, y: float, dx: float, dy: float) -> None:
        pass

    def on_cursor_scroll(self, x: float, y: float, scroll_x: float, scroll_y: float) -> None:
        pass