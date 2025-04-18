from jam.gui.frame import Frame

from resources import style

class SettingsFrame(Frame):

    def __init__(self, position: tuple[float, float], height: float, show_body: bool = False, show_shadow: bool = True):
        size = (300, height)
        super().__init__('SETTINGS', 0.0, position, size, show_body, show_shadow)
        self._tag_offset = height - self._tag_panel.height
        self._panel._set_segments((1, 12, 1, 1)) # BAD!!
        self._panel.radius = (0, style.format.corner_radius, 0, 0)
        self.update_position(position)