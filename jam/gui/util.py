from uuid import UUID, uuid4
from typing import Callable

from pyglet.shapes import Batch, Group, RoundedRectangle
from arcade import get_window, Camera2D, Rect, Text

from .core import Element, OVERLAY_SHADOW, OVERLAY_PRIMARY, OVERLAY_HIGHTLIGHT
from resources import style


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
            style.editor.padding,
            14,
            style.editor.colors.block,
        )
        self._shadow = RoundedRectangle(
            bottom_left[0] - 2 * style.editor.drop_x,
            bottom_left[1] - 2 * style.editor.drop_y,
            width,
            height,
            style.editor.padding,
            14,
            style.editor.colors.shadow,
        )

    def connect_renderer(self, batch: Batch | None):
        self._body.group = batch and OVERLAY_PRIMARY
        self._shadow.group = batch and OVERLAY_SHADOW

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
            bottom_left[0] + style.editor.padding,
            bottom_left[1] + style.editor.padding,
            style.editor.colors.connection,
            style.text.normal.size,
            font_name=style.text.normal.name,
            anchor_y="bottom",
        )
        Popup.__init__(
            self,
            self._text.content_width + 2 * style.editor.padding,
            self._text.content_height + 2 * style.editor.padding,
            bottom_left,
            uid,
        )

    def connect_renderer(self, batch: Batch | None):
        Popup.connect_renderer(self, batch)

        self._text.group = batch and OVERLAY_PRIMARY
        self._text.batch = batch


class PopupAction:

    def __init__(self, name, action: Callable, *args, **kwds):
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
                style.editor.colors.accent,
                style.text.normal.size,
                anchor_y="bottom",
                font_name=style.text.normal.name,
            )
            for name in self.actions
        }

        text_width = max(text.content_width for text in self._action_text.values())
        text_height = max(text.content_height for text in self._action_text.values())

        self._action_panels = {
            name: RoundedRectangle(
                0.0,
                0.0,
                text_width + 2 * style.editor.padding,
                text_height + 2 * style.editor.padding,
                style.editor.padding,
                14,
                style.editor.colors.background,
            )
            for name in self.actions
        }

        width = (
            max(panel.width for panel in self._action_panels.values())
            + 2 * style.editor.padding
        )
        height = (
            sum(panel.height for panel in self._action_panels.values())
            + (len(actions) + 1) * style.editor.padding
        )

        bottom = position[1] - height if top else position[1]
        left = position[0] - width if right else position[0]

        for idx, action in enumerate(actions):
            y = (
                bottom
                + style.editor.padding
                + idx * (3 * style.editor.padding + text_height)
            )
            self._action_panels[action.name].position = left + style.editor.padding, y
            self._action_text[action.name].position = (
                left + 2 * style.editor.padding,
                y + style.editor.padding,
            )
        Popup.__init__(self, width, height, (left, bottom), uid)

    def connect_renderer(self, batch: Batch | None):
        Popup.connect_renderer(self, batch)

        for action in self.actions:
            p = self._action_panels[action]
            p.group = batch and OVERLAY_PRIMARY
            p.batch = batch
            t = self._action_text[action]
            t.group = batch and OVERLAY_PRIMARY
            t.batch = batch

    def get_hovered_item(self, point: tuple[float, float]):
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
                style.editor.colors.block
                if highlight
                else style.editor.colors.background
            )
            self._action_text[name].color = (
                style.editor.colors.connection
                if highlight
                else style.editor.colors.accent
            )
            return

        for action in self.actions:
            h = action == name
            self._action_panels[action].color = (
                style.editor.colors.block if h else style.editor.colors.background
            )
            self._action_text[action].color = (
                style.editor.colors.connection if h else style.editor.colors.accent
            )

    def clear_highlight(self):
        for action in self.actions:
            self._action_panels[action].color = style.editor.colors.background
            self._action_text[action].color = style.editor.colors.accent
