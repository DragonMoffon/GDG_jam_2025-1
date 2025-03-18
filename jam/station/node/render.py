from .node import Block, Connection, Graph

from arcade.types import RGBA255, Rect
from arcade import Vec2, Camera2D, Text, get_window, ArcadeContext

from pyglet.shapes import Batch, BezierCurve, Line, RoundedRectangle, Circle

BLOCK_COLOUR = (51, 29, 44, 255)
BACKGROUND_COLOUR = (63, 46, 62, 255)
ACCENT_COLOUR = (167, 130, 149, 255)
CONNECTION_COLOUR = (239, 225, 209, 255)

FNT_SIZE = 12
PT_RADIUS = 3
PADDING = 2

LINE_THICKNESS = 2

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

    def update_position(self, bottom_left: Vec2):
        self.bottom_left = bottom_left

        self._title.position = (
            bottom_left.x + BLOCK_CORNER_RADIUS,
            bottom_left.y + self.height - BLOCK_HEADER_SIZE / 2.0,
        )
        self._box.position = bottom_left
        self._header.position = (
            bottom_left.x,
            bottom_left.y + self.height - BLOCK_HEADER_SIZE,
        )

        start_x = bottom_left.x + PADDING + PT_RADIUS
        start_y = (
            bottom_left.y + self.height - BLOCK_HEADER_SIZE - PADDING - FNT_SIZE / 2.0
        )
        for idx, name in enumerate(self._block.inputs):
            y = start_y - idx * (FNT_SIZE + PADDING)
            self._input_circles[name].position = start_x, y
            self._input_text[name].position = start_x + PADDING + PT_RADIUS, y

        start_x = bottom_left.x + self.width - PADDING - PT_RADIUS
        for idx, name in enumerate(self._block.outputs):
            y = start_y - idx * (FNT_SIZE + PADDING)
            self._output_circles[name].position = start_x, y
            self._output_text[name].position = start_x - PADDING - PT_RADIUS, y


class ConnectionRenderer:

    def __init__(
        self,
        connection: Connection,
        source: BlockRenderer,
        target: BlockRenderer,
        batch: Batch,
    ):
        self._connection = connection
        self._source = source
        self._target = target

        p1 = self._source._output_circles[self._connection.output]
        p2 = self._target._input_circles[self._connection.input]

        self._line = Line(
            p1.x, p1.y, p2.x, p2.y, LINE_THICKNESS, ACCENT_COLOUR, batch=batch
        )

    def update_position(self):
        p1 = self._source._output_circles[self._connection.output]
        p2 = self._target._input_circles[self._connection.input]

        self._line.x = p1.x
        self._line.y = p1.y
        self._line.x2 = p2.x
        self._line.y2 = p2.y


class GraphRenderer:

    def __init__(self, viewport: Rect, graph: Graph):
        self._graph = graph
        self._blocks: dict[UUID, BlockRenderer] = {}
        self._connections: dict[UUID, ConnectionRenderer] = {}
        self._mapping: dict[UUID, list[Connection]] = {}
        self._camera = Camera2D(viewport=viewport)
        self._batch = Batch()
        self._ctx = get_window().ctx

    def add_block(self, block: Block, bottom_left: Vec2):
        self._blocks[block.uid] = BlockRenderer(block, bottom_left, self._batch)
        self._mapping[block.uid] = []

    def move_block(self, block, bottom_left: Vec2):
        if block.uid not in self._blocks:
            self.add_block(block, bottom_left)
        else:
            self._blocks[block.uid].update_position(bottom_left)
            for connection in self._mapping[block.uid]:
                connection.update_position()

    def add_connection(self, connection):
        if (
            connection.source.uid not in self._blocks
            or connection.target.uid not in self._blocks
        ):
            return
        renderer = ConnectionRenderer(
            connection,
            self._blocks[connection.source.uid],
            self._blocks[connection.target.uid],
            self._batch,
        )
        self._connections[connection.uid] = renderer
        self._mapping[connection.source.uid].append(renderer)
        self._mapping[connection.target.uid].append(renderer)

    def draw(self):
        with self._camera.activate():
            self._ctx.active_framebuffer.clear(
                color=BACKGROUND_COLOUR, viewport=self._camera.viewport.lbwh_int
            )
            self._batch.draw()
