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

        # Edit Config Value
        self.text = ""
        self.panel: gui.TextPanel | None = None
        self.text_scroll: int = 0

    def set_mode_none(self):
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

        if self.panel is not None:
            # TODO: finish editing panel
            self.text = ""
            self.panel = None
            self.text_scroll = 0

    def set_mode_drag_block(self, block: gui.BlockElement):
        self._mode = EditorMode.DRAG_BLOCK

        cursor = self.get_cursor_pos()
        self._offset = Vec2(cursor[0] - block.left, cursor[1] - block.bottom)
        self._selected_block = block

    def set_mode_drag_connection(self):
        pass

    def set_mode_change_value(self):
        pass

    def set_mode_add_block(self):
        pass

    def set_mode_add_node(self):
        pass

    def draw(self) -> None: ...
    def on_update(self, delta_time: float) -> None: ...

    # -- UTIL METHODS --
    def get_cursor_pos(self) -> tuple[float, float]: ...


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