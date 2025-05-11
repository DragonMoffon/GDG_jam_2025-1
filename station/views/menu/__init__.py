from arcade import draw_rect_filled
from pyglet.sprite import Sprite

from resources import Style

from station.view import View
from station.graphics.background import ParallaxBackground
from station.gui.core import Gui, OVERLAY_HIGHLIGHT
from station.gui.util import PopupAction, SelectionPopup
from station.context import context
from station.views.game import GameView
from station.views.credits import has_credits, CreditsView
from station.input import inputs, Button
from station.graphics.backing import Backing


class MainMenuView(View):

    def __init__(self):
        View.__init__(self)
        self._background = ParallaxBackground(Style.Menu.Background)
        self._logo = Sprite(Style.Textures.logo_big)

        self._gui = Gui(self.window.default_camera)

        if has_credits():
            show_credits = (
                PopupAction("Credits", self.window.show_view, CreditsView(self)),
            )
        else:
            show_credits = ()

        save_names = context.get_save_names()[::-1]
        if len(save_names) == 1:
            launch = (
                PopupAction("New Game", self.new_save),
                PopupAction("Continue", self.continue_save),
            )
        elif save_names:
            saves = (
                PopupAction(f"Continue: {name}", self.pick_save, name)
                for name in save_names
            )
            launch = (
                PopupAction("New Game", self.new_save),
                *saves,
                PopupAction("Continue", self.continue_save),
            )
        else:
            launch = (
                PopupAction(
                    "Begin",
                    self.new_save,
                ),
            )

        self._popup = SelectionPopup(
            (*show_credits, *launch), (self.center_x, self.center_y)
        )
        self._gui.add_element(self._popup)
        self._fade_out: bool = False
        self._speed: float = Style.Menu.new_fade
        self._tranistion: float = Style.Menu.new_transition
        self._flash: float = Style.Menu.new_logo
        self._timer: float = 0.0

        self._debug_crash: bool = False

    def new_save(self) -> None:
        self._fade_out = True
        self._timer = self.window.time
        context.new_save()
        Style.Audio.crash.play("intro")

    def continue_save(self) -> None:
        self._fade_out = True
        self._timer = self.window.time
        self._speed = Style.Menu.continue_fade
        self._tranistion = Style.Menu.continue_transition
        self._flash = Style.Menu.continue_logo
        context.choose_first_save()
        Style.Audio.boot.play("intro")

    def pick_save(self, name: str) -> None:
        self._fade_out = True
        self._timer = self.window.time
        self._speed = Style.Menu.continue_fade
        self._tranistion = Style.Menu.continue_transition
        self._flash = Style.Menu.continue_logo
        context.choose_save(name)
        Style.Audio.boot.play("intro")

    def on_cursor_motion(self, x: float, y: float, dx: float, dy: float) -> None:
        l = self._popup.get_hovered_item((x, y))
        if l is not None:
            self._popup.highlight_action(l)
        self._background.cursor_motion(x, y, dx, dy)

    def on_input(self, button: Button, modifiers: int, pressed: bool) -> None:
        if not pressed:
            return

        if self._fade_out:
            # TODO: fade out audio?
            self.window.show_view(GameView())
            return

        if button == inputs.PRIMARY_CLICK:
            l = self._popup.get_hovered_item(inputs.cursor)
            if l is not None:
                self._popup.actions[l]()
        elif button == inputs.DEGUG_INPUT:
            self._debug_crash = True

    def on_draw(self) -> None:
        self.clear()
        self._background.draw()
        self._gui.draw()
        if self._fade_out:
            dt = self.window.time - self._timer
            fraction = dt / self._speed  # fade for five seconds
            amount = max(0.0, min(1.0, (1 - (1 - fraction) ** 3)))
            draw_rect_filled(self.window.rect, (0, 0, 0, int(255 * amount)))

            if dt >= self._flash:
                self._logo.color = (255, 255, 255, int(255 * amount))
                self._logo.draw()

    def on_update(self, delta_time: float) -> None:
        if self._debug_crash:
            raise RuntimeError("Debug Input: Fatal Crash Before Save Chosen")
        self._background.update()
        if not self._fade_out:
            return

        dt = self.window.time - self._timer

        if dt > self._tranistion:
            self.window.show_view(GameView())
