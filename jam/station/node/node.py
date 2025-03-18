from dataclasses import dataclass
from typing import Any, Self, Sequence

from uuid import uuid4, UUID

DEFAULTS: dict[type, Any] = {int: 0, float: 0.0, int | float: 0.0}

print(DEFAULTS[int | float])


def get_type_default[T](typ: type[T]) -> T:
    return DEFAULTS[typ]


class Block:
    inputs: dict[str, type] = {}
    outputs: dict[str, type] = {}

    def __init__(self, uid: UUID | None = None):
        self._uid: UUID = uid or uuid4()
        self._results: dict[str, Any] = {
            name: get_type_default(typ) for name, typ in self.outputs.items()
        }
        self._arguments: dict[str, Any] = {
            name: get_type_default(typ) for name, typ in self.inputs.items()
        }
        self._stale: bool = False

    def __repr__(self) -> str:
        return f"{self}{self._arguments}{self._results}"

    def __str__(self) -> str:
        return f"{block.name}<{block.uid}>"

    @property
    def uid(self) -> UUID:
        return self._uid

    @property
    def name(self) -> str:
        return self.__class__.__name__

    def __getitem__(self, name: str):
        if name not in self.outputs:
            raise KeyError(
                f"{name} is not an output of {Block.__class__.__name__} Block"
            )

        # If stale update the values
        if self._stale:
            self()
            self._stale = False

        return self._results[name]

    def __setitem__(self, name: str, value: Any):
        if name not in self.inputs:
            raise KeyError(f"{name} is not an argument of the {self.name} Block")
        assert (
            isinstance(value, self.inputs[name]),
            f"{type(value)} is not type for the input"
            f"{name} in the {self.name} Block",
        )

        if self._arguments[name] == value:
            return

        self._arguments[name] = value
        self._stale = True

    def func(self, **kwargs) -> dict[str, Any]:
        return {}

    def __call__(self) -> dict[str, Any]:
        rslt = self.func(**self._arguments)
        self._results.update(rslt)
        return rslt


class VariableBlock(Block):

    def __init__(self, name: str, uid: UUID | None = None):
        Block.__init__(self, uid)
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    def __setitem__(self, name: str, value: Any):
        if name not in self.outputs:
            raise KeyError(f"{name} if not an output of the {self.name} Block")
        assert (
            isinstance(value, self.outputs[name]),
            f"{type(value)} is not type for the output"
            f"{name} in the {self.name} Block",
        )

        self._results[name] = value


@dataclass
class Connection:
    source: Block
    output: str

    target: Block
    input: str

    uid: UUID


class Graph:

    def __init__(self):
        self._blocks: dict[UUID, Block] = {}
        self._connections: dict[UUID, Block] = {}

        # For every block (with inputs) we its
        self._inputs: dict[UUID, dict[str, Connection]] = {}

        # The finals are the blocks which the graph is trying to 'compute'
        self._finals: tuple[Block, ...] = ()

    def compute_finals(self):
        for final in self._finals:
            self.compute(final)

    def compute(self, target=None):
        """
        Starting from the target block we walk backwards through the connections
        building a directed connection graph which we then run through forwards.
        This has the benefit of skipping blocks that aren't connected to the output
        even if they're in the graph.

        This can actually take any block in the graph so for debugging you can query
        any block.
        """

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
