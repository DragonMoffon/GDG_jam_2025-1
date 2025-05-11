from __future__ import annotations

from .core import Editor, EditorMode


class SandboxEditor(Editor):

    def __init__(self) -> None:
        initial = SandboxNoneMode(self)
        Editor.__init__(self, initial)


class SandboxNoneMode(EditorMode[SandboxEditor]): ...
