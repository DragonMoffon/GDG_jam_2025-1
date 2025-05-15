from arcade import Camera2D
from station.gui.comms import CommsLogElement
from resources import style

from station.gui.core import ProjectorGroup, Element, Group
from station.gui.frame import Frame

from station.input import Axis, Button
from station.comms import comms


class CommsFrame(Frame):

    def __init__(
        self,
        tab_offset: float,
        height: float,
        show_body: bool = False,
        show_shadow: bool = True,
        parent: Element | None = None,
        layer: Group | None = None
    ):
        size = (450, height)

        Frame.__init__(
            self,
            "COMMS",
            tab_offset,
            size,
            show_body,
            show_shadow,
            True,
            parent,
            layer
        )

        self.camera = Camera2D(self.clip_rect)
        self.comms_layer = ProjectorGroup(self.camera, 0, self.clip_layer)

        # Comms time
        self.log: CommsLogElement | None = None
        self.update_comms()

    def update_comms(self) -> None:
        if self.log is not None:
            self.remove_child(self.log)
            self.log.clear_children()
        self.log = CommsLogElement(comms, self._clip.size[0], parent=self, layer=self.comms_layer)
        self.log.update_position((style.format.footer_size, self._clip.size[1]))

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