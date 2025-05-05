from __future__ import annotations
from typing import TYPE_CHECKING
from importlib.resources import path

import zipfile

from pathlib import Path
from uuid import UUID, uuid4

from jam.puzzle import Puzzle, PuzzleCollection, puzzles
from jam.controller import GraphController, write_graph_from_level

import resources.saves as save_path

if TYPE_CHECKING:
    from jam.gui.frame import FrameController
    from jam.views.game import GameView, LevelSelect
    from jam.views.game.comms import CommsFrame
    from jam.views.game.settings import SettingsFrame
    from jam.views.game.info import InfoFrame
    from jam.views.game.editor import EditorFrame


class SaveData:

    def __init__(self, source: zipfile.ZipFile, name: str = "1") -> None:
        self.name: str = name
        self._src: zipfile.ZipFile = source

        self._puzzle_solutions: dict[str, Path] = {}
        self._incomplete_puzzle_solutiohns: dict[str, Path] = {}
        self._completed_puzzles: list[Puzzle] = []
        self._sandbox_graphs: dict[str, Path] = {}

    def write(self) -> None:
        self._src.close()

    @property
    def completed_puzzles(self) -> tuple[Puzzle, ...]:
        return tuple(self._completed_puzzles)

    @property
    def completed_puzzle_names(self) -> tuple[str, ...]:
        return tuple(puzzle.name for puzzle in self._completed_puzzles)

    @property
    def completed_count(self) -> int:
        return len(self._completed_puzzles)

    @property
    def compeleted_graphs(self) -> tuple[Path, ...]:
        return tuple(self._puzzle_solutions)

    @property
    def incomplete_graphs(self) -> tuple[Path, ...]:
        return tuple(self._incomplete_puzzle_solutiohns)

    @property
    def sandbox_graphs(self) -> tuple[Path, ...]:
        return tuple(self._sandbox_graphs)

    def complete_puzzle(self, puzzle: Puzzle, solution: GraphController) -> None:
        self._completed_puzzles.append(puzzle)
        puzzle_pth = zipfile.Path(self._src)
        pth = write_graph_from_level(solution, puzzle, puzzle_pth)
        self._puzzle_solutions[puzzle.name] = pth

    def completed(self, puzzle: Puzzle) -> bool:
        return puzzle.name in self._puzzle_solutions


def read_savedata(pth: Path) -> SaveData:
    source = zipfile.ZipFile(pth)
    name = pth.stem
    save_data = SaveData(source, name)

    return save_data


def new_savedata(name: str, origin: Path) -> SaveData:
    source = zipfile.ZipFile(origin / f"{name}.svd", "x")
    return SaveData(source, name)


class Context:

    def __init__(self) -> None:

        with path(save_path, "save.cfg") as save_config:
            self._save_path: Path = Path(save_config).parent
        self._saves: dict[str, SaveData] = {}
        for save in self._save_path.glob("*.svd"):
            save_data = read_savedata(save)
            self._saves[save_data.name] = save_data

        self._current_save: SaveData | None = None

        self._frame_controller: FrameController | None = None
        self._editor_frame: EditorFrame | None = None
        self._info_frame: InfoFrame | None = None
        self._comms_frame: CommsFrame | None = None
        self._settings_frame: SettingsFrame | None = None

        self._level_select: LevelSelect | None = None

    def close(self) -> None:
        for save in self._saves.values():
            save.write()

    def get_save_names(self) -> tuple[str, ...]:
        return tuple(name for name in self._saves)

    def new_save(self) -> None:
        name = str(len(self._saves))
        self._saves[name] = self._current_save = new_savedata(name, self._save_path)

    def choose_first_save(self) -> None:
        if not self._saves:
            self.new_save()
            return
        self.choose_save("0")

    def choose_save(self, name: str) -> None:
        self._current_save = self._saves[name]

    def set_frames(
        self,
        controller: FrameController,
        editor: EditorFrame,
        info: InfoFrame,
        comms: CommsFrame,
        settings: SettingsFrame,
    ) -> None:
        self._frame_controller = controller
        self._editor_frame = editor
        self._info_frame = info
        self._comms_frame = comms
        self._settings_frame = settings

    def set_level_select(self, select: LevelSelect) -> None:
        self._level_select = select

    def clear_frames(self) -> None:
        self._frame_controller = None
        self._editor_frame = None
        self._info_frame = None
        self._comms_frame = None
        self._settings_frame = None

    def clear_level_select(self) -> None:
        self._level_select = None

    def open_editor_tab(
        self, puzzle: Puzzle | None = None, graph_src: Path | None = None
    ) -> None:
        if self._editor_frame is None:
            return
        self._editor_frame.open_editor(puzzle, graph_src)

    def close_editor_tab(self, name: str) -> None:
        if self._editor_frame is None:
            return
        self._editor_frame.close_editor(name)

    def hide_frame(self) -> None:
        if self._frame_controller is None:
            return
        self._frame_controller.deselect_frame()

    def show_editor_frame(self) -> None:
        if self._frame_controller is None or self._editor_frame is None:
            return
        self._frame_controller.select_frame(self._editor_frame)

    def show_info_frame(self) -> None:
        if self._frame_controller is None or self._info_frame is None:
            return
        self._frame_controller.select_frame(self._info_frame)

    def show_comms_frame(self) -> None:
        if self._frame_controller is None or self._comms_frame is None:
            return
        self._frame_controller.select_frame(self._comms_frame)

    def show_settings_frame(self) -> None:
        if self._frame_controller is None or self._settings_frame is None:
            return
        self._frame_controller.select_frame(self._settings_frame)

    def complete_puzzle(self, puzzle: Puzzle, solution: GraphController) -> None:
        if self._current_save is None:
            return
        self._current_save.complete_puzzle(puzzle, solution)
        self.close_editor_tab(puzzle.title)
        self.hide_frame()
        if self._level_select is not None:
            self._level_select.clear_puzzle(puzzle)

    def get_available_puzzles(self) -> tuple[Puzzle, ...]:
        if self._current_save is None:
            return []
        available = puzzles.get_available_puzzles(
            self._current_save.completed_count,
            set(self._current_save.completed_puzzle_names),
        )
        return tuple(p for p in available if not self._current_save.completed(p))


context = Context()
