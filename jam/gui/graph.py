from pyglet.graphics import Batch, Group
from pyglet.text import Label
from pyglet.shapes import RoundedRectangle, Line
from pyglet.sprite import Sprite

from resources import style


# from jam.graphics.line import Line

from jam.node.graph import Block, Connection, BlockComputation, OperationValue, TestCase

from .core import (
    Element,
    get_shadow_shader,
    BASE_PRIMARY,
    BASE_SHADOW,
    BASE_SPACING,
    OVERLAY_PRIMARY,
    OVERLAY_SHADOW,
)

formating = style.format
colors = style.colors


def get_segment_dist_sqr(
    s: tuple[float, float], e: tuple[float, float], p: tuple[float, float]
) -> float:
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
        *,
        links: tuple[tuple[float, float], ...] = (),
    ):
        Element.__init__(self, connection.uid)
        self._batch: Batch | None = None
        # TODO: add style attribute for connection start, and end

        self._connection: Connection = connection

        self._start: tuple[float, float] = start
        self._end: tuple[float, float] = end

        start_link = (start[0] + formating.corner_radius, start[1])
        end_link = (end[0] - formating.corner_radius, end[1])
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

        # self._joints: list[Circle] = [s_joint, m_joint, e_joint]
        # self._shadow_joints: list[Circle] = [s_s_joint, m_s_joint, e_s_joint]

    @property
    def connection(self) -> Connection:
        return self._connection

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

    def contains_point(self, point: tuple[float, float]) -> bool:
        # compute end line
        dist = get_segment_dist_sqr(self._links[-1], self._end, point)
        if dist <= formating.point_radius**2:
            return True

        pos = self._start
        # Check along all lines except end line
        for link in self._links:
            dist = get_segment_dist_sqr(pos, link, point)

            if dist <= formating.point_radius**2:
                return True

            pos = link

        return False

    def connect_renderer(self, batch: Batch | None) -> None:
        self._batch = batch
        for idx in range(len(self._links) + 1):  # fence post problem
            self._lines[idx].batch = batch
            self._shadow_lines[idx].batch = batch

        # for idx in range(len(self._links)):
        #     self._joints[idx].batch = batch
        #     self._shadow_joints[idx].batch = batch

    def update_start(self, point: tuple[float, float]) -> None:
        self._start = point

        link = point[0] + formating.corner_radius, point[1]
        link2 = self._links[1]
        self._links[0] = link

        self._lines[0].position = point
        self._lines[1].position = link
        self._lines[0].x2, self._lines[0].y2 = link
        self._lines[1].x2, self._lines[1].y2 = link2
        # self.joint[0].position = link

        shadow_point = (point[0] - formating.drop_x, point[1] - formating.drop_y)
        shadow_link = shadow_point[0] + formating.corner_radius, shadow_point[1]
        shadow_link2 = link2[0] - formating.drop_x, link2[1] - formating.drop_y

        self._shadow_lines[0].position = shadow_point
        self._shadow_lines[1].position = shadow_link
        self._shadow_lines[0].x2, self._shadow_lines[0].y2 = shadow_link
        self._shadow_lines[1].x2, self._shadow_lines[1].y2 = shadow_link2
        # self._shadow_joints[0].position = shadow_link

    def update_end(self, point: tuple[float, float]) -> None:
        self._end = point

        link = point[0] - formating.corner_radius, point[1]
        self._links[-1] = link

        self._lines[-1].position = link
        self._lines[-2].x2, self._lines[-2].y2 = link
        self._lines[-1].x2, self._lines[-1].y2 = point
        # self._joints[-1].position = link

        shadow_point = (point[0] - formating.drop_x, point[1] - formating.drop_y)
        shadow_link = shadow_point[0] - formating.corner_radius, shadow_point[1]

        self._shadow_lines[-1].position = shadow_link
        self._shadow_lines[-2].x2, self._shadow_lines[-2].y2 = shadow_link
        self._shadow_lines[-1].x2, self._shadow_lines[-1].y2 = shadow_point
        # self._shadow_joints[-1].position = shadow_point

    def update_link(self, link: int, point: tuple[float, float]) -> None:
        if not 0 < link < len(self._links):
            return  # ignore the start and end links

        self._links[link] = point
        n_link = self._links[link + 1]

        # self._joints[link].position = point
        # self._shadow_joints[link] = shadow

        pl = self._lines[link]
        nl = self._lines[link + 1]

        ps = self._shadow_lines[link]
        ns = self._shadow_lines[link + 1]

        pl.x2, pl.y2 = point
        ps.x2, ps.y2 = point[0] - formating.drop_x, point[1] - formating.drop_y

        nl.position = point
        nl.x2, nl.y2 = n_link

        ns.position = point[0] - formating.drop_x, point[1] - formating.drop_y
        ns.x2, ns.y2 = n_link[0] - formating.drop_x, n_link[1] - formating.drop_y

    def insert_link(self, link: int, point: tuple[float, float]) -> None:
        if not 0 < link < len(self._links):
            return  # ignore the start and end links
        old_start = self._links[link - 1]
        old_end = self._links[link]

        o_line = self._lines[link]
        o_line.position = point
        o_line.x2, o_line.y2 = old_end

        o_s_line = self._shadow_lines[link]
        o_s_line.position = point[0] - formating.drop_x, point[1] - formating.drop_y
        o_s_line.x2, o_s_line.y2 = (
            old_end[0] - formating.drop_x,
            old_end[1] - formating.drop_y,
        )

        n_line, n_s_line = self._create_link(old_start, point)

        self._lines.insert(link, n_line)
        # self._joints.insert(link, n_joint)
        self._shadow_lines.insert(link, n_s_line)
        # self._shadow_joints.insert(link, n_s_joint)
        self._links.insert(link, point)

    def remove_link(self, link: int) -> None:
        if not 2 <= link + 1 < len(self._links):
            return  # ignore the start and end

        new_start = self._links[link - 1]
        new_shadow = new_start[0] - formating.drop_x, new_start[1] - formating.drop_y

        self._lines.pop(link).batch = None
        # self._joints.pop(link).batch = None
        self._shadow_lines.pop(link).batch = None
        # self._shadow_joints.pop(link).batch = None
        self._links.pop(link)

        old_end = self._links[link]
        old_shadow = old_end[0] - formating.drop_x, old_end[1] - formating.drop_y

        line = self._lines[link]
        shadow = self._shadow_lines[link]

        line.position = new_start
        line.x2, line.y2 = old_end
        shadow.position = new_shadow
        shadow.x2, shadow.y2 = old_shadow

    def _create_link(
        self, start: tuple[float, float], end: tuple[float, float]
    ) -> tuple[Line, Line]:
        shadow_start = start[0] - formating.drop_x, start[1] - formating.drop_y
        shadow_end = end[0] - formating.drop_x, end[1] - formating.drop_y
        line = Line(
            *start,
            *end,
            formating.line_thickness,
            color=colors.highlight,
            batch=self._batch,
            group=BASE_PRIMARY,
        )
        # joint = Circle(
        #     *end,
        #     formating.line_thickness / 2.0,
        #     color=colors.highlight,
        #     batch=self._batch,
        #     group=BASE_PRIMARY,
        # )
        shadow_line = Line(
            *shadow_start,
            *shadow_end,
            formating.line_thickness,
            color=colors.dark,
            batch=self._batch,
            program=get_shadow_shader(),
            group=BASE_SHADOW,
        )
        # shadow_joint = Circle(
        #     *shadow_end,
        #     formating.line_thickness / 2.0,
        #     color=colors.dark,
        #     batch=self._batch,
        #     program=get_shadow_shader(),
        #     group=BASE_SHADOW,
        # )

        return line, shadow_line


class TextPanel(Element):

    def __init__(self, char_count: int = 6, group: Group = BASE_PRIMARY):
        self._text: Label = Label(
            "#" * char_count,
            0.0,
            0.0,
            0.0,
            font_name=style.text.normal.name,
            font_size=style.text.normal.size,
            color=colors.accent,
            group=group,
        )
        self._text_width = self._text.content_width
        self._panel: RoundedRectangle = RoundedRectangle(
            0.0,
            0.0,
            self._text.content_width + 2 * formating.padding,
            style.text.normal.size + 2 * formating.padding,
            formating.padding,
            4,
            colors.background,
            group=group,
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

    def update_position(self, point: tuple[float, float]) -> None:
        self._panel.position = point
        self._text.position = (
            point[0] + formating.padding,
            point[1] + formating.padding,
            0.0,
        )

    def contains_point(self, point: tuple[float, float]) -> bool:
        l, b = self._panel.position
        w, h = self._panel._width, self._panel._height

        return 0 <= point[0] - l <= w and 0 <= point[1] - b <= h

    def connect_renderer(self, batch: Batch | None = None) -> None:
        self._panel.batch = batch
        self._text.batch = batch


class BoolPanel(Element):

    def __init__(self, active: bool = False, group: Group = BASE_PRIMARY):
        self._active: bool = active
        self._sprite = Sprite(
            style.game.editor.check_inactive,
            0.0,
            0.0,
            0.0,
            group=group,
        )
        # self._sprite.color = colors.highlight
        if active:
            self._sprite.image = style.game.editor.check_active

    def connect_renderer(self, batch: Batch | None = None) -> None:
        self._sprite.batch = batch  # type: Ignore -- None

    def update_position(self, point: tuple[float, float]) -> None:
        self._sprite.position = point[0], point[1], 0.0

    def contains_point(self, point: tuple[float, float]) -> bool:
        l, b, *_ = self._sprite.position
        w, h = self._sprite.width, self._sprite.height
        return 0 <= point[0] - l <= w and 0 <= point[1] - b <= h

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

    @property
    def width(self) -> float:
        return self._sprite.height

    @property
    def height(self) -> float:
        return self._sprite.width


class ConnectionNodeElement(Element):

    def __init__(self, name: str = "", is_input: bool = True):
        Element.__init__(self)
        self._sprite = Sprite(
            style.game.editor.node_inactive,
            0.0,
            0.0,
            0.0,
            group=BASE_PRIMARY,
        )
        self._sprite.width = 2 * formating.point_radius
        self._sprite.height = 2 * formating.point_radius

        self._name: str = name
        self._label: Label | None = None
        if self._name:
            self._label = Label(
                name,
                0.0,
                0.0,
                0.0,
                font_name=style.text.normal.name,
                font_size=style.text.normal.size,
                color=colors.highlight,
                anchor_y="bottom",
                group=BASE_PRIMARY,
            )

        self._is_input: bool = is_input

        self._active: bool = False
        self._branch: bool = False

    def update_position(self, point: tuple[float, float]) -> None:
        s_x = point[0]
        if self._label is not None:
            l_x = point[0] + self._sprite.width + formating.padding
            if not self._is_input:
                s_x = point[0] + self._label.content_width + formating.padding
                l_x = point[0]

            l_y = point[1] + (self._sprite.height - self._label.content_height) / 2.0
            self._label.position = l_x, l_y + 1, 0.0
        self._sprite.position = s_x, point[1], 0.0

    def connect_renderer(self, batch: Batch | None) -> None:
        self._sprite.batch = batch  # type: ignore -- None
        if self._label is not None:
            self._label.batch = batch

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

    @property
    def width(self) -> float:
        if self._label is None:
            return self._sprite.width
        return self._sprite.width + formating.padding + self._label.content_width

    @property
    def height(self) -> float:
        return self._sprite.height


class TempValueElement(Element):

    def __init__(self, block: Block, connection: Connection):
        self._block = block
        self._connection = connection
        self._type: type[OperationValue] = block.type.outputs[connection.output]
        Element.__init__(self, block.uid)

        if self._type._typ is bool:
            self._panel = BoolPanel()
        else:
            self._panel = TextPanel()
            self._panel.text = str(block.config[connection.output].value)

        self._line = Line(
            0.0,
            0.0,
            1.0,
            1.0,
            formating.line_thickness,
            colors.highlight,
            group=BASE_PRIMARY,
        )

        self._panel_shadow = RoundedRectangle(
            0.0,
            0.0,
            self._panel.width,
            self._panel.height,
            formating.padding,
            12,
            colors.dark,
            program=get_shadow_shader(),
            group=BASE_SHADOW,
        )
        self._line_shadow = Line(
            0.0,
            0.0,
            1.0,
            1.0,
            formating.line_thickness,
            colors.dark,
            program=get_shadow_shader(),
            group=BASE_SHADOW,
        )

    @property
    def block(self) -> Block:
        return self._block

    @property
    def connection(self) -> Connection:
        return self._connection

    def update_end(self, point: tuple[float, float]) -> None:
        link = point[0] - formating.corner_radius, point[1]

        shadow_point = point[0] - formating.drop_x, point[1] - formating.drop_y
        shadow_link = link[0] - formating.drop_x, link[1] - formating.drop_y

        self._line.position = link
        self._line.x2, self._line.y2 = point

        self._line_shadow.position = shadow_link
        self._line_shadow.x2, self._line_shadow.y2 = shadow_point

        panel_pos = link[0] - self._panel.width, link[1] - self._panel.height * 0.5
        shadow_pos = panel_pos[0] - formating.drop_x, panel_pos[1] - formating.drop_y

        self._panel.update_position(panel_pos)
        self._panel_shadow.position = shadow_pos

    def get_hovered_config(self, point: tuple[float, float]) -> str | None:
        if not self.contains_point(point):
            return None
        return self._connection.output

    def get_config(self, name: str) -> TextPanel | BoolPanel:
        if name not in self.block.config:
            raise KeyError(f"{name} not a config of block type {self.block.type}")
        return self._panel

    def update_position(self, point: tuple[float, float]) -> None:
        self.update_end(point)

    def contains_point(self, point: tuple[float, float]) -> bool:
        return self._panel.contains_point(point)

    def connect_renderer(self, batch: Batch | None) -> None:
        self._panel.connect_renderer(batch)
        self._panel_shadow.batch = batch
        self._line.batch = batch
        self._line_shadow.batch = batch


class BlockElement(Element):

    def __init__(self, block: Block):
        super().__init__(block.uid)
        self._block = block

        self._input_nodes: dict[str, ConnectionNodeElement] = {}
        self._output_nodes: dict[str, ConnectionNodeElement] = {}
        self._config_panels: dict[str, TextPanel | BoolPanel] = {}

        body_width = formating.padding
        self.input_width = 0.0
        if block.type.inputs:
            for name in block.type.inputs:
                node = ConnectionNodeElement(name)
                self.input_width = max(node.width, self.input_width)
                self._input_nodes[name] = node
            body_width += self.input_width + formating.padding

        self.output_width = 0.0
        if block.type.outputs:
            for name in block.type.outputs:
                node = ConnectionNodeElement(name, False)
                self.output_width = max(node.width, self.output_width)
                self._output_nodes[name] = node
            body_width += self.output_width + formating.padding

        self.config_width = 0.0
        if block.type.config:
            for name, typ in block.type.config.items():
                if typ._typ is bool:
                    panel = BoolPanel()
                else:
                    panel = TextPanel()
                    panel.text = str(block.config[name].value)
                self.config_width = max(panel.width, self.config_width)
                self._config_panels[name] = panel
            body_width += self.config_width + formating.padding

        row_count = max(
            len(block.type.inputs), len(block.type.config), len(block.type.outputs)
        )
        body_height = row_count * (style.text.normal.size + 3 * formating.padding)

        self._title: Label = Label(
            block.type.name,
            0.0,
            0.0,
            0.0,
            anchor_y="bottom",
            font_name=style.text.normal.name,
            font_size=style.text.normal.size,
            color=colors.base,
            group=BASE_PRIMARY,
        )
        title_width = self._title.content_width + 2 * formating.corner_radius

        block_width = max(body_width, title_width)
        block_height = formating.header_size + body_height + formating.footer_size
        self._body: RoundedRectangle = RoundedRectangle(
            0.0,
            0.0,
            block_width,
            block_height,
            formating.corner_radius,
            12,
            colors.base,
            group=BASE_PRIMARY,
        )
        self._header: RoundedRectangle = RoundedRectangle(
            0.0,
            0.0,
            block_width,
            formating.header_size,
            (0, formating.corner_radius, formating.corner_radius, 0),
            12,
            colors.accent,
            group=BASE_PRIMARY,
        )
        self._shadow: RoundedRectangle = RoundedRectangle(
            0.0,
            0.0,
            block_width,
            block_height,
            formating.corner_radius,
            12,
            colors.dark,
            program=get_shadow_shader(),
            group=BASE_SHADOW,
        )
        self._select: RoundedRectangle = RoundedRectangle(
            0.0,
            0.0,
            block_width + 2 * formating.select_radius,
            block_height + 2 * formating.select_radius,
            formating.corner_radius + formating.select_radius,
            12,
            colors.highlight,
            group=BASE_SPACING,
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

    def connect_renderer(self, batch: Batch | None) -> None:
        self._shadow.batch = batch
        self._select.batch = batch
        self._body.batch = batch
        self._header.batch = batch

        self._title.batch = batch

        for node in self._input_nodes.values():
            node.connect_renderer(batch)

        for node in self._output_nodes.values():
            node.connect_renderer(batch)

        for panel in self._config_panels.values():
            panel.connect_renderer(batch)

    def update_position(self, point: tuple[float, float]) -> None:
        self._body.position = point
        self._select.position = (
            point[0] - formating.select_radius,
            point[1] - formating.select_radius,
        )
        self._header.position = (
            point[0],
            point[1] + self._body.height - formating.header_size,
        )
        self._shadow.position = point[0] - formating.drop_x, point[1] - formating.drop_y

        self._title.position = (
            point[0] + formating.corner_radius,
            self._header.y + formating.padding,
            0.0,
        )

        line_height = style.text.normal.size + 3 * formating.padding

        dx = formating.padding
        for idx, node in enumerate(self._input_nodes.values()):
            dy = (idx + 1) * line_height
            of = (style.text.normal.size + 2 * formating.padding - node.height) / 2.0
            node.update_position((point[0] + dx, self._header.y - dy + of))

            if self._input_connections[node.name] is not None:
                self._input_connections[node.name].update_end(node.link_pos)

        dx = self.width - formating.padding
        for idx, node in enumerate(self._output_nodes.values()):
            dy = (idx + 1) * line_height
            of = (style.text.normal.size + 2 * formating.padding - node.height) / 2.0
            node.update_position((point[0] + dx - node.width, self._header.y - dy + of))

            for connection in self._output_connections[node.name]:
                connection.update_start(node.link_pos)

        dx = 2 * formating.padding + self.input_width
        for idx, panel in enumerate(self._config_panels.values()):
            dy = (idx + 1) * line_height
            of = (style.text.normal.size + 2 * formating.padding - panel.height) / 2.0
            panel.update_position((point[0] + dx, self._header.y - dy + of))

    def contains_point(self, point: tuple[float, float]) -> bool:
        l, b = self._body.position
        return 0 <= point[0] - l <= self.width and 0 < point[1] - b <= self.height

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
    ):
        Element.__init__(self)
        self._values = values
        self._input_order = input_order

        line_height = style.text.normal.size + 2 * formating.padding
        h, w = 0.0, 0.0
        self._names: list[Label] = []
        self._panels: list[BoolPanel | TextPanel] = []
        self._text_width: float = 0.0
        self._panel_width: float = 0.0
        for name, value in values.items():
            label = Label(
                name,
                0.0,
                0.0,
                0.0,
                font_name=style.text.normal.name,
                font_size=style.text.normal.size,
                color=colors.highlight,
                group=OVERLAY_PRIMARY,
            )
            self._names.append(label)
            if value.type is bool:
                panel = BoolPanel(group=OVERLAY_PRIMARY)
                panel.active = value.value
            else:
                panel = TextPanel(group=OVERLAY_PRIMARY)
                panel.text = str(value.value)
            self._panels.append(panel)
            self._text_width = max(self._text_width, label.content_width)
            self._panel_width = max(self._panel_width, panel.width)
        w = self._text_width + self._panel_width + formating.padding
        h = len(values) * line_height + (len(values) - 1) * formating.padding

        self._success: BoolPanel | None = (
            BoolPanel(group=OVERLAY_PRIMARY) if success_marker else None
        )
        if success_marker:
            w += formating.padding + self._success.width

        self._body = RoundedRectangle(
            0.0,
            0.0,
            w + 3 * formating.padding,
            h + 2 * formating.padding,
            formating.padding,
            color=colors.base,
            group=OVERLAY_PRIMARY,
        )

    @property
    def width(self) -> float:
        return self._body.width

    @property
    def height(self) -> float:
        return self._body.height

    def connect_renderer(self, batch: Batch | None) -> None:
        self._body.batch = batch
        for panel in self._panels:
            panel.connect_renderer(batch)
        for name in self._names:
            name.batch = batch
        if self._success is not None:
            self._success.connect_renderer(batch)

    def contains_point(self, point: tuple[float, float]) -> bool:
        l, b = self._body.position
        w, h = self._body.width, self._body.height
        return 0 <= point[0] - l <= w and 0 <= point[1] - b <= h

    def update_position(self, point: tuple[float, float]) -> None:
        self._body.position = point

        if self._success is not None:
            sx = point[0] + self._body.width - self._success.width - formating.padding
            sy = point[1] + 0.5 * (self._body.height - self._success.height)
            self._success.update_position((sx, sy))

        if self._input_order:
            tx = point[0] + self._panel_width + 2 * formating.padding
            px = point[0] + formating.padding
        else:
            tx = point[0] + formating.padding
            px = point[0] + self._text_width + 2 * formating.padding

        line_height = style.text.normal.size + 3 * formating.padding
        y = point[1] + self._body.height
        for idx in range(len(self._values)):
            dy = y - (idx + 1) * line_height
            self._names[idx].position = tx, dy, 0.0
            self._panels[idx].update_position((px, dy))


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
        self._input: ValueGroup = ValueGroup(case.inputs)
        h = self._input.height
        wi = self._input.width
        if case.outputs is not None:
            out = ValueGroup(case.outputs, False, True)
            wo = out.width
            h = max(h, out.height)
        else:
            out = None
            wo = 0
        self._output: ValueGroup | None = out

        h += 2 * formating.padding
        self._input_body = RoundedRectangle(
            0.0,
            0.0,
            wi + 2 * formating.padding,
            h,
            formating.padding,
            color=colors.background,
            group=OVERLAY_PRIMARY,
        )
        self._output_body = RoundedRectangle(
            0.0,
            0.0,
            wo + 2 * formating.padding,
            h,
            formating.padding,
            color=colors.background,
            group=OVERLAY_PRIMARY,
        )

        self._nav_up_button = RoundedRectangle(
            0.0,
            0.0,
            32.0,
            32.0,
            formating.padding,
            color=colors.background,
            group=OVERLAY_PRIMARY,
        )
        self._nav_up_icon = Sprite(style.game.editor.nav_p, group=OVERLAY_PRIMARY)

        self._run_one_button = RoundedRectangle(
            0.0,
            0.0,
            32.0,
            32.0,
            formating.padding,
            color=colors.background,
            group=OVERLAY_PRIMARY,
        )
        self._run_one_icon = Sprite(style.game.editor.run_one, group=OVERLAY_PRIMARY)

        self._run_all_button = RoundedRectangle(
            0.0,
            0.0,
            32.0,
            32.0,
            formating.padding,
            color=colors.background,
            group=OVERLAY_PRIMARY,
        )
        self._run_all_icon = Sprite(style.game.editor.run_all, group=OVERLAY_PRIMARY)

        self._nav_down_button = RoundedRectangle(
            0.0,
            0.0,
            32.0,
            32.0,
            formating.padding,
            color=colors.background,
            group=OVERLAY_PRIMARY,
        )
        self._nav_down_icon = Sprite(style.game.editor.nav_n, group=OVERLAY_PRIMARY)

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

        self.wb = wb = 32.0 * len(self._buttons) + formating.padding * (
            len(self._buttons) - 1
        )

        body_width = max(wi + wo + formating.padding, wb) + 2 * formating.corner_radius
        body_height = h + 32.0 + formating.padding + 2 * formating.corner_radius

        self._body = RoundedRectangle(
            0.0,
            0.0,
            body_width,
            body_height,
            formating.corner_radius,
            color=colors.base,
            group=OVERLAY_PRIMARY,
        )
        self._shadow = RoundedRectangle(
            0.0,
            0.0,
            body_width,
            body_height,
            formating.corner_radius,
            color=colors.dark,
            program=get_shadow_shader(),
            group=OVERLAY_SHADOW,
        )

    def contains_point(self, point: tuple[float, float]) -> bool:
        l, b = self._body.position
        w, h = self._body.width, self._body.height
        return 0 <= point[0] - l <= w and 0 <= point[1] - b <= h

    def update_position(self, point: tuple[float, float]) -> None:
        self._body.position = point
        self._shadow.position = (
            point[0] - 2 * formating.drop_x,
            point[1] - 2 * formating.drop_y,
        )

        pw = self._input_body.width + self._output_body.width + formating.padding
        px = point[0] + (self._body.width - pw) / 2.0
        self._input_body.position = (
            px,
            point[1] + 32.0 + formating.padding + formating.corner_radius,
        )
        self._output_body.position = (
            px + formating.padding + self._input_body.width,
            point[1] + 32.0 + formating.padding + formating.corner_radius,
        )

        cx = point[0] + (self._body.width - self.wb) / 2.0
        y = point[1] + formating.corner_radius
        for idx, button in enumerate(self._buttons):
            icon = self._icons[idx]
            dx = cx + (32.0 + formating.padding) * idx
            button.position = dx, y
            icon.position = dx, y, 0.0

        self._input.update_position(
            (
                self._input_body.x + formating.padding,
                self._input_body.y + formating.padding,
            )
        )

        if self._output is not None:
            self._output.update_position(
                (
                    self._output_body.x + formating.padding,
                    self._output_body.y + formating.padding,
                )
            )

    def connect_renderer(self, batch: Batch | None) -> None:
        self._body.batch = batch
        self._shadow.batch = batch
        self._input_body.batch = batch
        self._output_body.batch = batch
        for button in self._buttons:
            button.batch = batch
        for icon in self._icons:
            icon.batch = batch
        self._input.connect_renderer(batch)
        if self._output is not None:
            self._output.connect_renderer(batch)

    def _create_inp_out(self):
        # TODO: don't assume they'll stay the same size
        case = self._tests[self._shown]
        self._input: ValueGroup = ValueGroup(case.inputs)
        if case.outputs is not None:
            out = ValueGroup(case.outputs, False, True)
        else:
            out = None
        self._output: ValueGroup | None = out

        self._input.connect_renderer(self._body.batch)
        self._output.connect_renderer(self._body.batch)

        self.update_position(self._body.position)

    def check_test_output(self):
        if self._output is None:
            return

        if self._output._success is None:
            return

        self._output._success.active = self.get_shown_test().complete

    def update_tests(self, test: list[TestCase]) -> None:
        if not test:
            return
        self._tests = test
        self._shown = self._shown % len(test)
        self._create_inp_out()

    def next_test(self):
        prev = self._shown
        self._shown = (self._shown + 1) % len(self._tests)
        if self._shown == prev:
            return
        self._create_inp_out()

    def prev_test(self):
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
        self._nav_up_icon.color = colors.highlight

    def select_nav_down(self) -> None:
        self.deselect_buttons()
        self._nav_down_icon.color = colors.highlight

    def select_run_one(self) -> None:
        self.deselect_buttons()
        self._run_one_icon.color = colors.highlight

    def select_run_all(self) -> None:
        self.deselect_buttons()
        self._run_all_icon.color = colors.highlight

    def deselect_buttons(self) -> None:
        for icon in self._icons:
            icon.color = colors.base

    def get_shown_test(self) -> TestCase:
        return self._tests[self._shown]

    def get_tests(self) -> list[TestCase]:
        return self._tests


class ResultsPanel(Element):

    def __init__(self, result: BlockComputation):
        Element.__init__(self)
        self._data = ValueGroup(result.outputs, input_order=False)
        self._shadow = RoundedRectangle(
            0.0,
            0.0,
            self._data.width,
            self._data.height,
            formating.padding,
            color=colors.dark,
            program=get_shadow_shader(),
            group=OVERLAY_SHADOW,
        )

    def connect_renderer(self, batch: Batch | None) -> None:
        self._data.connect_renderer(batch)
        self._shadow.batch = batch

    def update_position(self, point: tuple[float, float]) -> None:
        self._data.update_position(point)
        self._shadow.position = (
            point[0] - 2 * formating.drop_x,
            point[1] - 2 * formating.drop_y,
        )
