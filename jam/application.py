from arcade import Window as ArcadeWindow
from pyglet.input import get_controllers
from .input import inputs

class Window(ArcadeWindow):
    
    def __init__(self):
        ArcadeWindow.__init__(self)
        inputs.setup_input_reponses()

        controllers = get_controllers()
        if controllers:
            inputs.pick_controller(controllers[0])

    def _dispatch_updates(self, delta_time: float) -> None:
        ArcadeWindow._dispatch_updates(self, delta_time)
        inputs.__update__(delta_time)