from __future__ import annotations

from pathlib import Path
from tomllib import load
from uuid import UUID, uuid4
from dataclasses import dataclass
from typing import Self, TypeVar, Any, Generic, Mapping, Callable

from tomlkit import document, table, aot, inline_table, dump  # type: ignore -- unknownMemberType


_value_type = int | float | str | bool

T_co = TypeVar("T_co", int, float, str, bool, covariant=True)
O_co = TypeVar("O_co", int, float, str, bool, covariant=True)


class Value(Generic[T_co]):
    __auto_castable__: set[type[_value_type]] = set()
    _typ: type[T_co]

    def __init__(self, value: T_co) -> None:
        self._value: T_co = value

    @property
    def type(self) -> type[T_co]:
        return self._typ

    @property
    def value(self) -> T_co:
        return self._value

    def __str__(self):
        return f"{self._typ}<{self._value}>"

    def __hash__(self) -> int:
        return hash((self._typ, self.value))

    def __eq__(self, value: Value[Any]) -> bool:  # type: ignore --
        return value.type == self.type and value.value == self.value

    @classmethod
    def __cast__(cls, other: Value[O_co]) -> Self:
        return cls(cls._typ(other.value))

    @classmethod
    def __acast__(cls, other: Value[O_co]) -> Self:
        if other.type == cls._typ:
            return other  # type: ignore -- reportReturnType
        if other.type not in cls.__auto_castable__:
            raise TypeError(
                f"Cannot cast {other.type} into {cls._typ} automatically, you must use an explicit cast"
            )
        return cls.__cast__(other)


class IntValue(Value[int]):
    __auto_castable__ = set()
    _typ = int

    def __init__(self, value: int | None = None) -> None:
        super().__init__(value or 0)

    def __add__(self, other: Value[int] | Value[float]):
        try:
            if other.type is float:
                return FloatValue(float(self.value + other.value))
            elif other.type is int:
                return IntValue(int(self.value + other.value))
        except AttributeError as e:
            raise ValueError(
                f"Cannot add {other} to {self} as {other} is not a valid Value Type."
            ) from e

        raise ValueError(
            f"Cannot add {other} to {self} as {other} is not an int or float value."
        )

    def __bool__(self):
        return bool(self.value)


class FloatValue(Value[float]):
    __auto_castable__ = {int}
    _typ = float

    def __init__(self, value: float | None = None) -> None:
        super().__init__(value or 0.0)


class StrValue(Value[str]):
    __auto_castable__ = set()
    _typ = str

    def __init__(self, value: str | None = None) -> None:
        super().__init__(value or "")


class BoolValue(Value[bool]):
    __auto_castable__ = {str, float, int}
    _typ = bool

    def __init__(self, value: bool | None = None) -> None:
        super().__init__(value or False)

    def invert(self) -> BoolValue:
        return BoolValue(not self.value)


OperationValue = IntValue | FloatValue | StrValue | BoolValue
STR_CAST: dict[str, type[OperationValue]] = {
    "int": IntValue,
    "float": FloatValue,
    "bool": BoolValue,
    "str": StrValue,
}
TYPE_CAST: dict[type, type[OperationValue]] = {
    int: IntValue,
    float: FloatValue,
    bool: BoolValue,
    str: StrValue,
}

OperationReturn = (
    Mapping[str, OperationValue]
    | Mapping[str, FloatValue]
    | Mapping[str, FloatValue | IntValue]
    | Mapping[str, FloatValue | IntValue | BoolValue]
    | Mapping[str, FloatValue | IntValue | StrValue]
    | Mapping[str, FloatValue | BoolValue]
    | Mapping[str, FloatValue | BoolValue | StrValue]
    | Mapping[str, FloatValue | StrValue]
    | Mapping[str, IntValue]
    | Mapping[str, IntValue | BoolValue]
    | Mapping[str, IntValue | BoolValue | StrValue]
    | Mapping[str, IntValue | StrValue]
    | Mapping[str, BoolValue]
    | Mapping[str, BoolValue | StrValue]
    | Mapping[str, StrValue]
)

BlockOperation = Callable[..., OperationReturn]


class TestCase:

    def __init__(
        self,
        inputs: dict[str, OperationValue],
        outputs: dict[str, OperationValue],
    ) -> None:
        self.inputs = inputs
        self.outputs = outputs
        self.complete: bool = False

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TestCase):
            return False

        if self.inputs.keys() != other.inputs.keys():
            print(" no input match")
            return False
        if self.outputs.keys() != other.outputs.keys():
            print(" no output match")
            return False

        for name, value in self.inputs.items():
            if other.inputs[name].value != value.value:
                print(f" no input value match for: {name}")
                return False

        for name, value in self.outputs.items():
            if value.type is float:
                if round(value.value, 2) != round(other.outputs[name].value, 2):
                    print(f"no output value match for: {name}")
                    return False
            elif other.outputs[name].value != value.value:
                print(f" no  value match for: {name}")
                return False
        return True


@dataclass
class BlockComputation:
    inputs: Mapping[str, OperationValue]
    config: Mapping[str, OperationValue]
    outputs: Mapping[str, OperationValue]
    exception: Exception | None = None


class BlockType:
    __definitions__: dict[str, BlockType] = {}

    def __init__(
        self,
        name: str,
        operation: BlockOperation,
        inputs: dict[str, type[OperationValue]] | None = None,
        outputs: dict[str, type[OperationValue]] | None = None,
        config: dict[str, type[OperationValue]] | None = None,
        defaults: dict[str, OperationValue] | None = None,
        *,
        exclusive: bool = False,
    ) -> None:
        if name in self.__definitions__ and not exclusive:
            raise TypeError(
                f"A non-exclusive block of type {name} has already been defined"
            )
        if not exclusive:
            self.__definitions__[name] = self
        self.exclusive = exclusive

        self.name: str = name
        self.operation: BlockOperation = operation
        self.documentation = self.operation.__doc__

        self.inputs: dict[str, type[OperationValue]] = inputs or {}
        self.outputs: dict[str, type[OperationValue]] = outputs or {}
        self.config: dict[str, type[OperationValue]] = config or {}
        self.defaults: dict[str, OperationValue] = defaults or {}

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name


class Block:

    def __init__(
        self, typ: BlockType, uid: UUID | None = None, **kwds: OperationValue
    ) -> None:
        self.type: BlockType = typ
        self.uid: UUID = uid or uuid4()

        self.config: dict[str, OperationValue] = {
            name: value() for name, value in typ.config.items()
        }

        for kwd, value in kwds.items():
            if kwd not in self.type.config:
                raise KeyError(f"{kwd} is not a configuration of the {self.type} block")
            self.config[kwd] = value
        self.inputs: dict[str, UUID | None] = {name: None for name in typ.inputs}
        self.outputs: dict[str, list[UUID]] = {name: [] for name in typ.outputs}

    def __str__(self):
        return f"{self.type}<{self.uid}>"

    def __repr__(self):
        return self.__str__()

    def compute(self, **kwds: OperationValue) -> BlockComputation:
        exception = None
        try:
            if self.inputs.keys() != kwds.keys():
                raise TypeError(
                    f"{self.type.name} Block <{self.uid}> missing inputs: {set(self.inputs.keys()).difference(kwds.keys())}"
                )
            result = self.type.operation(**self.config, **kwds)
        except (TypeError, AttributeError, ValueError, KeyError) as e:
            print(f"{self} failed due to: {e}")
            exception = e
            result: Mapping[str, OperationValue] = {}
        return BlockComputation(kwds, self.config.copy(), result, exception)


class Connection:

    def __init__(
        self,
        source_: UUID,
        output_: str,
        target_: UUID,
        input_: str,
        uid: UUID | None = None,
    ):
        self.source = source_
        self.output = output_

        self.target = target_
        self.input = input_

        self.uid = uid or uuid4()

    def __str__(self):
        return f"{self.source}[{self.output}] -> [{self.input}]{self.target}"

    def __repr__(self):
        return self.__str__()


# -- VARIABLES --
# We don't need to define 'VariableBlock' as a type anymore yippee (just its operation)


def _variable(**kwds: OperationValue) -> dict[str, OperationValue]:
    return kwds


# We do need to define value blocks though


def value_func(cast: type[OperationValue]) -> BlockOperation:
    def __value(value: OperationValue) -> dict[str, OperationValue]:
        return {"value": cast.__acast__(value)}

    __value.__doc__ = f"""Create a {cast._typ.__name__}."""
    return __value


IntBlock = BlockType(
    "Int", value_func(IntValue), None, {"value": IntValue}, {"value": IntValue}
)


FloatBlock = BlockType(
    "Float", value_func(FloatValue), None, {"value": FloatValue}, {"value": FloatValue}
)


BoolBlock = BlockType(
    "Boolean",
    value_func(BoolValue),
    None,
    {"value": BoolValue},
    {"value": BoolValue},
)


StrBlock = BlockType(
    "String", value_func(StrValue), None, {"value": StrValue}, {"value": StrValue}
)

BLOCK_CAST: dict[type, BlockType] = {
    int: IntBlock,
    float: FloatBlock,
    bool: BoolBlock,
    str: StrBlock,
}


# -- Logic and Looping --

# if, elif, else
# for loop
# while loop

# -- SubGraph --


# TODO: ???


class Graph:

    def __init__(
        self,
        name: str = "graph",
        available: tuple[BlockType, ...] | None = None,
        sandbox: bool = False,
        cases: tuple[TestCase, ...] | None = None,
        input_block: UUID | None = None,
        output_block: UUID | None = None,
        *,
        source: str | None = None,
        _: None = None,
    ) -> None:
        self._name: str = name
        self._source: str | None = source

        self._blocks: dict[UUID, Block] = {}
        self._connections: dict[UUID, Connection] = {}

        self.available: tuple[BlockType, ...] = (
            available
            if available is not None
            else tuple(BlockType.__definitions__.values())
        )
        self.sandbox: bool = sandbox
        self.cases: tuple[TestCase, ...] = cases or ()
        self.input_uid: UUID | None = input_block
        self.output_uid: UUID | None = output_block

        # TODO: allow for running through select and every test case.
        # TODO: allow setting input and output block

    def get_block(self, uid: UUID) -> Block:
        if uid not in self._blocks:
            raise KeyError(f"Graph contains no block with uid {uid}")
        return self._blocks[uid]

    def get_connection(self, uid: UUID) -> Connection:
        if uid not in self._connections:
            raise KeyError(f"Graph contains no connection with uid {uid}")
        return self._connections[uid]

    @property
    def name(self) -> str:
        return self._name

    @property
    def source(self) -> str | None:
        return self._source

    @property
    def blocks(self) -> tuple[Block, ...]:
        return tuple(self._blocks.values())

    @property
    def connections(self) -> tuple[Connection, ...]:
        return tuple(self._connections.values())

    def add_block(self, block: Block) -> None:
        if block.uid in self._blocks:
            return

        self._blocks[block.uid] = block

    def remove_block(self, block: Block) -> None:
        if block.uid not in self._blocks:
            return

        for uid in block.inputs.values():
            if uid is None:
                continue
            self.remove_connection(self._connections[uid])

        for output in block.outputs.values():
            for uid in output:
                self.remove_connection(self._connections[uid])

        self._blocks.pop(block.uid)

    def add_connection(self, connection: Connection) -> None:
        if (
            connection.source not in self._blocks
            or connection.target not in self._blocks
        ):
            return

        if connection.uid in self._connections:
            return

        source = self._blocks[connection.source]
        target = self._blocks[connection.target]

        target_input = target.inputs[connection.input]
        if target_input is not None:
            self.remove_connection(self._connections[target_input])

        target.inputs[connection.input] = connection.uid
        source.outputs[connection.output].append(connection.uid)

        self._connections[connection.uid] = connection

    def remove_connection(self, connection: Connection) -> None:
        if connection.uid not in self._connections:
            return

        self._blocks[connection.source].outputs[connection.output].remove(
            connection.uid
        )
        self._blocks[connection.target].inputs[connection.input] = None

        self._connections.pop(connection.uid)

    def compute(self, target: Block) -> BlockComputation:
        """
        Starting from the target block we walk backwards through the connections
        building a directed connection graph which we then run through forwards.
        This has the benefit of skipping blocks that aren't connected to the output
        even if they're in the graph.

        This can take any block in the graph so for debugging you can query
        any block.
        """
        depths: dict[UUID, int] = {}
        layers: list[list[Block]] = []

        def _find_predicessors(block: Block, seen: set[UUID]) -> int:
            if block.uid in depths:
                return depths[block.uid] + 1

            if block.uid in seen:
                raise RecursionError(f"Block {block} refers to itself")

            seen = seen.union([block.uid])
            depth = 0

            for uid in block.inputs.values():
                if uid is None:
                    continue
                connection = self._connections[uid]
                input_block = self._blocks[connection.source]
                depth = max(depth, _find_predicessors(input_block, seen))

            depths[block.uid] = depth

            if depth == len(layers):
                layers.append([])
            layers[depth].append(block)

            return depth + 1

        _find_predicessors(target, set())

        computations: dict[UUID, BlockComputation] = {}

        for layer in layers:
            for block in layer:
                inputs: dict[str, OperationValue] = {}
                for name, uid in block.inputs.items():
                    if uid is None:
                        continue
                    connection = self._connections[uid]
                    computation = computations[connection.source]
                    inputs[name] = computation.outputs[connection.output]

                result: BlockComputation = block.compute(**inputs)
                computations[block.uid] = result
                if result.exception is not None:
                    # early exit if we hit an exception (and so can't find target value)
                    computations[target.uid] = BlockComputation(
                        {}, target.config.copy(), {}, result.exception
                    )
                    break

        return computations[target.uid]


def read_graph(path: Path, sandbox: bool = False) -> Graph:
    with open(path, "rb") as fp:
        raw_data = load(fp)

    config_table = raw_data["Config"]
    block_table = raw_data.get("Block", {})
    connection_table = raw_data.get("Connection", {})

    defined_types: dict[str, BlockType] = {}
    for variable_data in block_table.get("Variable", ()):
        inputs = {name: STR_CAST[typ] for name, typ in variable_data["inputs"].items()}
        outputs = {
            name: STR_CAST[typ] for name, typ in variable_data["outputs"].items()
        }
        config = {name: outputs[name] for name in outputs if name not in inputs}

        name = variable_data["name"]
        defined_types[name] = BlockType(
            name, _variable, inputs, outputs, config, exclusive=True
        )

    graph = Graph(name=config_table.get("name", ""), sandbox=sandbox)

    for block_data in block_table.get("Data", ()):
        uid = block_data.get("uid", None)
        if uid is not None:
            uid = UUID(uid)

        type_str = block_data["type"]
        if type_str in defined_types:
            block_type = defined_types[type_str]
        else:
            block_type = BlockType.__definitions__[type_str]

        config = {
            name: block_type.config[name](value)
            for name, value in block_data.get("config", {}).items()
        }

        block = Block(block_type, uid, **config)
        graph.add_block(block)

    for connection_data in connection_table.get("Data", ()):
        uid = connection_data.get("uid", None)
        if uid is not None:
            uid = UUID(uid)

        graph.add_connection(
            Connection(
                UUID(connection_data["source"]),
                connection_data["output"],
                UUID(connection_data["target"]),
                connection_data["input"],
                uid,
            )
        )

    return graph


def write_graph(path: Path, graph: Graph) -> None:
    toml = document()

    config_table = table()
    block_table = table()
    variables = aot()
    blocks = aot()
    connection_table = table()
    connections = aot()

    config_table["name"] = graph.name
    toml.add("Config", config_table)
    for block in graph.blocks:
        subtable = table()
        config = inline_table()

        subtable["uid"] = block.uid.hex
        subtable["type"] = block.type.name
        config.update(  # type: ignore -- unknownMemberType
            {name: typ.value for name, typ in block.config.items()}
        )
        subtable["config"] = config

        blocks.append(subtable)  # type: ignore -- unknownMemberType

        if block.type.exclusive:
            type_table = table()
            input_table = inline_table()
            input_table.update(  # type: ignore -- unknownMemberType
                {
                    name: str(typ._typ.__name__)
                    for name, typ in block.type.inputs.items()
                }
            )
            output_table = inline_table()
            output_table.update(  # type: ignore -- unknownMemberType
                {
                    name: str(typ._typ.__name__)
                    for name, typ in block.type.outputs.items()
                }
            )
            type_table["name"] = block.type.name
            type_table["inputs"] = input_table
            type_table["outputs"] = output_table
            variables.append(type_table)  # type: ignore -- unknownMemberType

    block_table["Variables"] = variables
    block_table["Data"] = blocks
    toml["Block"] = block_table

    for connection in graph.connections:
        subtable = table()
        subtable["uid"] = connection.uid.hex
        subtable["source"] = connection.source.hex
        subtable["output"] = connection.output
        subtable["target"] = connection.target.hex
        subtable["input"] = connection.input
        connections.append(subtable)  # type: ignore -- unknownMemberType
    connection_table["Data"] = connections
    toml["Connection"] = connection_table

    with open(path, "w", encoding="utf-8") as fp:
        dump(toml, fp)
