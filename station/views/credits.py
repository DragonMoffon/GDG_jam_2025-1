from pathlib import Path
import re

from arcade import Camera2D
from pyglet.shapes import Rectangle
from pyglet.sprite import Sprite
from resources import style

from station.graphics.format_label import FLabel
from station.markdown import markdown_label
from station.graphics.background import ParallaxBackground
from station.gui.core import get_shadow_shader
from station.view import View
from station.input import Button

HEADER_EX = r"^(#{1,6})\s+(.+)$"
STYLING = r"(\*{1,2}|_{1,2})(\S.*?\S|\S)\1"
LIST_EX = r"^\s*[-+*]\s+(.+)$"


def has_credits() -> bool:
    return Path("CREDITS.md").exists()


def get_credits() -> str:
    with open(Path("CREDITS.md"), encoding="utf-8") as fp:
        return fp.read()


class CreditsView(View):

    def __init__(self, back: View):
        View.__init__(self)
        self.back: View = back

        self._background = ParallaxBackground(style.menu.background)
        self._camera = Camera2D(projection=self.window.rect, position=(0.0, 0.0))

        self._rect = Rectangle(
            self.center_x,
            0,
            self.width * 0.4,
            self.height,
            style.colors.dark,
            program=get_shadow_shader(),
        )

        self._logo = Sprite(style.textures.credits_logo, 0, 0)

        text = get_credits()
        self._text = markdown_label(
            text,
            style.text.names.regular,
            self.center_x,
            self.center_y,
            width=self.width * 0.4,
            color=style.colors.highlight,
            anchor_x="left",
            anchor_y="center",
        )

        self._logo.x = self._text.x
        self._logo.y = self._text.y + (self._text.content_height / 2) + 25

    def on_draw(self) -> None:
        self.clear()
        self._background.draw()
        self._rect.draw()
        with self._camera.activate():
            self._logo.draw()
            self._text.draw()

    def on_update(self, delta_time: float) -> None:
        self._background.update()

    def on_cursor_motion(self, x: float, y: float, dx: float, dy: float) -> None:
        self._background.cursor_motion(x, y, dx, dy)

        h = self._text.content_height * (y / self.height - 0.5)
        self._camera.position = (0, int(h))

    def on_input(self, button: Button, modifiers: int, pressed: bool) -> None:
        if pressed:
            self.window.show_view(self.back)
