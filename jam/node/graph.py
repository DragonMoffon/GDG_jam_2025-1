from __future__ import annotations

from uuid import UUID, uuid4
from enum import EnumMeta, Enum as _Enum
from typing import Self, TypeVar, Any, Generic

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

    def __init__(self, typ: type[T], value: T) -> None:
        self._typ: type[T] = typ
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

    def __cast__(self, other: Value[O]) -> Self:
        return self.__class__(self._typ, self._typ(other.value))
    
    def __acast__(self, other: Value[O]) -> Self:
        if other.type not in self.__auto_castable__:
            raise TypeError(f'Cannot cast {other.type} into {self.type} automatically, you must use an explicit cast')
        return self.__cast__(other)

class IntValue(Value[int]):
    __auto_castable__ = {float, bool}
    
    def __init__(self, value: int | None = None) -> None:
        super().__init__(int, value or 0)

class FloatValue(Value[float]):
    __auto_castable__ = {int, bool}

    def __init__(self, value: float | None = None) -> None:
        super().__init__(float, value or 0.0)

class StrValue(Value[str]):
    __auto_castable__ = {bool}

    def __init__(self, value: str | None = None) -> None:
        super().__init__(str, value or "")

class BoolValue(Value[bool]):
    __auto_castable__ = {str}

    def __init__(self, value: bool | None = None) -> None:
        super().__init__(bool, value or False)

OperationValue = IntValue | FloatValue | StrValue | BoolValue
ControlValue = Enum | OperationValue

class BlockResult:

    def __init__(self) -> None:
        self._inputs: dict[str, OperationValue]
        self._dynamic_inputs: dict[str, tuple[OperationValue]]
        self._config: dict[str, OperationValue]
        self._outputs: dict[str, OperationValue]
        self._dynamic_outputs: dict[str, tuple[OperationValue]]

class Block:
    inputs: dict[str, type[OperationValue]] = dict()
    outputs: dict[str, type[OperationValue]] = dict()
    config: dict[str, type[ControlValue]] = dict()

    input_args: set[str] = set()
    output_args: set[str] = set()

    def __init__(self, name: str | None = None, uid: UUID | None = None, **kwds: ControlValue):
        self._uid: UUID = uid or uuid4()
        self._name: str = name or self.__class__.__name__
        self._configuration: dict[str, ControlValue] = {
            name: typ() for name, typ in self.config.items()
        }

        for kwd in kwds:
            if kwd not in self._configuration:
                raise KeyError(f"{kwd} is not a configuration of the {self._name} table")
            self._configuration[kwd] = kwds[kwd]

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return f"{self._name}<{self._uid}>"

    @property
    def uid(self) -> UUID:
        return self._uid

    @property
    def name(self) -> str:
        return self._name
    
    def get_config(self, name: str) -> ControlValue:
        if name not in self.config:
            raise KeyError(f"{name} is not a config of the {self._name} Block")
        return self._configuration[name]

    def set_config(self, name: str, value: ControlValue):
        if name not in self.config:
            raise KeyError(f"{name} is not a config of the {self._name} Block")
        assert isinstance(
            value, self.config[name]
        ), f"{type(value)} is not the type for the config {name} in the {self._name} Block"

        if self._configuration[name] == value:
            return

        self._configuration[name] = value
