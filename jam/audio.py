from pyglet.media import load, Source
from pyglet.media.player import Player, Source
from importlib.resources import path
from pathlib import Path

from resources.styles import base

class Audio:
    def __init__(self, root: Path | None = None):
        self._players: dict[str, Player] = {}
        self.root: Path = None
        if root is None:
            with path(base, "audio") as p:
                self.root = p
        else:
            self.root = root
        self._cache: dict[str, Source] = {}

    def play(self, sound_name: str, channel: str = "default", loop = False) -> None:
        if channel not in self._players:
            self._players[channel] = Player()

        player = self._players[channel]
        player.loop = loop

        if sound_name not in self._cache:
            sound_paths = self.root.glob(f"{sound_name}.*")
            try:
                sound_path = next(sound_paths)
                self._cache[sound_name] = load(sound_path)
            except StopIteration as e:
                raise ValueError(f"Invalid sound name {sound_name}.") from e

        sound = self._cache[sound_name]

        player.queue(sound)
        player.play()

    def stop(self, channel: str | None = None) -> None:
        if channel:
            self._players[channel].pause()
        else:
            for player in self._players.values():
                player.pause()

AUDIO = Audio()
