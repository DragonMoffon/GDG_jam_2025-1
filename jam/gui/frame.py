from uuid import UUID
from pyglet.graphics import Batch, Group
from pyglet.shapes import RoundedRectangle
from pyglet.text import Label
from .core import Element

from jam.input import Button, Axis

from resources import style

ACTIVE_GROUP = Group(0)
SHADOW_GROUP = Group(1)
TAG_GROUP = Group(2)

class Frame(Element):

    def __init__(self, name: str, tag_offset: float, position: tuple[float, float], size: tuple[float, float], show_body: bool = False, show_shadow: bool = True, anchor_top: bool = True, uid: UUID | None = None):
        Element.__init__(self, uid)
        self._name = name
        self._size = size
        self._position = position
        self._tag_offset: float = tag_offset
        self._anchor_top: bool = anchor_top

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
        radius = style.format.corner_radius + style.format.footer_size
        if anchor_top:
            hide_top = tag_offset < radius and 0.0 < tag_offset + self._tag_panel.height

            bottom_dist = size[1] - tag_offset - self._tag_panel.height
            hide_bottom = bottom_dist < radius and 0.0 < bottom_dist + self._tag_panel.height
        else:
            top_dist = size[1] - tag_offset - self._tag_panel.height
            hide_top = top_dist < radius and 0.0 < top_dist + self._tag_panel.height

            hide_bottom = tag_offset < radius and 0.0 < tag_offset + self._tag_panel.height

        top_radius = 0.0 if hide_top else radius
        top_segments = 1 if hide_top else 12  
        
        bottom_radius = 0.0 if hide_bottom else radius
        bottom_segments = 1 if hide_bottom else 12

        self._panel = RoundedRectangle(
            0.0, 0.0,
            size[0], size[1],
            (bottom_radius, top_radius, 0.0, 0.0),
            (bottom_segments, top_segments, 1, 1),
            color=style.colors.base,
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

    @property
    def panel_height(self):
        return self._panel.height

    def connect_renderer(self, batch: Batch | None):
        self._tag_shadow.batch = batch
        self._tag_panel.batch = batch
        self._panel.batch = batch
        self._tag_text.batch = batch

    def update_position(self, point: tuple[float, float]):
        self._position = point
        self._panel.position = point

        tag_y = point[1] + (self._panel.height - self._tag_offset - self._tag_panel.height if self._anchor_top else self._tag_offset)
        self._tag_panel.position = point[0] - self._tag_panel.width, tag_y
        self._tag_shadow.position = self._tag_panel.x - style.format.drop_x, self._tag_panel.y - style.format.drop_y
        self._tag_text.position = self._tag_panel.x + style.format.corner_radius / 2.0, self._tag_panel.y + self._tag_panel.height - style.format.corner_radius, 0.0

    @property
    def show_body(self):
        return self._show_body

    @show_body.setter
    def show_body(self, show: bool):
        self._show_body = show
        self._panel.visible = show

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
    
    def on_input(self, input: Button, modifiers: int, pressed: bool) -> bool | None:...
    def on_axis_change(self, axis: Axis, value_1: float, value_2: float):...
    def on_cursor_motion(self, x: float, y: float, dx: float, dy: float) -> bool | None:...
    def on_cursor_scroll(self, x: float, y: float, scroll_x: float, scroll_y: float) -> bool | None:...

    def on_draw(self):...
    def on_update(self, delta_time: float):...