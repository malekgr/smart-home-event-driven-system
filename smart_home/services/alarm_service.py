"""Simulate a fire alarm independently of the operating mode."""

from typing import Callable, List

from smart_home.events import SmokeDetected


class AlarmService:
    def __init__(self, output: Callable[[str], None] = print) -> None:
        self.active = False
        self.locations: List[str] = []
        self._output = output

    def on_smoke(self, event: SmokeDetected) -> None:
        self.active = True
        self.locations.append(event.location)
        self._output("AlarmService: FIRE ALARM ACTIVATED.")
