from __future__ import annotations

from pyglet.graphics import Batch, Group
from pyglet.graphics.shader import ShaderProgram

from arcade import get_window, ArcadeContext
import arcade.gl as gl
import pyglet.gl as pygl

_clip_vertex_source = """#version 330 core
in vec3 in_pos;
in vec2 in_uv;

out vec2 vs_uv;

uniform WindowBlock {
    mat4 projection;
    mat4 view;
} window;

void main(){
    gl_Position = window.projection * window.view * vec4(in_pos, 1.0);
    vs_uv = in_uv;
}
"""

_clip_fragment_source = """#version 330 core
in vec2 vs_uv;

out vec4 fs_colour;

uniform sampler2D target_texture;
uniform sampler2D clip_texture;

void main(){
    vec4 clip = vec4(vec3(1), texture(clip_texture, vs_uv).a);

    // if (clip.a == 0) discard;

    vec4 colour = texture(target_texture, vs_uv);
    fs_colour = colour * clip;
}

"""

class ClipGroup(Group):

    def __init__(self, target: gl.Texture2D, clip: gl.Texture2D, program: ShaderProgram, parent: Group | None = None) -> None:
        super().__init__(parent=parent)
        self.program = program
        self.target = target
        self.clip = clip


    def set_state(self) -> None:
        self.program.use()
        self.target.use(0)
        self.clip.use(1)

        pygl.glEnable(pygl.GL_BLEND)
        
        pygl.glBlendFunc(pygl.GL_SRC_ALPHA, pygl.GL_ONE_MINUS_SRC_ALPHA)

    def unset_state(self) -> None:
        pygl.glDisable(pygl.GL_BLEND)
        self.program.stop()
        
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.target},{self.clip})"

    def __eq__(self, other: ClipGroup) -> bool: # type: ignore
        return (other.__class__ is self.__class__ and
                self.program is other.program and
                self.parent == other.parent and
                self.target == other.target and
                self.clip == other.clip)

    def __hash__(self) -> int:
        return hash((self.program, self.parent, int.from_bytes(self.target.glo), int.from_bytes(self.clip.glo)))


class ClippingMask:
    
    def __init__(
            self,
            position: tuple[float, float],
            size: tuple[float, float],
            target_size: tuple[int, int],
            clip_size: tuple[int, int] | None = None,
            visible: bool = True,
            batch: Batch | None = None,
            group: Group | None = None
        ) -> None:
            
        if pygl.current_context is None:
            raise ValueError('No gl context currently')

        self._output_size = size
        self._output_position = position

        self._visible = visible

        self._target_size = target_size
        self._clip_size = target_size if clip_size is None else clip_size

        self._ctx: ArcadeContext = get_window().ctx
        self._target_framebuffer: gl.Framebuffer = self._ctx.framebuffer(
            color_attachments=[self._ctx.texture(self._target_size)]
        )
        self._clip_framebuffer: gl.Framebuffer = self._ctx.framebuffer(
            color_attachments=[self._ctx.texture(self._clip_size)]
        )

        self._program = pygl.current_context.create_program((_clip_vertex_source, 'vertex'), (_clip_fragment_source, 'fragment'))
        self._program['target_texture'] = 0
        self._program['clip_texture'] = 1

        self._batch = batch
        self._user_group = group
        self._group: ClipGroup = self._create_clip_group()

        self._create_vertex_list()

    def draw(self):
        self._group.set_state_recursive()
        self._vertex_list.draw(pygl.GL_TRIANGLES)
        self._group.unset_state_recursive()

    def _create_clip_group(self):
        return ClipGroup(self.target_texture, self.clip_texture, self._program, self._user_group)

    def _create_vertex_list(self):
        l, r = self._output_position[0], self._output_position[0] + self._output_size[0]
        b, t = self._output_position[1], self._output_position[1] + self._output_size[1]
        if not self._visible:
            l = r = b = t = 0.0

        self._vertex_list = self._program.vertex_list_indexed(
            4, pygl.GL_TRIANGLES, (0, 1, 2, 0, 2, 3), self._batch, self._group, # type: ignore 
            in_pos=('f', (l, b, 0.0, l, t, 0.0, r, t, 0.0, r, b, 0.0)),
            in_uv=('f', (0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 0.0))
        )

    def _update_position(self):
        l, r = self._output_position[0], self._output_position[0] + self._output_size[0]
        b, t = self._output_position[1], self._output_position[1] + self._output_size[1]
        if not self._visible:
            l = r = b = t = 0.0
        self._vertex_list.in_pos[:] = (l, b, 0.0, l, t, 0.0, r, t, 0.0, r, b, 0.0) # type: ignore 

    @property
    def target(self):
        self._target_framebuffer.clear(color=(0, 0, 0, 0))
        return self._target_framebuffer.activate()

    @property
    def clip(self):
        self._clip_framebuffer.clear(color=(0, 0, 0, 0))
        return self._clip_framebuffer.activate()
    
    @property
    def target_texture(self) -> gl.Texture2D:
        return self._target_framebuffer.color_attachments[0]

    @property
    def clip_texture(self) -> gl.Texture2D:
        return self._clip_framebuffer.color_attachments[0]

    @property
    def batch(self) -> Batch | None:
        """Graphics batch.

        The sprite can be migrated from one batch to another, or removed from
        its batch (for individual drawing).

        .. note:: Changing this can be an expensive operation as it involves deleting the vertex list and recreating it.
        """
        return self._batch

    @batch.setter
    def batch(self, batch: Batch | None) -> None:
        if self._batch == batch:
            return

        if batch is not None and self._batch is not None:
            self._batch.migrate(self._vertex_list, pygl.GL_TRIANGLES, self._group, batch)
            self._batch = batch
        else:
            self._vertex_list.delete()
            self._batch = batch
            self._create_vertex_list()

    @property
    def group(self) -> Group | None:
        """Parent graphics group specified by the user.

        This group will always be the parent of the internal sprite group.

        .. note:: Changing this can be an expensive operation as it involves a group creation and transfer.
        """
        return self._group

    @group.setter
    def group(self, group: Group | None) -> None:
        if self._user_group == group:
            return
        self._user_group = group
        self._group = self._create_clip_group()
        if self._batch is not None:
            self._batch.migrate(self._vertex_list, pygl.GL_TRIANGLES, self._group, self._batch)

    @property
    def visible(self) -> bool:
        """True if the sprite will be drawn."""
        return self._visible

    @visible.setter
    def visible(self, visible: bool) -> None:
        self._visible = visible
        self._update_position()

    @property
    def position(self):
        return self._output_position

    @position.setter
    def position(self, pos: tuple[float, float]):
        self._output_position = pos
        self._update_position()

    @property
    def size(self):
        return self._output_size
    
    @size.setter
    def size(self, size: tuple[float, float]):
        self._output_size = size
        self._update_position()

    def update_target_size(self, size: tuple[int, int]):
        if self._target_size == size:
            return

        self._target_size = size
        self._target_framebuffer.color_attachments[0].resize(size)

    def update_clip_size(self, size: tuple[int, int]):
        if self._clip_size == size:
            return

        self._clip_size = size
        self._clip_framebuffer.color_attachments[0].resize(size)