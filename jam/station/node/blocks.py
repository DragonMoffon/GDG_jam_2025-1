from .node import Block


class MultiplyBlock(Block):
    inputs = {"a": int | float, "b": int | float}
    outputs = {"x": int | float}

    def func(self, a: int | float, b: int | float):
        return {"x": a * b}


class TestBlock(Block):
    inputs = {
        "SKDA:SDKAsdADSA": int,
        "SDKKKKDKAKKKKKKKKKK": float,
        "1": int,
        "2": int,
        "3": int,
        "4": int,
    }
    outputs: {"sigma": int}

    def func(self, **kwds):
        return {"sigma": 100}


class TestNoInputBlock(Block):
    outputs = {"a": int, "b": float}

    def func(self):
        return {"a": 16, "b": 24.0}


class TestNoOutputBlock(Block):
    inputs = {"a": int, "b": float}

    def func(self, a: int, b: float):
        return {}
