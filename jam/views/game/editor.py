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
    ADD_CONNECTION = auto()


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

    @property
    def temporary(self) -> tuple[gui.TempValueElement, ...]:
        return tuple(self._temp_elements.values())

    def get_block(self, uid: UUID) -> gui.BlockElement:
        if uid not in self._block_elements:
            raise KeyError(f"No block with uid {uid}")
        return self._block_elements[uid]

    def get_connection(self, uid: UUID) -> gui.ConnectionElement:
        if uid not in self._connection_elements.values():
            raise KeyError(f"No connection with uid {uid}")

        return self._connection_elements[uid]

    def add_block(self, block: gui.BlockElement) -> None:
        self._graph.add_block(block._block)
        self._gui.add_element(block)
        self._block_elements[block.uid] = block

        for inp in block._input_connections:
            self.create_temporary(block, inp)

    def remove_block(self, block: gui.BlockElement) -> None:
        for connection in block._input_connections.values():
            if connection.uid in self._temp_elements:
                self.remove_temporary(connection)
            else:
                self._unlink_connection(connection)

        for output in block._output_connections.values():
            for connection in output:
                self._unlink_connection(connection)

        self._gui.remove_element(block)
        self._graph.remove_block(block.block)
        self._block_elements.pop(block.uid)

    def add_connection(self, connection: gui.ConnectionElement) -> None:
        self._link_connection(connection)
        self._graph.add_connection(connection.connection)

    def remove_connection(self, connection: gui.ConnectionElement) -> None:
        self._unlink_connection(connection)
        self._graph.remove_connection(connection.connection)

        target = self.get_block(connection.connection.uid)
        self.create_temporary(target, connection.connection.input)

    def _link_connection(self, connection: gui.ConnectionElement) -> None:
        target = self.get_block(connection.connection.target)
        inp = target._input_connections[connection.connection.input]
        if inp is not None:
            if inp.uid in self._connection_elements:
                self._unlink_connection(inp)
            elif inp.uid in self._temp_elements:
                self.remove_temporary(inp)
        target._input_connections[connection.connection.input] = connection
        source = self.get_block(connection.connection.source)
        source._output_connections[connection.connection.output].append(connection)

        target.get_input(connection.connection.input).active = True
        source.get_output(connection.connection.output).active = True

        self._connection_elements[connection.uid] = connection
        self._gui.add_element(connection)

    def _unlink_connection(self, connection: gui.ConnectionElement) -> None:
        target = self.get_block(connection.connection.target)
        source = self.get_block(connection.connection.source)

        target._input_connections[connection.connection.input] = None
        source._output_connections[connection.connection.output].remove(connection)

        target.get_input(connection.connection.input).active = False
        if not source._output_connections[connection.connection.output]:
            source.get_output(connection.connection.output).active = False

        self._connection_elements.pop(connection.uid)
        self._gui.remove_element(connection)

    def create_temporary(self, block: gui.BlockElement, inp: str) -> None:
        connection = block._input_connections[inp]
        if connection is not None:
            return

        block_typ = block.block.type
        temp_type = graph.BLOCK_CAST[block_typ.inputs[inp]._typ]
        temp_block = graph.Block(temp_type)
        temp_connection = graph.Connection(temp_block.uid, "value", block.uid, inp)
        element = gui.TempValueElement(temp_block, temp_connection)
        element.update_end(block.get_input(inp).link_pos)

        self._gui.add_element(element)
        self._graph.add_block(temp_block)
        self._graph.add_connection(temp_connection)

        block._input_connections[inp] = element
        self._temp_elements[temp_block.uid] = element

    def remove_temporary(self, temp: gui.TempValueElement) -> None:
        self._gui.remove_element(temp)


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
        self._hovered_block: gui.BlockElement | None = None

        # Drag Block
        self._selected_block: gui.BlockElement | None = None
        self._offset: Vec2 = Vec2()

        # Create Connection
        self._incomplete_connection: gui.ConnectionElement | None = None

        # Add Block
        self._select_position: tuple[float, float] = (0.0, 0.0)
        self._block_popup: util.SelectionPopup | None = None

        # Edit Config Value
        self._text = ""
        self._panel: gui.TextPanel | None = None
        self._text_scroll: int = 0

    def set_mode_none(self) -> None:
        self._mode = EditorMode.NONE

        if self._hovered_block is not None:
            self._hovered_block.deselect()
            self._hovered_block.remove_highlighting()
            self._hovered_block = None

        if self._selected_block is not None:
            self._selected_block.deselect()
            self._selected_block.remove_highlighting()
            self._selected_block = None
            self._offset = Vec2()

        if self._incomplete_connection is not None:
            # TODO: de-select connection blocks
            self._gui.remove_element(self._incomplete_connection)
            self._incomplete_connection = None

        if self._block_popup is not None:
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

        if self._hovered_block is not None:
            self._hovered_block.deselect()
            self._hovered_block = None

        cursor = self.get_base_cursor_pos()
        self._offset = Vec2(cursor[0] - block.left, cursor[1] - block.bottom)
        self._selected_block = block
        self._selected_block.select()

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

    def set_mode_add_connection(self, source: gui.BlockElement, output: str) -> None:
        self._mode = EditorMode.ADD_CONNECTION

        connection = graph.Connection(source.uid, output, None, None)
        start = source.get_output(output).link_pos
        end = self.get_base_cursor_pos()
        element = gui.ConnectionElement(connection, start, end)

        if self._hovered_block is not None:
            self._hovered_block.deselect()
            self._hovered_block = None

        self._selected_block = source
        self._selected_block.select()
        self._selected_block.highlight_output(output)

        self._incomplete_connection = element
        self._gui.add_element(element)

    # -- INPUT METHODS --

    def none_on_input(self, button: Button, modifiers: int, pressed: bool) -> None:
        if not pressed:
            if button == inputs.PRIMARY_CLICK:
                self._pan_camera = False
            return

        # TODO: saving??

        cursor = self.get_base_cursor_pos()

        # Find if we are hovering over a block
        clicked_block = None
        for block in self._controller.blocks:
            if block.near_point(cursor, 16.0):
                clicked_block = block
                break

        # Find if we are hovering over a noodle/joint
        clicked_noodle = None
        for noodle in self._controller.connections:
            if noodle.contains_point(cursor):
                clicked_noodle = noodle
                break

        if button == inputs.PRIMARY_CLICK:
            if clicked_block is not None:
                # TODO: Add panel editing self.set_mode_edit_config(block, config)
                output, dist = clicked_block.get_nearest_output(cursor)
                if dist <= 16.0:
                    self.set_mode_add_connection(clicked_block, output)
                    return
                elif clicked_block.contains_point(cursor):
                    self.set_mode_drag_block(clicked_block)
                return

            if clicked_noodle is not None:
                self.set_mode_drag_connection(clicked_noodle)
                return

            # If no block and no noodle clicked then pan the camera
            self._pan_camera = True
        elif button == inputs.SECONDARY_CLICK:
            if clicked_block is not None:
                self._controller.remove_block(clicked_block)
                return

            if clicked_noodle is not None:
                # TODO: destroy noodle / noodle node
                return

            # If no block and no noodle clicked then add new block
            self.set_mode_add_block()

    def drag_block_on_input(
        self, button: Button, modifiers: int, pressed: bool
    ) -> None:
        if button == inputs.PRIMARY_CLICK and not pressed:
            self.set_mode_none()
            return

    def add_connection_on_input(
        self, button: Button, modifiers: int, pressed: bool
    ) -> None:
        cursor = self.get_base_cursor_pos()
        if not pressed:
            hovered_block = None
            for block in self._controller.blocks:
                if block == self._selected_block:
                    continue
                if block.near_point(cursor, 16.0):
                    hovered_block = block
                    break
            if hovered_block is None:
                self.set_mode_none()
                return

            if self._hovered_block is not None:
                self._hovered_block.deselect()

            name, dist = hovered_block.get_nearest_input(cursor)
            if dist > 16:
                self.set_mode_none()
                return
            connection = self._incomplete_connection._connection
            connection.target = hovered_block.uid
            connection.input = name

            self._incomplete_connection.update_end(
                hovered_block.get_input(name).link_pos
            )

            self._controller.add_connection(self._incomplete_connection)
            self._incomplete_connection = None
            self.set_mode_none()
            return

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
            case EditorMode.ADD_CONNECTION:
                self.add_connection_on_input(button, modifiers, pressed)
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

        cursor = self.get_base_cursor_pos()
        hovered_block = None
        for block in self._controller.blocks:
            if block.near_point(cursor, 16.0):
                hovered_block = block
                break

        if self._hovered_block is not None:
            self._hovered_block.deselect()
        if hovered_block is not None:
            hovered_block.select()
            name, dist = hovered_block.get_nearest_output(cursor)
            if dist <= 16.0:
                hovered_block.highlight_output(name)
        self._hovered_block = hovered_block

    def drag_block_on_cursor_motion(
        self, x: float, y: float, dx: float, dy: float
    ) -> None:
        if self._selected_block is None:
            self.set_mode_none()
            return

        x, y = self.get_base_cursor_pos()
        self._selected_block.update_position((x - self._offset[0], y - self._offset[1]))

    def add_block_on_cursor_motion(
        self, x: float, y: float, dx: float, dy: float
    ) -> None:
        if self._block_popup is None:
            self.set_mode_none()
            return

        action = self._block_popup.get_hovered_item(self.get_overlay_cursor_pos())
        self._block_popup.highlight_action(action)

    def add_connection_on_cursor_motion(
        self, x: float, y: float, dx: float, dy: float
    ) -> None:
        if self._incomplete_connection is None:
            self.set_mode_none()

        cursor = self.get_base_cursor_pos()

        self._incomplete_connection.update_end(cursor)

        hovered_block = None
        for block in self._controller.blocks:
            if block == self._selected_block:
                continue
            if block.near_point(cursor, 16.0):
                hovered_block = block
                break

        if self._hovered_block is not None:
            self._hovered_block.deselect()
        if hovered_block is not None:
            hovered_block.select()
            name, dist = hovered_block.get_nearest_input(cursor)
            if dist <= 16.0:
                hovered_block.highlight_input(name)
        self._hovered_block = hovered_block

    def on_cursor_motion(self, x: float, y: float, dx: float, dy: float) -> None:
        match self._mode:
            case EditorMode.NONE:
                self.none_on_cursor_motion(x, y, dx, dy)
            case EditorMode.DRAG_BLOCK:
                self.drag_block_on_cursor_motion(x, y, dx, dy)
            case EditorMode.ADD_BLOCK:
                self.add_block_on_cursor_motion(x, y, dx, dy)
            case EditorMode.ADD_CONNECTION:
                self.add_connection_on_cursor_motion(x, y, dx, dy)
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
        block = graph.Block(typ)
        element = gui.BlockElement(block)
        element.update_position(position)
        self._controller.add_block(element)


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
