from __future__ import annotations
from typing import TYPE_CHECKING

from pathlib import Path
from uuid import UUID, uuid4

if TYPE_CHECKING:
    from jam.views.game import GameView
    from jam.views.game.comms import CommsFrame
    from jam.views.game.settings import SettingsFrame
    from jam.views.game.info import InfoFrame
    from jam.views.game.editor import EditorFrame

class SaveData:

    def __init__(self, uid: UUID | None) -> None:
        self.uid: UUID = uid or uuid4()

    @property
    def completed_puzzles(self):
        pass

    @property
    def completed_count(self):
        pass

    def get_puzzle_solution(self, puzzle: str):
        pass

    def get_graph(self, graph_name: str):
        pass

class Context:

    def __init__(self) -> None:
        self._editor_frame: EditorFrame | None = None
        self._info_frame: InfoFrame | None = None
        self._comms_frame: CommsFrame | None = None
        self._settings_frame: SettingsFrame | None = None
    
    def set_frames(self, editor: EditorFrame, info: InfoFrame, comms: CommsFrame, settings: SettingsFrame):
        self._editor_frame = editor
        self._info_frame = info
        self._comms_frame = comms
        self._settings_frame = settings

    def clear_frames(self):
        self._editor_frame = None
        self._info_frame = None
        self._comms_frame = None
        self._settings_frame = None

    def open_editor_tab(self, puzzle_src: Path | None = None, graph_src: Path | None = None): ...

    def show_editor_frame(self): ...
    def show_info_frame(self): ...
    def show_comms_frame(self): ...
    def show_settings_frame(self): ...

context = Context()