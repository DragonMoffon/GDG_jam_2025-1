from pathlib import Path
import re

from arcade import Camera2D
from resources import Style

from station.graphics.format_label import FLabel
from station.graphics.background import ParallaxBackground
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

        self._background = ParallaxBackground(Style.Menu.Background)
        self._camera = Camera2D(projection=self.window.rect, position=(0.0, 0.0))

        text = get_credits()
        self._text = FLabel(
            text,
            x=self.center_x,
            y=self.center_y,
            multiline=True,
            width=self.width * 0.5,
            anchor_x="left",
            anchor_y="center",
            font_name=Style.Text.Names.regular,
            font_size=Style.Text.Sizes.normal,
        )

        headers = re.finditer(HEADER_EX, text, flags=re.MULTILINE)
        for header in tuple(headers)[::-1]:
            title = header.group(2)
            self._text.document.delete_text(header.start(1), header.end(2))
            self._text.document.insert_text(
                header.start(1),
                title,
                {"font_size": Style.Text.Sizes[f"header_{len(header.group(1))}"]},
            )

        stylings = re.finditer(STYLING, self._text.text)
        # TODO: This doesn't work with nested formating
        for styling in tuple(stylings)[::-1]:
            txt = styling.group(2)
            m = len(styling.group(1))
            if m == 1:
                self._text.document.delete_text(styling.start(1), styling.end(2) + 1)
                self._text.document.insert_text(
                    styling.start(1),
                    txt,
                    {"italic": True},
                )
            elif m == 2:
                self._text.document.delete_text(styling.start(1), styling.end(2) + 2)
                self._text.document.insert_text(
                    styling.start(1),
                    txt,
                    {"weight": "bold"},
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
        self._camera.position = (0, int(h))

    def on_input(self, button: Button, modifiers: int, pressed: bool) -> None:
        if pressed:
            self.window.show_view(self.back)
