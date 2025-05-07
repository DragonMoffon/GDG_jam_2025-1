from pathlib import Path

from resources import style

from jam.graphics.format_label import FLabel
from jam.graphics.background import ParallaxBackground
from jam.view import View
from jam.input import Button


def has_credits() -> bool:
    return Path("CREDITS.md").exists


def get_credits() -> str:
    with open(Path("CREDITS.md")) as fp:
        return fp.read()


class CreditsView(View):

    def __init__(self, back: View):
        View.__init__(self)
        self.back: View = back

        self._background = ParallaxBackground(style.menu.background)
        self._text = FLabel(
            get_credits(),
            self.center_x,
            self.center_y + self.height / 3,
            anchor_x="center",
            anchor_y="center",
        )

    def on_draw(self) -> None:
        self.clear()
        self._background.draw()
        self._text.draw()

    def on_update(self, delta_time: float) -> None:
        self._background.update()

    def on_cursor_motion(self, x: float, y: float, dx: float, dy: float) -> None:
        self._background.cursor_motion(x, y, dx, dy)

    def on_input(self, button: Button, modifiers: int, pressed: bool) -> None:
        if pressed:
            self.window.show_view(self.back)
