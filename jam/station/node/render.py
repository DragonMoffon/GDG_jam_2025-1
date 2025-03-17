from .node import Block, Connection, Graph

from arcade.types import RGBA255, Rect
from arcade import Vec2, Camera2D, Text, get_window, ArcadeContext

from pyglet.shapes import Batch, BezierCurve, RoundedRectangle, Circle

BLOCK_COLOUR = (51, 29, 44, 255)
BACKGROUND_COLOUR = (63, 46, 62, 255)
ACCENT_COLOUR = (167, 130, 149, 255)
CONNECTION_COLOUR = (239, 225, 209, 255)

FNT_SIZE = 12
PT_RADIUS = 3
PADDING = 2

BLOCK_CORNER_RADIUS = 12
BLOCK_HEADER_SIZE = 24
BLOCK_FOOTER_SIZE = 30


class BlockRenderer:

    def __init__(self, block: Block, bottom_left: Vec2, batch: Batch):
        self._block = block
        self.bottom_left = bottom_left

        l = max(len(block.inputs), len(block.outputs))

        self._input_text = {
            name: Text(
                name,
                0.0,
                0.0,
                CONNECTION_COLOUR,
                font_size=FNT_SIZE,
                batch=batch,
                anchor_y="center",
            )
            for name in block.inputs
        }
        self._output_text = {
            name: Text(
                name,
                0.0,
                0.0,
                CONNECTION_COLOUR,
                font_size=FNT_SIZE,
                batch=batch,
                anchor_y="center",
                anchor_x="right",
            )
            for name in block.outputs
        }

        if self._input_text:
            max_input_txt = max(t.content_width for t in self._input_text.values())
        else:
            max_input_txt = 0.0

        if self._output_text:
            max_output_txt = max(t.content_width for t in self._output_text.values())
        else:
            max_output_txt = 0.0

        self.height = BLOCK_HEADER_SIZE + BLOCK_FOOTER_SIZE + (FNT_SIZE + PADDING) * l

        self._title = Text(
            block.name,
            bottom_left.x + BLOCK_CORNER_RADIUS,
            bottom_left.y + self.height - BLOCK_HEADER_SIZE / 2.0,
            BLOCK_COLOUR,
            anchor_y="center",
            batch=batch,
        )

        self.width = max(
            max_input_txt + max_output_txt + 5 * PADDING + 4 * PT_RADIUS,
            self._title.content_width + 2 * BLOCK_CORNER_RADIUS,
        )

        self._box = RoundedRectangle(
            bottom_left.x,
            bottom_left.y,
            self.width,
            self.height,
            BLOCK_CORNER_RADIUS,
            14,
            BLOCK_COLOUR,
            batch=batch,
        )
        self._header = RoundedRectangle(
            bottom_left.x,
            bottom_left.y + self.height - BLOCK_HEADER_SIZE,
            self.width,
            BLOCK_HEADER_SIZE,
            (0, BLOCK_CORNER_RADIUS, BLOCK_CORNER_RADIUS, 0),
            14,
            ACCENT_COLOUR,
            batch=batch,
        )

        self._input_circles = {}
        self._output_circles = {}

        start_x = bottom_left.x + PADDING + PT_RADIUS
        start_y = (
            bottom_left.y + self.height - BLOCK_HEADER_SIZE - PADDING - FNT_SIZE / 2.0
        )
        for idx, name in enumerate(block.inputs):
            y = start_y - idx * (FNT_SIZE + PADDING)
            self._input_circles[name] = Circle(
                start_x, y, PT_RADIUS, color=ACCENT_COLOUR, batch=batch
            )
            self._input_text[name].position = (start_x + PADDING + PT_RADIUS, y)

        start_x = bottom_left.x + self.width - PADDING - PT_RADIUS
        for idx, name in enumerate(block.outputs):
            y = start_y - idx * (FNT_SIZE + PADDING)
            self._output_circles[name] = Circle(
                start_x, y, PT_RADIUS, color=ACCENT_COLOUR, batch=batch
            )
            self._output_text[name].position = (start_x - PADDING - PT_RADIUS, y)


class ConnectionRenderer:

    def __init__(connection: Connection):
        pass


class GraphRenderer:

    def __init__(self, viewport: Rect, graph: Graph):
        self._graph = graph
        self._blocks: dict[UUID, BlockRenderer] = {}
        self._camera = Camera2D(viewport=viewport)
        self._batch = Batch()
        self._ctx = get_window().ctx

    def add_block(self, block: Block, bottom_left: Vec2):
        self._blocks[block.uid] = BlockRenderer(block, bottom_left, self._batch)

    def draw(self):
        with self._camera.activate():
            self._ctx.active_framebuffer.clear(
                color=BACKGROUND_COLOUR, viewport=self._camera.viewport.lbwh_int
            )
            self._batch.draw()
