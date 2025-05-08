from __future__ import annotations

from pyglet.graphics import Batch
from pyglet.shapes import RoundedRectangle
from pyglet.text import Label

from .core import BASE_SHADOW, Element, Point, BASE_PRIMARY, BASE_HIGHLIGHT, get_shadow_shader
from station.comms import Communication, CommunicatonLog
from resources import Style

class LogElement(Element):
    def connect_renderer(self, batch: Batch | None) -> None:
        return super().connect_renderer(batch)

    def contains_point(self, point: Point) -> bool:
        return super().contains_point(point)

    def update_position(self, point: Point) -> None:
        return super().update_position(point)

    @classmethod
    def from_comm(cls, comm: Communication, width: float) -> LogElement:
        if comm.speaker is None:
            return NarrationElement(comm, width)
        else:
            return MessageElement(comm, width)

class MessageElement(LogElement):
    def __init__(self, comm: Communication, width: float):
        _w = width - (Style.Format.footer_size * 2)
        self.speaker_text = Label(comm.speaker, 0, 0, 0, _w - (Style.Format.footer_size * 2), anchor_y = "top", font_name = Style.Text.Names.regular, font_size = Style.Text.Sizes.normal, italic = True, color = Style.Colors.bright, group = BASE_HIGHLIGHT)
        self.dialogue_text = Label(comm.dialogue, 0, 0, 0, _w - (Style.Format.footer_size * 2), anchor_y = "top", font_name = Style.Text.Names.regular, font_size = Style.Text.Sizes.normal, italic = False, color = Style.Colors.highlight, multiline = True, group = BASE_HIGHLIGHT)
        self.rectangle = RoundedRectangle(0, 0, _w, self.speaker_text.content_height + (Style.Format.footer_size * 2) + Style.Format.padding + self.dialogue_text.content_height, Style.Format.corner_radius, color = Style.Colors.base, group = BASE_PRIMARY)
        self.shadow_rectangle = RoundedRectangle(0, 0, self.rectangle.width, self.rectangle.height, Style.Format.corner_radius, color = Style.Colors.dark, group = BASE_SHADOW, program = get_shadow_shader())
        super().__init__()

    def connect_renderer(self, batch: Batch | None) -> None:
        self.shadow_rectangle.batch = batch
        self.rectangle.batch = batch
        self.speaker_text.batch = batch
        self.dialogue_text.batch = batch

    def update_position(self, point: Point) -> None:
        self.rectangle.position = point
        self.shadow_rectangle.position = point[0] - Style.Format.drop_x, point[1] - Style.Format.drop_y
        self.speaker_text.y = point[1] + self.rectangle.height - Style.Format.footer_size
        self.dialogue_text.y = self.speaker_text.y - self.speaker_text.content_height - Style.Format.padding

        self.speaker_text.x = self.dialogue_text.x = point[0] + Style.Format.footer_size

class NarrationElement(LogElement):
    def __init__(self, comm: Communication, width: float):
        self.dialogue_text = Label(comm.dialogue, 0, 0, 0, width - (Style.Format.footer_size * 4), align = "center", anchor_x = "center", anchor_y = "bottom", font_name = Style.Text.Names.regular, font_size = Style.Text.Sizes.normal, italic = True, color = Style.Colors.bright, multiline = True, group = BASE_HIGHLIGHT, weight = "bold")
        self.rectangle = RoundedRectangle(0, 0, width - (Style.Format.footer_size * 2), (Style.Format.padding * 2) + self.dialogue_text.content_height, Style.Format.corner_radius, color = Style.Colors.base, group = BASE_PRIMARY)
        self.rectangle.visible = False
        super().__init__()

    def connect_renderer(self, batch: Batch | None) -> None:
        self.rectangle.batch = batch
        self.dialogue_text.batch = batch

    def update_position(self, point: Point) -> None:
        self.rectangle.position = point
        self.dialogue_text.y = point[1] + Style.Format.padding
        self.dialogue_text.x = point[0] + (self.rectangle.width / 2)

class CommsLogElement(Element):
    def __init__(self, log: CommunicatonLog, width: float):
        self.elements = [LogElement.from_comm(comm, width) for comm in log.log]
        super().__init__()

    def update_position(self, point: Point) -> None:
        """TOP-LEFT"""
        y = point[1]
        for element in self.elements:
            y -= element.rectangle.height
            element.update_position((point[0], y))
            y -= Style.Format.footer_size

    def connect_renderer(self, batch: Batch) -> None:
        for element in self.elements:
            element.connect_renderer(batch)
