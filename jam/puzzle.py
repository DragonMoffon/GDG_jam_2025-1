from __future__ import annotations
from pathlib import Path
from importlib.resources import path
from tomllib import load as load_toml

from jam.node.graph import BlockType, TestCase, STR_CAST, _variable

import resources.puzzles as pzls

class Puzzle:
    __puzzles__: dict[str, Puzzle] = {}

    def __init__(
            self,
            name: str,
            title: str,
            description: str,
            available: tuple[BlockType, ...] | None,
            prerequisite_count: int,
            prerequisite_levels: list[str],
            input_type: BlockType,
            output_type: BlockType,
            source_graph: Path | None,
            tests: list[TestCase],
    ) -> None:
        self.name: str = name
        self.title: str = title
        self.description: str = description
        self.available: tuple[BlockType, ...] | None = available
        self.prerequisite_count: int = prerequisite_count
        self.prerequisite_levels: list[str] = prerequisite_levels
        self.input_type: BlockType = input_type
        self.output_type: BlockType = output_type
        self.source_graph: Path | None = source_graph
        self.tests: list[TestCase] = tests

        Puzzle.__puzzles__[self.name] = self

    @classmethod
    def get_puzzle(cls, name: str):
        if name not in cls.__puzzles__:
            return None
        return cls.__puzzles__[name]

def load_puzzle(path: Path) -> Puzzle:
    if path.stem in Puzzle.__puzzles__:
        puzzle = Puzzle.get_puzzle(path.stem)
        if puzzle is not None:
            return puzzle
    
    with open(path, "rb") as fp:
        raw_data = load_toml(fp)
    
    config_data = raw_data['Config']
    if 'available' in config_data:
        available = tuple(BlockType.__definitions__[typ] for typ in config_data['available'])
    else:
        available = None


    input_data = raw_data['Inputs']
    output_data = raw_data['Outputs']

    inputs = {name: STR_CAST[typ] for name, typ in input_data.items()}
    input_type = BlockType('Input', _variable, config=inputs.copy(), outputs=inputs.copy(), exclusive=True)

    outputs = {name: STR_CAST[typ] for name, typ in output_data.items()}
    output_type = BlockType('Output', _variable, inputs=outputs.copy(), exclusive=True)

    graph = config_data.get('base', None)
    if graph is not None:
        graph = path.parent / graph

    test_data: list[dict[str, dict[str, str | float | int | bool]]] = raw_data.get('Tests', [])
    tests: list[TestCase] = []
    for case in test_data:
        case_inputs = {name: inputs[name](value) for name, value in case['inputs'].items()}
        case_outputs = {name: outputs[name](value) for name, value in case['outputs'].items()}
        tests.append(TestCase(case_inputs, case_outputs))

    return Puzzle(
        config_data['name'],
        config_data['title'],
        config_data['description'],
        available,
        config_data['prerequisite_count'],
        config_data['prerequisite_levels'],
        input_type,
        output_type,
        graph,
        tests
    )

def write_puzzle(path: Path, puzzle: Puzzle) -> None:
    pass

class PuzzleCollection:

    def __init__(self, pth: Path) -> None:
        with open(pth, 'rb') as fp:
            raw_data = load_toml(fp)

        self._puzzles: dict[str, Puzzle] = {}
        self._pins: dict[str, tuple[tuple[float, float], tuple[float, float], int]] = {}

        for puzzle_path in pth.parent.glob('*.pzl'):
            try:
                puzzle = load_puzzle(puzzle_path)
                self._puzzles[puzzle.name] = puzzle
            except:
                continue

        for data in raw_data.get('Puzzle', []):
            target = data['puzzle']
            if target not in self._puzzles:
                continue
            self._pins[target] = (
                data['pin'],
                data['loc'],
                data['face']
            )

    def get_available_puzzles(self, count: int, completed: set[str]) -> list[Puzzle]:
        available: list[Puzzle] = []
        for puzzle in self._puzzles.values():
            if count < puzzle.prerequisite_count:
                continue
            req = completed.intersection(puzzle.prerequisite_levels)
            if len(req) != len(puzzle.prerequisite_levels):
                continue
            available.append(puzzle)

        return available
    
    def get_puzzle(self, name: str) -> Puzzle:
        return self._puzzles[name]
    
    def get_pin(self, puzzle: Puzzle) -> tuple[tuple[float, float], tuple[float, float], int]:
        return self._pins[puzzle.name]

with path(pzls, "puzzles.cfg") as pth:
    puzzles = PuzzleCollection(pth)