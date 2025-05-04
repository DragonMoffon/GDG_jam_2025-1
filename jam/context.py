from __future__ import annotations
from typing import TYPE_CHECKING

from pathlib import Path
from uuid import UUID, uuid4

if TYPE_CHECKING:
    from jam.gui.frame import FrameController
    from jam.views.game import GameView
    from jam.views.game.comms import CommsFrame
    from jam.views.game.settings import SettingsFrame
    from jam.views.game.info import InfoFrame
    from jam.views.game.editor import EditorFrame

    from jam.puzzle import Puzzle, PuzzleCollection

class SaveData:

    def __init__(self, uid: UUID | None) -> None:
        self.uid: UUID = uid or uuid4()

        self._puzzle_solutions: dict[str, Puzzle] = {}
        self._incomplete_puzzle_solutiohns: dict[str, Puzzle] = {}
        self._completed_puzzles: list[Puzzle] = []
        self._sandbox_graphs: dict[str, Path] = {}

    @property
    def completed_puzzles(self):
        pass

    @property
    def completed_count(self):
        pass

    @property
    def compeleted_graphs(self):
        pass

    @property
    def incomplete_graphs(self):
        pass

    @property
    def sandbox_graphs(self):
        pass

    def get_puzzle_solution(self, puzzle: str):
        pass

    def get_graph(self, graph_name: str):
        pass

class Context:

    def __init__(self) -> None:
        self._current_save: SaveData | None = None

        self._frame_controller: FrameController | None = None
        self._editor_frame: EditorFrame | None = None
        self._info_frame: InfoFrame | None = None
        self._comms_frame: CommsFrame | None = None
        self._settings_frame: SettingsFrame | None = None
    
    def set_frames(self, controller: FrameController, editor: EditorFrame, info: InfoFrame, comms: CommsFrame, settings: SettingsFrame):
        self._frame_controller = controller
        self._editor_frame = editor
        self._info_frame = info
        self._comms_frame = comms
        self._settings_frame = settings

    def clear_frames(self):
        self._frame_controller = None
        self._editor_frame = None
        self._info_frame = None
        self._comms_frame = None
        self._settings_frame = None

    def open_editor_tab(self, puzzle: Puzzle | None = None, graph_src: Path | None = None):
        if self._editor_frame is None:
            return
        self._editor_frame.open_editor(puzzle, graph_src)

    def show_editor_frame(self):
        if self._frame_controller is None or self._editor_frame is None:
            return
        self._frame_controller.select_frame(self._editor_frame)

    def show_info_frame(self):
        if self._frame_controller is None or self._info_frame is None:
            return
        self._frame_controller.select_frame(self._info_frame)

    def show_comms_frame(self):
        if self._frame_controller is None or self._comms_frame is None:
            return
        self._frame_controller.select_frame(self._comms_frame)

    def show_settings_frame(self):
        if self._frame_controller is None or self._settings_frame is None:
            return
        self._frame_controller.select_frame(self._settings_frame)

context = Context()