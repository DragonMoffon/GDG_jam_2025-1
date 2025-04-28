from pyglet.graphics import Batch
from pyglet.text import Label
from pyglet.shapes import RoundedRectangle, Line, Circle
from pyglet.sprite import Sprite

from resources import style

from jam.node.graph import (
    Value,
    Block,
    Connection,
    BlockComputation,
    OperationValue,
)
from .core import Element, get_shadow_shader

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
    ):
        Element.__init__(self, connection.uid)
        self._batch: Batch | None = None
        # TODO: add style attribute for connection start, and end

        self._connection: Connection = connection

        self._start: tuple[float, float] = start
        self._end: tuple[float, float] = end

        start_link = (start[0] + formating.corner_radius, start[1])
        end_link = (end[0] - formating.corner_radius, end[1])
        self._links: list[tuple[float, float]] = [start_link, end_link]

        s_line, s_joint, s_s_line, s_s_joint = self._create_link(start, start_link)
        m_line, m_joint, m_s_line, m_s_joint = self._create_link(start_link, end_link)
        e_line, e_joint, e_s_line, e_s_joint = self._create_link(end_link, end)

        self._lines: list[Line] = [s_line, m_line, e_line]
        self._joints: list[Circle] = [s_joint, m_joint, e_joint]

        self._shadow_lines: list[Line] = [s_s_line, m_s_line, e_s_line]
        self._shadow_joints: list[Circle] = [s_s_joint, m_s_joint, e_s_joint]

    def get_closest_link(self, point: tuple[float, float]) -> tuple[int, float]:
        smallest = float("inf")
        link_idx = 0
        for idx, link in enumerate(self._links):
            dist = (link[0] - point[0]) ** 2 + (link[1] - point[1]) ** 2
            if dist <= smallest:
                smallest = dist
                link_idx = idx
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

        for idx in range(len(self._links)):
            self._joints[idx].batch = batch
            self._shadow_joints[idx].batch = batch

    def update_start(self, point: tuple[float, float]) -> None:
        self._start = point

        link = point[0] + formating.corner_radius, point[1]
        self._links[0] = link

        self._lines[0].position = point
        self._lines[0].x2, self._lines[0].y2 = link
        self.joint[0].position = link

        shadow_point = (point[0] - formating.drop_x, point[1] - formating.drop_y)
        shadow_link = shadow_point[0] + formating.corner_radius, shadow_point[1]

        self._shadow_lines[0].position = shadow_point
        self._shadow_lines[0].x2, self._shadow_lines[0].y2 = shadow_link
        self._shadow_joints[0].position = shadow_link

    def update_end(self, point: tuple[float, float]) -> None:
        self._end = point

        link = point[-1] - formating.corner_radius, point[1]
        self._links[-1] = link

        self._lines[-1].position = point
        self._lines[-1].x2, self._lines[0].y2 = link
        self.joint[-1].position = link

        shadow_point = (point[0] - formating.drop_x, point[1] - formating.drop_y)
        shadow_link = shadow_point[0] - formating.corner_radius, shadow_point[1]

        self._shadow_lines[-1].position = shadow_point
        self._shadow_lines[-1].x2, self._shadow_lines[-1].y2 = shadow_link
        self._shadow_joints[-1].position = shadow_link

    def update_link(self, link: int, point: tuple[float, float]) -> None:
        if not 2 <= link + 1 < len(self._links):
            return  # ignore the start and end links

        shadow = point[0] - formating.drop_x, point[1] - formating.drop_y

        self._links[link] = point

        self._joints[link].position = point
        self._shadow_joints[link] = shadow

        self._lines[link].x2, self._lines[link].y2 = point
        self._shadow_lines[link].x2, self._shadow_lines[link].y2 = shadow

        self._lines[link + 1].position = point
        self._lshadow_ines[link + 1].position = shadow

    def insert_link(self, link: int, point: tuple[float, float]) -> None:
        if not 2 <= link + 1 < len(self._links):
            return  # ignore the start and end links
        old_start = self._links[link - 1]

        o_line = self._lines[link]
        o_line.position = point

        o_s_line = self._shadow_lines[link]
        o_s_line.position = point[0] - formating.drop_x, point[1] - formating.drop_y

        n_line, n_joint, n_s_line, n_s_joint = self._create_link(old_start, point)

        self._lines.insert(link, n_line)
        self._joints.insert(link, n_joint)
        self._shadow_lines.insert(link, n_s_line)
        self._shadow_joints.insert(link, n_s_joint)
        self._links.insert(link, point)

    def remove_link(self, link: int) -> None:
        if not 2 <= link + 1 < len(self._links):
            return  # ignore the start and end

        new_start = self._links[link - 1]
        new_shadow = new_start[0] - formating.drop_x, new_start[1] - formating.drop_y

        self._lines.pop(link).batch = None
        self._joints.pop(link).batch = None
        self._shadow_lines.pop(link).batch = None
        self._shadow_joints.pop(link).batch = None
        self._links.pop(link)

        self._lines[link].position = new_start
        self._shadow_lines[link].position = new_shadow

    def _create_link(
        self, start: tuple[float, float], end: tuple[float, float]
    ) -> tuple[Line, Circle, Line, Circle]:
        shadow_start = start[0] - formating.drop_x, start[1] - formating.drop_y
        shaodw_end = end[0] - formating.drop_x, end[1] - formating.drop_y
        line = Line(
            *start, *end, formating.line_thickness, colors.highlight, batch=self._batch
        )
        joint = Circle(
            *end, formating.line_thickness / 2.0, colors.highlight, batch=self._batch
        )
        shadow_line = Line(
            *shadow_start,
            *shaodw_end,
            formating.line_thickness,
            colors.dark,
            batch=self._batch,
            program=get_shadow_shader(),
        )
        shadow_joint = Circle(
            *shaodw_end,
            formating.line_thickness / 2.0,
            colors.dark,
            batch=self._batch,
            program=get_shadow_shader(),
        )

        return line, joint, shadow_line, shadow_joint


ALPHABET_SET = set(chr(n) for n in range(97, 123))
DIGIT_SET = set(chr(n) for n in range(48, 59))
DECIMAL_SET = DIGIT_SET.union(["."])


class TextPanel(Element):

    def __init__(self, char_count: int = 6, charset: set[str] | None = None):
        self._text: Label = Label(
            "#" * char_count,
            0.0,
            0.0,
            0.0,
            anchor_y="bottom",
            font_name=style.text.normal.name,
            font_size=style.text.normal.size,
        )
        self._panel: RoundedRectangle = RoundedRectangle(
            0.0,
            0.0,
            self._text.content_width + 2 * formating.padding,
            self._text.content_height + 2 * formating.padding,
            formating.padding,
            4,
            colors.accent,
        )

        self._charset: set[str] | None = charset

    @property
    def width(self) -> float:
        return self._panel.width

    @property
    def height(self) -> float:
        return self._panel.height

    def update_position(self, point: tuple[float, float]) -> None:
        self._panel.position = point
        self._text.position = (
            point[0] + formating.padding,
            point[1] + formating.padding,
            0.0,
        )

    def connect_renderer(self, batch: Batch | None = None) -> None:
        self._panel.batch = batch
        self._text.batch = batch


class BoolPanel(Element):

    def __init__(self, active: bool = False):
        self._active: bool = active
        self._sprite = Sprite(style.game.editor.check_inactive, 0.0, 0.0, 0.0)
        if active:
            self._sprite.image = style.game.editor.check_active

    def connect_renderer(self, batch: Batch | None = None) -> None:
        self._sprite.batch = batch  # type: Ignore -- None

    def update_position(self, point: tuple[float, float]) -> None:
        self._sprite.position = point

    @property
    def active(self) -> bool:
        return self._active

    @active.setter
    def active(self, active: bool):
        self._active = active
        if active:
            self._sprite.image = style.game.editor.check_active
        else:
            self._sprite.image = style.game.editor.check_inactive


class ConnectionNodeElement(Element):

    def __init__(self, name: str = "", is_input: bool = True):
        Element.__init__(self)
        self._sprite = Sprite(style.game.editor.node_inactive, 0.0, 0.0, 0.0)
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
                anchor_x="left" if is_input else "right",
                anchor_y="center",
            )

        self._is_input: bool = is_input

        self._active: bool = False
        self._branch: bool = False

    def update_position(self, point: tuple[float, float]) -> None:
        self._sprite.position = point[0], point[1], 0.0
        if self._label is not None:
            dx = (
                self._sprite.width + formating.padding
                if self._is_input
                else -formating.padding
            )
            dy = self._sprite.height / 2.0 + formating.padding
            self._label.position = point[0] + dx, point[1] + dy

    def connect_renderer(self, batch: Batch | None) -> None:
        self._sprite.batch = batch  # type: ignore -- None
        if self._label is not None:
            self._label.batch = batch

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

    @active.setter
    def active(self, branch: bool) -> None:
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
        return self._sprite.x + self._sprite.width.y

    @property
    def width(self) -> float:
        if self._label is None:
            return self._sprite.width
        return self._sprite.width + formating.padding + self._label.content_width

    @property
    def height(self) -> float:
        if self._label is None:
            return self._sprite.height
        return max(self._sprite.height, self._label.content_height)


class TempValueElement(Element):

    def __init__(self, position: tuple[float, float], value: OperationValue):
        pass

    def update_end(self, point: tuple[float, float]):
        pass


class BlockElement(Element):

    def __init__(self, block: Block):
        super().__init__(block.uid)
        self._bottom_left = (0.0, 0.0)
        self._block = block

        self._input_nodes: dict[str, ConnectionNodeElement] = {
            ConnectionNodeElement(name) for name in block.type.inputs
        }

        self._output_nodes: dict[str, ConnectionNodeElement] = {
            ConnectionNodeElement(name) for name in block.type.outputs
        }

        self._text_panels: dict[str, TextPanel | BoolPanel] = {
            (
                (
                    BoolPanel()
                    if typ.type is bool
                    else TextPanel(
                        charset=(
                            ALPHABET_SET
                            if typ.type is str
                            else (DIGIT_SET if typ.type is int else DECIMAL_SET)
                        )
                    )
                )
                for typ in block.type.config.values()
            )
        }

        self._title: Label = None
        self._body: RoundedRectangle = None
        self._header: RoundedRectangle = None
        self._shadow: RoundedRectangle = None
        self._select: RoundedRectangle = None

        self._input_connections: dict[str, TempValueElement | ConnectionElement] = {}
        self._output_connections: dict[str, ConnectionElement] = {}

    def get_input(self, name: str) -> ConnectionNodeElement:
        pass

    def get_output(self, name: str) -> ConnectionNodeElement:
        pass

    @property
    def left(self) -> float:
        return self._bottom_left[0]

    @property
    def bottom(self) -> float:
        return self._bottom_left[1]


class TempValueElement(Element):

    def __init__(self, position: tuple[float, float], value: OperationValue):
        pass

class GraphElement(Element):
    pass