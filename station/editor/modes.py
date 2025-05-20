from resources import style

from station.gui.core import Point
from station.gui.util import PopupAction, SelectionPopup
from station.gui.graph import BlockElement, ConnectionElement

from station.node.graph import Block, BlockType

from station.input import inputs, Button

from .base import Editor, EditorMode
from .commands import MoveElement


class DragBlockMode(EditorMode[Editor]):

    def __init__(self, editor: Editor, block: BlockElement):
        super().__init__(editor)

        self._selected_block: BlockElement = block
        self._offset: Point = (0.0, 0.0)

    def enter(self) -> None:
        self._selected_block.select()
        pos = self._selected_block.get_position()
        cursor = self.editor._cursor  # TODO: Once projectors are sorted fix.
        self._offset = cursor[0] - pos[0], cursor[1] - pos[1]

    def exit(self) -> None:
        style.audio.drop.play("ui")
        self._selected_block.deselect()
        self._selected_block.remove_highlighting()

        # You might instead create the move element at the start and pass
        # in the old position and update the new position now, but i'm
        # unsure.
        point = self._selected_block.get_position()
        self._editor.execute(MoveElement(self._selected_block, point))

    def on_cursor_motion(self, x: float, y: float, dx: float, dy: float) -> None:
        point = x - self._offset[0], y - self._offset[1]
        self._selected_block.update_position(point)

    def on_input(self, button: Button, modifiers: int, pressed: bool) -> None:
        if pressed:
            return  # We only care when primary is released.

        if button == inputs.PRIMARY_CLICK:
            self._editor.pop_mode()


class DragConnectionMode(EditorMode[Editor]):

    def __init__(self, editor: Editor, connection: ConnectionElement, link: int):
        super().__init__(editor)

        self._selected_connection: ConnectionElement = connection
        self._link: int = link

    def exit(self) -> None:
        pass

    def on_cursor_motion(self, x: float, y: float, dx: float, dy: float) -> None:
        # TODO: Once projectors are sorted fix.
        self._selected_connection.update_link(self._link, (x, y))

    def on_input(self, button: Button, modifiers: int, pressed: bool) -> None:
        if pressed:
            return  # We only care when primary is released.

        if button == inputs.PRIMARY_CLICK:
            self._editor.pop_mode()


class CreateBlockMode(EditorMode[Editor]):

    def __init__(
        self,
        editor: Editor,
    ):
        super().__init__(editor)
        self.selection_point: Point = (0.0, 0.0)
        self.add_block_popup: SelectionPopup | None = None

    def enter(self) -> None:
        if not self._editor.graph_controller.graph.available:
            self._editor.pop_mode()  # No adding a block for us

        # TODO: Once projectors are sorted fix.
        self.selection_point = self._editor.cursor
        layout_pos = self._editor.cursor
        top = layout_pos[1] > 0.5 * self._height
        right = layout_pos[0] > 0.5 * self._width

        dx = style.format.padding if right else -style.format.padding
        dy = style.format.padding if top else -style.format.padding
        self.add_block_popup = SelectionPopup(tuple(PopupAction("")))

    def _create_new_block(
        self, typ: BlockType, position: tuple[float, float]
    ) -> BlockElement:
        block = Block(typ)
        element = BlockElement(block)
        element.update_position(position)
        self._editor.graph_controller.add_block(element)
        return element


class CreateConnectionMode(EditorMode[Editor]): ...


class SaveGraphMode(EditorMode[Editor]): ...


class UpdateConfigMode(EditorMode[Editor]): ...
