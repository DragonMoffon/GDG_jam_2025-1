import re
from math import ceil, copysign, cos, floor, pi, sin, tan
from .graph import BlockType, FloatValue, IntValue, StrValue, BoolValue, OperationValue

# -- BLOCK TYPES --

# -- OPERATIONS --


def __add(
    a: IntValue | FloatValue, b: IntValue | FloatValue
) -> dict[str, IntValue | FloatValue]:
    """Add two values."""
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
    """Subtract two values."""
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
    """Multiply two values."""
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
    """Divide two values."""
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

def __sin(value: FloatValue | IntValue) -> dict[str, IntValue | FloatValue]:
    """Get the sine of a number."""
    _value = FloatValue.__acast__(value)
    return {"result": FloatValue(sin(_value.value))}


SinBlock = BlockType("Sin", __sin, {"value": FloatValue}, {"result": FloatValue})

def __cos(value: FloatValue | IntValue) -> dict[str, IntValue | FloatValue]:
    """Get the cosine of a number."""
    _value = FloatValue.__acast__(value)
    return {"result": FloatValue(cos(_value.value))}


CosBlock = BlockType("Cos", __cos, {"value": FloatValue}, {"result": FloatValue})

def __tan(value: FloatValue | IntValue) -> dict[str, IntValue | FloatValue]:
    """Get the tangent of a number."""
    _value = FloatValue.__acast__(value)
    return {"result": FloatValue(tan(_value.value))}


TanBlock = BlockType("Tan", __tan, {"value": FloatValue}, {"result": FloatValue})

def __pi() -> dict[str, FloatValue]:
    """Return the circle constant pi. (~3.14)"""
    return {"pi": FloatValue(pi)}


PiBlock = BlockType("Pi", __pi, {}, {"pi": FloatValue})

# -- Functions --


# cast
def __to_float(value: OperationValue) -> dict[str, FloatValue]:
    """Convert a value into a float."""
    return {"result": FloatValue.__cast__(value)}  # type: ignore -- point of a cast -.-


CastFloatBLock = BlockType(
    "Float Cast", __to_float, {"value": FloatValue}, {"result": FloatValue}
)


def __to_int(value: OperationValue) -> dict[str, IntValue]:
    """Convert a value into an integer."""
    return {"result": IntValue.__cast__(value)}  # type: ignore -- point of a cast -.-


CastIntBLock = BlockType(
    "Int Cast", __to_int, {"value": IntValue}, {"result": IntValue}
)


def __to_bool(value: OperationValue) -> dict[str, BoolValue]:
    """Convert a value into a boolean."""
    return {"result": BoolValue.__cast__(value)}  # type: ignore -- point of a cast -.-


CastBoolBLock = BlockType(
    "Boolean Cast", __to_bool, {"value": BoolValue}, {"result": BoolValue}
)


def __to_str(value: OperationValue) -> dict[str, StrValue]:
    """Convert a value into a string."""
    return {"result": StrValue.__cast__(value)}  # type: ignore -- point of a cast -.-


CastStrBLock = BlockType(
    "String Cast", __to_str, {"value": StrValue}, {"result": StrValue}
)


def __mod(
    value: FloatValue | IntValue, mod: FloatValue | IntValue
) -> dict[str, IntValue | FloatValue]:
    """Get the modulo (the remainder of a division) of `a` % `b`."""
    if value.type is int and mod.type is int:
        return {"result": IntValue(int(value.value % mod.value))}
    a_ = FloatValue.__acast__(value)
    b_ = FloatValue.__acast__(mod)

    return {"result": FloatValue(a_.value % b_.value)}


ModBlock = BlockType(
    "Modulo", __mod, {"value": FloatValue, "mod": FloatValue}, {"result": FloatValue}
)


def __abs(value: FloatValue | IntValue) -> dict[str, IntValue | FloatValue]:
    """Get the absolute value of a number."""
    if value.type is int:
        return {"result": IntValue(int(abs(value.value)))}
    _a = FloatValue.__acast__(value)
    return {"result": FloatValue(abs(_a.value))}


AbsBlock = BlockType("Absolute", __abs, {"value": FloatValue}, {"result": FloatValue})


def __round(value: FloatValue | IntValue, precision: IntValue) -> dict[str, FloatValue]:
    """Round a number to a certain amount of decimal places."""
    _value = FloatValue.__acast__(value)
    _precision = IntValue.__acast__(precision)
    return {"result": FloatValue(round(_value.value, _precision.value))}


RoundBlock = BlockType(
    "Round",
    __round,
    {"value": FloatValue, "precision": IntValue},
    {"result": FloatValue},
)


def __floor(value: FloatValue | IntValue) -> dict[str, FloatValue]:
    """Floor a value (round down.)"""
    _value = FloatValue.__acast__(value)
    return {"result": FloatValue(floor(_value.value))}


FloorBlock = BlockType("Floor", __floor, {"value": FloatValue}, {"result": FloatValue})


def __ceil(value: FloatValue | IntValue) -> dict[str, FloatValue]:
    """Ceiling a value (round up.)"""
    _value = FloatValue.__acast__(value)
    return {"result": FloatValue(ceil(_value.value))}


CeilBlock = BlockType("Ceiling", __ceil, {"value": FloatValue}, {"result": FloatValue})

def __sign(value: FloatValue | IntValue) -> dict[str, FloatValue | IntValue]:
    """Get the sign of the input value."""
    if value.type is int:
        return {"result": IntValue(int(copysign(1, value.value)))}
    _value = FloatValue.__acast__(value)
    return {"result": FloatValue(copysign(1.0, _value.value))}

SignBLock = BlockType("Sign", __sign, {"value": FloatValue}, {'result': FloatValue})


def __max(
    a: FloatValue | IntValue, b: FloatValue | IntValue
) -> dict[str, IntValue | FloatValue]:
    """Return the maximum of two values."""
    if a.type is int and b.type is int:
        return {"result": IntValue(int(max(a.value, b.value)))}
    _a = FloatValue.__acast__(a)
    _b = FloatValue.__acast__(b)
    return {"result": FloatValue(max(_a.value, _b.value))}


MaxBlock = BlockType(
    "Maximum",
    __max,
    {"a": FloatValue, "b": FloatValue},
    {"result": FloatValue},
)


def __min(
    a: FloatValue | IntValue, b: FloatValue | IntValue
) -> dict[str, IntValue | FloatValue]:
    """Return the minimum of two values."""
    if a.type is int and b.type is int:
        return {"result": IntValue(int(min(a.value, b.value)))}
    _a = FloatValue.__acast__(a)
    _b = FloatValue.__acast__(b)
    return {"result": FloatValue(min(_a.value, _b.value))}


MinBlock = BlockType(
    "Minimum",
    __min,
    {"a": FloatValue, "b": FloatValue},
    {"result": FloatValue},
)


def __incr(value: IntValue | FloatValue) -> dict[str, IntValue | FloatValue]:
    """Increment a value by one."""
    if value.type is float:
        return {"result": FloatValue(value.value + 1)}
    a_ = IntValue.__acast__(value)
    return {"result": IntValue(a_.value + 1)}


IncrBlock = BlockType("Increment", __incr, {"value": IntValue}, {"result": IntValue})


def __decr(value: IntValue | FloatValue) -> dict[str, IntValue | FloatValue]:
    """Decrement a value by one."""
    if value.type is float:
        return {"result": FloatValue(value.value - 1)}
    a_ = IntValue.__acast__(value)
    return {"result": IntValue(a_.value - 1)}


DecrBlock = BlockType("Decrement", __decr, {"value": IntValue}, {"result": IntValue})

# -- String Manipulation --


def __len(string: StrValue) -> dict[str, IntValue]:
    """Get the length of a string."""
    a_ = StrValue.__acast__(string)
    return {"result": IntValue(len(a_.value))}


LenBlock = BlockType("Length", __len, {"string": StrValue}, {"result": IntValue})


def __concat(a: StrValue, b: StrValue) -> dict[str, StrValue]:
    """Concatenate two strings."""
    a_ = StrValue.__acast__(a)
    b_ = StrValue.__acast__(b)
    return {"result": StrValue(a_.value + b_.value)}


ConcatBlock = BlockType(
    "Concat", __concat, {"a": StrValue, "b": StrValue}, {"result": StrValue}
)


def __replace(string: StrValue, old: StrValue, new: StrValue) -> dict[str, StrValue]:
    """Replace all instances of `old` with `new`."""
    string_ = StrValue.__acast__(string)
    old_ = StrValue.__acast__(old)
    new_ = StrValue.__acast__(new)
    return {"result": StrValue(string_.value.replace(old_.value, new_.value))}


RepBlock = BlockType(
    "Replace",
    __replace,
    {"string": StrValue, "old": StrValue, "new": StrValue},
    {"result": StrValue},
)

def __getchar(string: StrValue, idx: IntValue) -> dict[str, StrValue]:
    """Get a single character of a string by index."""
    string_ = StrValue.__acast__(string)
    idx_ = IntValue.__acast__(idx)
    return {"result": StrValue(string_.value[idx_.value])}


GetCharBlock = BlockType(
    "Get Char",
    __getchar,
    {"string": StrValue, "index": IntValue},
    {"result": StrValue}
)

def __ord(char: StrValue) -> dict[str, IntValue]:
    """Get the ASCII code of a single character. If given a string, returns the first character in the string's code."""
    char_ = StrValue.__acast__(char)
    return {"code": IntValue(ord(char_.value[0]))}


OrdBlock = BlockType(
    "Ord",
    __ord,
    {"char": StrValue},
    {"code": IntValue}
)

def __char(code: IntValue) -> dict[str, StrValue]:
    """Get a character from an ASCII code."""
    code_ = IntValue.__acast__(code)
    return {"char": StrValue(chr(code_.value))}


CharBlock = BlockType(
    "Char",
    __char,
    {"code": IntValue},
    {"char": StrValue}
)


def __substr(string: StrValue, start: IntValue, end: IntValue) -> dict[str, StrValue]:
    """Get a substring of a string from start to end index."""
    string_ = StrValue.__acast__(string)
    start_ = IntValue.__acast__(start)
    end_ = IntValue.__acast__(end)
    return {"result": StrValue(string_.value[start_:end_])}


SubstringBlock = BlockType(
    "Substring",
    __substr,
    {"string": StrValue, "start": IntValue, "end": IntValue},
    {"result": StrValue},
    defaults={"start": IntValue(0), "end": IntValue(-1)},
)


# -- killing Digi --
def _match(string: StrValue, pattern: StrValue) -> dict[str, BoolValue]:
    """Return whether or not a string matches a given RegEx pattern."""
    value_ = StrValue.__acast__(string)
    pattern_ = StrValue.__acast__(pattern)
    return {"result": BoolValue(re.match(pattern_.value, value_.value) is not None)}


MatchBlock = BlockType(
    "Match", _match, {"string": StrValue, "pattern": StrValue}, {"result": BoolValue}
)


def _format(
    value: BoolValue | IntValue | FloatValue | StrValue, format: StrValue
) -> dict[str, StrValue]:
    """Format a string with a Python formatting code."""
    _format = StrValue.__acast__(format)
    return {"result": StrValue(f"{value:_format.value}")}


FormatBlock = BlockType(
    "Format",
    _format,
    {"value": StrValue, "format": StrValue},
    {"result": StrValue},
)

# -- Boolean Logic


def __eq(a: OperationValue, b: OperationValue) -> dict[str, BoolValue]:
    """Does `a` equal `b`?"""
    return {"result": BoolValue(a.value == b.value)}


EqBlock = BlockType(
    "Equal", __eq, {"a": BoolValue, "b": BoolValue}, {"result": BoolValue}
)


def __neq(a: OperationValue, b: OperationValue) -> dict[str, BoolValue]:
    """Does `a` not equal `b`?"""
    return {"result": BoolValue(a.value != b.value)}


NeqBlock = BlockType(
    "Not Equal", __neq, {"a": BoolValue, "b": BoolValue}, {"result": BoolValue}
)


def __lt(a: FloatValue, b: FloatValue) -> dict[str, BoolValue]:
    """Is `a` less than `b`?"""
    a_ = FloatValue.__acast__(a)
    b_ = FloatValue.__acast__(b)
    return {"result": BoolValue(a_.value < b_.value)}


LtBlock = BlockType(
    "Less", __lt, {"a": FloatValue, "b": FloatValue}, {"result": BoolValue}
)


def __gt(a: FloatValue, b: FloatValue) -> dict[str, BoolValue]:
    """Is `a` greater than `b`?"""
    a_ = FloatValue.__acast__(a)
    b_ = FloatValue.__acast__(b)
    return {"result": BoolValue(a_.value > b_.value)}


GtBlock = BlockType(
    "Greater", __gt, {"a": FloatValue, "b": FloatValue}, {"result": BoolValue}
)


def __leq(a: FloatValue, b: FloatValue) -> dict[str, BoolValue]:
    """Is `a` less than or equal to `b`?"""
    a_ = FloatValue.__acast__(a)
    b_ = FloatValue.__acast__(b)
    return {"result": BoolValue(a_.value <= b_.value)}


LeqBlock = BlockType(
    "Less Or Equal", __leq, {"a": FloatValue, "b": FloatValue}, {"result": BoolValue}
)


def __geq(a: FloatValue, b: FloatValue) -> dict[str, BoolValue]:
    """Is `a` greater than or equal to `b`?"""
    a_ = FloatValue.__acast__(a)
    b_ = FloatValue.__acast__(b)
    return {"result": BoolValue(a_.value >= b_.value)}


GeqBlock = BlockType(
    "Greater Or Equal", __geq, {"a": FloatValue, "b": FloatValue}, {"result": BoolValue}
)


def __not(value: OperationValue) -> dict[str, BoolValue]:
    """Return not `a`."""
    a_ = BoolValue.__acast__(value) # type: ignore -- point of a cast -.-
    return {"result": BoolValue(not a_.value)}


NotBlock = BlockType("Not", __not, {"value": BoolValue}, {"result": BoolValue})


def __and(a: BoolValue, b: BoolValue) -> dict[str, BoolValue]:
    """Return `a` logically anded with `b`."""
    a_ = BoolValue.__acast__(a)
    b_ = BoolValue.__acast__(b)
    return {"result": BoolValue(a_.value and b_.value)}


AndBlock = BlockType(
    "And", __and, {"a": BoolValue, "b": BoolValue}, {"result": BoolValue}
)


def __or(a: BoolValue, b: BoolValue) -> dict[str, BoolValue]:
    """Return `a` logically ored with `b`."""
    a_ = BoolValue.__acast__(a)
    b_ = BoolValue.__acast__(b)
    return {"result": BoolValue(a_.value or b_.value)}


OrBlock = BlockType("Or", __or, {"a": BoolValue, "b": BoolValue}, {"result": BoolValue})


def __if(if_true: OperationValue, if_false: OperationValue, choice: BoolValue) -> dict[str, OperationValue]:
    """Choose between two values based on a boolean choice."""
    return {"result": if_true if choice.value else if_false}

IfBlock = BlockType("Choice", __if, {'if_true': FloatValue, 'if_false': FloatValue, 'choice': BoolValue}, {'result': FloatValue})

def __flag(value: IntValue) -> dict[str, BoolValue]:
    a_ = IntValue.__acast__(value)
    return {
        'bit_7': BoolValue(bool(a_.value & 0b10000000)),
        'bit_6': BoolValue(bool(a_.value & 0b01000000)),
        'bit_5': BoolValue(bool(a_.value & 0b00100000)),
        'bit_4': BoolValue(bool(a_.value & 0b00010000)),
        'bit_3': BoolValue(bool(a_.value & 0b00001000)),
        'bit_2': BoolValue(bool(a_.value & 0b00000100)),
        'bit_1': BoolValue(bool(a_.value & 0b00000010)),
        'bit_0': BoolValue(bool(a_.value & 0b00000001)),
    }

FlagBlock = BlockType(
    "Flag",
    __flag,
    {'value': IntValue},
    {
        'bit_7': BoolValue,
        'bit_6': BoolValue,
        'bit_5': BoolValue,
        'bit_4': BoolValue,
        'bit_3': BoolValue,
        'bit_2': BoolValue,
        'bit_1': BoolValue,
        'bit_0': BoolValue, 
    }
)

def __combine(bit_7: BoolValue, bit_6: BoolValue, bit_5: BoolValue, bit_4: BoolValue, bit_3: BoolValue, bit_2: BoolValue, bit_1: BoolValue, bit_0: BoolValue) -> dict[str, IntValue]:
    value = (
        BoolValue.__acast__(bit_7).value << 7 +
        BoolValue.__acast__(bit_6).value << 6 +
        BoolValue.__acast__(bit_5).value << 5 +
        BoolValue.__acast__(bit_4).value << 4 +
        BoolValue.__acast__(bit_3).value << 3 +
        BoolValue.__acast__(bit_2).value << 2 +
        BoolValue.__acast__(bit_1).value << 1 +
        BoolValue.__acast__(bit_0).value
    )
    return {'result': IntValue(value)}

CombineBlock = BlockType(
    "Combine",
    __combine,
    {
        'bit_7': BoolValue,
        'bit_6': BoolValue,
        'bit_5': BoolValue,
        'bit_4': BoolValue,
        'bit_3': BoolValue,
        'bit_2': BoolValue,
        'bit_1': BoolValue,
        'bit_0': BoolValue, 
    },
    {'result': IntValue}
)