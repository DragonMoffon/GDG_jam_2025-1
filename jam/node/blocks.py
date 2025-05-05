import re
from math import copysign
from .graph import BlockType, FloatValue, IntValue, StrValue, BoolValue, OperationValue

# -- BLOCK TYPES --

# -- OPERATIONS --


def __add(
    a: IntValue | FloatValue, b: IntValue | FloatValue
) -> dict[str, IntValue | FloatValue]:
    if a.type is int and b.type is int:
        return {"result": IntValue(a.value + b.value)}  # type: ignore -- reportArgumentType
    a_ = FloatValue.__acast__(a)
    b_ = FloatValue.__acast__(b)

    return {"result": FloatValue(a_.value + b_.value)}


AddBlock = BlockType(
    "Add",
    __add,
    {"a": FloatValue, "b": FloatValue},
    {"result": FloatValue},
)


def __sub(
    a: IntValue | FloatValue, b: IntValue | FloatValue
) -> dict[str, IntValue | FloatValue]:
    if a.type is int and b.type is int:
        return {"result": IntValue(a.value - b.value)}  # type: ignore -- reportArgumentType
    a_ = FloatValue.__acast__(a)
    b_ = FloatValue.__acast__(b)

    return {"result": FloatValue(a_.value - b_.value)}


SubBlock = BlockType(
    "Subtract",
    __sub,
    {"a": FloatValue, "b": FloatValue},
    {"result": FloatValue},
)


def __mul(
    a: IntValue | FloatValue, b: IntValue | FloatValue
) -> dict[str, IntValue | FloatValue]:
    if a.type is int and b.type is int:
        return {"result": IntValue(a.value * b.value)}  # type: ignore -- reportArgumentType
    a_ = FloatValue.__acast__(a)
    b_ = FloatValue.__acast__(b)

    return {"result": FloatValue(a_.value * b_.value)}


MulBlock = BlockType(
    "Multiply",
    __mul,
    {"a": FloatValue, "b": FloatValue},
    {"result": FloatValue},
)


def __div(
    a: IntValue | FloatValue, b: IntValue | FloatValue
) -> dict[str, IntValue | FloatValue]:
    if a.type is int and b.type is int:
        return {"result": IntValue(a.value // b.value)}  # type: ignore -- reportArgumentType
    a_ = FloatValue.__acast__(a)
    b_ = FloatValue.__acast__(b)

    return {"result": FloatValue(a_.value / b_.value)}


DivBlock = BlockType(
    "Divide",
    __div,
    {"a": FloatValue, "b": FloatValue},
    {"result": FloatValue},
)

# -- Functions --


# cast
def __to_float(): ...
def __to_int(): ...
def __to_bool(): ...
def __to_str(): ...


# mod


def __mod(
    value: FloatValue | IntValue, mod: FloatValue | IntValue
) -> dict[str, IntValue | FloatValue]:
    if value.type is int and mod.type is int:
        return {"result": IntValue(value.value % mod.value)}
    a_ = FloatValue.__acast__(value)
    b_ = FloatValue.__acast__(mod)

    return {"result": FloatValue(a_.value % b_.value)}


ModBlock = BlockType(
    "Modulo", __mod, {"value": FloatValue, "mod": FloatValue}, {"result": FloatValue}
)


def __abs(value: FloatValue | IntValue) -> dict[str, IntValue | FloatValue]:
    if value.type is int:
        return {"result": IntValue(abs(value.value))}
    _a = FloatValue.__acast__(value)
    return {"result": FloatValue(abs(_a.value))}


AbsBlock = BlockType("Absolute", __abs, {"value": FloatValue}, {"result": FloatValue})


def __round(value: FloatValue | IntValue, precision: IntValue) -> dict[str, FloatValue]:
    _value = FloatValue.__acast__(value)
    _precision = IntValue.__acast__(precision)
    return {"result": FloatValue(round(_value.value, _precision.value))}


RoundBlock = BlockType(
    "Round",
    __round,
    {"value": FloatValue, "precision": IntValue},
    {"result": FloatValue},
)

# TODO: sign


def __max(
    a: FloatValue | IntValue, b: FloatValue | IntValue
) -> dict[str, IntValue | FloatValue]:
    if a.type is int and b.type is int:
        _a = IntValue.__acast__(a)
        _b = IntValue.__acast__(b)
        return {"result": IntValue(max(_a.value, _b.value))}
    _a = FloatValue.__acast__(a)
    _b = FloatValue.__acast__(b)
    return {"result": FloatValue(max(_a.value, _b.value))}


MaxBlock = BlockType(
    "Maximum",
    __max,
    {"a": FloatValue | IntValue, "b": FloatValue | IntValue},
    {"result": FloatValue | IntValue},
)


def __min(
    a: FloatValue | IntValue, b: FloatValue | IntValue
) -> dict[str, IntValue | FloatValue]:
    if a.type is int and b.type is int:
        _a = IntValue.__acast__(a)
        _b = IntValue.__acast__(b)
        return {"result": IntValue(min(_a.value, _b.value))}
    _a = FloatValue.__acast__(a)
    _b = FloatValue.__acast__(b)
    return {"result": FloatValue(min(_a.value, _b.value))}


MinBlock = BlockType(
    "Minimum",
    __min,
    {"a": FloatValue | IntValue, "b": FloatValue | IntValue},
    {"result": FloatValue | IntValue},
)


def __incr(value: IntValue | FloatValue) -> dict[str, IntValue | FloatValue]:
    if value.type is float:
        return {"result": FloatValue(value.value + 1)}
    a_ = IntValue.__acast__(value)
    return {"result": IntValue(a_.value + 1)}


IncrBlock = BlockType("Increment", __incr, {"value": IntValue}, {"result": IntValue})


def __decr(value: IntValue | FloatValue) -> dict[str, IntValue | FloatValue]:
    if value.type is float:
        return {"result": FloatValue(value.value - 1)}
    a_ = IntValue.__acast__(value)
    return {"result": IntValue(a_.value - 1)}


IncrBlock = BlockType("Decrement", __decr, {"value": IntValue}, {"result": IntValue})

# -- String Manipulation --


def __len(a: StrValue) -> dict[str, IntValue]:
    a_ = StrValue.__acast__(a)
    return {"result": IntValue(len(a_.value))}


LenBlock = BlockType("Length", __len, {"a": StrValue}, {"result": IntValue})


def __concat(a: StrValue, b: StrValue) -> dict[str, StrValue]:
    a_ = StrValue.__acast__(a)
    b_ = StrValue.__acast__(b)
    return {"result": StrValue(a_.value + b_.value)}


ConcatBlock = BlockType(
    "Concat", __len, {"a": StrValue, "b": StrValue}, {"result": StrValue}
)


def __replace(a: StrValue, old: StrValue, new: StrValue) -> dict[str, StrValue]:
    a_ = StrValue.__acast__(a)
    old_ = StrValue.__acast__(old)
    new_ = StrValue.__acast__(new)
    return {"result": StrValue(a_.value.replace(old_, new_))}


RepBlock = BlockType(
    "Replace",
    __len,
    {"a": StrValue, "old": StrValue, "new": StrValue},
    {"result": StrValue},
)


def _substr(a: StrValue, start: IntValue, end: IntValue) -> dict[str, StrValue]:
    a_ = StrValue.__acast__(a)
    start_ = IntValue.__acast__(start)
    end_ = IntValue.__acast__(end)
    return {"result": StrValue(a_.value[start_:end_])}


SubstringBlock = BlockType(
    "Substring",
    __len,
    {"a": StrValue, "start": IntValue, "end": IntValue},
    {"result": StrValue},
    defaults={"start": IntValue(0), "end": IntValue(-1)},
)


# -- killing Digi --
def _match(value: StrValue, pattern: StrValue) -> dict[str, BoolValue]:
    value_ = StrValue.__acast__(value)
    pattern_ = StrValue.__acast__(pattern)
    return {"result": BoolValue(re.match(pattern_, value_) is not None)}

MatchBlock = BlockType(
    "Match", _match, {"a": StrValue, "pattern": StrValue}, {"result": BoolValue}
)

def _format(value: BoolValue | IntValue | FloatValue | StrValue, format: StrValue) -> dict[str, StrValue]:
    _format = StrValue.__acast__(format)
    return {"result": StrValue(f"{value:_format.value}")}

FormatBlock = BlockType(
    "Format", _format, {"value": StrValue | IntValue | FloatValue | BoolValue, "format": StrValue}, {"result": BoolValue}
)

# -- Boolean Logic


def __eq(a: OperationValue, b: OperationValue) -> dict[str, BoolValue]:
    return {"result": BoolValue(a.value == b.value)}


EqBlock = BlockType(
    "Equal", __eq, {"a": BoolValue, "b": BoolValue}, {"result": BoolValue}
)


def __neq(a: OperationValue, b: OperationValue) -> dict[str, BoolValue]:
    return {"result": BoolValue(a.value != b.value)}


NeqBlock = BlockType(
    "Not Equal", __neq, {"a": BoolValue, "b": BoolValue}, {"result": BoolValue}
)


def __lt(a: FloatValue, b: FloatValue) -> dict[str, BoolValue]:
    a_ = FloatValue.__acast__(a)
    b_ = FloatValue.__acast__(b)
    return {"result": BoolValue(a_.value < b_.value)}


LtBlock = BlockType(
    "Less", __lt, {"a": FloatValue, "b": FloatValue}, {"result": BoolValue}
)


def __gt(a: FloatValue, b: FloatValue) -> dict[str, BoolValue]:
    a_ = FloatValue.__acast__(a)
    b_ = FloatValue.__acast__(b)
    return {"result": BoolValue(a_.value > b_.value)}


GtBlock = BlockType(
    "Greater", __gt, {"a": FloatValue, "b": FloatValue}, {"result": BoolValue}
)


def __leq(a: FloatValue, b: FloatValue) -> dict[str, BoolValue]:
    a_ = FloatValue.__acast__(a)
    b_ = FloatValue.__acast__(b)
    return {"result": BoolValue(a_.value <= b_.value)}


LeqBlock = BlockType(
    "Less Or Equal", __leq, {"a": FloatValue, "b": FloatValue}, {"result": BoolValue}
)


def __geq(a: FloatValue, b: FloatValue) -> dict[str, BoolValue]:
    a_ = FloatValue.__acast__(a)
    b_ = FloatValue.__acast__(b)
    return {"result": BoolValue(a_.value >= b_.value)}


GeqBlock = BlockType(
    "Greater Or Equal", __geq, {"a": FloatValue, "b": FloatValue}, {"result": BoolValue}
)


def __not(value: OperationValue) -> dict[str, BoolValue]:
    a_ = BoolValue.__acast__(value)
    return {"result": BoolValue(not a_.value)}


NotBlock = BlockType("Not", __not, {"value": BoolValue}, {"result": BoolValue})


def __and(a: BoolValue, b: BoolValue) -> dict[str, BoolValue]:
    a_ = BoolValue.__acast__(a)
    b_ = BoolValue.__acast__(b)
    return {"result": BoolValue(a_.value and b_.value)}


AndBlock = BlockType(
    "And", __and, {"a": BoolValue, "b": BoolValue}, {"result": BoolValue}
)


def __or(a: BoolValue, b: BoolValue) -> dict[str, BoolValue]:
    a_ = BoolValue.__acast__(a)
    b_ = BoolValue.__acast__(b)
    return {"result": BoolValue(a_.value or b_.value)}


OrBlock = BlockType("Or", __or, {"a": BoolValue, "b": BoolValue}, {"result": BoolValue})
