from pathlib import Path
from enum import Enum, auto

from pyglet.graphics import Batch
from pyglet.shapes import RoundedRectangle
from arcade import LBWH, Vec2, Vec3, draw_line, Camera2D
from arcade.clock import GLOBAL_CLOCK
from arcade.camera.default import ViewportProjector
from arcade.future import background

from jam.node import loading, render, node
from jam.gui.frame import Frame, ACTIVE_GROUP
from jam.gui import util, core
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

        self.background = background.background_from_file(
            style.game.editor.background, size=clip_size
        )

        self._graph, positions = loading.read_graph(Path("graph.toml"))
        # self._graph = node.Graph("DebugGraph")
        self._renderer = render.GraphRenderer(clip_rect, self._graph)
        self._camera = Camera2D(clip_rect)
        self._gui = core.Gui(self._camera)

        self._output_block: node.Block | None = None
        for block in self._graph._blocks.values():
            if block.name == "Output":
                self._output_block = block
            self._renderer.add_block(block, Vec2(*positions.get(block.uid, (0.0, 0.0))))

        for connection in self._graph._connections.values():
            self._renderer.add_connection(connection)

        with self.cliping_mask.target:
            with self._clip_projector.activate():
                self.background.draw()

        Frame.__init__(
            self, "EDITOR", tag_offset, position, size, show_body, show_shadow
        )

        # Editor State
        self._mode = EditorMode.NONE
        self._cursor_pos = None
        self._popup: util.Popup | None = None
        self._move_camera: bool = False

        # Drag Block
        self._selected_block: render.BlockRenderer = None
        self._offset: Vec2 = Vec2()

        # Create Connection
        self._start_pos: tuple[float, float] = None
        self._source_block: render.BlockRenderer = None
        self._output: str = ""
        self._target_block: render.BlockRenderer = None
        self._input: str = ""

        # Edit Config Value
        self.text = ""
        self.panel: render.IONodeRenderer = None
        self.text_scroll: int = 0

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
    def show_body(self, show: bool) -> bool:
        self._show_body = show
        self._panel.visible = show
        self.cliping_mask.visible = show

    def on_input(self, input: Button, modifiers: int, pressed: bool) -> bool | None:
        match self._mode:
            case EditorMode.NONE:
                self.input_none_mode(input, modifiers, pressed)
            case EditorMode.ADD_BLOCK:
                self.input_add_block_mode(input, modifiers, pressed)
            case EditorMode.DRAG_BLOCK:
                self.input_drag_block_mode(input, modifiers, pressed)
            case EditorMode.DRAG_CONNECTION:
                self.input_drag_connection_mode(input, modifiers, pressed)
            case _:
                ...

    def input_none_mode(self, input: Button, modifiers: int, pressed: bool):
        if not pressed:
            if input == inputs.PRIMARY_CLICK:
                self._move_camera = False
            return
        
        if input == inputs.SAVE_INPUT and modifiers & inputs.SAVE_MOD == inputs.SAVE_MOD:
            self._move_camera = False
            loading.write_graph(
                Path(f"graph_{id(self._graph)}_{GLOBAL_CLOCK.time}.toml"),
                self._graph,
                self._renderer,
            )
            return

        x, y = self.get_cursor_pos()

        if self._popup is not None:
            self._gui.remove_element(self._popup)
            self._popup = None

        # Find if we are hovering over a block
        clicked_block = None
        for block in self._renderer._blocks.values():
            if block.contains_point((x, y)):
                clicked_block = block
                break

        if input == inputs.PRIMARY_CLICK:
            # If we are then check to see if:
            # a) we clicking a panel
            # b) we are dragging a node
            # otherwise drag the block
            if clicked_block is not None:
                if io_node := clicked_block.find_output_node((x, y)):
                    if self._selected_block is not None:
                        self._selected_block.deselect()
                    self._selected_block = None

                    self._source_block = clicked_block
                    clicked_block.select()

                    self._output = io_node.name
                    self._source_block.set_node_active(self._output, True, True)
                    self._start_pos = io_node.node.position
                    self._mode = EditorMode.DRAG_CONNECTION
                    return
                self._selected_block = clicked_block
                self._offset = Vec2(
                    clicked_block.bottom_left.x - x, clicked_block.bottom_left.y - y
                )
                self._mode = EditorMode.DRAG_BLOCK
                return

            # If we aren't over a block then lets check nodes
            for block in self._renderer._blocks.values():
                if io_node := block.find_output_node((x, y)):
                    self._source_block = block
                    self._output = io_node.name
                    self._source_block.set_node_active(self._output, True, True)
                    self._start_pos = io_node.node.position
                    self._mode = EditorMode.DRAG_CONNECTION
                    return
            
            # If we aren't over a block or near a node drag the camera
            self._move_camera = True

        elif input == inputs.SECONDARY_CLICK:
            if clicked_block is not None:
                self._renderer.remove_block(clicked_block._block)
                self._graph.remove_block(clicked_block._block)

            # If we aren't over a block or near a node create a popup
            self._popup = self.create_block_popup(self.get_cursor_pos_raw())
            self._gui.add_element(self._popup)

            self._mode = EditorMode.ADD_BLOCK

    def input_add_block_mode(self, input: Button, modifiers: int, pressed: bool):
        if not pressed:
            return

        if input == inputs.PRIMARY_CLICK:
            x, y = self.get_cursor_pos()
            if self._popup is None:
                self._mode = EditorMode.NONE
                self.on_input(input, modifiers, pressed)

            if not self._popup.contains_point((x, y)):
                self._gui.remove_element(self._popup)
                self._popup = None
                self._mode = EditorMode.NONE
                return

            action = self._popup.get_hovered_item((x, y))

            if action is not None:
                self._popup.actions[action]()

            self._gui.remove_element(self._popup)
            self._popup = None
            self._mode = EditorMode.NONE
        elif input == inputs.SECONDARY_CLICK:
            self._gui.remove_element(self._popup)
            self._popup = None
            self._mode = EditorMode.NONE

    def input_drag_block_mode(self, input: Button, modifiers: int, pressed: bool):
        if pressed:
            return

        if input == inputs.PRIMARY_CLICK:
            self._selected_block = None
            self._mode = EditorMode.NONE

    def input_drag_connection_mode(self, input: Button, modifiers: int, pressed: bool):
        if pressed:
            return

        if input == inputs.PRIMARY_CLICK:
            x, y = self.get_cursor_pos()
            self._source_block.deselect()
            for block in self._renderer._blocks.values():
                if block == self._source_block:
                    continue
                if io_node := block.find_input_node((x, y)):
                    self._target_block = block
                    self._input = io_node.name
                    break
            else:
                self._mode = EditorMode.NONE
                block = self._source_block._block
                if not self._graph._outputs[block.uid][self._output]:
                    self._source_block.set_node_active(self._output, False, True)
                self._source_block: render.BlockRenderer = None
                self._output: str = ""
                self._target_block: render.BlockRenderer = None
                self._input: str = ""
                return

            connection = node.Connection(
                self._source_block._block,
                self._output,
                self._target_block._block,
                self._input,
            )
            old = self._graph.add_connection(connection)

            if old != None:
                self._renderer.remove_connection(old)

            self._renderer.add_connection(connection)

            self._graph.compute(self._target_block._block)
            self._renderer.update_values()

            self._mode = EditorMode.NONE
            self._source_block: render.BlockRenderer = None
            self._output: str = ""
            self._target_block: render.BlockRenderer = None
            self._input: str = ""

    def on_axis_change(self, axis: Axis, value_1: float, value_2: float): ...

    def on_cursor_motion(self, x: float, y: float, dx: float, dy: float) -> bool | None:
        x, y = self.get_cursor_pos()
        match self._mode:
            case EditorMode.NONE:
                if self._move_camera:
                    pos = self._camera.position
                    self._camera.position = pos[0] - dx / self._camera.zoom, pos[1] - dy / self._camera.zoom
                    return

                for block in self._renderer._blocks.values():
                    if block.contains_point((x, y)):
                        if self._selected_block is not None:
                            self._selected_block.deselect()
                        self._selected_block = block
                        block.select()

                        io_node = block.find_input_node((x, y))
                        is_input = True
                        if io_node is None:
                            is_input = False
                            io_node = block.find_output_node((x, y))

                        if io_node is None:
                            break

                        if self._popup is not None:
                            self._gui.remove_element(self._popup)

                        if is_input:
                            value = block._block._arguments[io_node.name]
                        else:
                            value = block._block._results[io_node.name]

                        self._popup = util.InfoPopup(str(value), (x, y))
                        self._gui.add_element(self._popup)

                        break
                else:
                    if self._selected_block is not None:
                        self._selected_block.deselect()
                    self._selected_block = None
            case EditorMode.ADD_BLOCK:
                if self._popup is None:
                    self._mode = EditorMode.NONE
                    return

                action = self._popup.get_hovered_item((x, y))
                self._popup.highlight_action(action)
            case EditorMode.DRAG_BLOCK:
                self._renderer.move_block(
                    self._selected_block._block, Vec2(x, y) + self._offset
                )
            case EditorMode.DRAG_CONNECTION:
                for block in self._renderer._blocks.values():
                    if block.contains_point((x, y)):
                        if self._selected_block is not None:
                            self._selected_block.deselect()
                        self._selected_block = block
                        block.select()
                        break
                else:
                    if self._selected_block is not None:
                        self._selected_block.deselect()
                    self._selected_block = None
            case _:
                ...

    def on_cursor_scroll(
        self, x: float, y: float, scroll_x: float, scroll_y: float
    ) -> bool | None:
        if scroll_y != 0:
            self._camera.zoom = max(0.1, min(1.0, self._camera.zoom + scroll_y / 10))

    def on_draw(self):
        with self.cliping_mask.target:
            self.background.draw()
            with self._camera.activate():
                self._renderer.draw()

                match self._mode:
                    case EditorMode.DRAG_CONNECTION:
                        x, y = self.get_cursor_pos()
                        draw_line(
                            self._start_pos[0],
                            self._start_pos[1],
                            x,
                            y,
                            style.colors.highlight,
                            style.format.line_thickness,
                        )
                    case _:
                        pass

                if self._popup is not None and self._mode == EditorMode.NONE:
                    if not self._popup.contains_point(self.get_cursor_pos()):
                        self._gui.remove_element(self._popup)
                        self._popup = None
            with self._clip_projector.activate():
                self._gui.draw()

    def on_update(self, delta_time: float):
        if self._output_block is not None:
            self._graph.compute(self._output_block)

    def create_block_popup(self, pos: tuple[float, float]):
        def create_block(block_type: type):
            block = block_type()

            self._graph.add_block(block)
            self._renderer.add_block(block, Vec2(*self.get_cursor_pos()))

        top = pos[1] > 0.5 * self.panel_height
        right = pos[0] > 0.5 * self.panel_width

        dx = style.format.padding if right else -style.format.padding
        dy = style.format.padding if top else -style.format.padding

        return util.SelectionPopup(
            tuple(
                util.PopupAction(typ.__name__, create_block, typ)
                for typ in node.Block.__subclasses__()
            ),
            (pos[0] + dx, pos[1] + dy),
            top,
            right,
        )

    def get_cursor_pos_raw(self) -> tuple[float, float]:
        return (
            inputs.cursor[0] - self._panel.x - style.format.footer_size,
            inputs.cursor[1] - self._panel.y - style.format.footer_size,
        )
    
    def get_cursor_pos(self) -> tuple[float, float]:
        pos: Vec3 = self._camera.unproject(self.get_cursor_pos_raw())
        return pos.x, pos.y