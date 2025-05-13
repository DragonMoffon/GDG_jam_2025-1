from typing import Any
import re


from pyglet.customtypes import AnchorX, AnchorY, ContentVAlign
from pyglet.graphics import Batch, Group
from pyglet.graphics.shader import ShaderProgram

from station.graphics.format_label import FLabel
from resources import style

HEADER_EX = r"^(#{1,6})(\s+)(.+)$"
STYLING_EX = r"(\*{1,2}|_{1,2})(\S.*?\S|\S)\1"
MIX_EX = r"(\*{1,2}|_{1,2})(\S.*?\S|\S)\1|^(#{1,6})(\s+)(.+)$"
LIST_EX = r"^\s*[-+*]\s+(.+)$"


def markdown_label(
    text: str,
    font_name: str,
    x: float = 0.0,
    y: float = 0.0,
    z: float = 0.0,
    width: int | None = None,
    height: int | None = None,
    anchor_x: AnchorX = "left",
    anchor_y: AnchorY = "baseline",
    rotation: float = 0.0,
    dpi: int | None = None,
    stretch: bool | str = False,
    color: tuple[int, int, int, int] | tuple[int, int, int] = (255, 255, 255, 255),
    align: ContentVAlign = "left",
    batch: Batch | None = None,
    group: Group | None = None,
    program: ShaderProgram | None = None,
) -> FLabel:
    formating_sequences: list[tuple[int, int, dict[str, Any]]] = []
    effects = re.finditer(MIX_EX, text, flags=re.MULTILINE)
    adj = 0
    for effect in effects:
        if effect.group(1) is None:  # Finding Header
            string = effect.group(5)
            length = len(string)
            size = len(effect.group(3))

            start = effect.start(3) - adj
            end = effect.end(5) - adj
            styling = {"font_size": style.text.sizes[f"header_{size}"]}

            adj += len(effect.group(4))  # Also remove excess spaces
        else:  # Finding Styling
            string = effect.group(2)
            length = len(string)
            size = len(effect.group(1))

            start = effect.start(1) - adj
            end = effect.end(2) - adj + size
            styling = {"weight": "bold" if size == 2 else "normal", "italic": size == 1}

            adj += size

        adj += size
        text = text[:start] + string + text[end:]
        formating_sequences.append((start, start + length, styling))

    label = FLabel(
        text,
        x,
        y,
        z,
        width,
        height,
        anchor_x,
        anchor_y,
        rotation,
        "\n" in text,
        dpi,
        font_name,
        style.text.sizes.normal,
        "normal",
        False,
        stretch,
        color,
        align,
        batch,
        group,
        program,
    )

    for span in formating_sequences:
        label.document.set_style(*span)

    return label
