from __future__ import annotations
from typing import TYPE_CHECKING, Any
from pathlib import Path
from importlib.resources import path
from time import time_ns as get_time
from datetime import datetime
from os import mkdir
from shutil import rmtree

import traceback
import zipfile
from tomllib import load as load_toml
from tomlkit import dumps as dumps_toml

from jam.puzzle import Puzzle, puzzles
from jam.controller import GraphController, write_graph_from_level, write_graph

from resources import style

try:
    import resources.saves as save_path
except ModuleNotFoundError:
    import resources as rcs

    with path(rcs, "saves") as pth:
        pth.mkdir(exist_ok=True)

    import resources.saves as save_path

if TYPE_CHECKING:
    from jam.gui.frame import FrameController
    from jam.views.game import LevelSelect
    from jam.views.game.comms import CommsFrame
    from jam.views.game.settings import SettingsFrame
    from jam.views.game.info import InfoFrame
    from jam.views.game.editor import EditorFrame


class SaveData:

    def __init__(self, root: Path, info: SaveInfo) -> None:
        self._root: Path = root
        self._target: Path = info.path

        self._name: str = info.name
        self._creation_time: int = info.creation_time
        self._last_open_time: int = get_time()

        self._complete: dict[str, str] = info.completed_puzzles
        self._incomplete: dict[str, str] = info.incompleted_puzzles
        self._sandbox: dict[str, str] = info.sandbox_graphs

        self._tabs: list[str] = info.tabs

        self.update_cfg()

    @property
    def name(self) -> str:
        return self._name

    @property
    def creation_time(self) -> int:
        return self._creation_time

    @property
    def last_open_time(self) -> int:
        return self._last_open_time

    @property
    def completed(self) -> tuple[str, ...]:
        return tuple(self._complete)

    def has_completed(self, name: str) -> bool:
        return name in self._complete

    @property
    def incompleted(self) -> tuple[str, ...]:
        return tuple(self._incomplete)

    @property
    def sandbox(self) -> tuple[str, ...]:
        return tuple(self._sandbox)

    @property
    def number_completed(self) -> int:
        return len(self._complete)

    @property
    def number_attempted(self) -> int:
        return len(self._complete) + len(self._incomplete)

    def save_puzzle(self, puzzle: Puzzle, solution: GraphController) -> None:
        if puzzle.name in self._complete:
            return  # TODO: discuss what to do when saving an already solved puzzle?? (turn into sandbox but _how_?)
        target = f"{puzzle.name}.blk"
        pth = self._root / target
        self._incomplete[puzzle.name] = target
        write_graph_from_level(solution, puzzle, pth)
        self.update_cfg()

    def save_sandbox(self, graph: GraphController, name: str | None = None) -> None:
        if name is None:
            name = f"sandbox_{len(self._sandbox)}"
        target = f"{name}.blk"
        pth = self._root / target
        self._sandbox[name] = target
        write_graph(graph, pth)
        self.update_cfg()

    def complete_puzzle(self, puzzle: Puzzle, solution: GraphController) -> None:
        target = f"{puzzle.name}.blk"
        pth = self._root / target
        if puzzle.name in self._incomplete:
            self._incomplete.pop(puzzle.name)
            pth.unlink()
        self._complete[puzzle.name] = target
        write_graph_from_level(solution, puzzle, pth)
        self.update_cfg()

    def _update_cfg(self) -> str:
        return dumps_toml(
            {
                "Info": {
                    "name": self.name,
                    "creation_time": self.creation_time,
                    "last_open_time": self.last_open_time,
                    "tabs": self._tabs,
                },
                "Complete": self._complete,
                "Incomplete": self._incomplete,
                "Sandbox": self._sandbox,
            }
        )

    def update_cfg(self) -> None:
        with open(self._root / "save.cfg", "w") as fp:
            fp.write(self._update_cfg())

    def update_save(self) -> None:
        with zipfile.ZipFile(self._target, "w") as zip:
            zip.writestr("save.cfg", self._update_cfg())
            for item in self._complete.values():
                zip.write(self._root / item, item)
            for item in self._incomplete.values():
                zip.write(self._root / item, item)
            for item in self._sandbox.values():
                zip.write(self._root / item, item)

    def close_save(self) -> None:
        self.update_save()
        rmtree(self._root)

    def log_fatal_exception(self, exception: Exception):
        crash_time = datetime.now().strftime("%Y-%m-%d %H-%M")
        self.update_cfg()
        with open(self._root / "crash_log.txt", "w", encoding="utf-8") as fp:
            fp.write("".join(traceback.format_exception(exception)))
        self._root.rename(self._root.parent / f"crash-{crash_time}_{self._name}")


class SaveInfo:

    def __init__(self, pth: Path, cfg: dict[str, Any] | None = None) -> None:
        self._path: Path = pth
        if cfg is None:
            with zipfile.ZipFile(self._path, "r") as zip:
                with zip.open("save.cfg", "r") as fp:
                    cfg = load_toml(fp)
        self._name: str = cfg["Info"]["name"]
        self._creation_time: int = cfg["Info"]["creation_time"]
        self._last_open_time: int = cfg["Info"]["last_open_time"]

        self._complete_puzzles: dict[str, str] = cfg["Complete"]
        self._incomplete_puzzles: dict[str, str] = cfg["Incomplete"]
        self._sandbox_graphs: dict[str, str] = cfg["Sandbox"]

        self._tabs: list[str] = cfg["Info"]["tabs"]

    @property
    def name(self) -> str:
        return self._name

    @property
    def path(self) -> Path:
        return self._path

    @property
    def creation_time(self) -> int:
        return self._creation_time

    @property
    def last_open_time(self) -> int:
        return self._last_open_time

    @property
    def tabs(self) -> list[str]:
        return self._tabs.copy()

    @property
    def completed(self) -> tuple[str, ...]:
        return tuple(self._complete_puzzles)

    @property
    def completed_puzzles(self) -> dict[str, str]:
        return self._complete_puzzles.copy()

    def get_completed(self, name: str) -> str:
        return self._complete_puzzles[name]

    def has_completed(self, name: str) -> bool:
        return name in self._complete_puzzles

    @property
    def incompleted(self) -> tuple[str, ...]:
        return tuple(self._incomplete_puzzles)

    @property
    def incompleted_puzzles(self) -> dict[str, str]:
        return self._incomplete_puzzles.copy()

    def get_incompleted(self, name: str) -> str:
        return self._incomplete_puzzles[name]

    @property
    def sandbox(self) -> tuple[str, ...]:
        return tuple(self._sandbox_graphs)

    @property
    def sandbox_graphs(self) -> dict[str, str]:
        return self._sandbox_graphs.copy()

    def get_sandbox(self, name: str) -> str:
        return self._sandbox_graphs[name]

    @property
    def number_completed(self) -> int:
        return len(self._complete_puzzles)

    @property
    def number_attempted(self) -> int:
        return len(self._complete_puzzles) + len(self._incomplete_puzzles)

    @classmethod
    def create_new_save(cls, name: str, root: Path) -> SaveInfo:
        pth = root / f"{name}.svd"
        cfg: dict[str, Any] = {
            "Info": {},
            "Complete": {},
            "Incomplete": {},
            "Sandbox": {},
        }
        cfg["Info"]["name"] = name
        cfg["Info"]["creation_time"] = get_time()
        cfg["Info"]["last_open_time"] = get_time()
        cfg["Info"]["tabs"] = []
        with zipfile.ZipFile(pth, "x") as zip:
            zip.writestr("save.cfg", dumps_toml(cfg))
        return cls(pth, cfg)

    def open_save(self) -> SaveData:
        pth = self._path.parent / ".save"
        # Protect against the game not cleaning up the save folder.
        # It sucks we have to do this, but there is no deleting from a zip folder so yippeeeee
        if pth.exists():
            with open(pth / "save.cfg", "rb") as fp:
                cfg = load_toml(fp)
            launch_time = datetime.fromtimestamp(cfg["Info"]["last_open_time"] * 1e-9)
            pth.rename(
                self._path.parent
                / f"crash-{launch_time.strftime("%Y-%m-%d %H-%M")}_{cfg['Info']['name']}"
            )

        with zipfile.ZipFile(self._path, "r") as zip:
            mkdir(pth)
            zip.extractall(pth)
        return SaveData(pth, self)


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

    @property
    def save(self) -> SaveData | None:
        return self._current_save

    def close(self) -> None:
        if self._current_save is None:
            return

        self._current_save.close_save()
        # for save in self._saves.values():
        #     save.write()

    def get_save_names(self) -> tuple[str, ...]:
        return tuple(name for name in self._saves)

    def new_save(self) -> None:
        name = datetime.now().strftime("%Y-%m-%d %H-%M")
        self._saves[name] = SaveInfo.create_new_save(name, self._save_path)
        self.choose_save(name)

    def choose_first_save(self) -> None:
        oldest = 0
        name = None
        for save in self._saves.values():
            if save.last_open_time > oldest:
                oldest = save.last_open_time
                name = save.name
        if name is None:
            self.new_save()
            return
        self.choose_save(name)

    def choose_save(self, name: str) -> None:
        self._current_save = self._saves[name].open_save()

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
            return None
        self._current_save.complete_puzzle(puzzle, solution)
        self.close_editor_tab(puzzle.title)
        self.hide_frame()
        style.audio.confirm.play()
        if self._level_select is not None:
            self._level_select.clear_puzzle(puzzle)

    def get_available_puzzles(self) -> tuple[Puzzle, ...]:
        if self._current_save is None:
            return []
        available = puzzles.get_available_puzzles(
            self._current_save.number_completed,
            set(self._current_save.completed),
        )
        return tuple(
            puzzle
            for puzzle in available
            if not self._current_save.has_completed(puzzle.name)
        )

    def get_open_puzzle(self) -> Puzzle | None:
        if self._editor_frame is None:
            return None

        # TODO: AHHHHH
        return self._editor_frame._active_editor._puzzle


context = Context()
