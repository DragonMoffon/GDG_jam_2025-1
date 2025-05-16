from __future__ import annotations
from pathlib import Path

from pyglet.graphics import Group

from station.gui import GUI
from station.controller import read_graph
from .base import Editor, EditorMode


class SandboxEditor(Editor):

    def __init__(self, gui: GUI, layer: Group | None, source_path: Path) -> None:
        initial = SandboxNoneMode(self)
        Editor.__init__(self, initial, gui, layer, read_graph(source_path, gui, True))


class SandboxNoneMode(EditorMode[SandboxEditor]): ...
