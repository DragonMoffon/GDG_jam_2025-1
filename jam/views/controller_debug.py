from jam.input import Keys, MouseButtons, ControllerButtons, ControllerAxes
from jam.view import View

class ControllerView(View):

    def __init__(self) -> None:
        View.__init__(self)

    def on_input(self, input: Keys | MouseButtons | ControllerButtons, modifiers: int, pressed: bool) -> bool | None:
        print(input, modifiers, pressed)

    def on_axis_change(self, axis: ControllerAxes | str, value_1: float, value_2: float):
        print(axis, value_1, value_2)

    def on_cursor_motion(self, x: float, y: float, dx: float, dy: float) -> bool | None:
        print(x, y, dx, dy)

    def on_cursor_scroll(self, x: float, y: float, scroll_x: float, scroll_y: float) -> bool | None:
        print(x, y, scroll_x, scroll_y)