from uuid import UUID
from typing import TypeVar, Any
from math import copysign
from .node import (
    Block,
    get_type_default,
    number,
    Var,
    CastableTypes,
    ComparisonOpperators,
)

# -- VARIABLES --


class VariableBlock(Block):

    def func(self, **kwds) -> dict[str, Any]:
        self._configuration.update(kwds)
        return dict(**self._configuration)


T = TypeVar("T")


class DynamicVariableBlock(VariableBlock):

    def __init__(self, name: str | None = None, uid: UUID | None = None):
        self.outputs = dict(**self.outputs)
        self.inputs = dict(**self.inputs)
        self.config = self.outputs | self.inputs
        Block.__init__(self, name, uid)

    def add_variable(
        self, var: str, typ: type[T], dflt: T | None = None, output: bool = True
    ) -> None:
        if var in self.outputs or var in self.inputs:
            return

        self.config[var] = typ
        self._configuration[var] = dflt if dflt is not None else get_type_default(typ)

        if output:
            self.outputs[var] = typ
            self._results[var] = self._configuration[var]
            self._stale = True
        else:
            self.inputs[var] = typ
            self._arguments[var] = self._configuration[var]


# -- OPERATORS --


class AddBlock(Block):
    inputs = {"a": number, "b": number}
    outputs = {"x": number}

    def func(self, a: number, b: number):
        return {"x": a + b}


class SubtractBlock(Block):
    inputs = {"a": number, "b": number}
    outputs = {"x": number}

    def func(self, a: number, b: number):
        return {"x": a - b}


class DivideBlock(Block):
    inputs = {"a": number, "b": number}
    outputs = {"x": number}

    def func(self, a: number, b: number):
        if isinstance(b, int):
            return {"x": a // b}
        return {"x": a / b}


class MultiplyBlock(Block):
    inputs = {"a": number, "b": number}
    outputs = {"x": number}

    def func(self, a: number, b: number):
        return {"x": a * b}


# -- FUNCTIONS --


class CastBlock(Block):
    inputs = {"x": Var}
    config = {"type": CastableTypes}
    outputs = {"x": Var}

    def func(self, x: Any):
        return {"x", self._configuration["type"](x)}


class AbsoluteBlock(Block):
    inputs = {"x": number}
    outputs = {"x": number}

    def func(self, x: number):
        return {"x", abs(x)}


class ModuloBlock(Block):
    inputs = {"x": number, "m": number}
    outputs = {"x": number}

    def func(self, x: number, m: number):
        return {"x", x % m}


class SignBlock(Block):
    inputs = {"x": number}
    outputs = {"x": number}

    def func(self, x: number):
        return {"x": copysign(1, x)}


class CommparisonBlock(Block):
    inputs = {"a": number, "b": number}
    config = {"op": ComparisonOpperators}
    outputs = {"x": number}

    def func(self, a: number, b: number):
        v = False
        match self._configuration["op"]:
            case ComparisonOpperators.LT:
                v = a < b
            case ComparisonOpperators.GT:
                v = a > b
            case ComparisonOpperators.LE:
                v = a <= b
            case ComparisonOpperators.GE:
                v = a >= b
            case ComparisonOpperators.NE:
                v = a != b
            case ComparisonOpperators.EQ:
                b = a == b

        return {"x": v}


class MaxBlock(Block):
    inputs = {"a": number, "b": number}
    outputs = {"x": number}

    def func(self, a: number, b: number):
        return {"x": max(a, b)}


class MinBlock(Block):
    inputs = {"a": number, "b": number}
    outputs = {"x": number}

    def func(self, a: number, b: number):
        return {"x": min(a, b)}
