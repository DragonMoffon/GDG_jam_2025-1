from __future__ import annotations
from station.input import Button, Axis

from station.controller import GraphController


class EditorCommand:
    def execute(self): ...
    def undo(self): ...


class EditorMode[E: Editor]:
    def __init__(self, editor: E) -> None:
        self._editor: E = editor

    def enter(self) -> None: ...
    def exit(self) -> None: ...
    def on_input(self, button: Button, modifiers: int, pressed: bool) -> None: ...
    def on_axis_change(self, axis: Axis, value_1: float, value_2: float) -> None: ...
    def on_cursor_motion(self, x: float, y: float, dx: float, dy: float) -> None: ...
    def on_cursor_scroll(
        self, x: float, y: float, scroll_x: float, scroll_y: float
    ) -> None: ...
    def on_update(self, delta_time: float) -> None: ...
    def on_draw(self) -> None: ...


class Editor:

    def __init__(
        self, intial_mode: EditorMode[Editor], controller: GraphController
    ) -> None:
        # -- Mode Attributes --
        self._mode_stack: list[EditorMode[Editor]] = [intial_mode]
        self._mode: EditorMode[Editor] = intial_mode
        intial_mode.enter()
        self._max_mode_stack: int = -1  # TODO

        self._command_stack: list[EditorCommand] = []
        self._command_offset: int = 0
        self._max_command_stack: int = -1  # TODO

        # -- Editor Attributes --
        self._controller: controller
        self._gui: controller.gui
        self._graph: controller.graph

    def push_mode(self, mode: EditorMode[Editor]) -> None:
        # Push a mode onto the stack so that
        # we can pop it off later returning
        # to our previous state (whatever it was).
        # self._mode.exit() -- Exiting would stop this actually being a stack.
        self._mode_stack.append(mode)
        self._mode = mode
        self._mode.enter()

    def pop_mode(self) -> None:
        # Pop the top mode of the stack.
        # It isn't possible to pop the root mode
        # from the editor. For inheritience reasons
        # this is a custom NoneMode defined for each
        # editor type. Returns the mode we left (incase we need it).
        if len(self._mode_stack) == 1:
            return
        self._mode.exit()
        self._mode_stack.pop(-1)
        self._mode = self._mode_stack[-1]
        # self._mode.enter() -- Entering is only needed if we exit when we push.

    def set_mode(self, mode: EditorMode[Editor]) -> None:
        # Replace the top mode of the stack,
        # This enters and exits only the top
        # of the stack and doesn't touch whatever
        # is below.
        if len(self._mode_stack) == 1:
            self.push_mode(mode)
        self._mode.exit()
        self._mode_stack.pop(-1)
        self._mode_stack.append(mode)
        self._mode = mode
        self._mode.enter()

    def clear_mode(self) -> None:
        # Whipe the entire stack. This means we exit every
        # Mode that is currently entered. This whole
        # system is a long context manager that works
        # over time.
        if len(self._mode_stack) == 1:
            return
        for mode in self._mode_stack[-1:0:-1]:
            mode.exit()
        self._mode_stack = self._mode_stack[0:1]
        self._mode = self._mode_stack[0]
        self._mode.enter()

    def execute(self, command: EditorCommand) -> None:
        # Run a command which manipulates the data
        # that would be stored to disk (theoretically).
        # We store another stack of commands so we can reverse them.
        # An example command is 'MoveBlock' which doesn't happen as
        # the block is being moved, only once it's been placed.
        if self._command_offset:
            self._command_stack = self._command_stack[: -self._command_offset]
            self._command_offset = 0
        self._command_stack.append(command)
        command.execute()

    def undo(self) -> None:
        # Undo the action of a command.
        # Probably the most obvious command here
        if self._command_offset == len(self._command_stack):
            return None  # Cannot undo any more than this as we have reached the start of the command stack
        self._command_offset += 1
        command = self._command_stack[-self._command_offset]
        command.undo()

    def redo(self) -> None:
        # Much like undo lets us reverse a reverse.
        # The command offset is the pointer that lets
        # us track where in history we are looking.
        # If you do a new action it resets the command offset.
        if self._command_offset == 0:
            return  # Cannot redo any more than this as we have reached the end of the command stack
        command = self._command_stack[-self._command_offset]
        command.execute()
        self._command_offset += 1

    # -- Mode Events --

    def on_input(self, button: Button, modifiers: int, pressed: bool) -> None:
        self._mode.on_input(button, modifiers, pressed)

    def on_axis_changed(self, axis: Axis, value_1: float, value_2: float) -> None:
        self._mode.on_axis_change(axis, value_1, value_2)

    def on_cursor_motion(self, x: float, y: float, dx: float, dy: float) -> None:
        self._mode.on_cursor_motion(x, y, dx, dy)

    def on_cursor_scroll(
        self, x: float, y: float, scroll_x: float, scroll_y: float
    ) -> None:
        self._mode.on_cursor_scroll(x, y, scroll_x, scroll_y)

    def on_update(self, delta_time: float) -> None:
        self._mode.on_update(delta_time)

    def on_draw(self) -> None:
        self._mode.on_draw()

    # -- Visibility Events --
    # As per request these are called when the editor is shown irrespective of
    # how that happens. Opening New Tab, Switching Tab, Opening Frame.

    def on_show(self) -> None:
        # on_show isn't given to the mode,
        # because the editor is supposed
        # to be in NoneMode when we
        # show/hide the editor
        pass

    def on_hide(self) -> None:
        # on_hide isn't given to the mode,
        # because the editor is supposed
        # to be in NoneMode when we
        # show/hide the editor
        pass
