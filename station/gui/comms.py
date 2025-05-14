from __future__ import annotations
from uuid import UUID

from pyglet.graphics import Group

from station.graphics.shadow import get_shadow_shader
from station.comms import Communication, CommunicatonLog
from resources import style

from .core import Element, Point
from .elements import FLabel, RoundedRectangle


class LogElement(Element):
    @classmethod
    def from_comm(
        cls,
        comm: Communication,
        width: float,
        parent: Element | None = None,
        layer: Group | None = None,
        uid: UUID | None = None,
    ) -> LogElement:
        if comm.speaker is None:
            return NarrationElement(comm, width, parent, layer, uid)
        else:
            return MessageElement(comm, width, parent, layer, uid)


class MessageElement(LogElement):
    def __init__(
        self,
        comm: Communication,
        width: float,
        parent: Element | None = None,
        layer: Group | None = None,
        uid: UUID | None = None,
    ):
        LogElement.__init__(self, parent, layer, uid)
        _w = width - (style.format.footer_size * 2)
        self.speaker_text = FLabel(
            comm.speaker,
            0,
            0,
            0,
            _w - (style.format.footer_size * 2),
            anchor_y="top",
            font_name=style.text.names.regular,
            font_size=style.text.sizes.normal,
            italic=True,
            color=style.colors.bright,
            parent=self,
            layer=self.BODY(1),
        )
        self.dialogue_text = FLabel(
            comm.dialogue,
            0,
            0,
            0,
            _w - (style.format.footer_size * 2),
            anchor_y="top",
            font_name=style.text.names.regular,
            font_size=style.text.sizes.normal,
            italic=False,
            color=style.colors.highlight,
            multiline=True,
            parent=self,
            layer=self.BODY(1),
        )
        self.rectangle = RoundedRectangle(
            0,
            0,
            _w,
            self.speaker_text.height
            + (style.format.footer_size * 2)
            + style.format.padding
            + self.dialogue_text.height,
            style.format.corner_radius,
            color=style.colors.base,
            parent=self,
            layer=self.BODY(),
        )
        self.shadow_rectangle = RoundedRectangle(
            0,
            0,
            self.rectangle.width,
            self.rectangle.height,
            style.format.corner_radius,
            color=style.colors.dark,
            program=get_shadow_shader(),
            parent=self,
            layer=self.SHADOW(),
        )

    def contains_point(self, point: Point) -> bool:
        return self.rectangle.contains_point(point)

    def update_position(self, point: Point) -> None:
        self.rectangle.position = point
        self.shadow_rectangle.position = (
            point[0] - style.format.drop_x,
            point[1] - style.format.drop_y,
        )
        self.speaker_text.y = (
            point[1] + self.rectangle.height - style.format.footer_size
        )
        self.dialogue_text.y = (
            self.speaker_text.y - self.speaker_text.height - style.format.padding
        )

        self.speaker_text.x = self.dialogue_text.x = point[0] + style.format.footer_size

    def get_position(self) -> Point:
        return self.rectangle.get_position()

    def get_size(self) -> tuple[float, float]:
        return self.rectangle.get_size()


class NarrationElement(LogElement):
    def __init__(
        self,
        comm: Communication,
        width: float,
        parent: Element | None = None,
        layer: Group | None = None,
        uid: UUID | None = None,
    ):
        self.dialogue_text = FLabel(
            comm.dialogue,
            0,
            0,
            width - (style.format.footer_size * 4),
            align="center",
            anchor_x="center",
            anchor_y="bottom",
            font_name=style.text.names.regular,
            font_size=style.text.sizes.normal,
            italic=True,
            color=style.colors.bright,
            multiline=True,
            weight="bold",
            parent=self,
            layer=self.BODY(1),
        )
        self.rectangle = RoundedRectangle(
            0,
            0,
            width - (style.format.footer_size * 2),
            (style.format.padding * 2) + self.dialogue_text.height,
            style.format.corner_radius,
            color=style.colors.base,
            parent=self,
            layer=self.BODY(),
        )
        self.rectangle.visible = False
        super().__init__()

    def contains_point(self, point: Point) -> bool:
        return self.rectangle.contains_point(point)

    def update_position(self, point: Point) -> None:
        self.rectangle.update_position(point)
        self.dialogue_text.update_position(
            (point[0] + (self.rectangle.width / 2), point[1] + style.format.padding)
        )

    def get_position(self) -> Point:
        return self.rectangle.get_position()

    def get_size(self) -> tuple[float, float]:
        return self.rectangle.get_size()


class CommsLogElement(Element):
    def __init__(
        self,
        log: CommunicatonLog,
        width: float,
        parent: Element | None = None,
        layer: Group | None = None,
        uid: UUID | None = None,
    ):
        Element.__init__(self, parent, layer, uid)
        self._position: Point = (0.0, 0.0)
        self._width: float = width
        self._height: float = 0.0
        self.elements = [LogElement.from_comm(comm, width, self) for comm in log.log]

    def contains_point(self, point: Point) -> bool:
        l, t = self._position
        w, h = self._width, self._height
        return 0 <= point[0] - l <= w and 0 <= t - point[1] <= h

    def update_position(self, point: Point) -> None:
        """TOP-LEFT"""
        self._position = point
        y = point[1]
        for element in self.elements:
            y -= element.rectangle.height
            element.update_position((point[0], y))
            y -= style.format.footer_size
        # don't include final padding
        self._height = point[1] - y + style.format.footer_size

    def get_position(self) -> Point:
        return self._position

    def get_size(self) -> tuple[float, float]:
        return self._width, self._height
