from typing import Any

from arcade.types import RGBA255, Rect
from arcade import Vec2, Camera2D, Text, get_window, ArcadeContext

from pyglet.shapes import Batch, Group, BezierCurve, Line, RoundedRectangle, Circle

from .node import Block, Connection, Graph

from resources import style

editor = style.editor

BASE_GROUP = Group(order=2)
HIGHLIGHT_GROUP = Group(order=1)
SHADOW_GROUP = Group(order=0)


class IONodeRenderer:

    def __init__(
        self,
        text: str,
        typ: type,
        value: Any,
        node: bool = True,
        left: bool = True,
        active: bool = False,
        panel: bool = False,
        string: bool = True,
    ):
        self.name = text
        self._str = text
        self._typ = typ
        self._value = value

        self._bottom_left: Vec2 = Vec2(0.0, 0.0)

        self._has_node = node
        self._has_panel = panel
        self._is_left = left
        self._is_active = active

        self.text: Text = None
        self.node: Circle | None = None

        self.panel: RoundedRectangle | None = None
        self.panel_text: Text | None = None
        self._panel_text_scroll: int = 0

        width = editor.padding
        height = 0.0

        self.text = Text(
            self._str,
            0.0,
            0.0,
            color=editor.colors.connection,
            font_size=style.text.normal.size,
            font_name=style.text.normal.name,
            anchor_y="center",
        )
        width += self.text.content_width
        height = max(height, self.text.content_height + 2 * editor.padding)

        if node:
            color = editor.colors.connection if active else editor.colors.accent
            self.node = Circle(0.0, 0.0, style.editor.point_radius, color=color)
            size = 2 * (editor.point_radius + editor.padding)
            width += size
            height = max(height, size)

        if panel:
            self.panel_text = Text(
                "######",
                0.0,
                0.0,
                color=editor.colors.accent,
                font_size=style.text.normal.size,
                font_name=style.text.normal.name,
            )
            self.panel = RoundedRectangle(
                0.0,
                0.0,
                self.panel_text.content_width + 2 * editor.padding,
                style.text.normal.size + 2 * editor.padding,
                editor.padding,
                color=editor.colors.background,
            )
            width += self.panel.width
            height = max(height, self.panel.height)

            self.panel_text.text = str(self._value)[:6]

        self.width = width
        self.height = height

    def update_position(self, bottom_left: Vec2):
        l, b = bottom_left
        r = l + self.width

        if self._is_left:
            node_x = l + editor.padding + editor.point_radius
            text_x = node_x + editor.padding + editor.point_radius
            panel_x = text_x + self.text.content_width + editor.padding
        else:
            node_x = r - editor.padding - editor.point_radius
            text_x = l + editor.padding
            panel_x = text_x + self.text.content_width + editor.padding

        y = b + self.height * 0.5

        self.text.position = text_x, y + editor.padding
        if self._has_node:
            self.node.position = node_x, y
        if self._has_panel:
            panel_y = y - self.panel.height * 0.5
            self.panel.position = panel_x, panel_y
            self.panel_text.position = (
                panel_x + editor.padding,
                panel_y + editor.padding,
            )

    def connect_renderer(self, batch: Batch, group: bool = True):
        if group:
            self.text.group = BASE_GROUP

        self.text.batch = batch

        if self._has_node:
            if group:
                self.node.group = BASE_GROUP
            self.node.batch = batch

        if self._has_panel:
            if group:
                self.panel.group = BASE_GROUP
                self.panel_text.group = BASE_GROUP
            self.panel.batch = batch
            self.panel_text.batch = batch

    def disconnect_renderer(self):
        self.text.group = None

        if self._has_node:
            self.node.group = None

        if self._has_panel:
            self.panel.group = None
            self.panel_text.group = None

        self.connect_renderer(None)

    def update_value(self, value: Any | None = None, scroll: int | None = None):
        if value == self._value:
            return

        if value is None:
            value = self._value
        self._value = value

        if scroll is None:
            scroll = self._panel_text_scroll
        self._panel_text_scroll = scroll

        if self._has_panel:
            self.panel_text.text = str(value)[scroll : 6 + scroll]

    def set_active(self, active: bool = False):
        self._is_active = active

        if self._has_node:
            self.node.color = (
                editor.colors.connection if active else editor.colors.accent
            )

    def contains_point(self, point: tuple[float, float]):
        l, b = self._bottom_left
        return 0 <= point[0] - l <= self.width and 0 <= point[1] - b <= self.height

    def panel_contains_point(self, point: tuple[float, float]):
        if not self._has_panel:
            return False

        l, b = self.panel.position
        w, h = self.panel.width, self.panel.height
        return 0 <= point[0] - l <= w and 0 <= point[1] - b <= h

    def node_contains_point(self, point: tuple[float, float]):
        if not self._has_node:
            return False

        x, y = self.node.position
        return (
            abs(point[0] - x) <= editor.point_radius
            and abs(point[1] - y) <= editor.point_radius
        )


class BlockRenderer:

    def __init__(self, block: Block, bottom_left: Vec2):
        self._block = block
        self.bottom_left = bottom_left

        self._inputs: dict[str, IONodeRenderer] = {
            name: IONodeRenderer(
                name,
                block.inputs[name],
                block._arguments[name],
                True,
                True,
                False,
                name in block.config and name not in block.outputs,
                name not in block.outputs,
            )
            for name in block.inputs
        }
        self._outputs: dict[str, IONodeRenderer] = {
            name: IONodeRenderer(
                name,
                block.outputs[name],
                block._results[name],
                True,
                False,
                False,
                name in block.config,
            )
            for name in block.outputs
        }

        self._configs: dict[str, IONodeRenderer] = {
            name: IONodeRenderer(
                name,
                block.config[name],
                block._configuration[name],
                False,
                True,
                False,
                True,
            )
            for name in block.config
            if name not in block.inputs and name not in block.outputs
        }

        body_height = max(
            sum(v.height for v in self._inputs.values()),
            sum(v.height for v in self._outputs.values()),
            sum(v.height for v in self._configs.values()),
        )

        max_input_width = 0.0
        if self._inputs:
            max_input_width = max(v.width for v in self._inputs.values())

        max_output_width = 0.0
        if self._outputs:
            max_output_width = max(v.width for v in self._outputs.values())

        max_config_width = 0.0
        if self._configs:
            max_config_width = max(v.width for v in self._configs.values())

        self.max_input_width = max_input_width
        self.max_output_width = max_output_width
        self.max_config_width = max_config_width

        self.height = editor.block.header + editor.block.footer + body_height

        self._title = Text(
            block.name,
            bottom_left.x + editor.block.radius,
            bottom_left.y + self.height - editor.block.header / 2.0,
            editor.colors.block,
            font_size=style.text.normal.size,
            font_name=style.text.normal.name,
            anchor_y="center",
        )

        self.width = max(
            max_input_width + max_output_width + max_config_width + 2 * editor.padding,
            self._title.content_width + 2 * editor.block.radius,
        )

        self._box = RoundedRectangle(
            bottom_left.x,
            bottom_left.y,
            self.width,
            self.height,
            editor.block.radius,
            14,
            editor.colors.block,
        )
        self._shadow = RoundedRectangle(
            bottom_left.x - editor.drop_x,
            bottom_left.y - editor.drop_y,
            self.width,
            self.height,
            editor.block.radius,
            14,
            editor.colors.shadow,
        )
        self._select = RoundedRectangle(
            bottom_left.x - editor.block.select,
            bottom_left.y - editor.block.select,
            self.width + 2 * editor.block.select,
            self.height + 2 * editor.block.select,
            editor.block.radius + editor.block.select,
            14,
            editor.colors.select,
        )
        self._select.visible = False
        self._header = RoundedRectangle(
            bottom_left.x,
            bottom_left.y + self.height - editor.block.header,
            self.width,
            editor.block.header,
            (0, editor.block.radius, editor.block.radius, 0),
            14,
            editor.colors.accent,
        )

        self.update_position(bottom_left)

    def select(self):
        self._select.visible = True

    def deselect(self):
        self._select.visible = False

    def connect_renderer(self, batch: Batch, group=True):
        if group:
            self._title.group = BASE_GROUP
            self._box.group = BASE_GROUP
            self._header.group = BASE_GROUP

            self._select.group = HIGHLIGHT_GROUP

            self._shadow.group = SHADOW_GROUP

        self._title.batch = batch
        self._shadow.batch = batch
        self._box.batch = batch
        self._select.batch = batch
        self._header.batch = batch

        for io_node in self._inputs.values():
            io_node.connect_renderer(batch, group)

        for io_node in self._outputs.values():
            io_node.connect_renderer(batch, group)

        for io_node in self._configs.values():
            io_node.connect_renderer(batch, group)

    def disconnect_renderer(self):
        self._title.group = None
        self._box.group = None
        self._header.group = None
        self._select.group = None
        self._shadow.group = None
        self.connect_renderer(None, False)

    def update_position(self, bottom_left: Vec2):
        self.bottom_left = bottom_left

        self._title.position = (
            bottom_left.x + editor.block.radius,
            bottom_left.y + self.height - editor.block.header / 2.0,
        )
        self._shadow.position = (
            bottom_left.x - editor.drop_x,
            bottom_left.y - editor.drop_y,
        )
        self._box.position = bottom_left
        self._select.position = (
            bottom_left.x - editor.block.select,
            bottom_left.y - editor.block.select,
        )
        self._header.position = (
            bottom_left.x,
            bottom_left.y + self.height - editor.block.header,
        )

        input_x = bottom_left.x
        output_x = bottom_left.x + self.width
        config_x = bottom_left.x + self.max_input_width + editor.padding

        start_y = bottom_left.y + self.height - editor.block.header

        y = start_y
        for io_node in self._inputs.values():
            y -= io_node.height
            io_node.update_position(Vec2(input_x, y))

        y = start_y
        for io_node in self._outputs.values():
            y -= io_node.height
            io_node.update_position(Vec2(output_x - io_node.width, y))

        y = start_y
        for io_node in self._configs.values():
            y -= io_node.height
            io_node.update_position(Vec2(config_x, y))

    def update_values(self):
        block = self._block
        for name, io_node in self._inputs.items():
            if name in block.config:
                io_node.update_value(block._configuration[name])

        for name, io_node in self._configs.items():
            if name in block.config:
                io_node.update_value(block._configuration[name])

        for name, io_node in self._outputs.items():
            if name in block.config:
                io_node.update_value(block._configuration[name])

    def contains_point(self, point: tuple[float, float]):
        l, b = self.bottom_left
        return 0 <= point[0] - l <= self.width and 0 <= point[1] - b <= self.height

    def find_input_node(
        self, point: tuple[float, float], radius=16
    ) -> IONodeRenderer | None:
        if not self._inputs:
            return None

        r2 = radius * radius

        minimum = r2
        min_node = None
        for io_node in self._inputs.values():
            if io_node.node_contains_point(point):
                return io_node
            diff = (io_node.node.x - point[0]) ** 2 + (io_node.node.y - point[1]) ** 2
            if diff <= minimum:
                minimum = diff
                min_node = io_node

        return min_node

    def find_output_node(
        self, point: tuple[float, float], radius=16
    ) -> IONodeRenderer | None:
        if not self._outputs:
            return None

        r2 = radius * radius

        minimum = r2
        min_node = None
        for io_node in self._outputs.values():
            if io_node.node_contains_point(point):
                return io_node
            diff = (io_node.node.x - point[0]) ** 2 + (io_node.node.y - point[1]) ** 2
            if diff <= minimum:
                minimum = diff
                min_node = io_node

        return min_node

    def find_panel(self, point: tuple[float, float]):
        if not self._configs and not self._inputs and not self._outputs:
            return None

        for io_node in self._configs.values():
            if io_node.panel_contains_point(point):
                return io_node
        for io_node in self._inputs.values():
            if io_node.panel_contains_point(point):
                return io_node
        for io_node in self._outputs.values():
            if io_node.panel_contains_point(point):
                return io_node

        return None

    def set_node_active(self, name: str, active: bool = True, output: bool = False):
        if output:
            self._outputs[name].set_active(active)
        else:
            self._inputs[name].set_active(active)


class ConnectionRenderer:

    def __init__(
        self,
        connection: Connection,
        source: BlockRenderer,
        target: BlockRenderer,
    ):
        self._connection = connection
        self._source = source
        self._target = target

        p1 = self._source._outputs[self._connection.output].node
        p2 = self._target._inputs[self._connection.input].node

        self._line = Line(
            p1.x, p1.y, p2.x, p2.y, editor.line_thickness, editor.colors.connection
        )
        self._drop_shadow = Line(
            p1.x - editor.drop_x,
            p1.y - editor.drop_y,
            p2.x - editor.drop_x,
            p2.y - editor.drop_y,
            editor.line_thickness,
            editor.colors.shadow,
        )

    def update_position(self):
        p1 = self._source._outputs[self._connection.output].node
        p2 = self._target._inputs[self._connection.input].node

        self._line.x = p1.x
        self._drop_shadow.x = p1.x - editor.drop_x
        self._line.y = p1.y
        self._drop_shadow.y = p1.y - editor.drop_y
        self._line.x2 = p2.x
        self._drop_shadow.x2 = p2.x - editor.drop_x
        self._line.y2 = p2.y
        self._drop_shadow.y2 = p2.y - editor.drop_y

    def connect_renderer(self, batch: Batch, group: bool = True):
        if group:
            self._drop_shadow.group = SHADOW_GROUP
            self._line.group = BASE_GROUP
        self._drop_shadow.batch = batch
        self._line.batch = batch

    def disconnect_renderer(self):
        self._drop_shadow.group = None
        self._line.group = None
        self.connect_renderer(None, False)


class GraphRenderer:

    def __init__(self, viewport: Rect, graph: Graph):
        self._graph = graph
        self._blocks: dict[UUID, BlockRenderer] = {}
        self._connections: dict[UUID, ConnectionRenderer] = {}
        self._camera = Camera2D(viewport=viewport)
        self._batch = Batch()
        self._ctx = get_window().ctx

    def add_block(self, block: Block, bottom_left: Vec2) -> BlockRenderer:
        renderer = BlockRenderer(block, bottom_left)
        renderer.connect_renderer(self._batch)

        self._blocks[block.uid] = renderer

        return renderer

    def remove_block(self, block: Block):
        if block.uid not in self._blocks:
            return

        connections = self._graph.get_connections(block)

        for connection in connections:
            self.remove_connection(connection)

        renderer = self._blocks[block.uid]
        renderer.disconnect_renderer()

        self._blocks.pop(block.uid)

    def move_block(self, block, bottom_left: Vec2):
        if block.uid not in self._blocks:
            self.add_block(block, bottom_left)
        else:
            self._blocks[block.uid].update_position(bottom_left)

            for uid in self._graph._inputs[block.uid].values():
                self._connections[uid].update_position()

            for outputs in self._graph._outputs[block.uid].values():
                for uid in outputs:
                    self._connections[uid].update_position()

    def update_values(self, blocks: tuple[BlockRenderer, ...] = ()):
        if not blocks:
            blocks = self._blocks.values()

        for block in blocks:
            block.update_values()

    def add_connection(self, connection: Connection) -> ConnectionRenderer:
        if (
            connection.source.uid not in self._blocks
            or connection.target.uid not in self._blocks
        ):
            return
        renderer = ConnectionRenderer(
            connection,
            self._blocks[connection.source.uid],
            self._blocks[connection.target.uid],
        )
        renderer.connect_renderer(self._batch)

        self._connections[connection.uid] = renderer
        self._blocks[connection.source.uid].set_node_active(
            connection.output, True, True
        )
        self._blocks[connection.target.uid].set_node_active(
            connection.input, True, False
        )

        return renderer

    def remove_connection(self, connection: Connection):
        if connection.uid not in self._connections:
            return

        renderer = self._connections[connection.uid]
        renderer.disconnect_renderer()

        self._connections.pop(connection.uid)

        if len(self._graph._outputs[connection.source.uid][connection.output]) <= 1:
            self._blocks[connection.source.uid].set_node_active(
                connection.output, False, True
            )

        self._blocks[connection.target.uid].set_node_active(
            connection.input, False, False
        )

    def draw(self):
        with self._ctx.enabled(self._ctx.BLEND):
            with self._camera.activate():
                self._batch.draw()
