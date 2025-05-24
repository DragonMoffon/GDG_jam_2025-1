from __future__ import annotations

from pyglet.graphics import Batch, Group
from pyglet.graphics.vertexdomain import IndexedVertexList
from pyglet.graphics.shader import ShaderProgram
from pyglet.image import AbstractImage, Texture

import arcade.gl as gl
import pyglet.gl as pygl

_backing_vertex_souce = """#version 330 core
in vec3 in_position;
in vec2 in_uv;
in vec4 in_color;

out vec2 vs_uv;
out vec4 vs_color;

uniform WindowBlock {
    mat4 projection;
    mat4 view;
} window;

void main(){
    gl_Position = window.projection * window.view * vec4(in_position, 1.0);
    vs_uv = in_uv;
    vs_color = in_color;
}
"""
_backing_fragment_source = """#version 330 core
in vec2 vs_uv;
in vec4 vs_color;

out vec4 fs_colour;

uniform sampler2D backing;

void main(){
    fs_colour = texture(backing, vs_uv) * vs_color;
}

"""


def get_backing_shader() -> ShaderProgram:
    if pygl.current_context is None:
        raise ValueError("gl context does not exsist yet")
    program = pygl.current_context.create_program(
        (_backing_vertex_souce, "vertex"), (_backing_fragment_source, "fragment")
    )
    program["backing"] = 0
    return program


class BackingGroup(Group):

    def __init__(
        self,
        texture: Texture,
        filters: tuple[int, int],
        wrap: tuple[int, int],
        program: ShaderProgram,
        parent: Group | None = None,
    ):
        Group.__init__(self, parent=parent)

        self._texture = texture
        self._filters = filters
        self._wrap = wrap

        self._texture_filter = texture.min_filter, texture.mag_filter
        self._program = program

    def set_state(self) -> None:
        self._program.use()

        self._texture.bind()
        self._texture_filter = self._texture.min_filter, self._texture.mag_filter

        if self._texture_filter != self._filters:
            pygl.glTexParameteri(
                self._texture.target, pygl.GL_TEXTURE_MIN_FILTER, self._filters[0]
            )
            pygl.glTexParameteri(
                self._texture.target, pygl.GL_TEXTURE_MAG_FILTER, self._filters[1]
            )

        pygl.glTexParameteri(
            self._texture.target, pygl.GL_TEXTURE_WRAP_S, self._wrap[0]
        )
        pygl.glTexParameteri(
            self._texture.target, pygl.GL_TEXTURE_WRAP_T, self._wrap[1]
        )

        pygl.glEnable(pygl.GL_BLEND)
        pygl.glBlendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA)

    def unset_state(self) -> None:
        pygl.glDisable(pygl.GL_BLEND)
        self._program.stop()

        if self._texture_filter != self._filters:
            pygl.glTexParameteri(
                self._texture.target,
                pygl.GL_TEXTURE_MIN_FILTER,
                self._texture_filter[0],
            )
            pygl.glTexParameteri(
                self._texture.target,
                pygl.GL_TEXTURE_MAG_FILTER,
                self._texture_filter[1],
            )


class Backing:

    def __init__(
        self,
        image: AbstractImage,
        position: tuple[float, float] = (0.0, 0.0),
        size: tuple[float, float] | None = None,
        shift: tuple[float, float] = (0.0, 0.0),
        wrap_x: bool = True,
        wrap_y: bool = True,
        linear_x: bool = False,
        linear_y: bool = False,
        color: tuple[int, int, int] | tuple[int, int, int, int] = (255, 255, 255, 255),
        program: ShaderProgram | None = None,
        batch: Batch | None = None,
        group: Group | None = None,
    ):
        if size is None:
            size = image.width, image.height

        self._position: tuple[float, float] = position
        self._size: tuple[float, float] = size
        self._scale: tuple[int, int] = image.width, image.height
        self._shift: tuple[float, float] = shift
        self._color: tuple[float, float, float, float] = (color[0] / 255.0, color[1] / 255.0, color[2] / 255.0, 1.0 if len(color) < 4 else color[3] / 255.0)

        self._wrap = (
            gl.REPEAT if wrap_x else gl.CLAMP_TO_EDGE,
            gl.REPEAT if wrap_y else gl.CLAMP_TO_EDGE,
        )
        self._filter = (
            gl.LINEAR if linear_x else gl.NEAREST,
            gl.LINEAR if linear_y else gl.NEAREST,
        )

        self._program = program or get_backing_shader()
        self._image: AbstractImage = image

        self._user_group: Group | None = group
        self._group: BackingGroup = self._create_backing_group()
        self._batch: Batch | None = batch

        self._vertex_list: IndexedVertexList
        self._create_vertex_list()

    def _calculate_position(self) -> tuple[float, ...]:
        pl, pr = self._position[0], self._position[1] + self._size[0]
        pb, pt = self._position[1], self._position[1] + self._size[1]

        return pl, pb, 0.0, pl, pt, 0.0, pr, pt, 0.0, pr, pb, 0.0

    def _calculate_uv_shift(self) -> tuple[float, ...]:
        sx, sy = self._shift[0] / self._scale[0], self._shift[1] / self._scale[1]
        sl, sr = sx, sx + self._size[0] / self._scale[0]
        sb, st = sy, sy + self._size[1] / self._scale[1]

        return sl, sb, sl, st, sr, st, sr, sb

    def _create_vertex_list(self) -> None:
        c = self._color
        self._vertex_list = self._program.vertex_list_indexed(
            4,
            pygl.GL_TRIANGLES,
            (0, 1, 2, 0, 2, 3),
            self._batch,
            self._group,  # type: ignore
            in_position=("f", self._calculate_position()),
            in_uv=("f", self._calculate_uv_shift()),
            in_color=("f", (*c, *c, *c, *c))
        )

    def _create_backing_group(self):
        return BackingGroup(
            self._image.get_texture(),
            self._filter,
            self._wrap,
            self._program,
            self._user_group,
        )

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
            self._batch.migrate(
                self._vertex_list, pygl.GL_TRIANGLES, self._group, batch
            )
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
        self._group = self._create_backing_group()
        if self._batch is not None:
            self._batch.migrate(
                self._vertex_list, pygl.GL_TRIANGLES, self._group, self._batch
            )

    @property
    def position(self) -> tuple[float, float]:
        return self._position

    @position.setter
    def position(self, position: tuple[float, float]) -> None:
        if self._position == position:
            return
        self._position = position
        self._vertex_list.in_position[:] = self._calculate_position()

    @property
    def size(self) -> tuple[float, float]:
        return self._size

    @size.setter
    def size(self, size: tuple[float, float]) -> None:
        if self._size == size:
            return
        self._size = size
        self._vertex_list.in_position[:] = self._calculate_position()

    @property
    def shift(self) -> tuple[float, float]:
        return self._shift
    
    @shift.setter
    def shift(self, shift: tuple[float, float]) -> None:
        if shift == self._shift:
            return
        self._shift = shift
        self._vertex_list.in_uv[:] = self._calculate_uv_shift()

    @property
    def image(self) -> AbstractImage:
        return self._image

    @image.setter
    def image(self, image: AbstractImage) -> None:
        if image == self._image:
            return
        self._image = image
        self._scale = image.width, image.height
        self._vertex_list.in_uv[:] = self._calculate_uv_shift()
        self._group = self._create_backing_group()
        if self._batch is not None:
            self._batch.migrate(
                self._vertex_list, pygl.GL_TRIANGLES, self._group, self._batch
            )

    def draw(self) -> None:
        self._group.set_state_recursive()
        self._vertex_list.draw(gl.TRIANGLES)
        self._group.unset_state_recursive()
