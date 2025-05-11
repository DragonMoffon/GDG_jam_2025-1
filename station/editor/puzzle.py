from __future__ import annotations

from .core import Editor, EditorMode


class PuzzleEditor(Editor):

    def __init__(self) -> None:
        initial = PuzzleNoneMode(self)
        Editor.__init__(self, initial)


class PuzzleNoneMode(EditorMode[PuzzleEditor]): ...
