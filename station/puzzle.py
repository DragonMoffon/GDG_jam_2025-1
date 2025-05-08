from __future__ import annotations
from pathlib import Path
from enum import IntEnum
from importlib.resources import path
from tomllib import load as load_toml
from dataclasses import dataclass

from station.node.graph import BlockType, TestCase, OperationValue, STR_CAST, TYPE_CAST, _variable
import station.node.blocks  # noqa: F401 -- importing sets up the blocks

import resources.puzzles as pzls
from resources import Style
from resources.audio import Sound


class AlertOrientation(IntEnum):
    LEFT = 0
    TOP = 1
    RIGHT = 2
    BOTTOM = 3


@dataclass
class PuzzleAlert:
    pin: tuple[float, float] = (0.0, 0.0)
    loc: tuple[float, float] = (0.0, 0.0)
    pin_orientation: AlertOrientation = AlertOrientation.LEFT
    loc_orientation: AlertOrientation = AlertOrientation.RIGHT


@dataclass
class Puzzle:
    name: str
    title: str
    short_description: str
    description: str
    alert: PuzzleAlert
    ambience: Sound | None
    available: tuple[BlockType, ...] | None
    prerequisite_count: int
    prerequisite_levels: tuple[str, ...]
    input_type: BlockType
    output_type: BlockType
    constant_type: BlockType | None
    constant_values: dict[str, OperationValue]
    source_graph: Path | None
    tests: tuple[TestCase, ...]


def load_puzzle(path: Path) -> Puzzle:
    with open(path, "rb") as fp:
        raw_data = load_toml(fp)

    config_data = raw_data["Config"]

    if "ambience" in config_data:
        ambience = Style.Audio.Ambience[config_data["ambience"]]
    else:
        ambience = None

    if "available" in config_data:
        available = tuple(
            BlockType.__definitions__[typ] for typ in config_data["available"]
        )
    else:
        available = None

    input_data = raw_data["Inputs"]
    output_data = raw_data["Outputs"]
    const_data = raw_data.get("Constants", {})

    inputs = {name: STR_CAST[typ] for name, typ in input_data.items()}
    input_type = BlockType(
        "Input", _variable, config=inputs.copy(), outputs=inputs.copy(), exclusive=True
    )

    outputs = {name: STR_CAST[typ] for name, typ in output_data.items()}
    output_type = BlockType("Output", _variable, inputs=outputs.copy(), exclusive=True)

    if const_data:
        const_types = {name: TYPE_CAST[type(value)] for name, value in const_data.items()}
        const_values = {name: const_types[name](value) for name, value in const_data.items()}
        const_type = BlockType(
            "Constant", _variable, outputs=const_types.copy(), config=const_types.copy(), exclusive=True
        )
    else:
        const_values = {}
        const_type = None

    graph = config_data.get("base", None)
    if graph is not None:
        graph = path.parent / graph

    test_data: list[dict[str, dict[str, str | float | int | bool]]] = raw_data.get(
        "Tests", []
    )
    tests: list[TestCase] = []
    for case in test_data:
        case_inputs = {
            name: inputs[name](value) for name, value in case["inputs"].items()
        }
        case_outputs = {
            name: outputs[name](value) for name, value in case["outputs"].items()
        }
        tests.append(TestCase(case_inputs, case_outputs))

    alert_data = raw_data["Alert"]
    alert = PuzzleAlert(
        tuple(alert_data["pin"]),
        tuple(alert_data["loc"]),
        AlertOrientation(alert_data["pin_orientation"]),
        AlertOrientation(alert_data["loc_orientation"]),
    )

    return Puzzle(
        name=config_data["name"],
        title=config_data["title"],
        short_description=config_data["short_description"],
        description=config_data["description"],
        alert=alert,
        ambience=ambience,
        available=available,
        prerequisite_count=config_data.get("prerequisite_count", 0),
        prerequisite_levels=config_data.get("prerequisite_levels", []),
        input_type=input_type,
        output_type=output_type,
        constant_type=const_type,
        constant_values=const_values,
        source_graph=graph,
        tests=tuple(tests),
    )


class PuzzleCollection:

    def __init__(self, pth: Path) -> None:
        self._puzzles: dict[str, Puzzle] = {}
        self._pins: dict[str, tuple[tuple[float, float], tuple[float, float], int]] = {}

        for puzzle_path in Path(pth.parent).glob("*.pzl"):
            try:
                puzzle = load_puzzle(puzzle_path)
                self._puzzles[puzzle.name] = puzzle
            except Exception as e:
                print(f"{puzzle_path}: {e}")

    def get_available_puzzles(
        self, count: int, completed: set[str]
    ) -> tuple[Puzzle, ...]:
        available: list[Puzzle] = []
        for puzzle in self._puzzles.values():
            if count < puzzle.prerequisite_count:
                continue
            req = completed.intersection(puzzle.prerequisite_levels)
            if len(req) != len(puzzle.prerequisite_levels):
                continue
            available.append(puzzle)

        return tuple(available)

    def get_puzzle(self, name: str) -> Puzzle:
        return self._puzzles[name]


with path(pzls, "puzzles.cfg") as pth:
    puzzles = PuzzleCollection(pth)
