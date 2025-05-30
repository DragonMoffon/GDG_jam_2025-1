from arcade import draw_rect_filled
from pyglet.sprite import Sprite

from resources import style

from station.view import View
from station.gui.frame import Frame, FrameController
from station.gui.core import Gui
from station.gui.alert import AlertElement
from station.input import inputs, Button, Axis
from station.context import context
from station.puzzle import Puzzle
from station.graphics.background import ParallaxBackground
from station.comms import comms as station_comms

from .editor import EditorFrame
from .settings import SettingsFrame
from .comms import CommsFrame
from .info import InfoFrame


class LevelSelect:

    def __init__(self, gui: Gui) -> None:
        self._gui = gui
        self._offset = (0.0, 0.0)
        self._alerts: dict[str, AlertElement] = {}

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

    def clear_puzzle(self, puzzle: Puzzle) -> None:
        if puzzle.name not in self._alerts:
            return
        alert = self._alerts.pop(puzzle.name)
        self._gui.remove_element(alert)

    def find_new_puzzles(self) -> None:
        available = context.get_available_puzzles()
        for puzzle in available:
            if puzzle.name in self._alerts:
                continue
            alert = AlertElement(puzzle)
            self._gui.add_element(alert)
            self._alerts[puzzle.name] = alert
            style.audio.notification.play()
            if puzzle.comms:
                for comm in puzzle.comms:
                    station_comms.say(comm.dialogue, comm.speaker, comm.mood)
            context._comms_frame.update_comms()


class GameView(View):

    def __init__(self) -> None:
        View.__init__(self)
        self.background_color = style.game.background.color
        self._background = ParallaxBackground(style.game.background)
        self._logo = Sprite(style.textures.logo_big)
        self._logo.color = (255, 255, 255, 0)
        self._gui = Gui(self.window.default_camera)

        self._editor_frame = EditorFrame(0.0, (self.width, 0.0), 720)
        self._gui.add_element(self._editor_frame)

        self._info_frame = InfoFrame(
            self._editor_frame.tag_height + 2 * style.format.padding,
            (self.width, 0.0),
            720,
        )
        self._gui.add_element(self._info_frame)

        self._fade_in: bool = True
        self._timer: float = 0.0

        comm_offset = (
            self._editor_frame.tag_height
            + self._info_frame.tag_height
            + 3 * style.format.padding
        )
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
        self._level_check_time: float = self.window.time

        style.audio.ambience.wind.play("ambience1", True)

    def on_show_view(self) -> None:
        self._level_check_time = self.window.time + 2
        context.set_frames(
            self._frame_controller,
            self._editor_frame,
            self._info_frame,
            self._comms_frame,
            self._setting_frame,
        )
        context.set_level_select(self._level_select)

        self._fade_in = True
        self._timer = self.window.time

    def on_hide_view(self) -> None:
        context.clear_frames()
        context.clear_level_select()

    def select_frame(self, frame: Frame) -> None:
        self._frame_controller.select_frame(frame)

    def on_draw(self) -> None:
        self.clear()
        self._background.draw()
        self._frame_controller.on_draw()
        self._gui.draw()
        if self._fade_in:
            fraction = (self.window.time - self._timer) / 3.0
            amount = max(0.0, min(1.0, (1 - fraction) ** 3))
            draw_rect_filled(self.window.rect, (0, 0, 0, int(255 * amount)))
            self._logo.color = 255, 255, 255, int(255 * amount)
            self._logo.draw()
            if fraction >= 1.0:
                self._fade_in = False

    def on_update(self, delta_time: float) -> None:
        if self.window.time >= self._level_check_time:
            self._level_select.find_new_puzzles()
            self._level_check_time += 2.0  # wait 2 seconds

        self._background.update()
        self._level_select.update_offset(self._background.layer_offsets[0])
        self._frame_controller.on_update(delta_time)

    def on_input(self, button: Button, modifiers: int, pressed: bool) -> None:
        if not self._frame_controller.selected_frame and pressed:
            if button == inputs.PRIMARY_CLICK:
                alert = self._level_select.get_hovered_alert(inputs.cursor)
                if alert is not None:
                    context.open_editor_tab(alert.puzzle)
                    context.show_editor_frame()

        self._frame_controller.on_input(button, modifiers, pressed)

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
