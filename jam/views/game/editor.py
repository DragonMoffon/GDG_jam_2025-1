from pathlib import Path
from enum import Enum, auto
from importlib.resources import path

from pyglet.graphics import Batch
from pyglet.shapes import RoundedRectangle
from arcade import Rect, LBWH, Vec2, Vec3, Camera2D
from arcade.camera.default import ViewportProjector
from arcade.future import background

from resources import style
import resources.graphs as graph_path

from jam.node import graph
from jam.controller import (
    GraphController,
    read_graph,
    read_graph_from_level,
    write_graph,
    write_graph_from_level,
)
from jam.puzzle import Puzzle
from jam.gui import core, util, graph as gui
from jam.gui.frame import Frame
from jam.graphics.clip import ClippingMask
from jam.context import context
from jam.input import (
    inputs,
    Button,
    Axis,
    Keys,
    STR_KEY_SET,
    STR_ARRAY,
    STR_SET,
    LETTER_KEY_SET,
    TYPE_CHAR_SETS,
)


class EditorMode(Enum):
    NONE = 0
    DRAG_BLOCK = auto()
    DRAG_CONNECTION = auto()
    CHANGE_CONFIG = auto()
    ADD_BLOCK = auto()
    ADD_CONNECTION = auto()
    SAVE_GRAPH = auto()


class Editor:

    def __init__(
        self, region: Rect, puzzle: Puzzle | None = None, graph_src: Path | None = None
    ) -> None:
        self._region: Rect = region
        self._width = self._region.width
        self._height = self._region.height

        self.cursor_offset: tuple[float, float] = (0.0, 0.0)

        # Rendering
        self._base_camera = Camera2D(region)
        self._overlay_camera = Camera2D(region)
        self._background = background.background_from_file(  # type: ignore -- reportUnknownMemberType
            style.game.editor.background, size=(int(region.size.x), int(region.size.y))  # type: ignore -- reportArgumentType
        )
        self._gui = core.Gui(self._base_camera, self._overlay_camera)

        # Graph
        self._puzzle: Puzzle | None = puzzle
        self._graph_src: Path | None = graph_src
        if self._puzzle is not None:
            self._controller: GraphController = read_graph_from_level(
                self._puzzle, self._gui
            )
            self._graph: graph.Graph = self._controller.graph
        elif graph_src is not None:
            self._controller: GraphController = read_graph(graph_src, self._gui, True)
            self._graph: graph.Graph = self._controller.graph
        else:
            input_type = graph.BlockType(
                "Input", graph._variable, {}, {}, {}, exclusive=True
            )
            input_block = gui.BlockElement(graph.Block(input_type))
            input_block.update_position((50.0, 300.0))
            output_type = graph.BlockType(
                "Output", graph._variable, {}, {}, {}, exclusive=True
            )
            output_block = gui.BlockElement(graph.Block(output_type))
            output_block.update_position((750.0, 300.0))
            self._controller = GraphController(
                self._gui,
                "Sandbox",
                sandbox=True,
                input_block=input_block.uid,
                output_block=output_block.uid,
            )
            self._graph = self._controller.graph
            self._controller.add_block(input_block)
            self._controller.add_block(output_block)

        # Editor State
        self._mode = EditorMode.NONE
        self._pan_camera: bool = False
        self._hovered_block: gui.BlockElement | None = None
        self._results: gui.ResultsPanel | None = None
        self._test_runner: gui.TestRunner | None = None

        if self._puzzle is not None:
            self._test_runner = gui.TestRunner(self._puzzle.tests)
            self._test_runner.update_position((300.0, 50.0))
            self._gui.add_element(self._test_runner)

        # Drag Block
        self._selected_block: gui.BlockElement | None = None
        self._offset: Vec2 = Vec2()

        # Drag Noodle
        self._selected_noodle: gui.ConnectionElement | None = None
        self._link: int = 0

        # Create Connection
        self._incomplete_connection: gui.ConnectionElement | None = None

        # Add Block
        self._select_position: tuple[float, float] = (0.0, 0.0)
        self._block_popup: util.SelectionPopup | None = None

        # Edit Config Value
        self._config: str = ""
        self._prev_value: graph.OperationValue | None = None
        self._config_block: graph.Block | None = None
        self._config_panel: gui.TextPanel | None = None
        self._config_popup: util.TextInputPopup | None = None

        # Save Graph
        self._save_popup: util.TextInputPopup | None = None

    @property
    def name(self) -> str:
        return self._graph.name

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

        if self._selected_noodle is not None:
            self._selected_noodle = None
            self._link = 0

        if self._incomplete_connection is not None:
            self._gui.remove_element(self._incomplete_connection)
            self._incomplete_connection = None

        if self._block_popup is not None:
            self._gui.remove_element(self._block_popup)
            self._select_position = (0.0, 0.0)
            self._block_popup = None

        if self._config_panel is not None:
            if self._config_popup.text == "":
                config_type = self._config_block.type.config[self._config]
                value = config_type()
                self._config_block.config[self._config] = value

                self._config_panel.text = str(value.value)
                self._config_panel.offset = 0
            else:
                try:
                    config_type = self._config_block.type.config[self._config]
                    # Mega cludge to avoid .0 at the end of ints
                    if (
                        self._prev_value.type is float
                        and "." not in self._config_popup.text
                    ):
                        value = config_type(int(self._config_popup.text))
                    else:
                        value = config_type(
                            self._prev_value.type(self._config_popup.text)
                        )
                except ValueError:
                    self._config_panel.text = str(self._prev_value.value)
                    self._config_panel.offset = 0
                else:
                    self._config_panel.text = self._config_popup.text
                    self._config_panel.offset = 0
                    self._config_block.config[self._config] = value

            self._config = ""
            self._prev_value = None
            self._config_block = None
            self._config_panel = None
            self._gui.remove_element(self._config_popup)
            self._config_popup = None

        if self._save_popup is not None:
            self._gui.remove_element(self._save_popup)
            self._save_popup = None

        if self._results is not None:
            self._gui.remove_element(self._results)
            self._results = None

        if self._graph.output_uid is None:
            return

        output = self._controller.get_block(self._graph.output_uid)
        rslt = self._graph.compute(output.block)
        if not rslt.outputs:
            return

        self._results = gui.ResultsPanel(rslt)
        self._results.update_position(
            (
                output.left + output.width + style.format.corner_radius,
                output.bottom + style.format.footer_size,
            )
        )
        self._gui.add_element(self._results)

    def set_mode_drag_block(self, block: gui.BlockElement) -> None:
        self._mode = EditorMode.DRAG_BLOCK

        if self._hovered_block is not None:
            self._hovered_block.deselect()
            self._hovered_block = None

        cursor = self.get_base_cursor_pos()
        self._offset = Vec2(cursor[0] - block.left, cursor[1] - block.bottom)
        self._selected_block = block
        self._selected_block.select()

    def set_mode_drag_connection(
        self, noodle: gui.ConnectionElement, link: int
    ) -> None:
        self._mode = EditorMode.DRAG_CONNECTION
        self._selected_noodle = noodle
        self._link = link

    def set_mode_edit_config(
        self,
        block: gui.BlockElement | gui.TempValueElement,
        config: str,
    ) -> None:
        self._mode = EditorMode.CHANGE_CONFIG

        config_panel = block.get_config(config)
        config_type = block.block.config[config].type
        if config_type is bool:
            block.block.config[config] = block.block.config[config].invert()
            config_panel.active = block.block.config[config].value
            self.set_mode_none()
            return

        self._prev_value = block.block.config[config]
        self._config_block = block.block
        self._config_panel = config_panel

        x = config_panel.left + config_panel.width / 2.0
        y = config_panel.bottom + config_panel.height / 2.0

        charset, chararray = TYPE_CHAR_SETS[config_type]
        self._config_popup = util.TextInputPopup((x, y), charset, chararray)
        self._config_popup.text = str(self._prev_value.value)
        self._gui.add_element(self._config_popup)

        self._config = config

    def set_mode_add_block(self) -> None:
        if not self._graph.available:
            self.set_mode_none()
            return
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

    def set_mode_save_graph(self) -> None:
        self._mode = EditorMode.SAVE_GRAPH

        self._save_popup = util.TextInputPopup(
            self._overlay_camera.position, STR_SET, STR_ARRAY
        )
        self._save_popup.text = self._graph.name.replace(" ", "_")
        self._gui.add_element(self._save_popup)

    # -- INPUT METHODS --

    def none_on_input(self, button: Button, modifiers: int, pressed: bool) -> None:
        if not pressed:
            if button == inputs.PRIMARY_CLICK:
                self._pan_camera = False
            return
        cursor = self.get_base_cursor_pos()

        o_cursor = self.get_overlay_cursor_pos()
        if self._test_runner is not None and button == inputs.PRIMARY_CLICK:
            if self._test_runner.contains_point(o_cursor):
                if self._test_runner.over_nav_up(o_cursor):
                    self._test_runner.prev_test()
                elif self._test_runner.over_nav_down(o_cursor):
                    self._test_runner.next_test()
                elif self._test_runner.over_run_one(o_cursor):
                    test = self._test_runner.get_shown_test()
                    inp = self._controller.get_block(self._graph.input_uid)
                    inp.update_config(test.inputs)
                    out = self._controller.get_block(self._graph.output_uid)
                    rslt = self._graph.compute(out.block)
                    case = graph.TestCase(test.inputs, rslt.outputs)
                    test.complete = case == test
                    self._test_runner.check_test_output()
                elif self._test_runner.over_run_all(o_cursor):
                    tests = self._test_runner.get_tests()
                    inp = self._controller.get_block(self._graph.input_uid)
                    out = self._controller.get_block(self._graph.output_uid)
                    full_success = True
                    for test in tests:
                        inp.update_config(test.inputs)
                        rslt = self._graph.compute(out.block)
                        case = graph.TestCase(test.inputs, rslt.outputs)
                        test.complete = case == test
                        full_success = full_success and test.complete
                        if not full_success:
                            break

                    self._test_runner.check_test_output()

                    if full_success:
                        context.complete_puzzle(self._puzzle, self._controller)
                        return
                return

        # Find if we are hovering over a temp block
        clicked_temp = None
        for temp in self._controller.temporary:
            if temp.contains_point(cursor):
                clicked_temp = temp
                break

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
            if clicked_temp is not None:
                config = clicked_temp.get_hovered_config(cursor)
                if config is not None:
                    self.set_mode_edit_config(clicked_temp, config)
                    return

            if clicked_block is not None:
                config = clicked_block.get_hovered_config(cursor)
                if config is not None:
                    self.set_mode_edit_config(clicked_block, config)
                    return
                output, dist = clicked_block.get_nearest_output(cursor)
                if dist <= 16.0:
                    self.set_mode_add_connection(clicked_block, output)
                    return
                elif clicked_block.contains_point(cursor):
                    self.set_mode_drag_block(clicked_block)
                return

            if clicked_noodle is not None:
                link, dist = clicked_noodle.get_closest_link(cursor)
                if dist <= 16.0:
                    self.set_mode_drag_connection(clicked_noodle, link)
                    return
                line, dist = clicked_noodle.get_closest_line(cursor)
                clicked_noodle.insert_link(line, cursor)
                self.set_mode_drag_connection(clicked_noodle, line)
                return

            # If no block and no noodle clicked then pan the camera
            self._pan_camera = True
        elif button == inputs.SECONDARY_CLICK:
            if clicked_block is not None:
                if (
                    clicked_block.uid == self._graph.input_uid
                    or clicked_block.uid == self._graph.output_uid
                ):
                    return
                self._controller.remove_block(clicked_block)
                return

            if clicked_noodle is not None:
                link, dist = clicked_noodle.get_closest_link(cursor)
                if dist <= 16.0:
                    clicked_noodle.remove_link(link)
                    return
                self._controller.remove_connection(clicked_noodle)
                return

            # If no block and no noodle clicked then add new block
            self.set_mode_add_block()
        elif (
            button == inputs.SAVE_INPUT
            and modifiers & inputs.SAVE_MOD
            and self._graph.sandbox
        ):
            self.set_mode_save_graph()

    def drag_block_on_input(
        self, button: Button, modifiers: int, pressed: bool
    ) -> None:
        if button == inputs.PRIMARY_CLICK and not pressed:
            self.set_mode_none()
            return

    def drag_connection_on_input(
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
            style.audio.connection.play()
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
            style.audio.block.play()

            self.set_mode_none()

        elif button == inputs.SECONDARY_CLICK:
            self.set_mode_none()

    def edit_config_on_input(
        self, button: Button, modifiers: int, pressed: bool
    ) -> None:
        if not pressed:
            return

        if button == inputs.CANCEL:
            self._config_popup.text = str(self._prev_value.value)
            self.set_mode_none()
        elif button == inputs.CONFIRM:
            self.set_mode_none()
        elif button in STR_KEY_SET:
            if button in LETTER_KEY_SET and modifiers & inputs.SHIFT:
                button = button - 32
            self._config_popup.input_char(chr(button))
        elif button == inputs.BACKSPACE:
            self._config_popup.remove_char()
        elif button == inputs.NAV_UP:
            self._config_popup.incr_char()
        elif button == inputs.NAV_DOWN:
            self._config_popup.decr_char()
        elif button == inputs.NAV_RIGHT:
            self._config_popup.incr_cursor()
        elif button == inputs.NAV_LEFT:
            self._config_popup.decr_cursor()

    def save_graph_on_input(
        self, button: Button, modifiers: int, pressed: bool
    ) -> None:
        if not pressed:
            return

        if button in STR_KEY_SET:
            if modifiers & inputs.SHIFT == inputs.SHIFT:
                if button in LETTER_KEY_SET:
                    button = button - 32
                if button == Keys.MINUS:
                    button = Keys.UNDERSCORE
            self._save_popup.input_char(chr(button))
        elif button == inputs.SPACE:
            self._save_popup.input_char(chr(Keys.UNDERSCORE))
        elif button == inputs.CONFIRM:
            # TODO: fix no path
            self._graph._name = self._save_popup.text.replace("_", " ")
            if self._puzzle is not None:
                write_graph_from_level(self._controller, self._puzzle)
            else:
                with path(graph_path, f"{self._graph._name}.blk") as pth:
                    write_graph(self._controller, pth)
            self.set_mode_none()
        elif button == inputs.BACKSPACE:
            self._save_popup.remove_char()
        elif button == inputs.CANCEL:
            self.set_mode_none()
        elif button == inputs.NAV_UP:
            self._save_popup.incr_char()
        elif button == inputs.NAV_DOWN:
            self._save_popup.decr_char()
        elif button == inputs.NAV_RIGHT:
            self._save_popup.incr_cursor()
        elif button == inputs.NAV_LEFT:
            self._save_popup.decr_cursor()

    def on_input(self, button: Button, modifiers: int, pressed: bool) -> None:

        match self._mode:
            case EditorMode.NONE:
                self.none_on_input(button, modifiers, pressed)
            case EditorMode.DRAG_BLOCK:
                self.drag_block_on_input(button, modifiers, pressed)
            case EditorMode.DRAG_CONNECTION:
                self.drag_connection_on_input(button, modifiers, pressed)
            case EditorMode.ADD_CONNECTION:
                self.add_connection_on_input(button, modifiers, pressed)
            case EditorMode.ADD_BLOCK:
                self.add_block_on_input(button, modifiers, pressed)
            case EditorMode.CHANGE_CONFIG:
                self.edit_config_on_input(button, modifiers, pressed)
            case EditorMode.SAVE_GRAPH:
                self.save_graph_on_input(button, modifiers, pressed)
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

        o_cursor = self.get_overlay_cursor_pos()
        if self._test_runner is not None:
            self._test_runner.deselect_buttons()
            if self._test_runner.contains_point(o_cursor):
                if self._test_runner.over_nav_up(o_cursor):
                    self._test_runner.select_nav_up()
                elif self._test_runner.over_nav_down(o_cursor):
                    self._test_runner.select_nav_down()
                elif self._test_runner.over_run_one(o_cursor):
                    self._test_runner.select_run_one()
                elif self._test_runner.over_run_all(o_cursor):
                    self._test_runner.select_run_all()
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
        if (
            self._selected_block.uid == self._graph.output_uid
            and self._results is not None
        ):
            output = self._selected_block
            self._results.update_position(
                (
                    output.left + output.width + style.format.corner_radius,
                    output.bottom + style.format.footer_size,
                )
            )

    def drag_connection_on_cursor_motion(
        self, x: float, y: float, dx: float, dy: float
    ) -> None:
        self._selected_noodle.update_link(self._link, self.get_base_cursor_pos())

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
            case EditorMode.DRAG_CONNECTION:
                self.drag_connection_on_cursor_motion(x, y, dx, dy)
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
            if self._base_camera.zoom > 0.9:
                self._base_camera.zoom = 1.0

    # -- GAME EVENT METHODS --

    def draw(self) -> None:
        self._background.draw()
        self._gui.draw()

    def edit_config_on_update(self, delta_time: float) -> None:
        self._config_popup.update()

    def save_graph_on_update(self, delta_time: float) -> None:
        self._save_popup.update()

    def update(self, delta_time: float) -> None:
        match self._mode:
            case EditorMode.CHANGE_CONFIG:
                self.edit_config_on_update(delta_time)
            case EditorMode.SAVE_GRAPH:
                self.save_graph_on_update(delta_time)
            case _:
                pass

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
        clip_rect = self.clip_rect = LBWH(0.0, 0.0, clip_size[0], clip_size[1])
        self.cliping_mask = ClippingMask(
            (0.0, 0.0), clip_size, clip_size, group=core.OVERLAY_SPACING
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

        # self._editor = Editor(clip_rect)

        self._editor_tabs = util.PageRow()
        self._editors: dict[str, Editor] = {"Sandbox": Editor(clip_rect)}
        self._active_editor: Editor = self._editors["Sandbox"]
        tab = util.PageTab("Sandbox")
        self._editor_tabs.add_tab(tab)
        tab.select()

        Frame.__init__(
            self, "EDITOR", tag_offset, position, size, show_body, show_shadow
        )

    def select_editor(self, name: str):
        if name not in self._editors:
            return

        self._active_editor.set_mode_none()
        self._active_editor = self._editors[name]
        self._active_editor.cursor_offset = self.cliping_mask.position
        self._active_editor.set_mode_none()

    def open_editor(self, puzzle: Puzzle | None = None, graph_src: Path | None = None):
        if puzzle is None and graph_src is None and "Sandbox" in self._editors:
            self.select_editor("Sandbox")
            return
        if puzzle.name in self._editors:
            self.select_editor(puzzle.name)
            return
        editor = Editor(self.clip_rect, puzzle, graph_src)
        self._editors[editor.name] = editor
        tab = util.PageTab(editor.name)
        self._editor_tabs.add_tab(tab)
        self._editor_tabs.select_tab(tab, True)
        self.select_editor(editor.name)

    def close_editor(self, name: str):
        if name not in self._editors:
            return

        closing_editor = self._editors.pop(name)
        self._editor_tabs.rem_tab(self._editor_tabs.get_tab(name))
        if self._active_editor.name == name:
            self._active_editor = tuple(self._editors.values())[0]
            self._active_editor.set_mode_none()

        # TODO: decide what to do with closing editor

    def connect_renderer(self, batch: Batch | None) -> None:
        Frame.connect_renderer(self, batch)
        self.cliping_mask.batch = batch
        self._editor_tabs.connect_renderer(batch)

    def update_position(self, point: tuple[float, float]) -> None:
        Frame.update_position(self, point)
        self.cliping_mask.position = self._active_editor.cursor_offset = (
            point[0] + style.format.footer_size,
            point[1] + style.format.footer_size,
        )
        self._editor_tabs.update_position(
            (
                point[0] + style.format.footer_size,
                point[1] + style.format.footer_size + self.cliping_mask.size[1],
            )
        )

    @property
    def show_body(self) -> bool:
        return self._show_body

    @show_body.setter
    def show_body(self, show: bool) -> None:
        self._show_body = show
        self._panel.visible = show
        self.cliping_mask.visible = show

    def on_input(self, input: Button, modifiers: int, pressed: bool) -> None:
        if pressed:
            tab = self._editor_tabs.get_hovered_tab(inputs.cursor)
            if tab is not None:
                if input == inputs.PRIMARY_CLICK:
                    self._editor_tabs.select_tab(tab, True)
                    self.select_editor(tab.text)
                    return
                elif input == inputs.SECONDARY_CLICK:
                    if len(self._editors) == 1:
                        if "Sandbox" in self._editors:
                            return
                        self.open_editor()
                    self._editor_tabs.rem_tab(tab)
                    self.close_editor(tab.text)
                    return
        self._active_editor.on_input(input, modifiers, pressed)

    def on_axis_change(self, axis: Axis, value_1: float, value_2: float) -> None:
        self._active_editor.on_axis_change(axis, value_1, value_2)

    def on_cursor_motion(self, x: float, y: float, dx: float, dy: float) -> None:
        tab = self._editor_tabs.get_hovered_tab(inputs.cursor)
        if tab is not None:
            self._editor_tabs.select_tab(tab, True)
            self._editor_tabs.select_tab(
                self._editor_tabs.get_tab(self._active_editor.name)
            )
        else:
            self._editor_tabs.select_tab(
                self._editor_tabs.get_tab(self._active_editor.name), True
            )
        self._active_editor.on_cursor_motion(x, y, dx, dy)

    def on_cursor_scroll(
        self, x: float, y: float, scroll_x: float, scroll_y: float
    ) -> bool | None:
        self._active_editor.on_cursor_scroll(x, y, scroll_x, scroll_y)

    def on_draw(self) -> None:
        with self.cliping_mask.target:
            with self._clip_projector.activate():
                self._active_editor.draw()

    def on_update(self, delta_time: float):
        self._active_editor.update(delta_time)

    def on_hide(self) -> None:
        self._active_editor.set_mode_none()
