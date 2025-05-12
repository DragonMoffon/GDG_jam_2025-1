import sys

from pyglet import gl as pygl
from pyglet.graphics.shader import ShaderProgram

if sys.platform == "win32":
    vec4_color = "color"
else:
    vec4_color = "colors"

vertex_source = f"""#version 150 core
    in vec2 position;
    in vec2 translation;
    in vec4 {vec4_color};
    in float zposition;
    in float rotation;


    out vec4 vertex_color;

    uniform WindowBlock
    {{
        mat4 projection;
        mat4 view;
    }} window;

    mat4 m_rotation = mat4(1.0);
    mat4 m_translate = mat4(1.0);

    void main()
    {{
        m_translate[3][0] = translation.x;
        m_translate[3][1] = translation.y;
        m_rotation[0][0] =  cos(-radians(rotation));
        m_rotation[0][1] =  sin(-radians(rotation));
        m_rotation[1][0] = -sin(-radians(rotation));
        m_rotation[1][1] =  cos(-radians(rotation));

        gl_Position = window.projection * window.view * m_translate * m_rotation * vec4(position, zposition, 1.0);
        vertex_color = {vec4_color};
    }}
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


def get_shadow_shader() -> ShaderProgram:
    if pygl.current_context is None:
        raise ValueError("gl context does not exsist yet")
    return pygl.current_context.create_program(
        (vertex_source, "vertex"), (fragment_source, "fragment")
    )
