from pathlib import Path
from enum import Enum, auto

from pyglet.graphics import Batch
from pyglet.shapes import RoundedRectangle
from pyglet.text import Label
from arcade import Rect, LBWH, Vec2, Vec3, Camera2D
from arcade.camera.default import ViewportProjector
from arcade.future import background

from resources import style, audio

from station.node import graph
from station.controller import (
    GraphController,
    read_graph,
    read_graph_from_level,
)
from station.puzzle import Puzzle
from station.gui import core, util, graph as gui
from station.gui.frame import Frame
from station.graphics.clip import ClippingMask
from station.context import context
from station.input import (
    inputs,
    Button,
    Axis,
    Keys,
    STR_KEY_SET,
    STR_ARRAY,
    STR_SET,
    LETTER_KEY_SET,
    TYPE_CHAR_SETS,
)

class EditorFrame(Frame):
    
    def __init__(self):
        pass