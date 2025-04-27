from __future__ import annotations
from uuid import UUID, uuid4

from arcade import get_window
from pyglet import gl as pygl
from pyglet.graphics import Batch, Group
from arcade import get_window
from arcade.camera import Projector

class ProjectorGroup(Group):

    def __init__(self, order: int = 0) -> None:
        super().__init__(order)
        self.projector: Projector | None = None
        self._previous_projector: Projector | None = None

    def set_state(self) -> None:
        if self.projector is None:
            return
        self._previous_projector = get_window().current_camera
        self.projector.use()

    def unset_state(self) -> None:
        if self._previous_projector is None:
            return
        self._previous_projector.use()
        self._previous_projector = None

BASE_GROUP = ProjectorGroup(0)
OVERLAY_GROUP = ProjectorGroup(1)

BASE_SHADOW = Group(0, BASE_GROUP)
BASE_SPACING = Group(1, BASE_GROUP)
BASE_PRIMARY = Group(2, BASE_GROUP)
BASE_HIGHLIGHT = Group(3, BASE_GROUP)

OVERLAY_SHADOW = Group(0, OVERLAY_GROUP)
OVERLAY_SPACING = Group(1, OVERLAY_GROUP)
OVERLAY_PRIMARY = Group(2, OVERLAY_GROUP)
OVERLAY_HIGHLIGHT = Group(3, OVERLAY_GROUP)


vertex_source = """#version 150 core
    in vec2 position;
    in vec2 translation;
    in vec4 color;
    in float zposition;
    in float rotation;


    out vec4 vertex_color;

    uniform WindowBlock
    {
        mat4 projection;
        mat4 view;
    } window;

    mat4 m_rotation = mat4(1.0);
    mat4 m_translate = mat4(1.0);

    void main()
    {
        m_translate[3][0] = translation.x;
        m_translate[3][1] = translation.y;
        m_rotation[0][0] =  cos(-radians(rotation));
        m_rotation[0][1] =  sin(-radians(rotation));
        m_rotation[1][0] = -sin(-radians(rotation));
        m_rotation[1][1] =  cos(-radians(rotation));

        gl_Position = window.projection * window.view * m_translate * m_rotation * vec4(position, zposition, 1.0);
        vertex_color = color;
    }
"""

fragment_source = """#version 150 core
    in vec4 vertex_color;
    out vec4 final_color;

    const mat4 bayer = 1.0/16.0 * mat4(
        vec4(0, 8, 2, 10), 
        vec4(12, 4, 14, 6),
        vec4(3, 11, 1, 9),
        vec4(15, 7, 13, 5)
    );

    void main()
    {   
        ivec2 loc = ivec2(mod(gl_FragCoord.x, 4), mod(gl_FragCoord.y, 4));
        float col = (0.9 * bayer[loc.x][loc.y] - 0.5);
        if (col <= 0.0){
            discard;
        }
        
        final_color = vertex_color;
        // No GL_ALPHA_TEST in core, use shader to discard.
        if(final_color.a < 0.01){
            discard;
        }
    }
"""


def get_shadow_shader():
    if pygl.current_context is None:
        raise ValueError('gl context does not exsist yet')
    return pygl.current_context.create_program((vertex_source, 'vertex'), (fragment_source, 'fragment'))


class Element:

    def __init__(self, uid: UUID | None = None):
        self.uid = uid or uuid4()
        self.gui: Gui | None = None

    def connect_renderer(self, batch: Batch | None) -> None: ...

    def disconnect_renderer(self) -> None:
        self.connect_renderer(None)

    # -- VALUE METHODS --

    def contains_point(self, point: tuple[float, float]) -> bool: ...
    def update_position(self, point: tuple[float, float]) -> None: ...

    # -- EVENT RESPONSES --

    def __gui_connected__(self, gui: Gui) -> None: ...
    def __gui_disconnected__(self) -> None: ...

    def __cursor_entered__(self) -> None: ...
    def __cursor_exited__(self) -> None: ...

    def __cursor_pressed__(self) -> None: ...


class Gui:

    def __init__(self, base_projector: Projector, overlay_projector: Projector | None = None):
        self._ctx = get_window().ctx
        self._batch = Batch()
        self._base_camera = base_projector
        self._overlay_camera = overlay_projector if overlay_projector is not None else base_projector
        self._elements: dict[UUID, Element] = {}

    def enable(self):
        BASE_GROUP.projector = self._base_camera
        OVERLAY_GROUP.projector = self._overlay_camera

    def disable(self):
        BASE_GROUP.projector = None
        OVERLAY_GROUP.projector = None

    @property
    def renderer(self) -> Batch:
        return self._batch

    def draw(self):
        self._batch.draw()

    def add_element(self, element: Element) -> None:
        if element.uid in self._elements:
            return

        element.connect_renderer(self._batch)
        self._elements[element.uid] = element

        element.gui = self
        element.__gui_connected__(self)

    def remove_element(self, element: Element) -> None:
        if element.uid not in self._elements:
            return

        element.disconnect_renderer()
        self._elements.pop(element.uid)

        element.__gui_disconnected__()
        element.gui = None


class Frame:

    def __init__(self) -> None:
        pass
