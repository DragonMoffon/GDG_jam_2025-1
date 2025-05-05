from uuid import UUID
from enum import Enum

from pyglet.graphics import Batch, Group
from pyglet.shapes import RoundedRectangle
from pyglet.text import Label
from arcade.clock import GLOBAL_CLOCK

from .core import Element, get_shadow_shader, OVERLAY_SPACING, OVERLAY_PRIMARY, OVERLAY_HIGHLIGHT
from jam.input import inputs, Button, Axis
from resources import style

ACTIVE_GROUP = Group(0)
SHADOW_GROUP = Group(1)
TAG_GROUP = Group(2)


class Frame(Element):

    def __init__(self, name: str, tag_offset: float, position: tuple[float, float], size: tuple[float, float], show_body: bool = False, show_shadow: bool = True, anchor_top: bool = True, uid: UUID | None = None):
        Element.__init__(self, uid)
        self._name = name
        self._size = size
        self._position = position
        self._tag_offset: float = tag_offset
        self._anchor_top: bool = anchor_top

        self._show_body: bool = True
        self._show_shadow: bool = True

        self._tag_text = Label(
            '\n'.join(name),
            0, 0, 0,
            int(style.text.header.size) + 1,
            anchor_y='top',
            multiline=True,
            font_size=style.text.header.size,
            font_name=style.text.header.name,
            color=style.colors.highlight,
            group=OVERLAY_HIGHLIGHT
        )
        self._tag_text.set_style('line_spacing', style.text.header.size + style.format.padding)
        self._tag_panel = RoundedRectangle(
            0.0, 0.0,
            style.format.corner_radius + 2 * style.format.padding + self._tag_text.content_width,
            self._tag_text.content_height + 2 * style.format.corner_radius + 2 * style.format.padding,
            (style.format.corner_radius, style.format.corner_radius, 0, 0),
            (12, 12, 1, 1),
            color=style.colors.base,
            group=OVERLAY_HIGHLIGHT
        )
        self._tag_shadow = RoundedRectangle(
            0.0, 0.0,
            self._tag_panel.width + style.format.drop_x, self._tag_panel.height,
            (style.format.corner_radius, style.format.corner_radius, 0, 0),
            (12, 12, 1, 1),
            color=style.colors.dark,
            group=OVERLAY_PRIMARY,
            program=get_shadow_shader()
        )
        radius = style.format.corner_radius + style.format.footer_size
        if anchor_top:
            hide_top = tag_offset < radius and 0.0 < tag_offset + self._tag_panel.height

            bottom_dist = size[1] - tag_offset - self._tag_panel.height
            hide_bottom = bottom_dist < radius and 0.0 < bottom_dist + self._tag_panel.height
        else:
            top_dist = size[1] - tag_offset - self._tag_panel.height
            hide_top = top_dist < radius and 0.0 < top_dist + self._tag_panel.height

            hide_bottom = tag_offset < radius and 0.0 < tag_offset + self._tag_panel.height

        top_radius = 0.0 if hide_top else radius
        top_segments = 1 if hide_top else 12

        bottom_radius = 0.0 if hide_bottom else radius
        bottom_segments = 1 if hide_bottom else 12

        self._panel = RoundedRectangle(
            0.0, 0.0,
            size[0], size[1],
            (bottom_radius, top_radius, 0.0, 0.0),
            (bottom_segments, top_segments, 1, 1),
            color=style.colors.base,
            group=OVERLAY_SPACING
        )

        self.update_position(position)
        self.show_body = show_body
        self.show_shadow = show_shadow

    @property
    def tag_height(self) -> float:
        return self._tag_panel.height

    @property
    def panel_width(self) -> float:
        return self._panel.width

    @property
    def panel_height(self) -> float:
        return self._panel.height

    def connect_renderer(self, batch: Batch | None) -> None:
        self._tag_shadow.batch = batch
        self._tag_panel.batch = batch
        self._panel.batch = batch
        self._tag_text.batch = batch

    def update_position(self, point: tuple[float, float]) -> None:
        self._position = point
        self._panel.position = point

        tag_y = point[1] + (self._panel.height - self._tag_offset - self._tag_panel.height if self._anchor_top else self._tag_offset)
        self._tag_panel.position = point[0] - self._tag_panel.width, tag_y
        self._tag_shadow.position = self._tag_panel.x - style.format.drop_x, self._tag_panel.y - style.format.drop_y
        self._tag_text.position = self._tag_panel.x + style.format.corner_radius / 2.0, self._tag_panel.y + self._tag_panel.height - style.format.corner_radius, 0.0

    @property
    def show_body(self) -> bool:
        return self._show_body

    @show_body.setter
    def show_body(self, show: bool) -> None:
        self._show_body = show
        self._panel.visible = show

    @property
    def show_shadow(self) -> bool:
        return self._show_shadow

    @show_shadow.setter
    def show_shadow(self, show: bool) -> None:
        self._show_shadow = show
        self._tag_shadow.visible = show

    def select(self) -> None:
        self.show_body = True
        self.show_shadow = False
        self.on_select()

    def hide(self) -> None:
        self.show_body = False
        self.show_shadow = True
        self.on_hide()

    def contains_point(self, point: tuple[float, float]) -> bool:
        return (
            (0 <= point[0] - self._panel.x <= self._panel.width and 0 <= point[1] - self._panel.y <= self._panel.height)
            or (0 <= point[0] - self._tag_panel.x <= self._tag_panel.width and 0 <= point[1] - self._tag_panel.y <= self._tag_panel.height)
        )

    def tag_contains_point(self, point: tuple[float, float]) -> bool:
        return 0 <= point[0] - self._tag_panel.x <= self._tag_panel.width and 0 <= point[1] - self._tag_panel.y <= self._tag_panel.height

    def on_input(self, input: Button, modifiers: int, pressed: bool) -> bool | None: ...
    def on_axis_change(self, axis: Axis, value_1: float, value_2: float) -> bool | None: ...
    def on_cursor_motion(self, x: float, y: float, dx: float, dy: float) -> bool | None: ...
    def on_cursor_scroll(self, x: float, y: float, scroll_x: float, scroll_y: float) -> bool | None: ...

    def on_draw(self) -> None: ...
    def on_update(self, delta_time: float) -> None: ...

    def on_select(self) -> None: ...
    def on_hide(self) -> None: ...


class FrameAnimationMode(Enum):
    NONE = 0
    SHOW = 1
    HIDE = 2


class FrameController:

    def __init__(self, frames: tuple[Frame, ...], position: tuple[float, float]) -> None:
        self._frames: tuple[Frame, ...] = frames

        self._pos: tuple[float, float] = position

        self._selected_frame: Frame | None = None
        self._next_frame: Frame | None = None
        self._pending_frame: Frame | None = None

        self._animation_time: float = 0.0
        self._animation_mode: Enum = FrameAnimationMode.NONE

    def select_frame(self, frame: Frame) -> None:
        if frame == self._selected_frame:
            return

        if frame not in self._frames:
            raise ValueError(f'{frame} is not controlled by this controller.')

        if self._selected_frame is not None:
            self._animation_mode = FrameAnimationMode.HIDE
            self._animation_time = GLOBAL_CLOCK.time
            if self._next_frame is None:
                self._next_frame = frame
                style.audio.slide_in.play()
            else:
                self._pending_frame = frame
        elif self._next_frame is None:
            self._next_frame = frame
            frame.select()

            self._animation_mode = FrameAnimationMode.SHOW
            self._animation_time = GLOBAL_CLOCK.time
        else:
            self._pending_frame = frame

    def select_frame_by_idx(self, frame_idx: int) -> None:
        if not (0 <= frame_idx < len(self._frames)):
            raise IndexError(f'The controller only has {len(self._frames)} frames to select')
        self.select_frame(self._frames[frame_idx])

    def deselect_frame(self) -> None:
        if self._selected_frame is None or self._animation_mode != FrameAnimationMode.NONE:
            return

        self._animation_mode = FrameAnimationMode.HIDE
        self._animation_time = GLOBAL_CLOCK.time
        style.audio.slide_in.play()

    def on_input(self, input: Button, modifiers: int, pressed: bool) -> bool | None:
        if input == inputs.PRIMARY_CLICK and pressed:
            cursor = inputs.cursor
            close_frame = True
            for frame in self._frames:
                if frame == self._selected_frame and frame.tag_contains_point(cursor):
                    close_frame = True
                    break
                if frame.contains_point(cursor):
                    close_frame = False
                    if frame == self._selected_frame or frame == self._next_frame:
                        continue
                    self._pending_frame = frame
                    return

            if self._animation_mode != FrameAnimationMode.HIDE and close_frame:
                self.deselect_frame()
                return

        if self._selected_frame is not None:
            self._selected_frame.on_input(input, modifiers, pressed)

        if self._next_frame is not None and self._animation_mode == FrameAnimationMode.SHOW:
            self._next_frame.on_input(input, modifiers, pressed)

    def on_axis_change(self, axis: Axis, value_1: float, value_2: float) -> None:
        if self._selected_frame is not None:
            self._selected_frame.on_axis_change(axis, value_1, value_2)

        if self._next_frame is not None and self._animation_mode == FrameAnimationMode.SHOW:
            self._next_frame.on_axis_change(axis, value_1, value_2)

    def on_cursor_motion(self, x: float, y: float, dx: float, dy: float) -> bool | None:
        if self._selected_frame is not None:
            self._selected_frame.on_cursor_motion(x, y, dx, dy)

        if self._next_frame is not None and self._animation_mode == FrameAnimationMode.SHOW:
            self._next_frame.on_cursor_motion(x, y, dx, dy)

    def on_cursor_scroll(self, x: float, y: float, scroll_x: float, scroll_y: float) -> bool | None:
        if self._selected_frame is not None:
            self._selected_frame.on_cursor_scroll(x, y, scroll_x, scroll_y)

        if self._next_frame is not None and self._animation_mode == FrameAnimationMode.SHOW:
            self._next_frame.on_cursor_scroll(x, y, scroll_x, scroll_y)

    def on_draw(self) -> None:
        if self._selected_frame is not None:
            self._selected_frame.on_draw()

        if self._next_frame is not None and self._animation_mode == FrameAnimationMode.SHOW:
            self._next_frame.on_draw()

    def on_update(self, delta_time: float) -> None:
        time = GLOBAL_CLOCK.time
        length = time - self._animation_time
        fraction = length / style.game.panels.panel_speed

        if self._selected_frame is not None and self._animation_mode == FrameAnimationMode.HIDE:
            if fraction >= 1.0:
                self._selected_frame.hide()
                self._selected_frame.update_position(self._pos)
                self._selected_frame = None

                if self._next_frame is not None:
                    self._next_frame.select()

                    self._animation_mode = FrameAnimationMode.SHOW
                    self._animation_time = time + style.game.panels.panel_speed - length
                    style.audio.slide_out.play()
                else:
                    self._animation_mode = FrameAnimationMode.NONE
                    self._animation_time = 0.0
            else:
                x = self._pos[0] - (1 - fraction)**3 * self._selected_frame.panel_width
                self._selected_frame.update_position((x, self._pos[1]))
        elif self._next_frame is not None and self._animation_mode == FrameAnimationMode.SHOW:
            if fraction >= 1.0:
                self._selected_frame = self._next_frame
                self._next_frame = None

                self._animation_mode = FrameAnimationMode.NONE
                self._animation_time = 0.0

                self._selected_frame.update_position((self._pos[0] - self._selected_frame.panel_width, self._pos[1]))
            else:
                x = self._pos[0] - (1 - (1 - fraction)**3) * self._next_frame.panel_width
                self._next_frame.update_position((x, self._pos[1]))

        if self._pending_frame is not None and self._animation_mode == FrameAnimationMode.NONE:
            self.select_frame(self._pending_frame)
            self._pending_frame = None

        if self._selected_frame is not None:
            self._selected_frame.on_update(delta_time)

        if self._next_frame is not None and self._animation_mode == FrameAnimationMode.SHOW:
            self._next_frame.on_update(delta_time)

    @property
    def selected_frame(self) -> Frame | None:
        return self._selected_frame

    @property
    def next_frame(self) -> Frame | None:
        return self._next_frame

    @property
    def pending_frame(self) -> Frame | None:
        return self._pending_frame
