from __future__ import annotations
from pathlib import Path
from uuid import UUID, uuid4
from tomllib import load as load_toml

from jam.node.graph import BlockType, TestCase, STR_CAST, _variable

class Puzzle:
    __puzzles__: dict[str, Puzzle] = {}

    def __init__(
            self,
            name: str,
            title: str,
            description: str,
            available: tuple[BlockType, ...] | None,
            prerequisite_count: int,
            preequisite_levels: list[str],
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
        self.preequisite_levels: list[str] = preequisite_levels
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
    print(test_data)
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
        config_data['preequisite_levels'],
        input_type,
        output_type,
        graph,
        tests
    )

def write_puzzle(path: Path, puzzle: Puzzle) -> None:
    pass
