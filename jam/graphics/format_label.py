from pyglet.customtypes import AnchorX, AnchorY, ContentVAlign
from pyglet.text.document import FormattedDocument
from pyglet.text import DocumentLabel
from pyglet.graphics import Batch, Group
from pyglet.graphics.shader import ShaderProgram


class FLabel(DocumentLabel):
    """Formatted Text label."""

    def __init__(
            self, text: str = "",
            x: float = 0.0, y: float = 0.0, z: float = 0.0,
            width: int | None = None, height: int | None = None,
            anchor_x: AnchorX = "left", anchor_y: AnchorY = "baseline", rotation: float = 0.0,
            multiline: bool = False, dpi: int | None = None,
            font_name: str | None = None, font_size: float | None = None,
            weight: str = "normal", italic: bool | str = False, stretch: bool | str = False,
            color: tuple[int, int, int, int] | tuple[int, int, int] = (255, 255, 255, 255),
            align: ContentVAlign = "left",
            batch: Batch | None = None, group: Group | None = None,
            program: ShaderProgram | None = None,
    ) -> None:
        """Create a formated text label.

        Args:
            text:
                Text to display.
            x:
                X coordinate of the label.
            y:
                Y coordinate of the label.
            z:
                Z coordinate of the label.
            width:
                Width of the label in pixels, or None
            height:
                Height of the label in pixels, or None
            anchor_x:
                Anchor point of the X coordinate: one of ``"left"``,
                ``"center"`` or ``"right"``.
            anchor_y:
                Anchor point of the Y coordinate: one of ``"bottom"``,
                ``"baseline"``, ``"center"`` or ``"top"``.
            rotation:
                The amount to rotate the label in degrees. A positive amount
                will be a clockwise rotation, negative values will result in
                counter-clockwise rotation.
            multiline:
                If True, the label will be word-wrapped and accept newline
                characters.  You must also set the width of the label.
            dpi:
                Resolution of the fonts in this layout.  Defaults to 96.
            font_name:
                Font family name(s).  If more than one name is given, the
                first matching name is used.
            font_size:
                Font size, in points.
            weight:
                The 'weight' of the font (boldness). See the :py:class:`~Weight`
                enum for valid cross-platform weight names.
            italic:
                Italic font style.
            stretch:
                 Stretch font style.
            color:
                Font color as RGBA or RGB components, each within
                ``0 <= component <= 255``.
            align:
                Horizontal alignment of text on a line, only applies if
                a width is supplied. One of ``"left"``, ``"center"``
                or ``"right"``.
            batch:
                Optional graphics batch to add the label to.
            group:
                Optional graphics group to use.
            program:
                Optional graphics shader to use. Will affect all glyphs.
        """
        r, g, b, *a = color
        rgba = r, g, b, a[0] if a else 255

        super().__init__(
            FormattedDocument(text),
            x, y, z, width, height, anchor_x, anchor_y, rotation,
            multiline, dpi, batch, group, program, init_document=False
        )

        self.document.set_style(0, len(self.document.text), {
            "font_name": font_name,
            "font_size": font_size,
            "weight": weight,
            "italic": italic,
            "stretch": stretch,
            "color": rgba,
            "align": align,
        })
