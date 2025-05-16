from uuid import UUID
from enum import Enum

from pyglet.graphics import Batch, Group
from pyglet.shapes import RoundedRectangle as pyRoundedRectangle
from arcade import LBWH, Rect
from arcade.clock import GLOBAL_CLOCK
from arcade.camera.default import ViewportProjector

from resources import style, audio
from station.input import inputs, Button, Axis
from station.graphics.shadow import get_shadow_shader
from station.graphics.clip import ClippingMask, FramebufferGroup

from .core import Element, Point
from .elements import Label, RoundedRectangle


class FrameTab(Element):

    def __init__(
        self,
        text: str,
        parent: Element | None = None,
        layer: Group | None = None,
        uid: UUID | None = None,
    ):
        Element.__init__(self, parent, layer, uid)
        self._text = Label(
            "\n".join(text),
            0,
            0,
            int(style.text.sizes.header) + 1,
            anchor_y="top",
            multiline=True,
            font_name=style.text.names.monospace,
            font_size=style.text.sizes.header,
            color=style.colors.highlight,
            parent=self,
            layer=self.HIGHLIGHT(2),
        )
        self._text.label.set_style(
            "line_spacing", style.text.sizes.header + style.format.padding
        )
        self._panel = RoundedRectangle(
            0.0,
            0.0,
            self._text.width + style.format.corner_radius + 2 * style.format.padding,
            self._text.height
            + 2 * style.format.corner_radius
            + 2 * style.format.padding,
            (style.format.corner_radius, style.format.corner_radius, 0, 0),
            (12, 12, 1, 1),
            color=style.colors.base,
            parent=self,
            layer=self.HIGHLIGHT(1),
        )
        self._shadow = RoundedRectangle(
            0.0,
            0.0,
            self._panel.width + style.format.drop_x,
            self._panel.height,
            (style.format.corner_radius, style.format.corner_radius, 0, 0),
            (12, 12, 1, 1),
            color=style.colors.dark,
            program=get_shadow_shader(),
            parent=self,
            layer=self.HIGHLIGHT(0),
        )

    def contains_point(self, point: Point) -> bool:
        return self._panel.contains_point(point)

    def update_position(self, point: Point) -> None:
        self._panel.update_position(point)
        self._shadow.update_position(
            (point[0] - style.format.drop_x, point[1] - style.format.drop_y)
        )
        self._text.update_position(
            (
                point[0] + style.format.corner_radius / 2.0,
                point[1] + self._panel.height - style.format.corner_radius,
            )
        )

    def get_position(self) -> Point:
        return self._panel.get_position()

    def get_size(self) -> tuple[float, float]:
        return self._panel.get_size()

    @property
    def show_shadow(self) -> bool:
        return self._shadow._body.visible

    @show_shadow.setter
    def show_shadow(self, show: bool) -> None:
        self._shadow._body.visible = show


class Frame(Element):

    def __init__(
        self,
        name: str,
        tab_offset: float,
        size: tuple[float, float],
        show_body: bool = False,
        show_shadow: bool = True,
        anchor_top: bool = True,
        parent: Element | None = None,
        layer: Group | None = None,
        uid: UUID | None = None,
    ):
        Element.__init__(self, parent, layer, uid)
        self._name = name
        self._size = size
        self._position = (0.0, 0.0)
        self._tab_offset: float = tab_offset
        self._anchor_top: bool = anchor_top

        self._show_body: bool = True
        self._show_shadow: bool = True

        self._tab = FrameTab(name, self)

        top_radius, bottom_radius = self._calculate_tab_radii()
        top_segments = 12 if top_radius > 0.0 else 1
        bottom_segments = 12 if bottom_radius > 0.0 else 1

        self._panel = RoundedRectangle(
            0.0,
            0.0,
            size[0],
            size[1],
            (bottom_radius, top_radius, 0.0, 0.0),
            (bottom_segments, top_segments, 1, 1),
            color=style.colors.base,
            parent=self,
            layer=self.BODY(),
        )

        clip_size = int(size[0] - style.format.footer_size), int(
            size[1] - 2 * style.format.footer_size
        )
        self._clip = ClippingMask(
            (0.0, 0.0), clip_size, clip_size, visible=show_body, group=self.BODY(1)
        )
        self._render_clip_mask()

        self.clip_layer: FramebufferGroup = self._clip.target_group(style.colors.background)
        self.clip_layer.set_state()
        self.clip_layer.unset_state()

        self.show_body = show_body
        self.show_shadow = show_shadow

    def _render_clip_mask(self) -> None:
        clip_rect = LBWH(0.0, 0.0, *self._clip.size)
        viewport = ViewportProjector(clip_rect)
        radius = style.format.corner_radius
        with self._clip.clip:
            with viewport.activate():
                pyRoundedRectangle(
                    0,
                    0,
                    clip_rect.width,
                    clip_rect.height,
                    (radius, radius, 0, 0),
                    (12, 12, 1, 1),
                ).draw()

    def _calculate_tab_radii(self) -> tuple[float, float]:
        tab_offset = self._tab_offset
        size = self._size

        radius = style.format.corner_radius + style.format.footer_size
        if self._anchor_top:
            hide_top = tab_offset < radius and 0.0 < tab_offset + self._tab.height

            bottom_dist = size[1] - tab_offset - self._tab.height
            hide_bottom = bottom_dist < radius and 0.0 < bottom_dist + self._tab.height
        else:
            top_dist = size[1] - tab_offset - self._tab.height
            hide_top = top_dist < radius and 0.0 < top_dist + self._tab.height

            hide_bottom = tab_offset < radius and 0.0 < tab_offset + self._tab.height

        top_radius = 0.0 if hide_top else radius

        bottom_radius = 0.0 if hide_bottom else radius

        return top_radius, bottom_radius

    @property
    def tab_height(self) -> float:
        return self._tab.height
    
    @property
    def clip_rect(self) -> Rect:
        return LBWH(0.0, 0.0, *self._clip.size)

    def connect_renderer(self, batch: Batch | None) -> None:
        self._clip.batch = batch

    def set_visible(self, visible: bool) -> None:
        self._clip.visible = visible and self.show_body

    def contains_point(self, point: Point) -> bool:
        return self._panel.contains_point(point) or self._tab.contains_point(point)

    def tab_contains_point(self, point: tuple[float, float]) -> bool:
        return self._tab.contains_point(point)

    def update_position(self, point: Point) -> None:
        self._position = point
        self._panel.update_position(point)
        self._clip.position = (
            point[0] + style.format.footer_size,
            point[1] + style.format.footer_size,
        )

        tag_y = point[1] + (
            self._panel.height - self._tab_offset - self._tab.height
            if self._anchor_top
            else self._tab_offset
        )
        self._tab.update_position((point[0] - self._tab.width, tag_y))

    def get_position(self) -> Point:
        return self._panel.get_position()

    def update_size(self, size: tuple[int, int]) -> None:
        if size == self._size:
            return
        self._size = size
        self._panel.update_size(size)

        self._clip.size = size
        self._clip.update_clip_size(size)
        self._clip.update_target_size(size)
        self._render_clip_mask()

        self.update_position(self._position)

    def get_size(self) -> tuple[float, float]:
        return self._size

    def get_tab_position(self) -> Point:
        return self._tab.get_position()

    @property
    def show_body(self) -> bool:
        return self._show_body

    @show_body.setter
    def show_body(self, show: bool) -> None:
        self._show_body = show
        self._panel._body.visible = show
        self._clip.visible = show

    @property
    def show_shadow(self) -> bool:
        return self._show_shadow

    @show_shadow.setter
    def show_shadow(self, show: bool) -> None:
        self._show_shadow = show
        self._tab.show_shadow = show

    def select(self) -> None:
        self.show_body = True
        self.show_shadow = False
        self.on_select()

    def hide(self) -> None:
        self.show_body = False
        self.show_shadow = True
        self.on_hide()

    def on_input(self, button: Button, modifiers: int, pressed: bool) -> None: ...
    def on_axis_change(self, axis: Axis, value_1: float, value_2: float) -> None: ...
    def on_cursor_motion(self, x: float, y: float, dx: float, dy: float) -> None: ...

    def on_cursor_scroll(
        self, x: float, y: float, scroll_x: float, scroll_y: float
    ) -> None: ...

    def on_update(self, delta_time: float) -> None: ...

    def on_select(self) -> None: ...
    def on_hide(self) -> None: ...


class FrameAnimationMode(Enum):
    NONE = 0
    SHOW = 1
    HIDE = 2


class FrameController:

    def __init__(
        self, frames: tuple[Frame, ...], position: tuple[float, float]
    ) -> None:
        self._frames: tuple[Frame, ...] = frames

        self._pos: tuple[float, float] = position

        self._selected_frame: Frame | None = None
        self._next_frame: Frame | None = None
        self._pending_frame: Frame | None = None

        self._animation_time: float = 0.0
        self._animation_mode: Enum = FrameAnimationMode.NONE

        for frame in frames:
            frame.update_position(position)

    def select_frame(self, frame: Frame) -> None:
        if frame == self._selected_frame:
            return

        if frame not in self._frames:
            raise ValueError(f"{frame} is not controlled by this controller.")

        if self._selected_frame is not None:
            self._animation_mode = FrameAnimationMode.HIDE
            self._animation_time = GLOBAL_CLOCK.time
            style.audio.slide_in.play()
            if self._next_frame is None:
                self._next_frame = frame
            else:
                self._pending_frame = frame
        elif self._next_frame is None:
            self._next_frame = frame
            frame.select()

            self._animation_mode = FrameAnimationMode.SHOW
            self._animation_time = GLOBAL_CLOCK.time
            style.audio.slide_out.play()
        else:
            self._pending_frame = frame

    def select_frame_by_idx(self, frame_idx: int) -> None:
        if not (0 <= frame_idx < len(self._frames)):
            raise IndexError(
                f"The controller only has {len(self._frames)} frames to select"
            )
        self.select_frame(self._frames[frame_idx])

    def deselect_frame(self) -> None:
        if (
            self._selected_frame is None
            or self._animation_mode != FrameAnimationMode.NONE
        ):
            return

        self._animation_mode = FrameAnimationMode.HIDE
        self._animation_time = GLOBAL_CLOCK.time
        style.audio.slide_in.play()
        audio.stop("ambience2")

    def on_input(self, button: Button, modifiers: int, pressed: bool) -> bool | None:
        if button == inputs.PRIMARY_CLICK and pressed:
            cursor = inputs.cursor
            close_frame = True
            for frame in self._frames:
                if frame == self._selected_frame and frame.tab_contains_point(cursor):
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
            self._selected_frame.on_input(button, modifiers, pressed)

        if (
            self._next_frame is not None
            and self._animation_mode == FrameAnimationMode.SHOW
        ):
            self._next_frame.on_input(button, modifiers, pressed)

    def on_axis_change(self, axis: Axis, value_1: float, value_2: float) -> None:
        if self._selected_frame is not None:
            self._selected_frame.on_axis_change(axis, value_1, value_2)

        if (
            self._next_frame is not None
            and self._animation_mode == FrameAnimationMode.SHOW
        ):
            self._next_frame.on_axis_change(axis, value_1, value_2)

    def on_cursor_motion(self, x: float, y: float, dx: float, dy: float) -> bool | None:
        if self._selected_frame is not None:
            self._selected_frame.on_cursor_motion(x, y, dx, dy)

        if (
            self._next_frame is not None
            and self._animation_mode == FrameAnimationMode.SHOW
        ):
            self._next_frame.on_cursor_motion(x, y, dx, dy)

    def on_cursor_scroll(
        self, x: float, y: float, scroll_x: float, scroll_y: float
    ) -> bool | None:
        if self._selected_frame is not None:
            self._selected_frame.on_cursor_scroll(x, y, scroll_x, scroll_y)

        if (
            self._next_frame is not None
            and self._animation_mode == FrameAnimationMode.SHOW
        ):
            self._next_frame.on_cursor_scroll(x, y, scroll_x, scroll_y)

    def on_update(self, delta_time: float) -> None:
        time = GLOBAL_CLOCK.time
        length = time - self._animation_time
        fraction = length / style.game.panels.panel_speed

        if (
            self._selected_frame is not None
            and self._animation_mode == FrameAnimationMode.HIDE
        ):
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
                x = self._pos[0] - (1 - fraction) ** 3 * self._selected_frame.width
                self._selected_frame.update_position((x, self._pos[1]))
        elif (
            self._next_frame is not None
            and self._animation_mode == FrameAnimationMode.SHOW
        ):
            if fraction >= 1.0:
                self._selected_frame = self._next_frame
                self._next_frame = None

                self._animation_mode = FrameAnimationMode.NONE
                self._animation_time = 0.0

                x = self._pos[0] - self._selected_frame.width
                self._selected_frame.update_position((x, self._pos[1]))
            else:
                x = self._pos[0] - (1 - (1 - fraction) ** 3) * self._next_frame.width
                self._next_frame.update_position((x, self._pos[1]))

        if (
            self._pending_frame is not None
            and self._animation_mode == FrameAnimationMode.NONE
        ):
            self.select_frame(self._pending_frame)
            self._pending_frame = None

        if self._selected_frame is not None:
            self._selected_frame.on_update(delta_time)

        if (
            self._next_frame is not None
            and self._animation_mode == FrameAnimationMode.SHOW
        ):
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
