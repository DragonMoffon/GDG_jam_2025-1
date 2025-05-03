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

T = TypeVar("T")


class Variable(Block):

    def __init__(self, name: str | None = None, uid: UUID | None = None, **kwds):
        self.outputs = dict(**self.outputs)
        self.inputs = dict(**self.inputs)
        self.config = self.outputs | self.inputs | self.config
        self.locked: bool = False
        Block.__init__(self, name, uid, **kwds)

    def func(self, **kwds) -> dict[str, Any]:
        self._configuration.update(kwds)
        return dict(**self._configuration)

    def add_variable(
        self, var: str, typ: type[T], dflt: T | None = None, output: bool = True
    ) -> None:
        if self.locked:
            return

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

    def lock(self):
        self.locked = True


# -- OPERATORS --


class Add(Block):
    inputs = {"a": number, "b": number}
    outputs = {"x": number}

    def func(self, a: number, b: number):
        return {"x": a + b}


class Subtract(Block):
    inputs = {"a": number, "b": number}
    outputs = {"x": number}

    def func(self, a: number, b: number):
        return {"x": a - b}


class Divide(Block):
    inputs = {"a": number, "b": number}
    outputs = {"x": number}

    def func(self, a: number, b: number):
        if isinstance(b, int):
            return {"x": a // b}
        return {"x": a / b}


class Multiply(Block):
    inputs = {"a": number, "b": number}
    outputs = {"x": number}

    def func(self, a: number, b: number):
        return {"x": a * b}


# -- FUNCTIONS --


class Cast(Block):
    inputs = {"x": Var}
    config = {"type": CastableTypes}
    outputs = {"x": Var}

    def func(self, x: Any):
        return {"x", self._configuration["type"].value(x)}


class Absolute(Block):
    inputs = {"x": number}
    outputs = {"x": number}

    def func(self, x: number):
        return {"x", x.__class__(abs(x))}


class Modulo(Block):
    inputs = {"x": number, "m": number}
    outputs = {"x": number}

    def func(self, x: number, m: number):
        if m == 0:
            return {"x": 0}
        return {"x": x.__class__(x % m)}


class Sign(Block):
    inputs = {"x": number}
    outputs = {"x": number}

    def func(self, x: number):
        return {"x": x.__class__(copysign(1, x))}


class Commparison(Block):
    inputs = {"a": number, "b": number}
    config = {"op": ComparisonOpperators}
    outputs = {"x": bool}

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
                v = a == b

        return {"x": v}


class Max(Block):
    inputs = {"a": number, "b": number}
    outputs = {"x": number}

    def func(self, a: number, b: number):
        return {"x": max(a, b)}


class Min(Block):
    inputs = {"a": number, "b": number}
    outputs = {"x": number}

    def func(self, a: number, b: number):
        return {"x": min(a, b)}


class Condition(Block):
    inputs = {"a": number, "b": number, "c": bool}
    outputs = {"x": number}

    def func(self, a: number, b: number, c: bool):
        return {"x": a if c else b}


BLOCKS = {typ.__name__: typ for typ in Block.__subclasses__() if typ.__accessible__}
BLOCKS.update(
    {typ.__name__: typ for typ in Variable.__subclasses__() if typ.__accessible__}
)


def update_block_mapping():
    BLOCKS.update(
        {typ.__name__: typ for typ in Block.__subclasses__() if typ.__accessible__}
    )
    BLOCKS.update(
        {typ.__name__: typ for typ in Variable.__subclasses__() if typ.__accessible__}
    )
