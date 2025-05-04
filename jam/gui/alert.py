from uuid import UUID
from .core import Element

from jam.puzzle import Puzzle

class AlertElement(Element):

    def __init__(self, pin: tuple[float, float], location: tuple[float, float], direction: int, puzzle: Puzzle):
        Element.__init__(self)
        self._pin = pin
        self._location = location
        self._direction = direction
        self._puzzle = puzzle
