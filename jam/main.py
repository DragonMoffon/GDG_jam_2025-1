from .application import Window
from .views.game import GameView

def main():
    win = Window()
    win.show_view(GameView())
    win.run()
