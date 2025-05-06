from __future__ import annotations
from typing import TYPE_CHECKING, Any
from importlib.resources import path
from time import time_ns as get_time
from os import mkdir

import zipfile
from tomllib import load as load_toml
from tomlkit import dumps as dumps_toml

from pathlib import Path

from jam.puzzle import Puzzle, puzzles
from jam.controller import GraphController, write_graph_from_level

import resources.saves as save_path

if TYPE_CHECKING:
    from jam.gui.frame import FrameController
    from jam.views.game import LevelSelect
    from jam.views.game.comms import CommsFrame
    from jam.views.game.settings import SettingsFrame
    from jam.views.game.info import InfoFrame
    from jam.views.game.editor import EditorFrame


class SaveData:

    def __init__(self, source: zipfile.ZipFile, name: str = "1") -> None:
        self.name: str = name
        self._src: zipfile.ZipFile = source

        self._puzzle_solutions: dict[str, Path | zipfile.Path] = {}
        self._incomplete_puzzle_solutions: dict[str, Path | zipfile.Path] = {}
        self._completed_puzzles: list[Puzzle] = []
        self._sandbox_graphs: dict[str, Path | zipfile.Path] = {}

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
    def completed_graphs(self) -> tuple[Path | zipfile.Path, ...]:
        return tuple(self._puzzle_solutions.values())

    @property
    def incomplete_graphs(self) -> tuple[Path | zipfile.Path, ...]:
        return tuple(self._incomplete_puzzle_solutions.values())

    @property
    def sandbox_graphs(self) -> tuple[Path | zipfile.Path, ...]:
        return tuple(self._sandbox_graphs.values())

    def complete_puzzle(self, puzzle: Puzzle, solution: GraphController) -> None:
        self._completed_puzzles.append(puzzle)
        puzzle_pth = zipfile.Path(self._src, f"{puzzle.name}.pzl")
        write_graph_from_level(solution, puzzle, puzzle_pth)
        self._puzzle_solutions[puzzle.name] = puzzle_pth

    def save_incomplete(self, puzzle: Puzzle, working: GraphController) -> None:
        pass

    def completed(self, puzzle: Puzzle) -> bool:
        return puzzle.name in self._puzzle_solutions
    
    def close_save(self):
        pass


class SaveInfo:

    def __init__(self, pth: Path, cfg: dict[str, Any] | None = None) -> None:
        self._path: Path = pth
        if cfg is None:
            with zipfile.ZipFile(self._path, 'r') as zip:
                with zip.open('save.cfg', 'r') as fp:
                    cfg = load_toml(fp)
        self._name: str = cfg['Info']['name']
        self._creation_time: int = cfg['Info']['creation_time']
        self._last_launch_time: int = cfg['Info']['last_open_time']

        self._complete_puzzles: dict[str, str] = cfg['Complete']
        self._incomplete_puzzles: dict[str, str] = cfg['Incomplete']
        self._sandbox_graphs: dict[str, str] = cfg['Sandbox']

    @property
    def name(self) -> str: return self._name
    
    @property
    def creation_time(self) -> int: return self._creation_time

    @property
    def last_launch_time(self) -> int: return self._last_launch_time

    @classmethod
    def create_new_save(cls, name: str, root: Path) -> SaveInfo:
        pth = root / f"{name}.svd"
        with open(root / 'save.cfg', 'rb') as fp:
            cfg = load_toml(fp)
        cfg['Info']['name'] = name
        cfg['Info']['creation_time'] = get_time()
        cfg['Info']['last_open_time'] = get_time()
        with zipfile.ZipFile(pth, 'x') as zip:
            zip.writestr('save.cfg', dumps_toml(cfg))
        return cls(pth, cfg)
    
    def open_save(self) -> SaveData:
        with zipfile.ZipFile(self._path, 'r') as zip:
            pth = self._path.parent / 'save'
            mkdir(pth)
            zip.extractall(pth)

class Context:

    def __init__(self) -> None:

        with path(save_path, "save.cfg") as save_config:
            self._save_path: Path = Path(save_config).parent
        self._saves: dict[str, SaveInfo] = {}
        for save in self._save_path.glob("*.svd"):
            save_data = SaveInfo(save)
            self._saves[save_data.name] = save_data

        self._current_save: SaveData | None = None

        self._frame_controller: FrameController | None = None
        self._editor_frame: EditorFrame | None = None
        self._info_frame: InfoFrame | None = None
        self._comms_frame: CommsFrame | None = None
        self._settings_frame: SettingsFrame | None = None

        self._level_select: LevelSelect | None = None

    def close(self) -> None:
        self._current_save.close_save()
        # for save in self._saves.values():
        #     save.write()

    def get_save_names(self) -> tuple[str, ...]:
        return tuple(name for name in self._saves)

    def new_save(self) -> None:
        name = str(len(self._saves))
        self._saves[name] = SaveInfo.create_new_save(name, self._save_path)
        self.choose_save(name)

    def choose_first_save(self) -> None:
        if not self._saves:
            self.new_save()
            return
        self.choose_save("0")

    def choose_save(self, name: str) -> None:
        self._current_save = self._saves[name].open_save()
        # self._current_save = self._saves[name]

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

    def get_open_puzzle(self) -> Puzzle | None:
        if self._editor_frame is None:
            return

        # TODO: AHHHHH
        return self._editor_frame._active_editor._puzzle


context = Context()
