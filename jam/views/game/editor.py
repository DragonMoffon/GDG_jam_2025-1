from pathlib import Path
from enum import Enum, auto

from pyglet.graphics import Batch
from pyglet.shapes import RoundedRectangle
from arcade import Rect, LBWH, Vec2, Camera2D
from arcade.camera.default import ViewportProjector
from arcade.future import background

from jam.node import graph
from jam.gui import core, util, graph as gui
from jam.gui.frame import Frame, ACTIVE_GROUP
from jam.graphics.clip import ClippingMask
from jam.input import inputs, Button, Axis

from resources import style


class EditorMode(Enum):
    NONE = 0
    DRAG_BLOCK = auto()
    DRAG_CONNECTION = auto()
    CHANGE_CONFIG = auto()
    ADD_BLOCK = auto()
    ADD_NODE = auto()


class Editor:

    def __init__(self, region: Rect, graph_src: Path | None = None) -> None:
        self._region: Rect = region  #

        # Graph
        self._src: Path | None = graph_src
        self._graph, positions = (
            (graph.Graph(), {}) if not graph_src else graph.read_graph(graph_src)
        )

        # Rendering
        self._camera = Camera2D(region)
        self._background = background.background_from_file(  # type: ignore -- reportUnknownMemberType
            style.game.editor.background, size=(int(region.size.x), int(region.size.y))  # type: ignore -- reportArgumentType
        )
        self._gui = core.Gui(self._camera)

        # Editor State
        self._mode = EditorMode.NONE

        # Drag Block
        self._selected_block: gui.BlockElement | None = None
        self._offset: Vec2 = Vec2()

        # Create Connection
        self._start_pos: tuple[float, float] = (0.0, 0.0)
        self._source_block: gui.BlockElement | None = None
        self._target_block: gui.BlockElement | None = None
        self._output: str = ""
        self._input: str = ""

        # Add Block
        self._select_position: tuple[float, float] = (0.0, 0.0)
        self._block_popup: util.SelectionPopup | None = None

        # Edit Config Value
        self._text = ""
        self._panel: gui.TextPanel | None = None
        self._text_scroll: int = 0

    def set_mode_none(self) -> None:
        self._mode = EditorMode.NONE

        if self._selected_block is not None:
            # TODO: de-select selected block
            self._selected_block = None
            self._offset = Vec2()

        if self._source_block is not None:
            # TODO: de-select connection blocks
            self._start_pos = (0.0, 0.0)
            self._source_block = None
            self._target_block = None
            self._output = ""
            self._input = ""

        if self._block_popup is not None:
            # TODO: destroy block popup
            self._select_position = (0.0, 0.0)
            self._block_popup = None

        if self._panel is not None:
            # TODO: finish editing panel
            self._text = ""
            self._panel = None
            self._text_scroll = 0

    def set_mode_drag_block(self, block: gui.BlockElement) -> None:
        self._mode = EditorMode.DRAG_BLOCK

        cursor = self.get_cursor_pos()
        self._offset = Vec2(cursor[0] - block.left, cursor[1] - block.bottom)
        self._selected_block = block

    def set_mode_drag_connection(self) -> None:
        pass

    def set_mode_change_value(self) -> None:
        pass

    def set_mode_add_block(self) -> None:
        self._mode = EditorMode.ADD_BLOCK

        self._select_position = pos = self.get_cursor_pos()
        top = pos[1] > 0.5 * self.panel_height
        right = pos[0] > 0.5 * self.panel_width

        dx = style.format.padding if right else -style.format.padding
        dy = style.format.padding if top else -style.format.padding

        self._block_popup = util.SelectionPopup(
            tuple(
                util.PopupAction(typ.name, self.create_new_block, typ)
                for typ in graph.available
            ),
            (pos[0] + dx, pos[1] + dy),
            top,
            right
        )

    def set_mode_add_node(self) -> None:
        pass

    # -- INPUT METHODS --

    def none_on_input(self, button: Button, modifiers: int, pressed: bool) -> None:
        if not pressed:
            return

    def drag_block_on_input(self, button: Button, modifiers: int, pressed: bool) -> None: ...

    def create_connection_on_input(self, button: Button, modifiers: int, pressed: bool) -> None: ...

    def add_block_on_input(self, button: Button, modifiers: int, pressed: bool) -> None: ...

    def edit_config_on_input(self, button: Button, modifiers: int, pressed: bool) -> None: ...

    def on_input(self, button: Button, modifiers: int, pressed: bool) -> None:
        match self._mode:
            case EditorMode.NONE:
                self.none_on_input(button, modifiers, pressed)
            case EditorMode.DRAG_BLOCK:
                self.drag_block_on_input(button, modifiers, pressed)
            case EditorMode.ADD_NODE:
                self.create_connection_on_input(button, modifiers, pressed)
            case EditorMode.CHANGE_CONFIG:
                self.edit_config_on_input(button, modifiers, pressed)
            case _:
                pass

    # -- AXIS METHODS --

    def on_axis_change(self, axis: Axis, value_1: float, value_2: float) -> None:
        pass

    # -- CURSOR METHODS --

    def none_on_cursor_motion(self, x: float, y: float, dx: float, dy: float) -> None: ...
    def drag_block_on_cursor_motion(self, x: float, y: float, dx: float, dy: float) -> None: ...
    def create_connection_on_cursor_motion(self, x: float, y: float, dx: float, dy: float) -> None: ...

    def on_cursor_motion(self, x: float, y: float, dx: float, dy: float) -> None:
        match self._mode:
            case EditorMode.NONE:
                self.none_on_cursor_motion(x, y, dx, dy)
            case EditorMode.DRAG_BLOCK:
                self.drag_block_on_cursor_motion(x, y, dx, dy)
            case EditorMode.ADD_NODE:
                self.create_connection_on_cursor_motion(x, y, dx, dy)
            case _:
                pass

    def on_cursor_scroll(
        self, x: float, y: float, scroll_x: float, scroll_y: float
    ) -> bool | None: ...

    # -- GAME EVENT METHODS --

    def draw(self) -> None: ...
    def on_update(self, delta_time: float) -> None: ...

    # -- UTIL METHODS --
    def get_cursor_pos(self) -> tuple[float, float]: ...
    def create_new_block(self, typ: graph.BlockType) -> None: ...


class EditorFrame(Frame):

    def __init__(
        self,
        tag_offset: float,
        position: tuple[float, float],
        height: float,
        show_body: bool = False,
        show_shadow: bool = True,
    ):
        size = 1000, height

        # TODO: add tabs

        clip_size = int(size[0] - style.format.footer_size), int(
            size[1] - 2 * style.format.footer_size
        )
        clip_rect = LBWH(0.0, 0.0, clip_size[0], clip_size[1])
        self.cliping_mask = ClippingMask(
            (0.0, 0.0), clip_size, clip_size, group=ACTIVE_GROUP
        )
        self._clip_projector = ViewportProjector(clip_rect)
        with self.cliping_mask.clip:
            with self._clip_projector.activate():
                RoundedRectangle(
                    0.0,
                    0.0,
                    size[0] - style.format.footer_size,
                    size[1] - 2 * style.format.footer_size,
                    (style.format.corner_radius, style.format.corner_radius, 0.0, 0.0),
                    (12, 12, 1, 1),
                    color=(255, 255, 255, 255),
                ).draw()

        self._editor = Editor(clip_rect, Path('graph copy.toml'))

        Frame.__init__(self, 'EDITOR', tag_offset, position, size, show_body, show_shadow)

    def connect_renderer(self, batch: Batch | None) -> None:
        Frame.connect_renderer(self, batch)
        self.cliping_mask.batch = batch

    def update_position(self, point: tuple[float, float]) -> None:
        Frame.update_position(self, point)
        self.cliping_mask.position = (
            point[0] + style.format.footer_size,
            point[1] + style.format.footer_size,
        )

    @property
    def show_body(self) -> bool:
        return self._show_body

    @show_body.setter
    def show_body(self, show: bool) -> None:
        self._show_body = show
        self._panel.visible = show
        self.cliping_mask.visible = show

    def on_input(self, input: Button, modifiers: int, pressed: bool) -> bool | None: ...
    def on_axis_change(self, axis: Axis, value_1: float, value_2: float): ...
    def on_cursor_motion(self, x: float, y: float, dx: float, dy: float) -> bool | None: ...

    def on_cursor_scroll(
        self, x: float, y: float, scroll_x: float, scroll_y: float
    ) -> bool | None: ...

    def on_draw(self) -> None:
        with self.cliping_mask.target:
            with self._clip_projector.activate():
                self._editor.draw()