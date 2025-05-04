from jam.gui.frame import Frame

class InfoFrame(Frame):

    def __init__(self, tag_offset: float, position: tuple[float, float], height: float, show_body: bool = False, show_shadow: bool = True):
        super().__init__("INFO", tag_offset, position, (450, height), show_body, show_shadow, True)