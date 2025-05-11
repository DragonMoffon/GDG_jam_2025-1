from arcade import Window as ArcadeWindow
from pyglet.input import get_controllers

from resources import style

from .input import inputs


class Window(ArcadeWindow):
    def __init__(self):
        ArcadeWindow.__init__(
            self,
            style.application.window_width,
            style.application.window_height,
            style.application.window_name,
            resizable=True
        )
        self.set_minimum_size(style.application.min_width, style.application.min_height)
        self.set_icon(style.application.window_icon)
        inputs.setup_input_reponses()

        controllers = get_controllers()
        if controllers:
            inputs.pick_controller(controllers[0])

    def _dispatch_updates(self, delta_time: float) -> None:
        ArcadeWindow._dispatch_updates(self, delta_time)
        inputs.__update__(delta_time)
