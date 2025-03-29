from importlib.resources import path
from enum import Enum, auto

from arcade import View, Vec2, draw_line, key, MOUSE_BUTTON_RIGHT
from arcade.future import background

from jam.node import node, render, blocks
from jam.gui import core

from resources import style

import resources.ase as ase
from pathlib import Path


class EditorMode:
    NONE = 0
    DRAG_BLOCK = auto()
    DRAG_CONNECTION = auto()
    CHANGE_CONFIG = auto()
    ADD_BLOCK = auto()
    ADD_NODE = auto()


ADD_BLOCK_BUTTON = key.N


class BlockDebugView(View):

    def __init__(self, back: View | None = None):
        View.__init__(self)
        with path(ase) as pth:
            self.background = background.background_from_file(
                pth / "grid_1.png", size=self.size
            )
        self._back: View | None = back

        self._graph = node.Graph()
        self._renderer = render.GraphRenderer(self.window.rect, self._graph)
        self._gui = core.Gui(self.window.rect)

        self.inputs = blocks.DynamicVariable("Input")
        self.outputs = blocks.DynamicVariable("Output")

        self.inputs.add_variable("a", node.number, 12)
        self.inputs.add_variable("b", node.number, 16)
        self.inputs.add_variable("c", node.number, 19)

        self.outputs.add_variable("result", node.number, output=False)

        self._graph.add_block(self.inputs)
        self._graph.add_block(self.outputs)

        self._renderer.add_block(self.inputs, Vec2(100, self.height * 0.5))
        self._or = self._renderer.add_block(
            self.outputs, Vec2(self.width - 200, self.height * 0.5)
        )

        # Editor State
        self._mode = EditorMode.NONE
        self._mouse_pos = None
        self._popup: core.Popup | None = None

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

        # Addmove

    def create_block_popup(self, pos):
        def create_block(block_type: type):
            block = block_type()

            self._graph.add_block(block)
            self._renderer.add_block(block, Vec2(*self._mouse_pos))

        top = pos[1] > self.center_y
        right = pos[0] > self.center_x

        dx = style.editor.padding if right else -style.editor.padding
        dy = style.editor.padding if top else -style.editor.padding

        return core.SelectionPopup(
            tuple(
                core.PopupAction(typ.__name__, create_block, typ)
                for typ in node.Block.__subclasses__()
            ),
            (pos[0] + dx, pos[1] + dy),
            top,
            right,
        )

    def on_key_press(self, symbol, modifier):
        match self._mode:
            case EditorMode.NONE:
                if symbol == ADD_BLOCK_BUTTON:
                    self._selected_block = None
                    self._offset = Vec2()
                    self._mode = EditorMode.ADD_NODE

    def on_mouse_motion(self, x, y, dx, dy):
        self._mouse_pos = (x, y)
        match self._mode:
            case EditorMode.NONE:
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

                        self._popup = core.InfoPopup(str(value), (x, y))
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

    def on_mouse_drag(self, x, y, dx, dy, button, modifier):
        self._mouse_pos = (x, y)
        match self._mode:
            case EditorMode.NONE:
                return
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
            case EditorMode.ADD_BLOCK:
                self.on_mouse_motion(x, y, dx, dy)

    def on_mouse_press(self, x, y, button, modifier):
        self._mouse_pos = (x, y)

        match self._mode:
            case EditorMode.NONE:
                if self._popup is not None:
                    self._gui.remove_element(self._popup)
                    self._popup = None

                # Find if we are hovering over a block
                clicked_block = None
                for block in self._renderer._blocks.values():
                    if block.contains_point((x, y)):
                        clicked_block = block
                        break

                # If we are then check to see if:
                # a) we clicking a panel
                # b) we are dragging a node
                # otherwise drag the block
                if clicked_block is not None:
                    if button == MOUSE_BUTTON_RIGHT and not (
                        clicked_block._block == self.inputs
                        or clicked_block._block == self.outputs
                    ):
                        self._renderer.remove_block(clicked_block._block)
                        self._graph.remove_block(clicked_block._block)
                        return

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

                # If we aren't over a block or near a node create a popup
                self._popup = self.create_block_popup((x, y))
                self._gui.add_element(self._popup)

                self._mode = EditorMode.ADD_BLOCK

            case EditorMode.DRAG_BLOCK:
                return
            case EditorMode.DRAG_CONNECTION:
                return
            case EditorMode.ADD_BLOCK:
                if self._popup is None:
                    self._mode = EditorMode.NONE
                    return self.on_mouse_press(x, y, button, modifier)

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
                return

    def on_mouse_release(self, x, y, button, modifier):
        self._mouse_pos = (x, y)
        match self._mode:
            case EditorMode.NONE:
                return
            case EditorMode.DRAG_BLOCK:
                self._selected_block = None
                self._mode = EditorMode.NONE
            case EditorMode.DRAG_CONNECTION:
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

    def on_draw(self):
        self.clear(color=style.editor.colors.background)
        self.background.draw()
        self._renderer.draw()

        match self._mode:
            case EditorMode.DRAG_CONNECTION:
                draw_line(
                    self._start_pos[0],
                    self._start_pos[1],
                    self._mouse_pos[0],
                    self._mouse_pos[1],
                    style.editor.colors.connection,
                    style.editor.line_thickness,
                )

        if self._popup is not None and self._mode == EditorMode.NONE:
            if not self._popup.contains_point(self._mouse_pos):
                self._gui.remove_element(self._popup)
                self._popup = None

        self._gui.draw()
