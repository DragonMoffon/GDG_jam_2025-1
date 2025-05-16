from __future__ import annotations

from pyglet.graphics import Batch
from pyglet.shapes import RoundedRectangle
from pyglet.text import Label

from .core import BASE_SHADOW, Element, Point, BASE_PRIMARY, BASE_HIGHLIGHT, get_shadow_shader
from station.comms import Communication, CommunicatonLog
from resources import style

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
        _w = width - (style.format.footer_size * 2)
        self.speaker_text = Label(comm.speaker, 0, 0, 0, _w - (style.format.footer_size * 2), anchor_y = "top", font_name = style.text.names.regular, font_size = style.text.sizes.normal, italic = True, color = style.colors.bright, group = BASE_HIGHLIGHT)
        self.dialogue_text = Label(comm.dialogue, 0, 0, 0, _w - (style.format.footer_size * 2), anchor_y = "top", font_name = style.text.names.regular, font_size = style.text.sizes.normal, italic = False, color = style.colors.highlight, multiline = True, group = BASE_HIGHLIGHT)
        self.rectangle = RoundedRectangle(0, 0, _w, self.speaker_text.content_height + (style.format.footer_size * 2) + style.format.padding + self.dialogue_text.content_height, style.format.corner_radius, color = style.colors.base, group = BASE_PRIMARY)
        self.shadow_rectangle = RoundedRectangle(0, 0, self.rectangle.width, self.rectangle.height, style.format.corner_radius, color = style.colors.dark, group = BASE_SHADOW, program = get_shadow_shader())
        super().__init__()

    def connect_renderer(self, batch: Batch | None) -> None:
        self.shadow_rectangle.batch = batch
        self.rectangle.batch = batch
        self.speaker_text.batch = batch
        self.dialogue_text.batch = batch

    def update_position(self, point: Point) -> None:
        self.rectangle.position = point
        self.shadow_rectangle.position = point[0] - style.format.drop_x, point[1] - style.format.drop_y
        self.speaker_text.y = point[1] + self.rectangle.height - style.format.footer_size
        self.dialogue_text.y = self.speaker_text.y - self.speaker_text.content_height - style.format.padding

        self.speaker_text.x = self.dialogue_text.x = point[0] + style.format.footer_size

class NarrationElement(LogElement):
    def __init__(self, comm: Communication, width: float):
        self.dialogue_text = Label(comm.dialogue, 0, 0, 0, width - (style.format.footer_size * 4), align = "center", anchor_x = "center", anchor_y = "bottom", font_name = style.text.names.regular, font_size = style.text.sizes.normal, italic = True, color = style.colors.bright, multiline = True, group = BASE_HIGHLIGHT, weight = "bold")
        self.rectangle = RoundedRectangle(0, 0, width - (style.format.footer_size * 2), (style.format.padding * 2) + self.dialogue_text.content_height, style.format.corner_radius, color = style.colors.base, group = BASE_PRIMARY)
        self.rectangle.visible = False
        super().__init__()

    def connect_renderer(self, batch: Batch | None) -> None:
        self.rectangle.batch = batch
        self.dialogue_text.batch = batch

    def update_position(self, point: Point) -> None:
        self.rectangle.position = point
        self.dialogue_text.y = point[1] + style.format.padding
        self.dialogue_text.x = point[0] + (self.rectangle.width / 2)

class CommsLogElement(Element):
    def __init__(self, log: CommunicatonLog, width: float):
        self.width = width
        self.elements = [LogElement.from_comm(comm, width) for comm in log.log]
        super().__init__()

    def append(self, comm: Communication) -> None:
        self.elements.append(LogElement.from_comm(comm, self.width))

    def update_position(self, point: Point) -> None:
        """TOP-LEFT"""
        y = point[1]
        for element in self.elements:
            y -= element.rectangle.height
            element.update_position((point[0], y))
            y -= style.format.footer_size

    def connect_renderer(self, batch: Batch) -> None:
        for element in self.elements:
            element.connect_renderer(batch)
