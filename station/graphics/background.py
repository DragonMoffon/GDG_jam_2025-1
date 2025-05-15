from math import cos, sin, tau

from arcade.clock import GLOBAL_CLOCK
from pyglet.graphics import Batch, Group

from resources import style
from resources.style import FloatMotionMode, Background as StyleBackground

from station.graphics.backing import Backing


class ParallaxBackground:

    def __init__(
        self, background: StyleBackground | None = None, layer: Group | None = None
    ):
        if background is None:
            background = style.menu.background
        self._data: StyleBackground = background
        self._base: Backing = Backing(
            background.base, background.base_offset, group=Group(0, layer)
        )
        self._layers: tuple[Backing, ...] = tuple(
            Backing(floating.texture, floating.offset, group=Group(idx + 1, layer))
            for idx, floating in enumerate(background.layers)
        )

        self.layer_offsets: list[tuple[float, float]] = [(0.0, 0.0)] * len(self._layers)

    def connect_renderer(self, batch: Batch | None) -> None:
        self._base.batch = batch
        for backing in self._layers:
            backing.batch = batch

    def disconnect_renderer(self) -> None:
        self.connect_renderer(None)

    def cursor_motion(self, x: float, y: float, dx: float, dy: float) -> None:
        for idx, layer in enumerate(self._layers):
            data = self._data.layers[idx]
            origin = (
                data.foci[0] * layer.size[0],
                data.foci[1] * layer.size[1],
            )
            shift = int((origin[0] - x) / (data.depth)), int(
                (origin[1] - y) / (data.depth)
            )
            layer.position = shift
            self.layer_offsets[idx] = (
                shift[0] - layer.shift[0],
                shift[1] - layer.shift[1],
            )

    def update(self) -> None:
        t = GLOBAL_CLOCK.time
        for idx, layer in enumerate(self._layers):
            data = self._data.layers[idx]
            fraction = (t + data.sync) % data.rate / data.rate
            match data.mode:
                case FloatMotionMode.CIRCLE:
                    x = data.scale * cos(fraction * tau)
                    y = data.scale * sin(fraction * tau)
                case FloatMotionMode.DIAGONAL:
                    x = data.scale * cos(fraction * tau)
                    y = x
            layer.shift = (x, y)
            self.layer_offsets[idx] = layer.position[0] - x, layer.position[1] - y

    def draw(self):
        self._base.draw()
        for layer in self._layers:
            layer.draw()
