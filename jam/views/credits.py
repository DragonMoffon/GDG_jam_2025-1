from pathlib import Path

from arcade import Camera2D
from resources import style

from jam.graphics.format_label import FLabel
from jam.graphics.background import ParallaxBackground
from jam.view import View
from jam.input import Button


def has_credits() -> bool:
    return Path("CREDITS.md").exists


def get_credits() -> str:
    with open(Path("CREDITS.md"), encoding="utf-8") as fp:
        return fp.read()


class CreditsView(View):

    def __init__(self, back: View):
        View.__init__(self)
        self.back: View = back

        self._background = ParallaxBackground(style.menu.background)
        self._camera = Camera2D(projection=self.window.rect)
        self._text = FLabel(
            get_credits(),
            x=self.center_x,
            y=self.center_y,
            multiline=True,
            width=self.width * 2.0 / 3.0,
            anchor_x="center",
            anchor_y="center",
            align="center",
            font_name=style.text.normal.name,
            font_size=style.text.normal.size,
        )

    def on_draw(self) -> None:
        self.clear()
        self._background.draw()
        with self._camera.activate():
            self._text.draw()

    def on_update(self, delta_time: float) -> None:
        self._background.update()

    def on_cursor_motion(self, x: float, y: float, dx: float, dy: float) -> None:
        self._background.cursor_motion(x, y, dx, dy)

        h = self._text.content_height * (y / self.height - 0.5)
        self._camera.position = (0.0, h)

    def on_input(self, button: Button, modifiers: int, pressed: bool) -> None:
        if pressed:
            self.window.show_view(self.back)
