from station.gui.frame import Frame

from resources import Style


class SettingsFrame(Frame):

    def __init__(
        self,
        position: tuple[float, float],
        height: float,
        show_body: bool = False,
        show_shadow: bool = True,
    ):
        size = (450, height)
        super().__init__(
            "SETTINGS", 0.0, position, size, show_body, show_shadow, anchor_top=False
        )
