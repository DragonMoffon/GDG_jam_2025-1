from uuid import UUID
from pyglet.graphics import Group

from resources import style

from station.graphics.shadow import get_shadow_shader
from station.node.graph import (
    Block,
    Connection,
    BlockComputation,
    OperationValue,
    TestCase,
)

from .core import Element, Point
from .elements import Label, Line, RoundedRectangle, Sprite


def get_segment_dist_sqr(s: Point, e: Point, p: Point) -> float:
    length = e[0] - s[0], e[1] - s[1]
    l2 = length[0] ** 2 + length[1] ** 2
    diff = p[0] - s[0], p[1] - s[1]
    if l2 == 0.0:
        return diff[0] ** 2 + diff[1] ** 2

    t = max(0.0, min(1.0, (length[0] * diff[0] + length[1] * diff[1]) / l2))
    proj = s[0] + t * length[0], s[1] + t * length[1]
    dist = (proj[0] - p[0]) ** 2 + (proj[1] - p[1]) ** 2

    return dist


class ConnectionElement(Element):

    def __init__(
        self,
        connection: Connection,
        start: tuple[float, float],
        end: tuple[float, float],
        parent: Element | None = None,
        layer: Group | None = None,
        *,
        links: tuple[tuple[float, float], ...] = (),
    ):
        Element.__init__(self, parent, layer, connection.uid)
        # TODO: add Style attribute for connection start, and end

        self._connection: Connection = connection

        self._start: tuple[float, float] = start
        self._end: tuple[float, float] = end

        start_link = (start[0] + style.format.corner_radius, start[1])
        end_link = (end[0] - style.format.corner_radius, end[1])
        self._links: list[tuple[float, float]] = [start_link, *links, end_link]

        self._lines: list[Line] = []
        self._shadow_lines: list[Line] = []

        prev = start
        for link in self._links:
            line, shadow = self._create_link(prev, link)
            self._lines.append(line)
            self._shadow_lines.append(shadow)
            prev = link
        line, shadow = self._create_link(prev, end)
        self._lines.append(line)
        self._shadow_lines.append(shadow)

    @property
    def connection(self) -> Connection:
        return self._connection

    def contains_point(self, point: tuple[float, float]) -> bool:
        # compute end line
        dist = get_segment_dist_sqr(self._links[-1], self._end, point)
        if dist <= style.format.point_radius**2:
            return True

        pos = self._start
        # Check along all lines except end line
        for link in self._links:
            dist = get_segment_dist_sqr(pos, link, point)

            if dist <= style.format.point_radius**2:
                return True

            pos = link

        return False

    def update_position(self, point: Point) -> None:
        self.update_start(point)

    def get_position(self) -> Point:
        return self._start

    def get_size(self) -> tuple[float, float]:
        return self._end[0] - self._start[0], self._end[1] - self._start[1]

    def get_closest_link(self, point: tuple[float, float]) -> tuple[int, float]:
        # TODO: make it not exlude start and end links?
        smallest = float("inf")
        link_idx = 0
        for idx, link in enumerate(self._links[1:-1]):
            dist = (link[0] - point[0]) ** 2 + (link[1] - point[1]) ** 2
            if dist <= smallest:
                smallest = dist
                link_idx = idx + 1
        return link_idx, smallest**0.5

    def get_closest_line(self, point: tuple[float, float]) -> tuple[int, float]:
        smallest = float("inf")
        line_idx = 0

        for idx, line in enumerate(self._lines):
            dist = get_segment_dist_sqr(line.position, (line.x2, line.y2), point)

            if dist < smallest:
                smallest = dist
                line_idx = idx

        return line_idx, smallest**0.5

    def update_start(self, point: tuple[float, float]) -> None:
        self._start = point

        link = point[0] + style.format.corner_radius, point[1]
        shadow_point = (point[0] - style.format.drop_x, point[1] - style.format.drop_y)
        shadow_link = shadow_point[0] + style.format.corner_radius, shadow_point[1]

        self._links[0] = link

        self._lines[0].update_position(point)
        self._lines[0].update_position2(link)
        self._lines[1].update_position(link)

        self._shadow_lines[0].update_position(shadow_point)
        self._shadow_lines[0].update_position2(shadow_link)
        self._shadow_lines[1].update_position(shadow_link)

    def update_end(self, point: tuple[float, float]) -> None:
        self._end = point

        link = point[0] - style.format.corner_radius, point[1]
        shadow_point = (point[0] - style.format.drop_x, point[1] - style.format.drop_y)
        shadow_link = shadow_point[0] - style.format.corner_radius, shadow_point[1]

        self._links[-1] = link

        self._lines[-1].update_position(link)
        self._lines[-2].update_position2(link)
        self._lines[-1].update_position2(point)

        self._shadow_lines[-1].update_postion(shadow_link)
        self._shadow_lines[-2].update_position2(shadow_link)
        self._shadow_lines[-1].update_position2(shadow_point)

    def update_link(self, link: int, point: tuple[float, float]) -> None:
        if not 0 < link < len(self._links):
            return  # ignore the start and end links
        shadow = point[0] - style.format.drop_x, point[1] - style.format.drop_y

        self._links[link] = point

        pl = self._lines[link]
        nl = self._lines[link + 1]

        ps = self._shadow_lines[link]
        ns = self._shadow_lines[link + 1]

        pl.update_position2(point)
        ps.update_position2(shadow)

        nl.update_position(point)
        ns.update_position(shadow)

    def insert_link(self, link: int, point: tuple[float, float]) -> None:
        if not 0 < link < len(self._links):
            return  # ignore the start and end links
        shadow = point[0] - style.format.drop_x, point[1] - style.format.drop_y

        old_start = self._links[link - 1]

        self._lines[link].update_position(point)
        self._shadow_lines[link].update_position(shadow)

        n_line, n_s_line = self._create_link(old_start, point)

        self._lines.insert(link, n_line)
        self._shadow_lines.insert(link, n_s_line)
        self._links.insert(link, point)

    def remove_link(self, link: int) -> None:
        if not 2 <= link + 1 < len(self._links):
            return  # ignore the start and end

        start = self._links[link - 1]
        shadow = start[0] - style.format.drop_x, start[1] - style.format.drop_y

        self.remove_child(self._lines.pop(link))
        self.remove_child(self._shadow_lines.pop(link))
        self._links.pop(link)

        self._lines[link].update_position(start)
        self._shadow_lines[link].update_position(shadow)

    def _create_link(
        self, start: tuple[float, float], end: tuple[float, float]
    ) -> tuple[Line, Line]:
        shadow_start = start[0] - style.format.drop_x, start[1] - style.format.drop_y
        shadow_end = end[0] - style.format.drop_x, end[1] - style.format.drop_y
        line = Line(
            *start,
            *end,
            style.format.line_thickness,
            color=style.colors.highlight,
            parent=self,
            layer=self.BODY(4),
        )
        shadow_line = Line(
            *shadow_start,
            *shadow_end,
            style.format.line_thickness,
            color=style.colors.dark,
            program=get_shadow_shader(),
            parent=self,
            layer=self.SHADOW(),
        )

        return line, shadow_line


class TextPanel(Element):

    def __init__(
        self,
        char_count: int = 6,
        parent: Element | None = None,
        layer: Group | None = None,
        uid: UUID | None = None,
    ):
        Element.__init__(self, parent, layer, uid)
        self._text: Label = Label(
            "#" * char_count,
            0.0,
            0.0,
            0.0,
            font_name=style.text.names.monospace,
            font_size=style.text.sizes.normal,
            color=style.colors.accent,
            parent=self,
        )
        self._text_width = self._text.width
        self._panel: RoundedRectangle = RoundedRectangle(
            0.0,
            0.0,
            self._text.width + 2 * style.format.padding,
            style.text.sizes.normal + 2 * style.format.padding,
            style.format.padding,
            4,
            style.colors.background,
            parent=self,
        )

        self._full_text = self._text.text = ""
        self._count = char_count
        self._cursor = 0

    @property
    def text(self) -> str:
        return self._full_text

    @text.setter
    def text(self, text: str) -> None:
        self._full_text = text
        sub = text[self._cursor : self._cursor + self._count]
        self._text.text = sub

    @property
    def offset(self) -> int:
        return self._cursor

    @offset.setter
    def offset(self, offset: int) -> None:
        self._cursor = offset
        sub = self._full_text[offset : offset + self._count]
        self._text.text = sub

    @property
    def width(self) -> float:
        return self._panel.width

    @property
    def height(self) -> float:
        return self._panel.height

    @property
    def left(self) -> float:
        return self._panel.x

    @property
    def bottom(self) -> float:
        return self._panel.y

    def contains_point(self, point: Point) -> bool:
        return self._panel.contains_point(point)

    def update_position(self, point: Point) -> None:
        self._panel.update_position(point)
        self._text.update_position(
            (
                point[0] + style.format.padding,
                point[1] + style.format.padding,
            )
        )

    def get_position(self) -> Point:
        return self._panel.get_position()

    def get_size(self) -> tuple[float, float]:
        return self._panel.get_size()


class BoolPanel(Sprite):

    def __init__(
        self,
        x: float = 0.0,
        y: float = 0.0,
        active: bool = False,
        parent: Element | None = None,
        layer: Group | None = None,
        uid: UUID | None = None,
    ):
        Sprite.__init__(
            style.game.editor.check_inactive, x, y, parent=parent, layer=layer, uid=uid
        )
        self._active: bool = active
        self._sprite.color = style.colors.highlight
        if active:
            self._sprite.image = style.game.editor.check_active

    @property
    def active(self) -> bool:
        return self._active

    @active.setter
    def active(self, active: bool) -> None:
        self._active = active
        if active:
            self._sprite.image = style.game.editor.check_active
        else:
            self._sprite.image = style.game.editor.check_inactive


class ConnectionNodeElement(Element):

    def __init__(
        self,
        name: str = "",
        is_input: bool = True,
        parent: Element | None = None,
        layer: Group | None = None,
        uid: UUID | None = None,
    ):
        Element.__init__(self, parent, layer, uid)
        self._sprite = Sprite(
            style.game.editor.node_inactive, 0.0, 0.0, 0.0, parent=self
        )
        self._sprite.width = 2 * style.format.point_radius
        self._sprite.height = 2 * style.format.point_radius
        self._sprite.color = style.colors.highlight

        self._name: str = name
        self._label: Label | None = None
        if self._name:
            self._label = Label(
                name,
                0.0,
                0.0,
                0.0,
                font_name=style.text.names.monospace,
                font_size=style.text.sizes.normal,
                color=style.colors.highlight,
                anchor_y="bottom",
                parent=self,
            )

        self._is_input: bool = is_input

        self._active: bool = False
        self._branch: bool = False

    def contains_point(self, point: Point) -> bool:
        l, b = self.get_position()
        w, h = self.get_size()
        return 0 <= point[0] - l <= w and 0 <= point[1] - b <= h

    def update_position(self, point: Point) -> None:
        s_x = point[0]
        if self._label is not None:
            l_x = point[0] + self._sprite.width + style.format.padding
            if not self._is_input:
                s_x = point[0] + self._label.width + style.format.padding
                l_x = point[0]

            l_y = point[1] + (self._sprite.height - self._label.height) / 2.0
            self._label.position = l_x, l_y + 1, 0.0
        self._sprite.position = s_x, point[1], 0.0

    def get_position(self) -> Point:
        if self._label is None or self._is_input:
            return self._sprite.get_position()
        return self._label.get_position()

    def get_size(self) -> tuple[float, float]:
        w, h = self._sprite.get_size
        if self._label is None:
            return w, h
        return w + style.format.padding + self._label.width, h

    @property
    def name(self) -> str:
        return self._name

    @property
    def center(self) -> tuple[float, float]:
        return (
            self._sprite.x + self._sprite.width / 2.0,
            self._sprite.y + self._sprite.height / 2.0,
        )

    @property
    def active(self) -> bool:
        return self._active

    @active.setter
    def active(self, active: bool) -> None:
        self._active = active
        if active:
            if self._branch:
                self._sprite.image = style.game.editor.branch_active
            else:
                self._sprite.image = style.game.editor.node_active
        else:
            if self._branch:
                self._sprite.image = style.game.editor.branch_inactive
            else:
                self._sprite.image = style.game.editor.node_inactive

    @property
    def branch(self) -> bool:
        return self._branch

    @branch.setter
    def branch(self, branch: bool) -> None:
        self._branch = branch
        if branch:
            if self._active:
                self._sprite.image = style.game.editor.branch_active
            else:
                self._sprite.image = style.game.editor.branch_inactive
        else:
            if self._active:
                self._sprite.image = style.game.editor.node_active
            else:
                self._sprite.image = style.game.editor.node_inactive

    @property
    def link_pos(self) -> tuple[float, float]:
        y = self._sprite.y + self._sprite.height / 2.0
        if self._is_input:
            return self._sprite.x, y
        return self._sprite.x + self._sprite.width, y


class TempValueElement(Element):

    def __init__(
        self,
        block: Block,
        connection: Connection,
        parent: Element | None = None,
        layer: Group | None = None,
    ):
        self._block = block
        self._connection = connection
        self._type: type[OperationValue] = block.type.outputs[connection.output]
        Element.__init__(self, parent, layer, block.uid)

        if self._type._typ is bool:
            self._panel = BoolPanel(parent=self, layer=self.BODY())
        else:
            self._panel = TextPanel(parent=self, layer=self.BODY())
            self._panel.text = str(block.config[connection.output].value)

        self._line = Line(
            0.0,
            0.0,
            1.0,
            1.0,
            style.format.line_thickness,
            style.colors.highlight,
            parent=self,
            layer=self.BODY(4),
        )

        self._panel_shadow = RoundedRectangle(
            0.0,
            0.0,
            self._panel.width,
            self._panel.height,
            style.format.padding,
            12,
            style.colors.dark,
            program=get_shadow_shader(),
            parent=self,
            layer=self.SHADOW(),
        )
        self._line_shadow = Line(
            0.0,
            0.0,
            1.0,
            1.0,
            style.format.line_thickness,
            style.colors.dark,
            program=get_shadow_shader(),
            parent=self,
            layer=self.SHADOW(),
        )

    @property
    def block(self) -> Block:
        return self._block

    @property
    def connection(self) -> Connection:
        return self._connection

    @property
    def left(self) -> float:
        return self._panel.left

    @property
    def bottom(self) -> float:
        return self._panel.bottom

    def contains_point(self, point: Point) -> bool:
        return self._panel.contains_point(point)

    def update_position(self, point: Point) -> None:
        self.update_end(point)

    def get_position(self) -> Point:
        return self._line.get_position2()

    def get_size(self) -> tuple[float, float]:
        return self._panel.get_size()

    def update_end(self, point: tuple[float, float]) -> None:
        link = point[0] - style.format.corner_radius, point[1]

        shadow_point = point[0] - style.format.drop_x, point[1] - style.format.drop_y
        shadow_link = link[0] - style.format.drop_x, link[1] - style.format.drop_y

        self._line.update_position(link)
        self._line.update_position2(point)

        self._line_shadow.update_position(shadow_link)
        self._line_shadow.update_position2(shadow_point)

        panel_pos = link[0] - self._panel.width, link[1] - self._panel.height * 0.5
        shadow_pos = (
            panel_pos[0] - style.format.drop_x,
            panel_pos[1] - style.format.drop_y,
        )

        self._panel.update_position(panel_pos)
        self._panel_shadow.update_position(shadow_pos)

    def get_hovered_config(self, point: tuple[float, float]) -> str | None:
        if not self.contains_point(point):
            return None
        return self._connection.output

    def get_config(self, name: str) -> TextPanel | BoolPanel:
        if name not in self.block.config:
            raise KeyError(f"{name} not a config of block type {self.block.type}")
        return self._panel


class BlockElement(Element):

    def __init__(
        self, block: Block, parent: Element | None = None, layer: Group | None = None
    ):
        Element.__init__(self, parent, layer, block.uid)
        self._block = block

        self._input_nodes: dict[str, ConnectionNodeElement] = {}
        self._output_nodes: dict[str, ConnectionNodeElement] = {}
        self._config_panels: dict[str, TextPanel | BoolPanel] = {}

        body_width = style.format.padding
        self.input_width = 0.0
        if block.type.inputs:
            for name in block.type.inputs:
                node = ConnectionNodeElement(
                    name, True, parent=self, layer=self.BODY(1)
                )
                self.input_width = max(node.width, self.input_width)
                self._input_nodes[name] = node
            body_width += self.input_width + style.format.padding

        self.output_width = 0.0
        if block.type.outputs:
            for name in block.type.outputs:
                node = ConnectionNodeElement(
                    name, False, parent=self, layer=self.BODY(1)
                )
                self.output_width = max(node.width, self.output_width)
                self._output_nodes[name] = node
            body_width += self.output_width + style.format.padding

        self.config_width = 0.0
        if block.type.config:
            for name, typ in block.type.config.items():
                if typ._typ is bool:
                    panel = BoolPanel(parent=self, layer=self.BODY(1))
                else:
                    panel = TextPanel(parent=self, layer=self.BODY(1))
                    panel.text = str(block.config[name].value)
                self.config_width = max(panel.width, self.config_width)
                self._config_panels[name] = panel
            body_width += self.config_width + style.format.padding

        row_count = max(
            len(block.type.inputs), len(block.type.config), len(block.type.outputs)
        )
        body_height = row_count * (style.text.sizes.normal + 3 * style.format.padding)

        self._title: Label = Label(
            block.type.name,
            0.0,
            0.0,
            0.0,
            anchor_y="bottom",
            font_name=style.text.names.monospace,
            font_size=style.text.sizes.normal,
            color=style.colors.base,
            parent=self,
            layer=self.BODY(2),
        )
        title_width = self._title.width + 2 * style.format.corner_radius

        block_width = max(body_width, title_width)
        block_height = style.format.header_size + body_height + style.format.footer_size
        self._body: RoundedRectangle = RoundedRectangle(
            0.0,
            0.0,
            block_width,
            block_height,
            style.format.corner_radius,
            12,
            style.colors.base,
            parent=self,
            layer=self.BODY(),
        )
        self._header: RoundedRectangle = RoundedRectangle(
            0.0,
            0.0,
            block_width,
            style.format.header_size,
            (0, style.format.corner_radius, style.format.corner_radius, 0),
            12,
            style.colors.accent,
            parent=self,
            layer=self.BODY(1),
        )
        self._shadow: RoundedRectangle = RoundedRectangle(
            0.0,
            0.0,
            block_width,
            block_height,
            style.format.corner_radius,
            12,
            style.colors.dark,
            program=get_shadow_shader(),
            parent=self,
            layer=self.SHADOW(),
        )
        self._select: RoundedRectangle = RoundedRectangle(
            0.0,
            0.0,
            block_width + 2 * style.format.select_radius,
            block_height + 2 * style.format.select_radius,
            style.format.corner_radius + style.format.select_radius,
            12,
            style.colors.highlight,
            parent=self,
            layer=self.SPACING(),
        )
        self._select.visible = False

        self._input_connections: dict[
            str, TempValueElement | ConnectionElement | None
        ] = {name: None for name in block.type.inputs}
        self._output_connections: dict[str, list[ConnectionElement]] = {
            name: [] for name in block.type.outputs
        }

    @property
    def block(self) -> Block:
        return self._block

    def contains_point(self, point: tuple[float, float]) -> bool:
        l, b = self._body.position
        w, h = self.get_size()
        return 0 <= point[0] - l <= w and 0 < point[1] - b <= h

    def update_position(self, point: tuple[float, float]) -> None:
        self._body.update_position(point)
        h = self._body.height
        self._select.update_position(
            (
                point[0] - style.format.select_radius,
                point[1] - style.format.select_radius,
            )
        )
        self._header.update_position(
            (point[0], point[1] + h - style.format.header_size)
        )
        self._shadow.update_position(
            (point[0] - style.format.drop_x, point[1] - style.format.drop_y)
        )

        self._title.update_position(
            (
                point[0] + style.format.corner_radius,
                self._header.y + style.format.padding,
            )
        )

        hy = self._header.y
        line_height = style.text.sizes.normal + 3 * style.format.padding
        sub_line_height = style.text.sizes.normal + 2 * style.format.padding

        dx = style.format.padding
        for idx, node in enumerate(self._input_nodes.values()):
            dy = (idx + 1) * line_height
            of = (sub_line_height - node.height) / 2.0
            node.update_position((point[0] + dx, hy - dy + of))

            if self._input_connections[node.name] is not None:
                self._input_connections[node.name].update_end(node.link_pos)

        dx = self.width - style.format.padding
        for idx, node in enumerate(self._output_nodes.values()):
            dy = (idx + 1) * line_height
            of = (sub_line_height - node.height) / 2.0
            node.update_position((point[0] + dx - node.width, hy - dy + of))

            for connection in self._output_connections[node.name]:
                connection.update_start(node.link_pos)

        dx = 2 * style.format.padding + self.input_width
        for idx, panel in enumerate(self._config_panels.values()):
            dy = (idx + 1) * line_height
            of = (sub_line_height - panel.height) / 2.0
            panel.update_position((point[0] + dx, hy - dy + of))

    def get_position(self) -> Point:
        return self._body.get_position()

    def get_size(self) -> tuple[float, float]:
        return self._body.get_size()

    def near_point(self, point: tuple[float, float], radius: float) -> bool:
        l, b = self.left, self.bottom
        w, h = self.width + radius, self.height + radius
        return -radius <= point[0] - l <= w and -radius <= point[1] - b <= h

    def get_nearest_input(self, point: tuple[float, float]) -> tuple[str, float]:
        maximum = float("inf")
        name = ""
        for node in self._input_nodes.values():
            pos = node.center
            dist = (pos[0] - point[0]) ** 2 + (pos[1] - point[1]) ** 2
            if dist < maximum:
                name = node.name
                maximum = dist

        return name, maximum**0.5

    def get_nearest_output(self, point: tuple[float, float]) -> tuple[str, float]:
        maximum = float("inf")
        name = ""
        for node in self._output_nodes.values():
            pos = node.center
            dist = (pos[0] - point[0]) ** 2 + (pos[1] - point[1]) ** 2
            if dist < maximum:
                name = node.name
                maximum = dist

        return name, maximum**0.5

    def get_hovered_config(self, point: tuple[float, float]) -> str | None:
        if not self.contains_point(point):
            return None

        for config, panel in self._config_panels.items():
            if panel.contains_point(point):
                return config
        return None

    def get_input(self, name: str) -> ConnectionNodeElement:
        if name not in self._input_nodes:
            raise KeyError(f"{self._block.type} does not have input {name}")
        return self._input_nodes[name]

    def get_output(self, name: str) -> ConnectionNodeElement:
        if name not in self._output_nodes:
            raise KeyError(f"{self._block.type} does not have outpyt {name}")
        return self._output_nodes[name]

    def get_config(self, name: str) -> TextPanel | BoolPanel:
        if name not in self._config_panels:
            raise KeyError(f"{self._block.type} does not have config {name}")
        return self._config_panels[name]

    def highlight_input(self, name: str, only: bool = True) -> None:
        if name not in self._input_nodes:
            return

        if only:
            for node in self._input_nodes.values():
                if self._block.inputs[node.name] is None:
                    node.active = False

        self._input_nodes[name].active = not self._block.inputs[name]

    def highlight_output(self, name: str, only: bool = True) -> None:
        if name not in self._output_nodes:
            return

        if only:
            for node in self._output_nodes.values():
                if not self._block.outputs[node.name]:
                    node.active = False

        self._output_nodes[name].active = not self._block.outputs[name]

    def remove_highlighting(self) -> None:
        for node in self._input_nodes.values():
            node.active = self._block.inputs[node.name] is not None

        for node in self._output_nodes.values():
            node.active = len(self._block.outputs[node.name]) > 0

    def select(self) -> None:
        self._select.visible = True

    def deselect(self) -> None:
        self._select.visible = False
        self.remove_highlighting()

    def update_config(self, config: dict[str, OperationValue]) -> None:
        for name, value in config.items():
            if value.type is bool:
                self._config_panels[name].active = value.value
            else:
                self._config_panels[name].text = str(value.value)

            self._block.config[name] = value

    @property
    def left(self) -> float:
        return self._body.x

    @property
    def bottom(self) -> float:
        return self._body.y

    @property
    def width(self) -> float:
        return self._body.width

    @property
    def height(self) -> float:
        return self._body.height


class ValueGroup(Element):

    def __init__(
        self,
        values: dict[str, OperationValue],
        input_order: bool = True,
        success_marker: bool = False,
        show_names: bool = True,
        parent: Element | None = None,
        layer: Group | None = None,
        uid: UUID | None = None,
    ):
        Element.__init__(self, parent, layer, uid)
        self._values = values
        self._input_order = input_order

        line_height = style.text.sizes.normal + 2 * style.format.padding
        h, w = 0.0, 0.0
        self._names: list[Label] = []
        self._panels: list[BoolPanel | TextPanel] = []
        self._text_width: float = 0.0
        self._panel_width: float = 0.0
        for name, value in values.items():
            label = Label(
                name if show_names else "",
                0.0,
                0.0,
                0.0,
                font_name=style.text.names.monospace,
                font_size=style.text.sizes.normal,
                color=style.colors.highlight,
                parent=self,
                layer=self.NEXT(),
            )
            self._names.append(label)
            if value.type is bool:
                panel = BoolPanel(parent=self, layer=self.NEXT())
                panel.active = value.value
            else:
                panel = TextPanel(parent=self, layer=self.NEXT())
                panel.text = str(value.value)
            self._panels.append(panel)
            self._text_width = max(self._text_width, label.width)
            self._panel_width = max(self._panel_width, panel.width)
        w = self._text_width + self._panel_width + style.format.padding
        h = len(values) * line_height + (len(values) - 1) * style.format.padding

        self._success: BoolPanel | None = (
            BoolPanel(parent=self, layer=self.NEXT()) if success_marker else None
        )
        if success_marker:
            w += style.format.padding + self._success.width

        self._body = RoundedRectangle(
            0.0,
            0.0,
            w + 3 * style.format.padding,
            h + 2 * style.format.padding,
            style.format.padding,
            color=style.colors.base,
            parent=self,
        )

    def contains_point(self, point: Point) -> bool:
        return self._body.contains_point(point)

    def update_position(self, point: Point) -> None:
        self._body.position = point

        if self._success is not None:
            sx = (
                point[0] + self._body.width - self._success.width - style.format.padding
            )
            sy = point[1] + 0.5 * (self._body.height - self._success.height)
            self._success.update_position((sx, sy))

        if self._input_order:
            tx = point[0] + self._panel_width + 2 * style.format.padding
            px = point[0] + style.format.padding
        else:
            tx = point[0] + style.format.padding
            px = point[0] + self._text_width + 2 * style.format.padding

        line_height = style.text.sizes.normal + 3 * style.format.padding
        y = point[1] + self._body.height
        for idx in range(len(self._values)):
            dy = y - (idx + 1) * line_height
            self._names[idx].update_position(tx, dy)
            self._panels[idx].update_position((px, dy))

    def get_position(self) -> Point:
        return self._body.get_position()

    def get_size(self) -> tuple[float, float]:
        return self._body.get_size()


class TestRunner(Element):

    def __init__(
        self,
        tests: list[TestCase],
    ):
        Element.__init__(self)
        self._tests: list[TestCase] = tests
        self._shown: int = 0

        if not tests:
            raise ValueError("TestRunner requires atleast one test")

        case = self._tests[0]
        self._input: ValueGroup = ValueGroup(
            case.inputs, parent=self, layer=self.BODY(2)
        )
        h = self._input.height
        wi = self._input.width
        if case.outputs is not None:
            out = ValueGroup(case.outputs, False, True, parent=self, layer=self.BODY(2))
            out._success.active = case.complete
            wo = out.width
            h = max(h, out.height)
        else:
            out = None
            wo = 0
        self._output: ValueGroup | None = out

        h += 2 * style.format.padding
        self._input_body = RoundedRectangle(
            0.0,
            0.0,
            wi + 2 * style.format.padding,
            h,
            style.format.padding,
            color=style.colors.background,
            parent=self,
            layer=self.BODY(1),
        )
        self._output_body = RoundedRectangle(
            0.0,
            0.0,
            wo + 2 * style.format.padding,
            h,
            style.format.padding,
            color=style.colors.background,
            parent=self,
            layer=self.BODY(1),
        )

        self._nav_up_button = RoundedRectangle(
            0.0,
            0.0,
            32.0,
            32.0,
            style.format.padding,
            color=style.colors.background,
            parent=self,
            layer=self.BODY(1),
        )
        self._nav_up_icon = Sprite(
            style.game.editor.nav_p, parent=self, layer=self.BODY(2)
        )

        self._run_one_button = RoundedRectangle(
            0.0,
            0.0,
            32.0,
            32.0,
            style.format.padding,
            color=style.colors.background,
            parent=self,
            layer=self.BODY(1),
        )
        self._run_one_icon = Sprite(
            style.game.editor.run_one, parent=self, layer=self.BODY(2)
        )

        self._run_all_button = RoundedRectangle(
            0.0,
            0.0,
            32.0,
            32.0,
            style.format.padding,
            color=style.colors.background,
            parent=self,
            layer=self.BODY(1),
        )
        self._run_all_icon = Sprite(
            style.game.editor.run_all, parent=self, layer=self.BODY(2)
        )

        self._nav_down_button = RoundedRectangle(
            0.0,
            0.0,
            32.0,
            32.0,
            style.format.padding,
            color=style.colors.background,
            parent=self,
            layer=self.BODY(1),
        )
        self._nav_down_icon = Sprite(
            style.game.editor.nav_n, parent=self, layer=self.BODY(2)
        )

        self._buttons = [
            self._nav_up_button,
            self._run_one_button,
            self._run_all_button,
            self._nav_down_button,
        ]
        self._icons = [
            self._nav_up_icon,
            self._run_one_icon,
            self._run_all_icon,
            self._nav_down_icon,
        ]
        self.deselect_buttons()

        self.wb = wb = 32.0 * len(self._buttons) + style.format.padding * (
            len(self._buttons) - 1
        )

        body_width = (
            max(wi + wo + style.format.padding, wb) + 2 * style.format.corner_radius
        )
        body_height = h + 32.0 + style.format.padding + 2 * style.format.corner_radius

        self._body = RoundedRectangle(
            0.0,
            0.0,
            body_width,
            body_height,
            style.format.corner_radius,
            color=style.colors.base,
            parent=self,
            layer=self.BODY(),
        )
        self._shadow = RoundedRectangle(
            0.0,
            0.0,
            body_width,
            body_height,
            style.format.corner_radius,
            color=style.colors.dark,
            program=get_shadow_shader(),
            parent=self,
            layer=self.SHADOW(),
        )

    def contains_point(self, point: tuple[float, float]) -> bool:
        l, b = self._body.position
        w, h = self._body.width, self._body.height
        return 0 <= point[0] - l <= w and 0 <= point[1] - b <= h

    def update_position(self, point: tuple[float, float]) -> None:
        self._body.update_position(point)
        self._shadow.update_position(
            (
                point[0] - 2 * style.format.drop_x,
                point[1] - 2 * style.format.drop_y,
            )
        )

        pw = self._input_body.width + self._output_body.width + style.format.padding
        px = point[0] + (self._body.width - pw) / 2.0
        self._input_body.update_position(
            (
                px,
                point[1] + 32.0 + style.format.padding + style.format.corner_radius,
            )
        )
        self._output_body.update_position(
            (
                px + style.format.padding + self._input_body.width,
                point[1] + 32.0 + style.format.padding + style.format.corner_radius,
            )
        )

        cx = point[0] + (self._body.width - self.wb) / 2.0
        y = point[1] + style.format.corner_radius
        for idx, button in enumerate(self._buttons):
            icon = self._icons[idx]
            dx = cx + (32.0 + style.format.padding) * idx
            button.update_position(dx, y)
            icon.update_position(dx, y)

        self._input.update_position(
            (
                self._input_body.x + style.format.padding,
                self._input_body.y + style.format.padding,
            )
        )

        if self._output is not None:
            self._output.update_position(
                (
                    self._output_body.x + style.format.padding,
                    self._output_body.y + style.format.padding,
                )
            )

    def get_position(self) -> Point:
        return self._body.get_position()

    def get_size(self) -> tuple[float, float]:
        return self._body.get_size()

    def _create_inp_out(self) -> None:
        # TODO: don't assume they'll stay the same size
        case = self._tests[self._shown]
        self.remove_child(self._input)
        self._input.clear_children()
        self._input = ValueGroup(case.inputs, parent=self, layer=self.BODY(2))
        if case.outputs is not None:
            out = ValueGroup(case.outputs, False, True, parent=self, layer=self.BODY(2))
            out._success.active = case.complete
        else:
            out = None

        if self._output is not None:
            self.remove_child(self._output)
            self._output.clear_children()
        self._output = out
        self.update_position(self._body.position)

    def check_test_output(self) -> None:
        if self._output is None or self._output._success is None:
            return

        self._output._success.active = self.get_shown_test().complete

    def update_tests(self, test: list[TestCase]) -> None:
        if not test:
            return
        self._tests = test
        self._shown = self._shown % len(test)
        self._create_inp_out()

    def next_test(self) -> None:
        prev = self._shown
        self._shown = (self._shown + 1) % len(self._tests)
        if self._shown == prev:
            return
        self._create_inp_out()

    def prev_test(self) -> None:
        prev = self._shown
        self._shown = (self._shown - 1) % len(self._tests)
        if self._shown == prev:
            return
        self._create_inp_out()

    def over_nav_up(self, point: tuple[float, float]) -> bool:
        l, b = self._nav_up_button.position
        w, h = self._nav_up_button.width, self._run_one_button.height
        return 0 <= point[0] - l <= w and 0 <= point[1] - b <= h

    def over_run_one(self, point: tuple[float, float]) -> bool:
        l, b = self._run_one_button.position
        w, h = self._run_one_button.width, self._run_one_button.height
        return 0 <= point[0] - l <= w and 0 <= point[1] - b <= h

    def over_run_all(self, point: tuple[float, float]) -> bool:
        l, b = self._run_all_button.position
        w, h = self._run_all_button.width, self._run_all_button.height
        return 0 <= point[0] - l <= w and 0 <= point[1] - b <= h

    def over_nav_down(self, point: tuple[float, float]) -> bool:
        l, b = self._nav_down_button.position
        w, h = self._nav_down_button.width, self._run_one_button.height
        return 0 <= point[0] - l <= w and 0 <= point[1] - b <= h

    def select_nav_up(self) -> None:
        self.deselect_buttons()
        self._nav_up_icon.color = style.colors.highlight

    def select_nav_down(self) -> None:
        self.deselect_buttons()
        self._nav_down_icon.color = style.colors.highlight

    def select_run_one(self) -> None:
        self.deselect_buttons()
        self._run_one_icon.color = style.colors.highlight

    def select_run_all(self) -> None:
        self.deselect_buttons()
        self._run_all_icon.color = style.colors.highlight

    def deselect_buttons(self) -> None:
        for icon in self._icons:
            icon.color = style.colors.base

    def get_shown_test(self) -> TestCase:
        return self._tests[self._shown]

    def get_tests(self) -> list[TestCase]:
        return self._tests


class ResultsPanel(Element):

    def __init__(self, result: BlockComputation):
        Element.__init__(self)
        self._data = ValueGroup(
            result.outputs,
            input_order=False,
            show_names=False,
            parent=self,
            layer=self.BODY(),
        )
        self._shadow = RoundedRectangle(
            0.0,
            0.0,
            self._data.width,
            self._data.height,
            style.format.padding,
            color=style.colors.dark,
            program=get_shadow_shader(),
            parent=self,
            layer=self.SHADOW(),
        )

    def update_position(self, point: Point) -> None:
        self._data.update_position(point)
        self._shadow.position = (
            point[0] - 2 * style.format.drop_x,
            point[1] - 2 * style.format.drop_y,
        )

    def get_position(self) -> Point:
        return self._data.get_position()

    def get_size(self) -> tuple[float, float]:
        return self._data.get_size()
