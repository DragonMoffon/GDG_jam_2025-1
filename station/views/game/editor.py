from pathlib import Path
from pyglet.graphics import Group

from station.gui.core import Element
from station.gui.frame import Frame

from station.editor.base import Editor
from station.editor.sandbox import SandboxEditor

class EditorFrame(Frame):

    def __init__(
            self,
            offset: float,
            height: float,
            show_body: bool = False,
            show_shadow: bool = True,
            parent: Element | None = None,
            layer: Group | None = None
        ):
        size = (1000, height)
        Frame.__init__(self, 'EDITOR', offset, size, show_body, show_shadow, True, parent, layer)

        self._editor: Editor | None = None

    def open_sandbox(self):
        if self.gui is None:
            return
        size = int(self.clip_rect.width), int(self.clip_rect.height)
        self._editor = SandboxEditor(size, self.gui, self.clip_layer, Path()/"connect_mainbus.blk")
