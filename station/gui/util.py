from uuid import UUID
from typing import Callable, Any

from pyglet.graphics import Batch
from pyglet.shapes import RoundedRectangle
from pyglet.text import Label
from arcade import Text
from arcade.clock import GLOBAL_CLOCK

from resources import Style

from station.graphics.format_label import FLabel

from .core import (
    Element,
    OVERLAY_SHADOW,
    OVERLAY_PRIMARY,
    OVERLAY_HIGHLIGHT,
    get_shadow_shader,
)


class Popup(Element):

    def __init__(
        self,
        width: float,
        height: float,
        bottom_left: tuple[float, float],
        uid: UUID | None = None,
    ):
        Element.__init__(self, uid)

        self.width = width
        self.height = height
        self.bottom_left = bottom_left

        self._body = RoundedRectangle(
            bottom_left[0],
            bottom_left[1],
            width,
            height,
            Style.Format.padding,
            14,
            Style.Colors.base,
            group=OVERLAY_PRIMARY,
        )
        self._shadow = RoundedRectangle(
            bottom_left[0] - 2 * Style.Format.drop_x,
            bottom_left[1] - 2 * Style.Format.drop_y,
            width,
            height,
            Style.Format.padding,
            14,
            Style.Colors.dark,
            program=get_shadow_shader(),
            group=OVERLAY_SHADOW,
        )

    def connect_renderer(self, batch: Batch | None):
        self._body.group = OVERLAY_PRIMARY
        self._shadow.group = OVERLAY_SHADOW

        self._body.batch = batch
        self._shadow.batch = batch

    def contains_point(self, point: tuple[float, float]):
        l, b = self.bottom_left
        w, h = self.width, self.height
        return 0 <= point[0] - l <= w and 0 <= point[1] - b <= h


class InfoPopup(Popup):

    def __init__(
        self, text: str, bottom_left: tuple[float, float], uid: UUID | None = None
    ):
        self._text = Text(
            text,
            bottom_left[0] + Style.Format.padding,
            bottom_left[1] + Style.Format.padding,
            Style.Colors.highlight,
            Style.Text.Sizes.normal,
            font_name=Style.Text.Names.monospace,
            anchor_y="bottom",
        )
        Popup.__init__(
            self,
            self._text.content_width + 2 * Style.Format.padding,
            self._text.content_height + 2 * Style.Format.padding,
            bottom_left,
            uid,
        )

    def connect_renderer(self, batch: Batch | None):
        Popup.connect_renderer(self, batch)

        self._text.group = OVERLAY_PRIMARY
        self._text.batch = batch


class PopupAction:

    def __init__(self, name: str, action: Callable[..., None], *args: Any, **kwds: Any):
        self.name = name
        self.action = action
        self._args = args
        self._kwds = kwds

    def __call__(self):
        return self.action(*self._args, **self._kwds)


class SelectionPopup(Popup):

    def __init__(
        self,
        actions: tuple[PopupAction, ...],
        position: tuple[float, float],
        top: bool = False,
        right: bool = False,
        uid: UUID | None = None,
    ):

        self.actions = {action.name: action for action in actions}
        self._action_text = {
            name: Text(
                name,
                0.0,
                0.0,
                Style.Colors.accent,
                Style.Text.Sizes.normal,
                anchor_y="bottom",
                font_name=Style.Text.Names.monospace,
                group=OVERLAY_HIGHLIGHT,
            )
            for name in self.actions
        }

        text_width = max(text.content_width for text in self._action_text.values())
        text_height = max(text.content_height for text in self._action_text.values())

        self._action_panels = {
            name: RoundedRectangle(
                0.0,
                0.0,
                text_width + 2 * Style.Format.padding,
                text_height + 2 * Style.Format.padding,
                Style.Format.padding,
                14,
                Style.Colors.background,
                group=OVERLAY_HIGHLIGHT,
            )
            for name in self.actions
        }

        width = (
            max(panel.width for panel in self._action_panels.values())
            + 2 * Style.Format.padding
        )
        height = (
            sum(panel.height for panel in self._action_panels.values())
            + (len(actions) + 1) * Style.Format.padding
        )

        bottom = position[1] - height if top else position[1]
        left = position[0] - width if right else position[0]

        for idx, action in enumerate(actions):
            y = (
                bottom
                + Style.Format.padding
                + idx * (3 * Style.Format.padding + text_height)
            )
            self._action_panels[action.name].position = left + Style.Format.padding, y
            self._action_text[action.name].position = (
                left + 2 * Style.Format.padding,
                y + Style.Format.padding,
            )
        Popup.__init__(self, width, height, (left, bottom), uid)

    def connect_renderer(self, batch: Batch | None):
        Popup.connect_renderer(self, batch)

        for action in self.actions:
            p = self._action_panels[action]
            p.batch = batch
            t = self._action_text[action]
            t.batch = batch

    def get_hovered_item(self, point: tuple[float, float]) -> str | None:
        for name, panel in self._action_panels.items():
            if (
                0 <= point[0] - panel.x <= panel.width
                and 0 <= point[1] - panel.y <= panel.height
            ):
                return name
        return None

    def highlight_action(
        self, name: str | None, highlight: bool = True, only: bool = False
    ):
        if name not in self.actions and name is not None:
            return

        if name is None:
            only = False

        if only or not highlight:
            self._action_panels[name].color = (
                Style.Colors.base if highlight else Style.Colors.background
            )
            self._action_text[name].color = (
                Style.Colors.highlight if highlight else Style.Colors.accent
            )
            return

        for action in self.actions:
            h = action == name
            self._action_panels[action].color = (
                Style.Colors.base if h else Style.Colors.background
            )
            self._action_text[action].color = (
                Style.Colors.highlight if h else Style.Colors.accent
            )

    def clear_highlight(self):
        for action in self.actions:
            self._action_panels[action].color = Style.Colors.background
            self._action_text[action].color = Style.Colors.accent


class TextInput:

    def __init__(
        self, charset: set[str], chararray: tuple[str, ...], max_char: int = -1
    ):
        self._charset = charset
        self._chararray = chararray
        self._max_char = max_char
        self._str = ""
        self._idx = 0

    @property
    def set(self) -> set[str]:
        return self._charset

    @property
    def array(self) -> tuple[str, ...]:
        return self._chararray

    @property
    def max(self) -> int:
        return self._max_char

    @property
    def cursor(self) -> int:
        return self._idx

    @property
    def text(self) -> str:
        return self._str

    @property
    def size(self) -> int:
        return len(self._str)

    @property
    def at_start(self) -> bool:
        return self._idx == 0

    @property
    def at_end(self) -> bool:
        return self._idx == len(self._str)

    @property
    def at_max(self) -> bool:
        return self._max_char >= 0 and self._idx == self._max_char

    @property
    def is_max(self) -> bool:
        return self._max_char >= 0 and len(self._str) == self._max_char

    def incr_cursor(self, wrap: bool = True) -> int:
        self._idx += 1
        if self._idx > len(self._str):
            self._idx = 0 if wrap else len(self._str)
        return self._idx

    def decr_cursor(self, wrap: bool = True) -> int:
        self._idx -= 1
        if self._idx < 0:
            self._idx = len(self._str) if wrap else 0
        return self._idx

    def move_cursor(self, new: int) -> int:
        self._idx = new % len(self._str)
        return self._idx

    def add_char(self, char: str) -> str:
        if char not in self._charset:
            return self._str

        if self._max_char >= 0 and len(self._str) == self._max_char:
            return self._str

        self._str = f"{self._str[:self._idx]}{char}{self._str[self._idx:]}"
        self.incr_cursor(wrap=False)
        return self._str

    def rem_char(self) -> str:
        if self._idx <= 0:
            self._idx = 0
            return self._str

        self.decr_cursor(wrap=False)
        self._str = f"{self._str[:self._idx]}{self._str[self._idx + 1:]}"
        return self._str

    def incr_char(self) -> str:
        if self.at_end:
            if not self.is_max:
                self._str = self._str + self._chararray[0]
            return self._str
        char = self._str[self._idx]
        idx = (self._chararray.index(char) + 1) % len(self._chararray)
        new = self._chararray[idx]
        self._str = f"{self._str[:self._idx]}{new}{self._str[self._idx + 1:]}"
        return self._str

    def decr_char(self) -> str:
        if self.at_end:
            if not self.is_max:
                self._str = self._str + self._chararray[-1]
            return self._str
        char = self._str[self._idx]
        idx = self._chararray.index(char) - 1
        new = self._chararray[idx]
        self._str = f"{self._str[:self._idx]}{new}{self._str[self._idx + 1:]}"
        return self._str

    def set_char(self, new: str) -> str:
        if new not in self._charset or self.at_end:
            return self._str
        self._str = f"{self._str[:self._idx]}{new}{self._str[self._idx + 1:]}"
        return self._str

    def set_text(self, text: str, cursor: int = -1) -> str:
        if self._max_char >= 0:
            text = text[: self._max_char]
        self._str = text
        if cursor >= 0:
            self._idx = min(len(self._str), cursor)
        else:
            self._idx = len(self._str)

        return self._str

    def clear_text(self) -> None:
        self._str = ""
        self._idx = 0


class TextInputPopup(Popup):

    def __init__(
        self,
        center: tuple[float, float],
        charset: set[str],
        chararray: tuple[str, ...],
        max_char: int = -1,
        blink: bool = True,
    ):
        self._text_input = TextInput(charset, chararray, max_char)
        count = min(12, max_char) if max_char > 0 else 12
        self._text = FLabel(
            "#" * count,
            center[0],
            center[1],
            0.0,
            font_name=Style.Text.Names.monospace,
            font_size=Style.Text.Sizes.header,
            color=Style.Colors.accent,
            group=OVERLAY_HIGHLIGHT,
            anchor_x="center",
            anchor_y="center",
        )
        width = self._text.content_width + 2 * Style.Format.padding
        height = self._text.content_height + 2 * Style.Format.padding
        self._text.text = " "

        Popup.__init__(
            self,
            width,
            height,
            (center[0] - width / 2.0, center[1] - height / 2.0),
        )

        self._blink = blink
        self._highlight = True
        self._blink_time = GLOBAL_CLOCK.time + Style.Game.Editor.blink_speed

    def update(self) -> None:
        if not self._blink:
            return
        if GLOBAL_CLOCK.time >= self._blink_time:
            dt = Style.Game.Editor.blink_speed + self._blink_time - GLOBAL_CLOCK.time
            self._blink_time = GLOBAL_CLOCK.time + (dt % Style.Game.Editor.blink_speed)
            self._highlight = not self._highlight
            self.clear_highlight()
            self.highlight_cursor()

    def update_position(self, point: tuple[float, float]) -> None:
        Popup.update_position(self, point)
        self._text.position = (
            point[0] + self._body.width * 0.5,
            point[1] + self._body.height * 0.5,
            0.0,
        )

    def connect_renderer(self, batch: Batch | None) -> None:
        Popup.connect_renderer(self, batch)
        self._text.batch = batch

    def input_char(self, char: str) -> None:
        if self._text_input.at_end:
            self._text.text = self._text.text.strip()
        self._text.text = self._text_input.add_char(char)
        if self._text_input.at_end:
            self._text.text += " "
        self.clear_highlight()
        self.highlight_cursor()

        if len(self._text.text) >= 12:
            width = self._text.content_width + 2 * Style.Format.padding
            x = self._body.x - (width - self._body.width) * 0.5
            self._body.width = self._shadow.width = width
            self._body.x = x
            self._shadow.x = x - 2 * Style.Format.drop_x

    def remove_char(self) -> None:
        if self._text_input.at_end:
            self._text.text = self._text.text.strip()
        self._text.text = self._text_input.rem_char()
        if self._text_input.at_end:
            self._text.text += " "
        self.clear_highlight()
        self.highlight_cursor()

        if len(self._text.text) >= 12:
            width = self._text.content_width + 2 * Style.Format.padding
            x = self._body.x - (width - self._body.width) * 0.5
            self._body.width = self._shadow.width = width
            self._body.x = x
            self._shadow.x = x - 2 * Style.Format.drop_x

    def incr_cursor(self) -> None:
        if self._text_input.at_end:
            self._text.text = self._text.text.strip()
        self._text_input.incr_cursor()
        if self._text_input.at_end:
            self._text.text += " "
        self.clear_highlight()
        self.highlight_cursor()

    def decr_cursor(self) -> None:
        if self._text_input.at_end:
            self._text.text = self._text.text.strip()
        self._text_input.decr_cursor()
        if self._text_input.at_end:
            self._text.text += " "
        self.clear_highlight()
        self.highlight_cursor()

    def incr_char(self) -> None:
        if self._text_input.at_end:
            self._text.text = self._text.text.strip()
        self._text.text = self._text_input.incr_char()
        if self._text_input.at_end:
            self._text.text += " "
        self.clear_highlight()
        self.highlight_cursor()

    def decr_char(self) -> None:
        if self._text_input.at_end:
            self._text.text = self._text.text.strip()
        self._text.text = self._text_input.decr_char()
        if self._text_input.at_end:
            self._text.text += " "
        self.clear_highlight()
        self.highlight_cursor()

    def highlight_cursor(self) -> None:
        if not self._highlight:
            return
        self._text.document.set_style(
            self.cursor,
            self.cursor + 1,
            {"color": Style.Colors.base, "background_color": Style.Colors.accent},
        )

    def clear_highlight(self) -> None:
        self._text.document.set_style(
            0,
            len(self._text.text),
            {"color": Style.Colors.accent, "background_color": None},
        )

    @property
    def text(self) -> str:
        return self._text_input.text

    @text.setter
    def text(self, text: str) -> None:
        self._text.text = self._text_input.set_text(text)
        if self._text_input.at_end:
            self._text.text += " "
        self.clear_highlight()
        self.highlight_cursor()

        if len(self._text.text) >= 12:
            width = self._text.content_width + 2 * Style.Format.padding
            x = self._body.x - (width - self._body.width) * 0.5
            self._body.width = self._shadow.width = width
            self._body.x = x
            self._shadow.x = x - 2 * Style.Format.drop_x

    @property
    def cursor(self) -> int:
        return self._text_input.cursor


class PageTab(Element):

    def __init__(self, text: str):
        Element.__init__(self)
        self._text = Label(
            text,
            0,
            0,
            0,
            color=Style.Colors.accent,
            font_name=Style.Text.Names.monospace,
            font_size=Style.Text.Sizes.normal,
            anchor_y="bottom",
            group=OVERLAY_PRIMARY,
        )
        self._panel = RoundedRectangle(
            0.0,
            0.0,
            self._text.content_width + 2 * Style.Format.corner_radius,
            self._text.content_height + 2 * Style.Format.padding,
            (Style.Format.corner_radius, 0.0, 0.0, Style.Format.corner_radius),
            (12, 1, 1, 12),
            color=Style.Colors.base,
            group=OVERLAY_PRIMARY,
        )

    def connect_renderer(self, batch: Batch | None) -> None:
        self._panel.batch = batch
        self._text.batch = batch

    def contains_point(self, point: tuple[float, float]) -> bool:
        l, b = self._panel.position
        w, h = self._panel.width, self._panel.height
        return 0 <= point[0] - l <= w and 0 <= point[1] - b <= h

    @property
    def text(self) -> str:
        return self._text.text

    @property
    def width(self):
        return self._panel.width

    @property
    def height(self):
        return self._panel.height

    def update_position(self, point: tuple[float, float]) -> None:
        self._panel.position = point
        self._text.position = (
            point[0] + Style.Format.corner_radius,
            point[1] + Style.Format.padding,
            0.0,
        )

    def select(self):
        self._text.set_style("color", Style.Colors.highlight)
        self._panel.color = Style.Colors.base

    def deselect(self):
        self._text.set_style("color", Style.Colors.accent)
        self._panel.color = Style.Colors.base


class PageRow(Element):

    def __init__(self):
        Element.__init__(self)
        self._position: tuple[float, float] = (0.0, 0.0)
        self._size: tuple[float, float] = (0.0, 0.0)
        self._batch: Batch | None = None
        self._tabs: list[PageTab] = []
        self._tab_map: dict[str, PageTab] = {}

    def connect_renderer(self, batch: Batch | None) -> None:
        self._batch = batch
        for tab in self._tabs:
            tab.connect_renderer(batch)

    def contains_point(self, point: tuple[float, float]) -> bool:
        l, t = self._position
        w, h = self._size
        return 0 <= point[0] - l <= w and 0 <= t - point[1] <= h

    def get_hovered_tab(self, point: tuple[float, float]) -> PageTab | None:
        for tab in self._tabs:
            if tab.contains_point(point):
                return tab
        return None

    def update_position(self, point: tuple[float, float]) -> None:
        self._position = point
        self.layout_tabs()

    def layout_tabs(self):
        l, t = self._position
        w, h = 0.0, 0.0
        for tab in self._tabs:
            tab.update_position((l + w, t - tab.height))
            w = w + tab.width
            h = max(h, tab.height)

    def add_tab(self, tab: PageTab, idx: int = -1):
        if tab.text in self._tab_map:
            return
        tab.connect_renderer(self._batch)
        self._tabs.insert(idx, tab)
        self._tab_map[tab.text] = tab
        self.layout_tabs()

    def rem_tab(self, tab: PageTab):
        if tab.text not in self._tab_map:
            return
        tab.disconnect_renderer()
        self._tabs.remove(tab)
        self._tab_map.pop(tab.text)
        self.layout_tabs()

    def select_tab(self, tab: PageTab, only: bool = False):
        if only:
            for other in self._tabs:
                other.deselect()
        tab.select()

    def get_tab(self, name: str) -> PageTab:
        return self._tab_map[name]
