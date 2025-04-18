from jam.gui.frame import Frame


class EditorFrame(Frame):

    def __init__(self, tag_offset: float, position: tuple[float, float], height: float, show_body: bool = False, show_shadow: bool = True):
        size = 1000, height
        Frame.__init__(self, 'EDITOR', tag_offset, position, size, show_body, show_shadow)