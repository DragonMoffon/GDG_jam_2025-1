import pyglet
from pyglet.gl import GL_LINEAR

from .context import context
from .application import Window
from .views.menu import MainMenuView


def main() -> None:
    pyglet.image.Texture.default_min_filter = GL_LINEAR
    pyglet.image.Texture.default_mag_filter = GL_LINEAR
    win = Window()
    win.show_view(MainMenuView())
    win.run()
    context.close()
