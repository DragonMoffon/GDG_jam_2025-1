from __future__ import annotations
from pyglet.graphics import Group

from station.gui import GUI
from station.controller import GraphController
from station.puzzle import Puzzle

from .base import Editor
from .modes import NoneMode


class PuzzleEditor(Editor):

    def __init__(
        self,
        puzzle: Puzzle,
        size: tuple[int, int],
        gui: GUI,
        layer: Group | None = None,
    ) -> None:
        initial = PuzzleNoneMode(self)
        Editor.__init__(self, size, initial, gui, layer)
        self._puzzle: Puzzle = puzzle

    @property
    def puzzle(self) -> Puzzle:
        return self._puzzle


class PuzzleNoneMode(NoneMode[PuzzleEditor]): ...
