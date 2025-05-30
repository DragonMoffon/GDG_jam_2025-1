from arcade import LBWH, Camera2D
from arcade.camera.default import ViewportProjector
from pyglet.shapes import RoundedRectangle
from pyglet.text import Label

from station.gui.comms import CommsLogElement
from resources import style

from station.gui.frame import Frame

from station.graphics.clip import ClippingMask
from station.graphics.format_label import FLabel
from station.gui import core
from station.input import Axis, Button
from station.comms import comms


class CommsFrame(Frame):

    def __init__(
        self,
        tag_offset: float,
        position: tuple[float, float],
        height: float,
        show_body: bool = False,
        show_shadow: bool = True,
    ):
        size = (450, height)

        # -- CREATE CLIP MASK --

        # shrinks the clip by a padding value (jank uses block footer size)
        clip_size = int(size[0] - style.format.footer_size), int(
            size[1] - 2 * style.format.footer_size
        )
        # The viewport of the cliping mask.
        clip_rect = LBWH(0.0, 0.0, clip_size[0], clip_size[1])
        # Start position, target size, clip size, grouping for working with the frame rendering
        self.cliping_mask = ClippingMask(
            (0.0, 0.0), clip_size, clip_size, group=core.OVERLAY_SPACING
        )
        # A projector that acts like arcade's default. Use if you want things to not move within the clip.
        self._clip_projector = ViewportProjector(clip_rect)

        self.label = Label(
            "[COMMS OFFLINE]",
            x=size[0] / 2,
            y=size[1] / 2,
            color=style.colors.highlight,
            font_name=style.text.names.monospace,
            align="center",
            anchor_x="center",
            anchor_y="center",
        )

        # activate the clip texture to draw into, use the basic clip projector,
        # then create and immediatly use a rounded rectangle.
        with self.cliping_mask.clip:
            with self._clip_projector.activate():
                RoundedRectangle(
                    0.0,
                    0.0,
                    size[0] - style.format.footer_size,
                    size[1] - 2 * style.format.footer_size,
                    (style.format.corner_radius, style.format.corner_radius, 0.0, 0.0),
                    (12, 12, 1, 1),
                    color=(255, 255, 255, 255),
                ).draw()

        # This has to happen before init because the Frame called update_position which refers to the clipping mask

        Frame.__init__(
            self,
            "COMMS",
            tag_offset,
            position,
            size,
            show_body,
            show_shadow,
            anchor_top=True,
        )

        self.camera = Camera2D(
            clip_rect
        )  # Camera2D with the viewport of the clip_rect to draw the gui.
        self.frame_gui: core.Gui = core.Gui(
            self.camera
        )  # The gui that gets clipped by the mask.

        # Comms time
        self.width = clip_rect.width
        self.height = clip_rect.height
        self.log: CommsLogElement = None
        self.update_comms()

    def update_comms(self) -> None:
        if self.log is not None:
            self.frame_gui.remove_element(self.log)
        self.log = CommsLogElement(comms, self.width - self._tag_panel.width)
        self.log.update_position((style.format.footer_size, self.height - style.format.footer_size))
        self.frame_gui.add_element(self.log)

    def on_draw(self) -> None:
        with self.cliping_mask.target as fbo:
            fbo.clear(color=style.colors.background)
            self.frame_gui.draw()

    def connect_renderer(self, batch: core.Batch | None) -> None:
        Frame.connect_renderer(self, batch)
        self.cliping_mask.batch = batch

    def update_position(self, point: tuple[float, float]) -> None:
        Frame.update_position(self, point)
        self.cliping_mask.position = (
            point[0] + style.format.footer_size,
            point[1] + style.format.footer_size,
        )

    def on_input(self, button: Button, modifiers: int, pressed: bool) -> None:
        pass

    def on_axis_change(self, axis: Axis, value_1: float, value_2: float) -> None:
        pass

    def on_cursor_motion(self, x: float, y: float, dx: float, dy: float) -> None:
        pass

    def on_cursor_scroll(
        self, x: float, y: float, scroll_x: float, scroll_y: float
    ) -> None:
        pass

    def on_select(self) -> None: ...
    def on_hide(self) -> None: ...
