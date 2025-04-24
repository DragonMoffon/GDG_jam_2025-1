from __future__ import annotations

from uuid import UUID, uuid4
from enum import EnumMeta, Enum as _Enum
from dataclasses import dataclass, field
from typing import Self, TypeVar, Any, Generic, Protocol

# -- Cursed Default Enum Stuff --
class DefaultEnumMeta(EnumMeta):
    def __call__(cls, value=None, *args, **kwargs) -> type[_Enum]: # type: ignore
        if value is None:
            return cls(0)
        return EnumMeta.__call__(cls, value, *args, **kwargs) # type: ignore


class Enum(_Enum, metaclass=DefaultEnumMeta):...

_value_type = int | float | str | bool

T = TypeVar('T', int, float, str, bool, covariant=True)
O = TypeVar('O', int, float, str, bool, covariant=True)


class Value(Generic[T]):
    __auto_castable__: set[type[_value_type]] = set()
    _typ: type[T]

    def __init__(self, value: T) -> None:
        self._value: T = value

    @property
    def type(self):
        return self._typ
    
    @property
    def value(self):
        return self._value
    
    def __str__(self):
        return f'{self._typ}<{self._value}>'

    def __hash__(self) -> int:
        return hash((self._typ, self.value))

    def __eq__(self, value: Value[Any]) -> bool: # type: ignore
        return value.type == self.type and value.value == self.value

    @classmethod
    def __cast__(cls, other: Value[O]) -> Self:
        return cls(cls._typ(other.value))
    
    @classmethod
    def __acast__(cls, other: Value[O]) -> Self:
        if other.type not in cls.__auto_castable__:
            raise TypeError(f'Cannot cast {other.type} into {cls._typ} automatically, you must use an explicit cast')
        return cls.__cast__(other)


class IntValue(Value[int]):
    __auto_castable__ = {float, bool}
    _typ = int
    
    def __init__(self, value: int | None = None) -> None:
        super().__init__(value or 0)

    def __add__(self, other: Value[int] | Value[float]):
        try:
            if other.type == float:
                return FloatValue(float(self.value + other.value))
            elif other.type == int:
                return IntValue(int(self.value + other.value))
        except AttributeError:
            raise ValueError(f'Cannot add {other} to {self} as {other} is not a valid Value Type.')

        raise ValueError(f'Cannot add {other} to {self} as {other} is not an int or float value.')
        
    def __bool__(self):
        return bool(self.value)


class FloatValue(Value[float]):
    __auto_castable__ = {int, bool}
    _typ = float

    def __init__(self, value: float | None = None) -> None:
        super().__init__(value or 0.0)


class StrValue(Value[str]):
    __auto_castable__ = {bool}
    _typ = str

    def __init__(self, value: str | None = None) -> None:
        super().__init__(value or "")


class BoolValue(Value[bool]):
    __auto_castable__ = {str}
    _typ = bool

    def __init__(self, value: bool | None = None) -> None:
        super().__init__(value or False)


OperationValue = IntValue | FloatValue | StrValue | BoolValue
ControlValue = Enum | OperationValue


class BlockOperation(Protocol):
    def __call__(self, config: dict[str, ControlValue], **kwds: OperationValue | tuple[OperationValue, ...]) -> dict[str, OperationValue | tuple[OperationValue, ...]]: ...


@dataclass
class BlockComputation:
    source: UUID
    type: BlockType
    inputs: dict[str, OperationValue | tuple[OperationValue, ...]]
    outputs: dict[str, OperationValue | tuple[OperationValue, ...]]
    config: dict[str, ControlValue]
    exception: Exception | None = None

    def get_arg_input(self, name: str) -> tuple[OperationValue, ...]:
        if name not in self.type.variable_inputs:
            raise KeyError(f'{name} is not a variable length input of the {self.type.name} block')
        return self.inputs[name] # type: ignore
    
    def get_input(self, name: str) -> OperationValue:
        if name in self.type.variable_inputs:
            raise KeyError(f'{name} is a variable length input of the {self.type.name} block')
        return self.inputs[name] # type: ignore
    
    def get_arg_output(self, name: str) -> tuple[OperationValue, ...]:
        if name not in self.type.variable_outputs:
            raise KeyError(f'{name} is not a variable length output of the {self.type.name} block')
        return self.outputs[name] # type: ignore
    
    def get_output(self, name: str) -> OperationValue:
        if name in self.type.variable_outputs:
            raise KeyError(f'{name} is a variable length output of the {self.type.name} block')
        return self.outputs[name] # type: ignore
    
    def get_config(self, name: str) -> ControlValue:
        return self.config[name]


@dataclass
class BlockType:
    name: str
    operation: BlockOperation

    inputs: dict[str, type[OperationValue]]
    outputs: dict[str, type[OperationValue]]
    config: dict[str, type[ControlValue]]

    variable_inputs: set[str]
    variable_outputs: set[str]

    def compute(self, block: Block, **kwds: OperationValue | tuple[OperationValue, ...]) -> BlockComputation:
        exception = None
        try:
            if self.inputs.keys() != kwds.keys():
                raise TypeError(f'{self.name} Block <{block.uid}> missing inputs: {set(self.inputs.keys()).difference(kwds.keys())}')
            result = self.operation(block.config, **kwds)
        except Exception as e:
            exception = e
            result = {}
        return BlockComputation(block.uid, self, kwds, result, block.config.copy(), exception)


@dataclass
class Block:
    type: BlockType
    config: dict[str, ControlValue]
    uid: UUID = field(default_factory=uuid4)


@dataclass
class Branch: ...


@dataclass
class Connection:
    source: Block
    output: str

    target: Block
    input: str

    branch: Branch | None = None
    uid: UUID = field(default_factory=uuid4)


class Graph:

    def __init__(self, name: str = "graph", *, future: bool = False) -> None:
        self._name: str = name

        self._blocks: dict[UUID, Block] = {}
        self._connections: dict[UUID, Block] = {}