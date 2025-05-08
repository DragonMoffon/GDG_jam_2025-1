from math import cos, sin, tau

from arcade.clock import GLOBAL_CLOCK
from arcade.future.background import Background, BackgroundGroup

from resources import Style
from resources.style import FloatMotionMode, Background as StyleBackground


class ParallaxBackground:

    def __init__(self, background: StyleBackground | None = None):
        if background is None:
            background = Style.menu.background
        self._data: StyleBackground = background
        self._base: Background = Background.from_file(
            background.base, background.base_offset
        )
        self._layers: tuple[Background, ...] = tuple(
            Background.from_file(floating.src, floating.offset)
            for floating in background.layers
        )
        self._background = BackgroundGroup([self._base, *self._layers])

        self.layer_offsets: list[tuple[float, float]] = [(0.0, 0.0)] * len(self._layers)

    def cursor_motion(self, x: float, y: float, dx: float, dy: float) -> None:
        for idx, layer in enumerate(self._layers):
            data = self._data.layers[idx]
            origin = (
                data.foci[0] * layer.texture.texture.width,
                data.foci[1] * layer.texture.texture.height,
            )
            shift = int((origin[0] - x) / (data.depth)), int(
                (origin[1] - y) / (data.depth)
            )
            layer.pos = shift
            self.layer_offsets[idx] = (
                shift[0] - layer.texture.offset[0],
                shift[1] - layer.texture.offset[1],
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
            layer.texture.offset = (x, y)
            self.layer_offsets[idx] = layer.pos[0] - x, layer.pos[1] - y

    def draw(self) -> None:
        self._background.draw()
