from arcade import LBWH, Camera2D
from arcade.camera.default import ViewportProjector
from pyglet.shapes import RoundedRectangle
from pyglet.text import Label

from resources import style

from jam.context import context
from jam.gui.frame import Frame

from jam.graphics.clip import ClippingMask
from jam.gui import core
from jam.input import inputs, Axis, Button

INFO_TEXT = """
[CATASTROPHIC FAILURE - SYSTEMS OFFLINE]

A starship careens past the station, taking a chunk of the center ring
with it and smashing into the main column.

The computers didn't like that.
Comms are offline. Lives are at stake. We need to get this place up and running fast.

Go to each wing and repair the logic used to run the different aspects of the station.
Each system has a code graph. Use the blocks provided and add new ones
to make each system run according to spec.
"""


class InfoFrame(Frame):

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
            INFO_TEXT,
            x=size[0] / 2,
            y=size[1] / 2,
            color=style.colors.highlight,
            font_name=style.text.normal.name,
            align="center",
            anchor_x="center",
            anchor_y="center",
            multiline="True",
            width=size[0] * 0.8,
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
            "INFO",
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

    def on_draw(self) -> None:
        with self.cliping_mask.target as fbo:
            fbo.clear(color=style.colors.background)
            with self.camera.activate():
                self.frame_gui.draw()
                self.label.draw()

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

    def on_select(self) -> None:
        self.label.text = INFO_TEXT
        if puz := context.get_open_puzzle():
            self.label.text += "\n------\n\n[CURRENT TASK]\n\n" + puz.description
