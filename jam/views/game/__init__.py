from arcade import Camera2D

from resources import style

from jam.view import View
from jam.gui.frame import Frame, FrameController
from jam.gui.core import Gui
from jam.gui.alert import AlertElement
from jam.input import inputs, Button, Axis
from jam.context import context
from jam.puzzle import puzzles
from jam.graphics.background import ParallaxBackground

from .editor import EditorFrame
from .settings import SettingsFrame
from .comms import CommsFrame
from .info import InfoFrame


class LevelSelect:

    def __init__(self, gui: Gui) -> None:
        self._gui = gui
        puzzle = puzzles.get_puzzle('connect_mainbus')
        pin, loc, face = puzzles.get_pin(puzzle)

        alert = AlertElement(pin, loc, face, puzzle)
        self._gui.add_element(alert)
        self._offset = (0.0, 0.0)
        self._alerts: dict[str, AlertElement] = {puzzle.name: alert}

    def update_offset(self, offset: tuple[float, float]) -> None:
        self._offset = offset
        for alert in self._alerts.values():
            alert.update_offset(offset)

    def get_hovered_alert(self, point: tuple[float, float]) -> AlertElement | None:
        for alert in self._alerts.values():
            if alert.contains_point(point):
                return alert
        return None

    def highlight_alert(self, alert: AlertElement | None = None) -> None:
        for other in self._alerts.values():
            other.deselect()

        if alert is not None:
            alert.highlight()


class GameView(View):

    def __init__(self) -> None:
        View.__init__(self)
        self.background_color = style.game.background.colour
        self._background = ParallaxBackground()
        self._background_projector = Camera2D(self.window.rect)
        self._panel_projector = Camera2D(self.window.rect)
        self._gui = Gui(
            self._background_projector,
            self._panel_projector
        )

        self._editor_frame = EditorFrame(0.0, (self.width, 0.0), 720)
        self._gui.add_element(self._editor_frame)

        self._info_frame = InfoFrame(
            self._editor_frame.tag_height + 2 * style.format.padding,
            (self.width, 0.0),
            720,
        )
        self._gui.add_element(self._info_frame)

        comm_offset = self._editor_frame.tag_height + self._info_frame.tag_height + 3 * style.format.padding
        self._comms_frame = CommsFrame(
            comm_offset,
            (self.width, 0.0),
            720,
        )
        self._gui.add_element(self._comms_frame)

        self._setting_frame = SettingsFrame((self.width, 0.0), 720)
        self._gui.add_element(self._setting_frame)

        self._frame_controller = FrameController(
            (
                self._editor_frame,
                self._setting_frame,
                self._info_frame,
                self._comms_frame,
            ),
            (self.width, 0.0),
        )

        self._level_select: LevelSelect = LevelSelect(self._gui)

        style.audio.ambient_wind.play('ambience1', True)

    def on_show_view(self) -> None:
        context.set_frames(self._frame_controller, self._editor_frame, self._info_frame, self._comms_frame, self._setting_frame)

    def on_hide_view(self) -> None:
        context.clear_frames()

    def select_frame(self, frame: Frame):
        self._frame_controller.select_frame(frame)

    def on_draw(self) -> None:
        self.clear()
        self._background.draw()
        self._frame_controller.on_draw()
        self._gui.draw()

    def on_update(self, delta_time: float) -> None:
        self._background.update()
        self._level_select.update_offset(self._background.layer_offsets[0])
        self._frame_controller.on_update(delta_time)

    def on_input(self, input: Button, modifiers: int, pressed: bool) -> None:
        if not self._frame_controller.selected_frame and pressed:
            if input == inputs.PRIMARY_CLICK:
                alert = self._level_select.get_hovered_alert(inputs.cursor)
                if alert is not None:
                    context.open_editor_tab(alert.puzzle)
                    context.show_editor_frame()

        self._frame_controller.on_input(input, modifiers, pressed)

    def on_axis_change(self, axis: Axis, value_1: float, value_2: float) -> None:
        self._frame_controller.on_axis_change(axis, value_1, value_2)

    def on_cursor_motion(self, x: float, y: float, dx: float, dy: float) -> None:
        self._background.cursor_motion(x, y, dx, dy)
        self._level_select.update_offset(self._background.layer_offsets[0])
        if not self._frame_controller.selected_frame:
            alert = self._level_select.get_hovered_alert(inputs.cursor)
            self._level_select.highlight_alert(alert)
        self._frame_controller.on_cursor_motion(x, y, dx, dy)

    def on_cursor_scroll(
        self, x: float, y: float, scroll_x: float, scroll_y: float
    ) -> None:
        self._frame_controller.on_cursor_scroll(x, y, scroll_x, scroll_y)
