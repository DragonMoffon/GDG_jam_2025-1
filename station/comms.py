from dataclasses import dataclass

from resources import style

@dataclass
class Communication:
    dialogue: str
    speaker: str | None
    mood: str | None
    tab: str | None

    read: bool = False

    @property
    def speaker_id(self) -> str:
        return "narrator" if self.speaker is None else self.speaker.replace(" ", "-").casefold()

    @property
    def portrait(self) -> str | None:
        if self.speaker is None:
            return None
        elif self.mood is None:
            return f"{self.speaker_id}-default"
        else:
            return f"{self.speaker_id}-{self.mood}"

    def mark_read(self) -> None:
        self.read = True


class CommunicatonLog:
    def __init__(self):
        self.log: list[Communication] = []

    def say(self, s: str, speaker: str | None = None, mood: str | None = None, tab: str | None = None) -> None:
        self.log.append(Communication(s, speaker, mood, tab))
        style.audio.incoming_comm.play("notification")

    def read_all(self) -> None:
        for c in self.log:
            c.mark_read()

comms = CommunicatonLog()

# Dummy data: get rid of this later!
# comms.say("CS returns to LMG the next day.")
# comms.say("Welcome to Linus Media Group! Come on in. I'll show you to your desk.", "Linus")
# comms.say("Thanks, Linus.", "CS")
# comms.say("Linus leads CS to his new desk.")
# comms.say("Wow! I thought this was a starting office. Why do I get such a cool setup?", "CS", "happy")
# comms.say("Actually, this is our *worst* setup. You'll get upgraded after you've been here for a while.", "Linus")
