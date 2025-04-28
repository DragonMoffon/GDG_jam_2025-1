from pathlib import Path
from enum import Enum, auto
from uuid import UUID

from pyglet.graphics import Batch
from pyglet.shapes import RoundedRectangle
from arcade import Rect, LBWH, Vec2, Vec3, Camera2D
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


class GraphController:

    def __init__(
        self,
        block_graph: graph.Graph,
        editor_gui: core.Gui,
        positions: dict[UUID, tuple[float, float]] | None = None,
    ):
        if positions is None:
            positions = {}

        self._graph = block_graph
        self._gui = editor_gui

        self._block_elements: dict[UUID, gui.BlockElement] = {}
        self._connection_elements: dict[UUID, gui.ConnectionElement] = {}

        self._temp_elements: dict[UUID, gui.TempValueElement] = {}

        self._init_graph(positions)

    def _init_graph(self, positions: dict[UUID, tuple[float, float]]) -> None:
        for block in self._graph.blocks:
            pos = positions.get(block.uid, (0.0, 0.0))
            element = gui.BlockElement(block)
            element.update_position(pos)
            self._block_elements[block.uid] = element
            self._gui.add_element(element)

        for connection in self._graph.connections:
            source = self._block_elements[connection.source]
            origin = source.get_output(connection.output)
            target = self._block_elements[connection.target]
            final = target.get_input(connection.input)

            element = gui.ConnectionElement(connection, origin.link_pos, final.link_pos)

    @property
    def blocks(self) -> tuple[gui.BlockElement, ...]:
        return tuple(self._block_elements.values())

    @property
    def connections(self) -> tuple[gui.ConnectionElement, ...]:
        return tuple(self._connection_elements.values())


class Editor:

    def __init__(self, region: Rect, graph_src: Path | None = None) -> None:
        self._region: Rect = region
        self._width = self._region.width
        self._height = self._region.height

        self.cursor_offset: tuple[float, float] = (0.0, 0.0)

        # Graph
        self._src: Path | None = graph_src
        self._graph, positions = (
            (graph.Graph(), {}) if not graph_src else graph.read_graph(graph_src)
        )

        self._blocks: dict[UUID, gui.BlockElement] = {}
        self._connections: dict[UUID, gui.ConnectionElement] = {}

        # Rendering
        self._base_camera = Camera2D(region)
        self._overlay_camera = Camera2D(region)
        self._background = background.background_from_file(  # type: ignore -- reportUnknownMemberType
            style.game.editor.background, size=(int(region.size.x), int(region.size.y))  # type: ignore -- reportArgumentType
        )
        self._gui = core.Gui(self._base_camera, self._overlay_camera)

        self._controller: GraphController = GraphController(
            self._graph, self._gui, positions
        )

        # Editor State
        self._mode = EditorMode.NONE
        self._pan_camera: bool = False

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
            self._gui.remove_element(self._block_popup)
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

    def set_mode_drag_connection(self, noodle: gui.ConnectionElement) -> None:
        pass

    def set_mode_change_value(self) -> None:
        pass

    def set_mode_add_block(self) -> None:
        self._mode = EditorMode.ADD_BLOCK

        self._select_position = pos = self.get_overlay_cursor_pos()
        layout_pos = self.get_cursor_pos()
        top = layout_pos[1] > 0.5 * self._height
        right = layout_pos[0] > 0.5 * self._width

        dx = style.format.padding if right else -style.format.padding
        dy = style.format.padding if top else -style.format.padding

        self._block_popup = util.SelectionPopup(
            tuple(
                util.PopupAction(typ.name, self.create_new_block, typ, pos)
                for typ in self._graph.available
            ),
            (pos[0] + dx, pos[1] + dy),
            top,
            right,
        )
        self._gui.add_element(self._block_popup)

    def set_mode_add_node(self) -> None:
        pass

    # -- INPUT METHODS --

    def none_on_input(self, button: Button, modifiers: int, pressed: bool) -> None:
        if not pressed:
            if button == inputs.PRIMARY_CLICK:
                self._pan_camera = False
            return

        # TODO: saving??

        x, y = self.get_cursor_pos()

        # Find if we are hovering over a block
        clicked_block = None
        for block in self._controller.blocks:
            if block.contains_point((x, y)):
                clicked_block = block
                break

        # Find if we are hovering over a noodle/joint
        clicked_noodle = None
        for noodle in self._controller.connections:
            if noodle.contains_point((x, y)):
                clicked_noodle = noodle
                break

        if button == inputs.PRIMARY_CLICK:
            if clicked_block is not None:
                # TODO: Check to see if connection clicked (self.set_mode_add_connection)
                self.set_mode_drag_block(clicked_block)
                return

            if clicked_noodle is not None:
                self.set_mode_drag_connection(clicked_noodle)
                return

            # If no block and no noodle clicked then pan the camera
            self._pan_camera = True
        elif button == inputs.SECONDARY_CLICK:
            if clicked_block is not None:
                # TODO: destroy block
                return

            if clicked_noodle is not None:
                # TODO: destroy noodle / noodle node
                return

            # If no block and no noodle clicked then add new block
            self.set_mode_add_block()

    def drag_block_on_input(
        self, button: Button, modifiers: int, pressed: bool
    ) -> None: ...

    def create_connection_on_input(
        self, button: Button, modifiers: int, pressed: bool
    ) -> None: ...

    def add_block_on_input(self, button: Button, modifiers: int, pressed: bool) -> None:
        if not pressed:
            return

        if button == inputs.PRIMARY_CLICK:
            cursor = self.get_overlay_cursor_pos()
            if self._block_popup is None or not self._block_popup.contains_point(
                cursor
            ):
                self.set_mode_none()
                self.on_input(button, modifiers, pressed)
                return

            action = self._block_popup.get_hovered_item(cursor)
            if action is not None:
                self._block_popup.actions[action]()

            self.set_mode_none()

        elif button == inputs.SECONDARY_CLICK:
            self.set_mode_none()

    def edit_config_on_input(
        self, button: Button, modifiers: int, pressed: bool
    ) -> None: ...

    def on_input(self, button: Button, modifiers: int, pressed: bool) -> None:
        match self._mode:
            case EditorMode.NONE:
                self.none_on_input(button, modifiers, pressed)
            case EditorMode.DRAG_BLOCK:
                self.drag_block_on_input(button, modifiers, pressed)
            case EditorMode.ADD_NODE:
                self.create_connection_on_input(button, modifiers, pressed)
            case EditorMode.ADD_BLOCK:
                self.add_block_on_input(button, modifiers, pressed)
            case EditorMode.CHANGE_CONFIG:
                self.edit_config_on_input(button, modifiers, pressed)
            case _:
                pass

    # -- AXIS METHODS --

    def on_axis_change(self, axis: Axis, value_1: float, value_2: float) -> None:
        pass

    # -- CURSOR METHODS --

    def none_on_cursor_motion(self, x: float, y: float, dx: float, dy: float) -> None:
        if self._pan_camera:
            pos = self._base_camera.position
            self._base_camera.position = self._overlay_camera.position = (
                pos[0] - dx / self._base_camera.zoom,
                pos[1] - dy / self._base_camera.zoom,
            )
            self._background.texture.offset = self._base_camera.position
            return

    def drag_block_on_cursor_motion(
        self, x: float, y: float, dx: float, dy: float
    ) -> None: ...

    def add_block_on_cursor_motion(
        self, x: float, y: float, dx: float, dy: float
    ) -> None:
        if self._block_popup is None:
            self.set_mode_none()
            return

        action = self._block_popup.get_hovered_item(self.get_overlay_cursor_pos())
        self._block_popup.highlight_action(action)

    def create_connection_on_cursor_motion(
        self, x: float, y: float, dx: float, dy: float
    ) -> None: ...

    def on_cursor_motion(self, x: float, y: float, dx: float, dy: float) -> None:
        match self._mode:
            case EditorMode.NONE:
                self.none_on_cursor_motion(x, y, dx, dy)
            case EditorMode.DRAG_BLOCK:
                self.drag_block_on_cursor_motion(x, y, dx, dy)
            case EditorMode.ADD_BLOCK:
                self.add_block_on_cursor_motion(x, y, dx, dy)
            case EditorMode.ADD_NODE:
                self.create_connection_on_cursor_motion(x, y, dx, dy)
            case _:
                pass

    def on_cursor_scroll(
        self, x: float, y: float, scroll_x: float, scroll_y: float
    ) -> bool | None:
        if scroll_y:
            self._base_camera.zoom = max(
                0.5, min(1.0, self._base_camera.zoom + scroll_y / 10)
            )

    # -- GAME EVENT METHODS --

    def draw(self) -> None:
        self._background.draw()
        self._gui.draw()

    def update(self, delta_time: float) -> None: ...

    # -- UTIL METHODS --
    def get_cursor_pos(self) -> tuple[float, float]:
        pos = inputs.cursor
        return pos[0] - self.cursor_offset[0], pos[1] - self.cursor_offset[1]

    def get_base_cursor_pos(self) -> tuple[float, float]:
        pos: Vec3 = self._base_camera.unproject(self.get_cursor_pos())
        return pos.x, pos.y

    def get_overlay_cursor_pos(self) -> tuple[float, float]:
        pos: Vec3 = self._overlay_camera.unproject(self.get_cursor_pos())
        return pos.x, pos.y

    def create_new_block(
        self, typ: graph.BlockType, position: tuple[float, float]
    ) -> None:
        pass


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

        self._editor = Editor(clip_rect, Path("graph copy.toml"))

        Frame.__init__(
            self, "EDITOR", tag_offset, position, size, show_body, show_shadow
        )

    def connect_renderer(self, batch: Batch | None) -> None:
        Frame.connect_renderer(self, batch)
        self.cliping_mask.batch = batch

    def update_position(self, point: tuple[float, float]) -> None:
        Frame.update_position(self, point)
        self.cliping_mask.position = self._editor.cursor_offset = (
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

    def on_input(self, input: Button, modifiers: int, pressed: bool) -> bool | None:
        self._editor.on_input(input, modifiers, pressed)

    def on_axis_change(self, axis: Axis, value_1: float, value_2: float):
        self._editor.on_axis_change(axis, value_1, value_2)

    def on_cursor_motion(self, x: float, y: float, dx: float, dy: float) -> bool | None:
        self._editor.on_cursor_motion(x, y, dx, dy)

    def on_cursor_scroll(
        self, x: float, y: float, scroll_x: float, scroll_y: float
    ) -> bool | None:
        self._editor.on_cursor_scroll(x, y, scroll_x, scroll_y)

    def on_draw(self) -> None:
        with self.cliping_mask.target:
            with self._clip_projector.activate():
                self._editor.draw()

    def on_hide(self) -> None:
        self._editor.set_mode_none()
        self._editor._gui.disable()

    def on_select(self) -> None:
        self._editor._gui.enable()
