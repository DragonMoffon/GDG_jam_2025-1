from arcade import View, Vec2

from jam.station.node import node, render, blocks


class BlockDebugView(View):

    def __init__(self, back: View | None = None):
        View.__init__(self)
        self._back: View | None = back

        self._graph = node.Graph()
        self._renderer = render.GraphRenderer(self.window.rect, self._graph)

        self._renderer.add_block(blocks.MultiplyBlock(), Vec2(10, 40))
        self._renderer.add_block(blocks.TestBlock(), Vec2(10, 150))
        self._renderer.add_block(blocks.TestNoInputBlock(), Vec2(300, 40))
        self._renderer.add_block(blocks.TestNoOutputBlock(), Vec2(300, 150))

    def on_draw(self):
        self._renderer.draw()
