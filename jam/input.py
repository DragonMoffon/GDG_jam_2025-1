from __future__ import annotations

from sys import platform
from enum import StrEnum, IntEnum
from typing import Callable
from math import pow

from pyglet.input import Controller
from arcade import get_window, Window, Vec2


class ControllerButtons(StrEnum):
    TOP_FACE = "y"
    RIGHT_FACE = "b"
    LEFT_FACE = "x"
    BOTTOM_FACE = "a"
    LEFT_SHOULDER = "leftshoulder"
    RIGHT_SHOULDER = "rightshoulder"
    LEFT_TRIGGER = "lefttrigger"
    RIGHT_TRIGGER = "righttrigger"
    START = "start"
    BACK = "back"
    GUIDE = "guide"
    LEFT_STICK = "leftstick"
    RIGHT_STICK = "rightstick"

    LEFT_LEFT = "leftleft"
    LEFT_RIGHT = "leftright"
    LEFT_UP = "leftup"
    LEFT_DOWN = "leftdown"

    RIGHT_LEFT = "rightleft"
    RIGHT_RIGHT = "rightright"
    RIGHT_UP = "rightup"
    RIGHT_DOWN = "rightdown"

    DPAD_LEFT = "dpleft"
    DPAD_RIGHT = "dpright"
    DPAD_UP = "dpup"
    DPAD_DOWN = "dpdown"


class ControllerAxes(StrEnum):
    LEFT_STICK = 'leftstick'
    RIGHT_STICK = 'rightstick'
    LEFT_TRIGGER = 'lefttrigger'
    RIGHT_TRIGGER = 'righttrigger'
    DPAD = 'dpad'

    LEFT_X = 'leftx'
    LEFT_Y = 'lefty'
    RIGHT_X = 'rightx'
    RIGHT_Y = 'righty'


class KeyModifiers(IntEnum):
    # Key modifiers
    # Done in powers of two, so you can do a bit-wise 'and' to detect
    # multiple modifiers.
    MOD_SHIFT = 1
    MOD_CTRL = 2
    MOD_ALT = 4
    MOD_CAPSLOCK = 8
    MOD_NUMLOCK = 16
    MOD_WINDOWS = 32
    MOD_COMMAND = 64
    MOD_OPTION = 128
    MOD_SCROLLLOCK = 256
    
    # Platform-specific base hotkey modifier
    MOD_ACCEL = MOD_COMMAND if platform == "darwin" else MOD_CTRL


class MouseButtons(IntEnum):
    # LEFT and MOUSE_1 are aliases of each other
    LEFT = 1
    MOUSE_1 = 1

    # MIDDLE and MOUSE_3 are aliases of each other
    MIDDLE = 2
    MOUSE_3 = 2

    # RIGHT and MOUSE_2 are aliases of each other
    RIGHT = 4
    MOUSE_2 = 4

    MOUSE_4 = 8
    MOUSE_5 = 16


class Keys(IntEnum):
    # Keys
    BACKSPACE = 65288
    TAB = 65289
    LINEFEED = 65290
    CLEAR = 65291
    RETURN = 65293
    ENTER = 65293
    PAUSE = 65299
    SCROLLLOCK = 65300
    SYSREQ = 65301
    ESCAPE = 65307
    HOME = 65360
    LEFT = 65361
    UP = 65362
    RIGHT = 65363
    DOWN = 65364
    PAGEUP = 65365
    PAGEDOWN = 65366
    END = 65367
    BEGIN = 65368
    DELETE = 65535
    SELECT = 65376
    PRINT = 65377
    EXECUTE = 65378
    INSERT = 65379
    UNDO = 65381
    REDO = 65382
    MENU = 65383
    FIND = 65384
    CANCEL = 65385
    HELP = 65386
    BREAK = 65387
    MODESWITCH = 65406
    SCRIPTSWITCH = 65406
    MOTION_UP = 65362
    MOTION_RIGHT = 65363
    MOTION_DOWN = 65364
    MOTION_LEFT = 65361
    MOTION_NEXT_WORD = 1
    MOTION_PREVIOUS_WORD = 2
    MOTION_BEGINNING_OF_LINE = 3
    MOTION_END_OF_LINE = 4
    MOTION_NEXT_PAGE = 65366
    MOTION_PREVIOUS_PAGE = 65365
    MOTION_BEGINNING_OF_FILE = 5
    MOTION_END_OF_FILE = 6
    MOTION_BACKSPACE = 65288
    MOTION_DELETE = 65535
    NUMLOCK = 65407
    NUM_SPACE = 65408
    NUM_TAB = 65417
    NUM_ENTER = 65421
    NUM_F1 = 65425
    NUM_F2 = 65426
    NUM_F3 = 65427
    NUM_F4 = 65428
    NUM_HOME = 65429
    NUM_LEFT = 65430
    NUM_UP = 65431
    NUM_RIGHT = 65432
    NUM_DOWN = 65433
    NUM_PRIOR = 65434
    NUM_PAGE_UP = 65434
    NUM_NEXT = 65435
    NUM_PAGE_DOWN = 65435
    NUM_END = 65436
    NUM_BEGIN = 65437
    NUM_INSERT = 65438
    NUM_DELETE = 65439
    NUM_EQUAL = 65469
    NUM_MULTIPLY = 65450
    NUM_ADD = 65451
    NUM_SEPARATOR = 65452
    NUM_SUBTRACT = 65453
    NUM_DECIMAL = 65454
    NUM_DIVIDE = 65455

    # Numbers on the numberpad
    NUM_0 = 65456
    NUM_1 = 65457
    NUM_2 = 65458
    NUM_3 = 65459
    NUM_4 = 65460
    NUM_5 = 65461
    NUM_6 = 65462
    NUM_7 = 65463
    NUM_8 = 65464
    NUM_9 = 65465

    F1 = 65470
    F2 = 65471
    F3 = 65472
    F4 = 65473
    F5 = 65474
    F6 = 65475
    F7 = 65476
    F8 = 65477
    F9 = 65478
    F10 = 65479
    F11 = 65480
    F12 = 65481
    F13 = 65482
    F14 = 65483
    F15 = 65484
    F16 = 65485
    F17 = 65486
    F18 = 65487
    F19 = 65488
    F20 = 65489
    F21 = 65490
    F22 = 65491
    F23 = 65492
    F24 = 65493
    LSHIFT = 65505
    RSHIFT = 65506
    LCTRL = 65507
    RCTRL = 65508
    CAPSLOCK = 65509
    LMETA = 65511
    RMETA = 65512
    LALT = 65513
    RALT = 65514
    LWINDOWS = 65515
    RWINDOWS = 65516
    LCOMMAND = 65517
    RCOMMAND = 65518
    LOPTION = 65488
    ROPTION = 65489
    SPACE = 32
    EXCLAMATION = 33
    DOUBLEQUOTE = 34
    HASH = 35
    POUND = 35
    DOLLAR = 36
    PERCENT = 37
    AMPERSAND = 38
    APOSTROPHE = 39
    PARENLEFT = 40
    PARENRIGHT = 41
    ASTERISK = 42
    PLUS = 43
    COMMA = 44
    MINUS = 45
    PERIOD = 46
    SLASH = 47

    # Numbers on the main keyboard
    KEY_0 = 48
    KEY_1 = 49
    KEY_2 = 50
    KEY_3 = 51
    KEY_4 = 52
    KEY_5 = 53
    KEY_6 = 54
    KEY_7 = 55
    KEY_8 = 56
    KEY_9 = 57
    COLON = 58
    SEMICOLON = 59
    LESS = 60
    EQUAL = 61
    GREATER = 62
    QUESTION = 63
    AT = 64
    BRACKETLEFT = 91
    BACKSLASH = 92
    BRACKETRIGHT = 93
    ASCIICIRCUM = 94
    UNDERSCORE = 95
    GRAVE = 96
    QUOTELEFT = 96
    A = 97
    B = 98
    C = 99
    D = 100
    E = 101
    F = 102
    G = 103
    H = 104
    I = 105
    J = 106
    K = 107
    L = 108
    M = 109
    N = 110
    O = 111
    P = 112
    Q = 113
    R = 114
    S = 115
    T = 116
    U = 117
    V = 118
    W = 119
    X = 120
    Y = 121
    Z = 122
    BRACELEFT = 123
    BAR = 124
    BRACERIGHT = 125
    ASCIITILDE = 126


Button = Keys | MouseButtons | ControllerButtons
Axis = ControllerAxes | str

OnInputCallable = Callable[[Button, int, bool], None]
OnAxisChangeCallable = Callable[[Axis, float, float], None]
OnCursorMotionCallable = Callable[[float, float, float, float], None]
OnCursorScrollCallable = Callable[[float, float, float, float], None]

class MultiInput:

    def __init__(self, base: Button, alt: Button, ) -> None:
        self.base: Button = base
        self.alt: Button = alt

    def __get__(self, obj: InputManager | None, objtype: type | None = None):
        if obj is None:
            return self

        if obj.using_alt:
            return self.alt
        return self.base

    def __set__(self, obj: InputManager, value: Keys | MouseButtons | ControllerButtons):
        if obj.using_alt:
            self.alt = value
        else:
            self.base = value

 
class MultiMods:

    def __init__(self, base: int = 0xFF, alt: int = 0xFF) -> None:
        self.base = base
        self.alt = alt

    def __get__(self, obj: InputManager | None, objtype: type | None = None):
        if obj is None:
            return self

        if obj.using_alt:
            return self.alt
        return self.base

    def __set__(self, obj: InputManager, value: int):
        if obj.using_alt:
            self.alt = value
        else:
            self.base = value

    def __and__(self, other: int) -> int:
        return other & self.base
    
    def __rand__(self, other: int) -> int:
        return self.__and__(other)


class InputManager:

    def __init__(self) -> None:
        # -- window --
        self._window: Window = None # type: ignore

        # -- Controller Values --
        self._current_controller: Controller | None = None
        self._using_controller: bool = False

        self._left_stick_positions: tuple[float, float] = (0.0, 0.0)
        self._right_stick_positions: tuple[float, float] = (0.0, 0.0)
        self._dpad_positions: tuple[float, float] = (0.0, 0.0)

        self._cursor_axis = ControllerAxes.LEFT_STICK

        self._trigger_values: tuple[float, float] = (0.0, 0.0)
        self._trigger_levels: tuple[float, float] = (0.95, 0.95)

        # -- Keyboard Values --
        self._modifiers: int = 0

        # -- Cursor Values --
        self._cursor_position: tuple[float, float] = (0.0, 0.0)
        self._cursor_velocity: tuple[float, float] = (0.0, 0.0)

        self._cursor_motion: bool = False

        self._cursor_speed: float = 240.0
        self._cursor_deadzone: tuple[float, float] = (0.075, 0.075)

    def __update__(self, delta_time: float):
        if self._current_controller is None or not self._using_controller:
            return
        
        match self._cursor_axis:
            case ControllerAxes.RIGHT_STICK:
                vec = self._right_stick_positions
            case ControllerAxes.LEFT_STICK:
                vec = self._left_stick_positions
            case ControllerAxes.DPAD:
                vec = self._dpad_positions
            case _:
                vec = self._right_stick_positions
        
        vec = 0 if abs(vec[0]) < self._cursor_deadzone[0] else vec[0], 0 if abs(vec[1]) < self._cursor_deadzone[1] else vec[1]
        vel = (vec[0]**2 + vec[1]**2)**0.5
        if vel == 0.0:
            return

        vec = vec[0] / vel, vec[1] / vel # normalise the vec to get the direction
        vel = min(1.0, vel) # Clamp vel to 1.0 since not all joysticks are perfectly circular
        speed = pow(self._cursor_speed, vel) * delta_time # Get the speed and account for dt. (cursor_speed * cursor_speed^(x-1) = cursor_speed^x)

        self._cursor_velocity = speed * vec[0], speed * vec[1]
        self._cursor_position = self._cursor_position[0] + self._cursor_velocity[0], self._cursor_position[1] + self._cursor_velocity[1]

        self._cursor_motion = True
        self._window.set_mouse_position(int(self._cursor_position[0]), int(self._cursor_position[1]))
        self._window.dispatch_event('on_cursor_motion', self._cursor_position[0], self._cursor_position[1], self._cursor_velocity[0], self._cursor_velocity[1])


    def setup_input_reponses(self):
        self._window = get_window()

        self._window.push_handlers(
            on_key_press=self.on_key_press,
            on_key_release=self.on_key_release,
            on_mouse_press=self.on_mouse_press,
            on_mouse_release=self.on_mouse_release,
            on_mouse_motion=self.on_mouse_motion,
            on_mouse_drag=self.on_mouse_drag,
            on_mouse_scroll=self.on_mouse_scroll
        )

        self._window.register_event_type('on_input')
        self._window.register_event_type('on_axis_change')
        self._window.register_event_type('on_cursor_motion')
        self._window.register_event_type('on_cursor_scroll')
        
    def pick_controller(self, controller: Controller | None = None):
        if self._current_controller == controller:
            return
        
        if self._current_controller is not None:
            self._current_controller.remove_handlers(
                on_button_press=self.on_controller_press,
                on_button_release=self.on_controller_release,
                on_stick_motion=self.on_stick_motion,
                on_dpad_motion=self.on_dpad_motion,
                on_trigger_motion=self.on_trigger_motion
            )
            self._current_controller.close()

        self._left_stick_positions: tuple[float, float] = (0.0, 0.0)
        self._right_stick_positions: tuple[float, float] = (0.0, 0.0)
        self._dpad_positions: tuple[float, float] = (0.0, 0.0)
        self._trigger_values: tuple[float, float] = (0.0, 0.0)
        
        if controller is None:
            return

        self._current_controller = controller

        controller.open()
        controller.push_handlers(
            on_button_press=self.on_controller_press,
            on_button_release=self.on_controller_release,
            on_stick_motion=self.on_stick_motion,
            on_dpad_motion=self.on_dpad_motion,
            on_trigger_motion=self.on_trigger_motion
        )

    # -- TRANSLATING INPUTS --

    def on_key_press(self, symbol: int, modifiers: int):
        if symbol not in Keys:
            return

        key = Keys(symbol)
        self._using_controller = False
        self._modifiers = modifiers
        self._window.dispatch_event('on_input', key, modifiers, True)

    def on_key_release(self, symbol: int, modifiers: int):
        if symbol not in Keys:
            return

        key = Keys(symbol)
        self._using_controller = False
        self._modifiers = modifiers
        self._window.dispatch_event('on_input', key, modifiers, False)

    def on_mouse_press(self, x: int, y: int, button: int | MouseButtons, modifiers: int):
        button = MouseButtons(button)
        self._using_controller = False
        self._cursor_position = (float(x), float(y))
        self._cursor_velocity = (0.0, 0.0)
        
        self._modifiers = modifiers

        self._window.dispatch_event('on_input', button, self._modifiers, True)

    def on_mouse_release(self, x: int, y: int, button: int | MouseButtons, modifiers: int):
        button = MouseButtons(button)
        self._using_controller = False
        self._cursor_position = (float(x), float(y))
        self._cursor_velocity = (0.0, 0.0)
        
        self._modifiers = modifiers

        self._window.dispatch_event('on_input', button, self._modifiers, False)

    def on_mouse_motion(self, x: int, y: int, dx: int, dy: int):
        if self._cursor_motion:
            self._cursor_motion = False
            return
        self._using_controller = False
        self._cursor_position = (float(x), float(y))
        self._cursor_velocity = (float(dx), float(dy))

        self._window.dispatch_event('on_cursor_motion', float(x), float(y), float(dx), float(dy))

    def on_mouse_drag(self, x: int, y: int, dx: int, dy: int, _buttons: int, modifiers: int):
        self._using_controller = False
        self._cursor_position = (float(x), float(y))
        self._cursor_velocity = (float(dx), float(dy))

        self._modifiers = modifiers

        self._window.dispatch_event('on_cursor_motion', float(x), float(y), float(dx), float(dy))

    def on_mouse_scroll(self, x: int, y: int, scroll_x: int, scroll_y: int):
        self._using_controller = False
        self._cursor_position = (float(x), float(y))
        self._cursor_velocity = (0.0, 0.0)

        self._window.dispatch_event('on_cursor_scroll', float(x), float(y), float(scroll_x), float(scroll_y))

    def on_controller_press(self, _controller: Controller, button: str):
        if button not in ControllerButtons:
            return

        button = ControllerButtons(button)
        self._using_controller = True
        self._window.dispatch_event('on_input', button, self._modifiers, True)

    def on_controller_release(self, _controller: Controller, button: str):
        if button not in ControllerButtons:
            return

        button = ControllerButtons(button)
        self._using_controller = True
        self._window.dispatch_event('on_input', button, self._modifiers, False)

    def on_stick_motion(self, _controller: Controller, axis: str, value: Vec2):
        self._using_controller = True

        if axis == ControllerAxes.LEFT_STICK:
            if value[0] >= -2 * self._cursor_deadzone[0] and self._left_stick_positions[0] < -2 * self._cursor_deadzone[0]:
                self._window.dispatch_event('on_input', ControllerButtons.LEFT_LEFT, self._modifiers, False)
            elif value[0] <= 2 * self._cursor_deadzone[0] and self._left_stick_positions[0] > 2 * self._cursor_deadzone[0]:
                self._window.dispatch_event('on_input', ControllerButtons.LEFT_RIGHT, self._modifiers, False)

            if value[0] > 2 * self._cursor_deadzone[0] and self._left_stick_positions[0] <= 2 * self._cursor_deadzone[0]:
                self._window.dispatch_event('on_input', ControllerButtons.LEFT_RIGHT, self._modifiers, True)
            elif value[0] < -2 * self._cursor_deadzone[0] and self._left_stick_positions[0] >= -2 * self._cursor_deadzone[0]:
                self._window.dispatch_event('on_input', ControllerButtons.LEFT_LEFT, self._modifiers, True)
            
            if value[1] >= -2 * self._cursor_deadzone[1] and self._left_stick_positions[1] < -2 * self._cursor_deadzone[1]:
                self._window.dispatch_event('on_input', ControllerButtons.LEFT_DOWN, self._modifiers, False)
            elif value[1] <= 2 * self._cursor_deadzone[1] and self._left_stick_positions[1] > 2 * self._cursor_deadzone[1]:
                self._window.dispatch_event('on_input', ControllerButtons.LEFT_UP, self._modifiers, False)

            if value[1] > 2 * self._cursor_deadzone[1] and self._left_stick_positions[1] <= 2 * self._cursor_deadzone[1]:
                self._window.dispatch_event('on_input', ControllerButtons.LEFT_UP, self._modifiers, True)
            elif value[1] < -2 * self._cursor_deadzone[1] and self._left_stick_positions[1] >= -2 * self._cursor_deadzone[1]:
                self._window.dispatch_event('on_input', ControllerButtons.LEFT_DOWN, self._modifiers, True)

            self._left_stick_positions = value
        elif axis == ControllerAxes.RIGHT_STICK:
            if value[0] >= -2 * self._cursor_deadzone[0] and self._right_stick_positions[0] < -2 * self._cursor_deadzone[0]:
                self._window.dispatch_event('on_input', ControllerButtons.RIGHT_LEFT, self._modifiers, False)
            elif value[0] <= 2 * self._cursor_deadzone[0] and self._right_stick_positions[0] > 2 * self._cursor_deadzone[0]:
                self._window.dispatch_event('on_input', ControllerButtons.RIGHT_RIGHT, self._modifiers, False)

            if value[0] > 2 * self._cursor_deadzone[0] and self._right_stick_positions[0] <= 2 * self._cursor_deadzone[0]:
                self._window.dispatch_event('on_input', ControllerButtons.RIGHT_RIGHT, self._modifiers, True)
            elif value[0] < -2 * self._cursor_deadzone[0] and self._right_stick_positions[0] >= -2 * self._cursor_deadzone[0]:
                self._window.dispatch_event('on_input', ControllerButtons.RIGHT_LEFT, self._modifiers, True)
            
            if value[1] >= -2 * self._cursor_deadzone[1] and self._right_stick_positions[1] < -2 * self._cursor_deadzone[1]:
                self._window.dispatch_event('on_input', ControllerButtons.RIGHT_DOWN, self._modifiers, False)
            elif value[1] <= 2 * self._cursor_deadzone[1] and self._right_stick_positions[1] > 2 * self._cursor_deadzone[1]:
                self._window.dispatch_event('on_input', ControllerButtons.RIGHT_UP, self._modifiers, False)

            if value[1] > 2 * self._cursor_deadzone[1] and self._right_stick_positions[1] <= 2 * self._cursor_deadzone[1]:
                self._window.dispatch_event('on_input', ControllerButtons.RIGHT_UP, self._modifiers, True)
            elif value[1] < -2 * self._cursor_deadzone[1] and self._right_stick_positions[1] >= -2 * self._cursor_deadzone[1]:
                self._window.dispatch_event('on_input', ControllerButtons.RIGHT_DOWN, self._modifiers, True)

            self._right_stick_positions = value

        self._window.dispatch_event('on_axis_change', ControllerAxes(axis), value.x, value.y)

    def on_dpad_motion(self, _controller: Controller, value: Vec2):
        self._using_controller = True

        # controller buttons
        if value[0] >= 0.0 and self._dpad_positions[0] < 0.0:
            self._window.dispatch_event('on_input', ControllerButtons.DPAD_LEFT, self._modifiers, False)
        elif value[0] <= 0.0 and self._dpad_positions[0] > 0.0:
            self._window.dispatch_event('on_input', ControllerButtons.DPAD_RIGHT, self._modifiers, False)
        
        if value[0] > 0.0 and self._dpad_positions[0] <= 0.0:
            self._window.dispatch_event('on_input', ControllerButtons.DPAD_RIGHT, self._modifiers, True)
        elif value[0] < 0.0 and self._dpad_positions[0] >= 0.0:
            self._window.dispatch_event('on_input', ControllerButtons.DPAD_LEFT, self._modifiers, True)

        if value[1] >= 0.0 and self._dpad_positions[1] < 0.0:
            self._window.dispatch_event('on_input', ControllerButtons.DPAD_DOWN, self._modifiers, False)
        elif value[1] <= 0.0 and self._dpad_positions[1] > 0.0:
            self._window.dispatch_event('on_input', ControllerButtons.DPAD_UP, self._modifiers, False)
        
        if value[1] > 0.0 and self._dpad_positions[1] <= 0.0:
            self._window.dispatch_event('on_input', ControllerButtons.DPAD_UP, self._modifiers, True)
        elif value[1] < 0.0 and self._dpad_positions[1] >= 0.0:
            self._window.dispatch_event('on_input', ControllerButtons.DPAD_DOWN, self._modifiers, True)

        self._dpad_positions = value
        self._window.dispatch_event('on_axis_change', ControllerAxes.DPAD, value.x, value.y)

    def on_trigger_motion(self, _controller: Controller, axis: str, value: float):
        if axis == ControllerAxes.LEFT_TRIGGER:
            if value < self._trigger_levels[0] and self._trigger_values[0] >= self._trigger_levels[0]:
                self._window.dispatch_event('on_input', ControllerButtons.LEFT_TRIGGER, self._modifiers, False)

            if value >= self._trigger_levels[0] and self._trigger_values[0] < self._trigger_levels[0]:
                self._window.dispatch_event('on_input', ControllerButtons.LEFT_TRIGGER, self._modifiers, True)

            self._trigger_values = value, self._trigger_values[1]
        elif axis == ControllerAxes.RIGHT_TRIGGER:
            if value < self._trigger_levels[1] and self._trigger_values[0] >= self._trigger_levels[1]:
                self._window.dispatch_event('on_input', ControllerButtons.RIGHT_TRIGGER, self._modifiers, False)
            
            if value >= self._trigger_levels[1] and self._trigger_values[1] < self._trigger_levels[1]:
                self._window.dispatch_event('on_input', ControllerButtons.RIGHT_TRIGGER, self._modifiers, True)

            self._trigger_values = self._trigger_values[0], value
        
        self._using_controller = True
        self._window.dispatch_event('on_axis_change', ControllerAxes(axis), value, value)

    # -- PROPERTIES --

    @property
    def using_controller(self):
        return self._using_controller
    
    @property
    def using_alt(self):
        return self._using_controller
    
    @property
    def cursor(self) -> tuple[float, float]:
        return self._cursor_position

    # -- INPUTS --

    TEST_INPUT = MultiInput(Keys.A, ControllerButtons.BOTTOM_FACE)

    PRIMARY_CLICK = MultiInput(MouseButtons.LEFT, ControllerButtons.BOTTOM_FACE)
    SECONDARY_CLICK = MultiInput(MouseButtons.RIGHT, ControllerButtons.LEFT_FACE)

    SAVE_INPUT = MultiInput(Keys.S, ControllerButtons.GUIDE)
    SAVE_MOD = MultiMods(KeyModifiers.MOD_CTRL)

inputs = InputManager()
