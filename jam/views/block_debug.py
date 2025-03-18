from arcade import View, Vec2

from jam.station.node import node, render, blocks


class BlockDebugView(View):

    def __init__(self, back: View | None = None):
        View.__init__(self)
        self._back: View | None = back

        self._graph = node.Graph()
        self._renderer = render.GraphRenderer(self.window.rect, self._graph)

        self.a = blocks.IntVariableBlock("a")
        self.b = blocks.IntVariableBlock("b")
        self.c = blocks.IntVariableBlock("c")

        self._graph.add_block(self.a)
        self._graph.add_block(self.b)
        self._graph.add_block(self.c)

        self.a.set_config("x", 12)
        self.b.set_config("x", 16)
        self.c.set_config("x", 19)

        self.mul_1 = blocks.MultiplyBlock()
        self.mul_2 = blocks.MultiplyBlock()

        self._graph.add_block(self.mul_1)
        self._graph.add_block(self.mul_2)

        self.connection_1 = node.Connection(self.a, "x", self.mul_1, "a")
        self.connection_2 = node.Connection(self.b, "x", self.mul_1, "b")
        self.connection_3 = node.Connection(self.mul_1, "x", self.mul_2, "a")
        self.connection_4 = node.Connection(self.c, "x", self.mul_2, "b")

        self._renderer.add_block(self.a, Vec2(100, 300))
        self._renderer.add_block(self.b, Vec2(100, 200))
        self._renderer.add_block(self.c, Vec2(100, 100))

        self._renderer.add_block(self.mul_1, Vec2(150, 250))
        self._renderer.add_block(self.mul_2, Vec2(300, 150))

        self._graph.add_connection(self.connection_1)
        self._graph.add_connection(self.connection_2)
        self._graph.add_connection(self.connection_3)
        self._graph.add_connection(self.connection_4)

        self._renderer.add_connection(self.connection_1)
        self._renderer.add_connection(self.connection_2)
        self._renderer.add_connection(self.connection_3)
        self._renderer.add_connection(self.connection_4)

        self._graph.compute(self.mul_2)

        self._selected_block: render.BlockRenderer = None
        self._offset: Vec2 = Vec2()

    def on_mouse_drag(self, x, y, dx, dy, button, modifier):
        if self._selected_block is None:
            return

        self._renderer.move_block(
            self._selected_block._block, Vec2(x, y) + self._offset
        )

    def on_mouse_press(self, x, y, button, modifier):
        if self._selected_block is not None:
            return

        for block in self._renderer._blocks.values():
            l, b = block.bottom_left
            r, t = l + block.width, b + block.height

            if l <= x <= r and b <= y <= t:
                self._selected_block = block
                self._offset = Vec2(l - x, b - y)
                return

    def on_mouse_release(self, x, y, button, modifier):
        self._selected_block = None

    def on_draw(self):
        self._renderer.draw()
