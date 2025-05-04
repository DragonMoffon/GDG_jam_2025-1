import re
from .graph import BlockType, BlockOperation, FloatValue, IntValue, StrValue, BoolValue

# -- String ops --
def __len(a: StrValue) -> dict[str, IntValue]:
    a_ = StrValue.__acast__(a)
    return {"result": IntValue(len(a_.value))}

LenBlock = BlockType("Length", __len, {'a': StrValue}, {'result': IntValue})

def __concat(a: StrValue, b: StrValue) -> dict[str, StrValue]:
    a_ = StrValue.__acast__(a)
    b_ = StrValue.__acast__(b)
    return {"result": StrValue(a_.value + b_.value)}

ConcatBlock = BlockType("Concat", __len, {'a': StrValue, 'b': StrValue}, {'result': StrValue})

def __replace(a: StrValue, old: StrValue, new: StrValue) -> dict[str, StrValue]:
    a_ = StrValue.__acast__(a)
    old_ = StrValue.__acast__(old)
    new_ = StrValue.__acast__(new)
    return {"result": StrValue(a_.value.replace(old_, new_))}

RepBlock = BlockType("Replace", __len, {'a': StrValue, 'old': StrValue, 'new': StrValue}, {'result': StrValue})

def _substr(a: StrValue, start: IntValue, end: IntValue) -> dict[str, StrValue]:
    a_ = StrValue.__acast__(a)
    start_ = IntValue.__acast__(start)
    end_ = IntValue.__acast__(end)
    return {"result": StrValue(a_.value[start_:end_])}

SubstringBlock = BlockType("Substring", __len, {'a': StrValue, 'start': IntValue, 'end': IntValue}, {'result': StrValue},
                           defaults = {"start_": 0, "end_": -1})

# -- killing Digi --
def _match(a: StrValue, pattern: StrValue) -> dict[str, BoolValue]:
    a_ = StrValue.__acast__(a)
    pattern_ = StrValue.__acast__(pattern)
    return {"result": BoolValue(re.match(pattern_, a_) is not None)}

MatchBlock = BlockType("Match", __len, {'a': StrValue, 'pattern': StrValue}, {'result': BoolValue})
