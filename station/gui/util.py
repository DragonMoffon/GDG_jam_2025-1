from uuid import UUID
from typing import Callable, Any

from pyglet.graphics import Group

from resources import style

from station.graphics.shadow import get_shadow_shader

from .core import Element, Point
from .elements import Label, RoundedRectangle


class PopupAction:

    def __init__(self, name: str, action: Callable[..., None], *args: Any, **kwds: Any):
        self.name = name
        self.action = action
        self._args = args
        self._kwds = kwds

    def __call__(self):
        return self.action(*self._args, **self._kwds)


class SelectionPopup(Element):

    def __init__(
        self,
        actions: tuple[PopupAction, ...],
        top: bool = False,
        right: bool = False,
        parent: Element | None = None,
        layer: Group | None = None,
        uid: UUID | None = None,
    ):
        Element.__init__(self, parent, layer, uid)
        self._right = right
        self._top = top

        self.actions = {action.name: action for action in actions}
        self._action_text = {
            name: Label(
                name,
                0.0,
                0.0,
                color=style.colors.accent,
                font_size=style.text.sizes.normal,
                font_name=style.text.names.monospace,
                anchor_y="bottom",
                parent=self,
                layer=self.BODY(2),
            )
            for name in self.actions
        }

        self._text_width = max(text.width for text in self._action_text.values())
        self._text_height = max(text.height for text in self._action_text.values())

        self._action_panels = {
            name: RoundedRectangle(
                0.0,
                0.0,
                self._text_width + 2 * style.format.padding,
                self._text_height + 2 * style.format.padding,
                style.format.padding,
                14,
                style.colors.background,
                parent=self,
                layer=self.BODY(1),
            )
            for name in self.actions
        }

        width = (
            max(panel.width for panel in self._action_panels.values())
            + 2 * style.format.padding
        )
        height = (
            sum(panel.height for panel in self._action_panels.values())
            + (len(actions) + 1) * style.format.padding
        )

        self._body = RoundedRectangle(
            0.0,
            0.0,
            width,
            height,
            style.format.padding,
            14,
            style.colors.base,
            parent=self,
            layer=self.BODY(),
        )
        self._shadow = RoundedRectangle(
            0.0,
            0.0,
            width,
            height,
            style.format.padding,
            14,
            style.colors.dark,
            program=get_shadow_shader(),
            parent=self,
            layer=self.SHADOW(),
        )

    def contains_point(self, point: Point) -> bool:
        return self._body.contains_point(point)

    def update_position(self, point: Point) -> None:
        left = point[0] - self._body.width if self._right else point[0]
        bottom = point[1] - self._body.height if self._top else point[1]
        self._body.update_position((left, bottom))
        self._shadow.update_position(
            (left - 2 * style.format.drop_x, bottom - 2 * style.format.drop_y)
        )

        x = left + style.format.padding
        dy = 3 * style.format.padding + self._text_height
        for idx, action in enumerate(self.actions):
            y = bottom + style.format.padding + idx * dy
            self._action_panels[action].update_position((x, y))
            self._action_text[action].update_position(
                (
                    x + style.format.padding,
                    y + style.format.padding,
                )
            )

    def get_position(self) -> Point:
        return self._body.get_position()

    def get_size(self) -> tuple[float, float]:
        return self._body.get_size()

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
    ) -> None:
        if name not in self.actions and name is not None:
            return

        if name is None:
            only = False

        if only or not highlight:
            self._action_panels[name].color = (
                style.colors.base if highlight else style.colors.background
            )
            self._action_text[name].color = (
                style.colors.highlight if highlight else style.colors.accent
            )
            return

        for action in self.actions:
            h = action == name
            self._action_panels[action].color = (
                style.colors.base if h else style.colors.background
            )
            self._action_text[action].color = (
                style.colors.highlight if h else style.colors.accent
            )

    def clear_highlight(self) -> None:
        for action in self.actions:
            self._action_panels[action].color = style.colors.background
            self._action_text[action].color = style.colors.accent


class PageTab(Element):

    def __init__(
        self,
        text: str,
        content: Element,
        parent: Element | None = None,
        layer: Group | None = None,
        uid: UUID | None = None,
    ):
        Element.__init__(self, parent, layer, uid)
        self._text = Label(
            text,
            0,
            0,
            0,
            color=style.colors.accent,
            font_name=style.text.names.monospace,
            font_size=style.text.sizes.normal,
            anchor_y="bottom",
            parent=self,
            layer=self.BODY(),
        )
        self._panel = RoundedRectangle(
            0.0,
            0.0,
            self._text.width + 2 * style.format.corner_radius,
            self._text.height + 2 * style.format.padding,
            (style.format.corner_radius, 0.0, 0.0, style.format.corner_radius),
            (12, 1, 1, 12),
            color=style.colors.base,
            parent=self,
            layer=self.BODY(1),
        )
        self.content: Element = content

    @property
    def text(self) -> str:
        return self._text.label.text

    def contains_point(self, point: tuple[float, float]) -> bool:
        return self._panel.contains_point(point)

    def update_position(self, point: tuple[float, float]) -> None:
        self._panel.update_position(point)
        self._text.update_position(
            (
                point[0] + style.format.corner_radius,
                point[1] + style.format.padding,
            )
        )

    def get_position(self) -> Point:
        return self._panel.get_position()

    def get_size(self) -> tuple[float, float]:
        return self._panel.get_size()

    def select(self) -> None:
        self._text.label.set_style("color", style.colors.highlight)
        self._panel.color = style.colors.base

    def deselect(self) -> None:
        self._text.label.set_style("color", style.colors.accent)
        self._panel.color = style.colors.base


class PageRow(Element):

    def __init__(self):
        Element.__init__(self)
        self._position: tuple[float, float] = (0.0, 0.0)
        self._size: tuple[float, float] = (0.0, 0.0)
        self._tabs: list[PageTab] = []
        self._tab_map: dict[str, PageTab] = {}

    def contains_point(self, point: Point) -> bool:
        l, t = self._position
        w, h = self._size
        return 0 <= point[0] - l <= w and 0 <= t - point[1] <= h

    def update_position(self, point: Point) -> None:
        self._position = point
        self.layout_tabs()

    def get_position(self) -> Point:
        return self._position

    def get_size(self) -> Point:
        return self._size

    def get_hovered_tab(self, point: Point) -> PageTab | None:
        for tab in self._tabs:
            if tab.contains_point(point):
                return tab
        return None

    def layout_tabs(self) -> None:
        l, t = self._position
        w, h = 0.0, 0.0
        for tab in self._tabs:
            tab.update_position((l + w, t - tab.height))
            w = w + tab.width
            h = max(h, tab.height)
        self._size = w, h

    def add_tab(self, tab: PageTab, idx: int = -1) -> None:
        if tab.text in self._tab_map:
            return
        self.add_child(tab)
        self._tabs.insert(idx, tab)
        self._tab_map[tab.text] = tab
        self.layout_tabs()

    def rem_tab(self, tab: PageTab) -> None:
        if tab.text not in self._tab_map:
            return
        self.remove_child(tab)
        self._tabs.remove(tab)
        self._tab_map.pop(tab.text)
        self.layout_tabs()

    def select_tab(self, tab: PageTab, only: bool = False) -> None:
        if only:
            for other in self._tabs:
                other.deselect()
        tab.select()

    def get_tab(self, name: str) -> PageTab:
        return self._tab_map[name]
