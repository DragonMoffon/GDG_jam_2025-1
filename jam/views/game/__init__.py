from enum import Enum

from pyglet.graphics import Batch

from jam.view import View
from jam.gui.frame import Frame, FrameController
from jam.input import inputs, Button, Axis


from .editor import EditorFrame
from .settings import SettingsFrame

from resources import style

class FrameAnimationMode(Enum):
    NONE = 0
    SHOW = 1
    HIDE = 2

class GameView(View):

    def __init__(self) -> None:
        View.__init__(self)
        self.background_color = style.colors.dark
        self._batch = Batch()

        self._editor_frame = EditorFrame(0.0, (self.width, 0.0), 720)
        self._editor_frame.connect_renderer(self._batch)

        self._info_frame = Frame('INFO', self._editor_frame.tag_height + 2 * style.format.padding, (self.width, 0.0), (450, 720))
        self._info_frame.connect_renderer(self._batch)

        self._comms_frame = Frame('COMMS', self._editor_frame.tag_height + self._info_frame.tag_height + 3 * style.format.padding, (self.width, 0.0), (450, 720))
        self._comms_frame.connect_renderer(self._batch)

        self._setting_frame = SettingsFrame((self.width, 0.0), 720)
        self._setting_frame.connect_renderer(self._batch)

        self._frame_controller = FrameController((self._editor_frame, self._setting_frame, self._info_frame, self._comms_frame), (self.width, 0.0))


    def on_draw(self) -> bool | None:
        self.clear()
        self._frame_controller.on_draw()
        self._batch.draw()

    def on_update(self, delta_time: float) -> bool | None:
        self._frame_controller.on_update(delta_time)
        
    def on_input(self, input: Button, modifiers: int, pressed: bool) -> bool | None:
        self._frame_controller.on_input(input, modifiers, pressed)

    def on_axis_change(self, axis: Axis, value_1: float, value_2: float):
        self._frame_controller.on_axis_change(axis, value_1, value_2)

    def on_cursor_motion(self, x: float, y: float, dx: float, dy: float) -> bool | None:
        self._frame_controller.on_cursor_motion(x, y, dx, dy)
    
    def on_cursor_scroll(self, x: float, y: float, scroll_x: float, scroll_y: float) -> bool | None:
        self._frame_controller.on_cursor_scroll(x, y, scroll_x, scroll_y)
