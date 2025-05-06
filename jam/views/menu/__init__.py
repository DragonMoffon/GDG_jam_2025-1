from arcade import draw_rect_filled
from pyglet.sprite import Sprite

from resources import style

from jam.view import View
from jam.graphics.background import ParallaxBackground
from jam.gui.core import Gui
from jam.gui.util import PopupAction, SelectionPopup
from jam.context import context
from jam.views.game import GameView
from jam.input import inputs, Button


class MainMenuView(View):
    SLOW_FADE = 4.0
    SLOW_TRANSITION = 6.0
    FAST_FADE = 1.0
    FAST_TRANSITION = 1.5

    def __init__(self):
        View.__init__(self)
        self._background = ParallaxBackground(style.menu.background)
        self._logo = Sprite(style.textures.logo_big)
        self._logo.color = (255, 255, 255, 0)

        self._gui = Gui(self.window.default_camera)

        if context.get_save_names():
            saves = (
                PopupAction(f"Continue: {name}", self.pick_save, name)
                for name in context.get_save_names()[::-1]
            )
            oppts = (PopupAction("New Game", self.new_save), *saves, PopupAction("Continue", self.continue_save))
        else:
            oppts = (PopupAction("Begin", self.new_save,),)
    
        self._popup = SelectionPopup(
            oppts, (self.center_x, self.center_y)
        )
        self._gui.add_element(self._popup)
        self._fade_out: bool = False
        self._speed: float = self.SLOW_FADE
        self._tranistion: float = self.SLOW_TRANSITION
        self._timer: float = 0.0

    def new_save(self) -> None:
        self._fade_out = True
        self._timer = self.window.time
        context.new_save()
        style.audio.crash.play()

    def continue_save(self) -> None:
        self._fade_out = True
        self._timer = self.window.time
        self._speed = self.FAST_FADE
        self._tranistion = self.FAST_TRANSITION
        context.choose_first_save()

    def pick_save(self, name: str) -> None:
        self._fade_out = True
        self._timer = self.window.time
        self._speed = self.FAST_FADE
        self._tranistion = self.FAST_TRANSITION
        context.choose_save(name)

    def on_cursor_motion(self, x, y, dx, dy) -> None:
        l = self._popup.get_hovered_item((x, y))
        if l is not None:
            self._popup.highlight_action(l)
        self._background.cursor_motion(x, y, dx, dy)

    def on_input(self, button: Button, modifiers: int, pressed: bool) -> None:
        if button == inputs.PRIMARY_CLICK and pressed:
            l = self._popup.get_hovered_item(inputs.cursor)
            if l is not None:
                self._popup.actions[l]()

    def on_draw(self) -> None:
        self.clear()
        self._background.draw()
        self._gui.draw()
        if self._fade_out:
            fraction = (
                self.window.time - self._timer
            ) / self._speed  # fade for five seconds
            amount = max(0.0, min(1.0, (1 - (1 - fraction) ** 3)))
            draw_rect_filled(self.window.rect, (0, 0, 0, int(255 * amount)))
            self._logo.color = (255, 255, 255, int(255 * amount))
            self._logo.draw()

    def on_update(self, delta_time: float) -> None:
        self._background.update()
        if not self._fade_out:
            return

        if self.window.time - self._timer > self._tranistion:
            self.window.show_view(GameView())
