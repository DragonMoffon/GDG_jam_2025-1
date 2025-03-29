from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Self, Sequence
from enum import Enum, StrEnum
from uuid import uuid4, UUID

number = int | float


class Var:
    __value__: Var = None

    def __new__(cls):
        if cls.__value__ is None:
            cls.__value__ = object.__new__(cls)
        return cls.__value__

    def __str__(self):
        return "Var"


class CastableTypes(Enum):
    BOOL = bool
    INT = int
    FLOAT = float

    def __str__(self):
        return str(self.value.__name__)


class ComparisonOpperators(StrEnum):
    LT = "<"
    GT = ">"
    LE = "<="
    GE = ">="
    NE = "!="
    EQ = "=="


DEFAULTS: dict[type, Any] = {
    int: 0,
    float: 0.0,
    bool: False,
    number: 0,
    Var: Var(),
    CastableTypes: CastableTypes.BOOL,
    ComparisonOpperators: ComparisonOpperators.EQ,
}


def get_type_default[T](typ: type[T]) -> T:
    return DEFAULTS[typ]


class Block:
    inputs: dict[str, type] = {}
    outputs: dict[str, type] = {}
    config: dict[str, type] = {}

    def __init__(self, name: str | None = None, uid: UUID | None = None):
        self._uid: UUID = uid or uuid4()
        self._results: dict[str, Any] = {
            name: get_type_default(typ) for name, typ in self.outputs.items()
        }
        self._arguments: dict[str, Any] = {
            name: get_type_default(typ) for name, typ in self.inputs.items()
        }
        self._configuration: dict[str, Any] = {
            name: get_type_default(typ) for name, typ in self.config.items()
        }
        self._stale: bool = False
        self._name: str = name or self.__class__.__name__

    def __repr__(self) -> str:
        return f"{self}{self._arguments}{self._results}"

    def __str__(self) -> str:
        return f"{self.name}<{self.uid}>"

    @property
    def uid(self) -> UUID:
        return self._uid

    @property
    def name(self) -> str:
        return self._name

    def __getitem__(self, name: str):
        if name not in self.outputs:
            raise KeyError(f"{name} is not an output of the {self.name} Block")

        # If stale update the values
        if self._stale:
            self()
            self._stale = False

        return self._results[name]

    def __setitem__(self, name: str, value: Any):
        if name not in self.inputs:
            raise KeyError(f"{name} is not an argument of the {self.name} Block")
        assert isinstance(
            value, self.inputs[name]
        ), f"{type(value)} is not the type for the input {name} in the {self.name} Block"

        if self._arguments[name] == value:
            return

        self._arguments[name] = value
        self._stale = True

    def set_config(self, name: str, value: Any):
        if name not in self.config:
            raise KeyError(f"{name} is not a config of the {self.name} Block")
        assert isinstance(
            value, self.config[name]
        ), f"{type(value)} is not the type for the config {name} in the {self.name} Block"

        if self._configuration[name] == value:
            return

        self._configuration[name] = value
        self._stale = True

    def func(self, **kwargs) -> dict[str, Any]:
        return {}

    def __call__(self) -> dict[str, Any]:
        rslt = self.func(**self._arguments)
        self._results.update(rslt)
        return rslt


@dataclass
class Connection:
    source: Block
    output: str

    target: Block
    input: str

    uid: UUID = field(default_factory=uuid4)


class Graph:

    def __init__(self):
        self._blocks: dict[UUID, Block] = {}
        self._connections: dict[UUID, Connection] = {}

        self._inputs: dict[UUID, dict[str, UUID]] = {}
        self._outputs: dict[UUID, dict[str, list[UUID]]] = {}

    def add_connection(self, connection: Connection) -> Connection | None:
        inputs = self._inputs[connection.target.uid]
        outputs = self._outputs[connection.source.uid]
        old = None
        if connection.input in inputs:
            old = self._connections[inputs[connection.input]]
            self._outputs[old.source.uid][old.output].remove(old.uid)
            del self._connections[old.uid]

        inputs[connection.input] = connection.uid
        outputs[connection.output].append(connection.uid)
        self._connections[connection.uid] = connection

        return old

    def remove_connection(self, connection: Connection):
        inputs = self._inputs[connection.target.uid]
        outputs = self._outputs[connection.source.uid]

        outputs[connection.output].remove(connection)
        del inputs[connection.input]
        del self._connections[connection.uid]

    def add_block(self, block: Block):
        self._blocks[block.uid] = block

        self._inputs[block.uid] = {}
        self._outputs[block.uid] = {name: [] for name in block.outputs}

    def remove_block(self, block: Block):
        for connection in self._inputs[block.uid].values():
            self.remove_connection(connection)

        for outputs in self._outputs[block.uid].values():
            for connection in outputs:
                self.remove_connection(connection)

        del self._inputs[block.uid]
        del self._outputs[block.uid]

    def compute(self, target: Block):
        """
        Starting from the target block we walk backwards through the connections
        building a directed connection graph which we then run through forwards.
        This has the benefit of skipping blocks that aren't connected to the output
        even if they're in the graph.

        This can take any block in the graph so for debugging you can query
        any block.
        """

        depths: dict[UUID, int] = {}

        def _find_predicessors(block: Block, seen: set = set()):
            if block.uid in depths:
                return depths[block.uid] + 1

            if block.uid in seen:
                raise RecursionError(f"Block {block} references itself")
            seen = seen.union({block.uid})

            depth = 0

            connections = self._inputs[block.uid]
            for uid in connections.values():
                connection = self._connections[uid]
                depth = max(_find_predicessors(connection.source, seen), depth)

            depths[block.uid] = depth

            return depth + 1

        # Step One
        max_depth = _find_predicessors(target)

        # Step Two
        layers = [list() for _ in range(max_depth)]
        for uid, depth in depths.items():
            layers[depth].append(self._blocks[uid])
        layers.append([target])

        # We can skip the first layer as they have no connections
        for layer in layers[1:]:
            for block in layer:
                for uid in self._inputs[block.uid].values():
                    connection = self._connections[uid]
                    block[connection.input] = connection.source[connection.output]

        return target()

        # Step one:
        # Walk backwards from the target while keeping track of already seen blocks.
        # Using this walk order every seen block based on the number of blocks
        # that need to be computed first. This should leave all the connectionless
        # blocks with zero and the rest from there

        # Step two:
        # sort the blocks based on the number of preceding blocks

        # Step three:
        # for each block run through their connections getting the values and setting
        # their inputs. This only works because of the sorting

        # Step four:
        # profit???

        # TODO: Branching and Looping
