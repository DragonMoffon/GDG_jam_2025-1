from math import cos, sin, tau

from pyglet.graphics import Batch
from arcade.clock import GLOBAL_CLOCK
from arcade.future.background import Background, BackgroundGroup

from resources import style
from resources.style import FloatMotionMode

from jam.view import View
from jam.gui.frame import Frame, FrameController
from jam.input import Button, Axis

from .editor import EditorFrame
from .settings import SettingsFrame


class ParallaxBackground:

    def __init__(self):
        self._base: Background = Background.from_file(
            style.game.background.base, style.game.background.base_offset
        )
        self._layers: tuple[Background, ...] = tuple(
            Background.from_file(floating.src, floating.offset)
            for floating in style.game.background.layers
        )
        self._background = BackgroundGroup([self._base, *self._layers])

    def cursor_motion(self, x: float, y: float, dx: float, dy: float) -> None:
        for idx, layer in enumerate(self._layers):
            data = style.game.background.layers[idx]
            origin = (
                data.foci[0] * layer.texture.texture.width,
                data.foci[1] * layer.texture.texture.height,
            )
            shift = (x - origin[0]) / (data.depth), (y - origin[1]) / (data.depth)
            layer.pos = shift

    def update(self) -> None:
        t = GLOBAL_CLOCK.time
        for idx, layer in enumerate(self._layers):
            data = style.game.background.layers[idx]
            fraction = (t + data.sync) % data.rate / data.rate
            match data.mode:
                case FloatMotionMode.CIRCLE:
                    x = data.scale * cos(fraction * tau)
                    y = data.scale * sin(fraction * tau)
                    layer.texture.offset = (x, y)

    def draw(self) -> None:
        self._background.draw()


class GameView(View):

    def __init__(self) -> None:
        View.__init__(self)
        self.background_color = style.game.background.colour
        self._background = ParallaxBackground()
        self._batch = Batch()

        self._editor_frame = EditorFrame(0.0, (self.width, 0.0), 720)
        self._editor_frame.connect_renderer(self._batch)

        self._info_frame = Frame(
            "INFO",
            self._editor_frame.tag_height + 2 * style.format.padding,
            (self.width, 0.0),
            (450, 720),
        )
        self._info_frame.connect_renderer(self._batch)

        self._comms_frame = Frame(
            "COMMS",
            self._editor_frame.tag_height
            + self._info_frame.tag_height
            + 3 * style.format.padding,
            (self.width, 0.0),
            (450, 720),
        )
        self._comms_frame.connect_renderer(self._batch)

        self._setting_frame = SettingsFrame((self.width, 0.0), 720)
        self._setting_frame.connect_renderer(self._batch)

        self._frame_controller = FrameController(
            (
                self._editor_frame,
                self._setting_frame,
                self._info_frame,
                self._comms_frame,
            ),
            (self.width, 0.0),
        )

    def on_draw(self) -> None:
        self.clear()
        self._background.draw()
        self._frame_controller.on_draw()
        self._batch.draw()

    def on_update(self, delta_time: float) -> None:
        self._background.update()
        self._frame_controller.on_update(delta_time)

    def on_input(self, input: Button, modifiers: int, pressed: bool) -> None:
        self._frame_controller.on_input(input, modifiers, pressed)

    def on_axis_change(self, axis: Axis, value_1: float, value_2: float) -> None:
        self._frame_controller.on_axis_change(axis, value_1, value_2)

    def on_cursor_motion(self, x: float, y: float, dx: float, dy: float) -> None:
        self._background.cursor_motion(x, y, dx, dy)
        self._frame_controller.on_cursor_motion(x, y, dx, dy)

    def on_cursor_scroll(
        self, x: float, y: float, scroll_x: float, scroll_y: float
    ) -> None:
        self._frame_controller.on_cursor_scroll(x, y, scroll_x, scroll_y)
