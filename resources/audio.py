from pathlib import Path

from pyglet.media import load as load_audio, Source
from pyglet.media.player import Player


class Audio:
    def __init__(self):
        self._players: dict[str, Player] = {}

    def play(self, sound: Source, channel: str = "default", loop=False) -> None:
        if channel not in self._players:
            self._players[channel] = Player()

        player = self._players[channel]
        # Bodging this together -- bad for memory
        player.pause()
        player.next_source()

        player.queue(sound)
        player.play()

    def stop(self, channel: str | None = None) -> None:
        if channel is not None:
            self._players[channel].pause()
        else:
            for player in self._players.values():
                player.pause()


AUDIO = Audio()


class Sound:
    __cache__: dict[Path, Source] = {}

    def __init__(self, pth: Path):
        if str(pth) not in Sound.__cache__:
            Sound.__cache__[str(pth)] = load_audio(pth)
        self._source: Source = Sound.__cache__[str(pth)]

    def play(self, channel: str = "default", loop: bool = False) -> None:
        AUDIO.play(self._source, channel, loop)
