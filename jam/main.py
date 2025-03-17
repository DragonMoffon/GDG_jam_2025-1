from arcade import Window

from .views.block_debug import BlockDebugView


class JamWindow(Window): ...


def main():
    win = JamWindow()
    win.show_view(BlockDebugView())
    win.run()
