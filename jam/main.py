import pyglet
from pyglet.gl import GL_LINEAR

from .application import Window
from .views.game import GameView


def main() -> None:
    pyglet.image.Texture.default_min_filter = GL_LINEAR
    pyglet.image.Texture.default_mag_filter = GL_LINEAR
    win = Window()
    win.show_view(GameView())
    win.run()
