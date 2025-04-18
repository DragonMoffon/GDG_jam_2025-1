from enum import Enum

from pyglet.graphics import Batch

from jam.view import View
from jam.gui.frame import Frame
from jam.input import inputs, Button

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

        self._info_frame = Frame('INFO', self._editor_frame.tag_height + 2 * style.format.padding, (self.width, 0.0), (300, 720))
        self._info_frame.connect_renderer(self._batch)

        self._comms_frame = Frame('COMMS', self._editor_frame.tag_height + self._info_frame.tag_height + 3 * style.format.padding, (self.width, 0.0), (300, 720))
        self._comms_frame.connect_renderer(self._batch)

        self._setting_frame = SettingsFrame((self.width, 0.0), 720)
        self._setting_frame.connect_renderer(self._batch)

        self._frames = (self._editor_frame, self._setting_frame, self._info_frame, self._comms_frame)

        self._active_frame: Frame | None = None
        self._next_frame: Frame | None = None
        self._pending_frame: Frame | None = None
        self._frame_animation: FrameAnimationMode = FrameAnimationMode.NONE
        self._frame_time: float = 0.0

    def on_draw(self) -> bool | None:
        self.clear()
        with self.window._ctx.enabled(self.window._ctx.BLEND):
            self._batch.draw()

    def on_update(self, delta_time: float) -> bool | None:
        if self._active_frame is not None and self._frame_animation == FrameAnimationMode.HIDE:
            time = self.window.time
            length = time - self._frame_time
            fraction = length / style.game.panels.panel_speed
            
            if fraction >= 1.0:
                self._active_frame.show_body = False
                self._active_frame.show_shadow = True
                
                self._active_frame.update_position((self.width, 0.0))
                self._active_frame = None

                # Choose what to do next
                if self._next_frame is not None:
                    self._next_frame.show_body = True
                    self._next_frame.show_shadow = False

                    self._frame_animation = FrameAnimationMode.SHOW
                    self._frame_time = time + style.game.panels.panel_speed - length # Account for 'overstep'
                else:
                    self._frame_animation = FrameAnimationMode.NONE
                    self._frame_time = 0.0
            else:
                self._active_frame.update_position((self.width - (1 - fraction)**3 * self._active_frame.panel_width, 0.0))

        elif self._next_frame is not None and self._frame_animation == FrameAnimationMode.SHOW:
            time = self.window.time
            length = time - self._frame_time
            fraction = length / style.game.panels.panel_speed
            
            if fraction >= 1.0:
                self._active_frame = self._next_frame
                self._next_frame = None

                self._frame_animation = FrameAnimationMode.NONE
                self._frame_time = 0.0
                self._active_frame.update_position((self.width - self._active_frame.panel_width, 0.0))
            else:
                self._next_frame.update_position((self.width - (1 - (1-fraction)**3) * self._next_frame.panel_width, 0.0))

        if self._pending_frame is not None and self._frame_animation == FrameAnimationMode.NONE:
            self._next_frame = self._pending_frame
            self._pending_frame = None

            if self._active_frame is None:
                self._next_frame.show_body = True
                self._next_frame.show_shadow = False

            self._frame_animation = FrameAnimationMode.HIDE if self._active_frame is not None else FrameAnimationMode.SHOW
            self._frame_time = self.window.time
        

    def on_input(self, input: Button, modifiers: int, pressed: bool) -> bool | None:
        if input == inputs.PRIMARY_CLICK and pressed:
            close_frame = True
            for frame in self._frames:
                if frame.contains_point(inputs.cursor):
                    close_frame = False
                    if frame is self._active_frame or frame is self._next_frame:
                        continue
                    self._pending_frame = frame
                    break

            if self._active_frame is not None and self._frame_animation != FrameAnimationMode.HIDE and close_frame:
                self._frame_time = self.window.time
                self._frame_animation = FrameAnimationMode.HIDE
                
