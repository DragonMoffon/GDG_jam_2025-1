from uuid import UUID
from pyglet.graphics import Batch, Group
from pyglet.shapes import RoundedRectangle
from pyglet.text import Label
from .core import Element

from resources import style

ACTIVE_GROUP = Group(0)
SHADOW_GROUP = Group(1)
TAG_GROUP = Group(2)

class Frame(Element):

    def __init__(self, name: str, tag_offset: float, position: tuple[float, float], size: tuple[float, float], show_body: bool = False, show_shadow: bool = True, uid: UUID | None = None):
        Element.__init__(self, uid)
        self._name = name
        self._size = size
        self._position = position
        self._tag_offset: float = tag_offset

        self._show_body: bool = True
        self._show_shadow: bool = True

        self._tag_text = Label(
            '\n'.join(name),
            0, 0, 0,
            int(style.text.header.size) + 1,
            anchor_y='top',
            multiline=True,
            font_size=style.text.header.size,
            font_name=style.text.header.name,
            color=style.colors.highlight,
            group=TAG_GROUP
        )
        self._tag_text.set_style('line_spacing', style.text.header.size + style.format.padding)
        self._tag_panel = RoundedRectangle(
            0.0, 0.0,
            style.format.corner_radius + 2 * style.format.padding + self._tag_text.content_width,
            self._tag_text.content_height + 2 * style.format.corner_radius + 2 * style.format.padding,
            (style.format.corner_radius, style.format.corner_radius, 0, 0),
            (12, 12, 1, 1),
            color=style.colors.base,
            group=TAG_GROUP
        )
        self._tag_shadow = RoundedRectangle(
            0.0, 0.0,
            self._tag_panel.width + style.format.drop_x, self._tag_panel.height,
            (style.format.corner_radius, style.format.corner_radius, 0, 0),
            (12, 12, 1, 1),
            color=style.colors.shadow,
            group=SHADOW_GROUP
        )
        top_radius = style.format.corner_radius if tag_offset >= style.format.corner_radius else 0.0
        top_segments = 12 if tag_offset >= style.format.corner_radius else 1
        self._panel = RoundedRectangle(
            0.0, 0.0,
            size[0], size[1],
            (style.format.corner_radius + style.format.footer_size, top_radius, 0.0, 0.0),
            (12, top_segments, 1, 1),
            color=style.colors.base,
            group=ACTIVE_GROUP
        )
        self._interal = RoundedRectangle(
            0.0, 0.0,
            size[0] - style.format.footer_size, size[1] - 2*style.format.footer_size,
            (style.format.corner_radius, style.format.corner_radius, 0.0, 0.0),
            (12, 12, 1, 1),
            color=style.colors.background,
            group=ACTIVE_GROUP
        )

        self.update_position(position)
        self.show_body = show_body
        self.show_shadow = show_shadow

    @property
    def tag_height(self):
        return self._tag_panel.height
    
    @property
    def panel_width(self):
        return self._size[0]

    def connect_renderer(self, batch: Batch | None):
        self._tag_shadow.batch = batch
        self._tag_panel.batch = batch
        self._panel.batch = batch
        self._interal.batch = batch
        self._tag_text.batch = batch

    def update_position(self, point: tuple[float, float]):
        self._position = point
        self._panel.position = point
        self._interal.position = point[0] + style.format.footer_size, point[1] + style.format.footer_size
        self._tag_panel.position = point[0] - self._tag_panel.width, point[1] + self._panel.height - self._tag_offset - self._tag_panel.height
        self._tag_shadow.position = self._tag_panel.x - style.format.drop_x, self._tag_panel.y - style.format.drop_y
        self._tag_text.position = self._tag_panel.x + style.format.corner_radius / 2.0, self._tag_panel.y + self._tag_panel.height - style.format.corner_radius, 0.0

    @property
    def show_body(self):
        return self._show_body

    @show_body.setter
    def show_body(self, show: bool):
        self._show_body = show
        self._panel.visible = show
        self._interal.visible = show

    @property
    def show_shadow(self):
        return self._show_shadow

    @show_shadow.setter
    def show_shadow(self, show: bool):
        self._show_shadow = show
        self._tag_shadow.visible = show

    def contains_point(self, point: tuple[float, float]) -> bool:
        return (
            (0 <= point[0] - self._panel.x <= self._panel.width and 0 <= point[1] - self._panel.y <= self._panel.height )
            or
            (0 <= point[0] - self._tag_panel.x <= self._tag_panel.width and 0 <= point[1] - self._tag_panel.y <= self._tag_panel.height)
        )