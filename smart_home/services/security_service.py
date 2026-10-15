"""Record security events and apply mode-dependent alert rules."""

from dataclasses import dataclass
from datetime import datetime
from typing import Callable, List

from smart_home.events import DoorOpened, Event, MotionDetected, SmokeDetected
from smart_home.state import Mode, SystemState


@dataclass(frozen=True)
class SecurityRecord:
    event_type: str
    location: str
    timestamp: datetime
    mode: Mode


class SecurityService:
    def __init__(
        self, state: SystemState, output: Callable[[str], None] = print
    ) -> None:
        self.records: List[SecurityRecord] = []
        self.alerts: List[str] = []
        self._state = state
        self._output = output

    def _record(self, event: Event, location: str) -> None:
        self.records.append(SecurityRecord(
            type(event).__name__, location, event.timestamp, self._state.mode
        ))

    def _alert(self, message: str) -> None:
        self.alerts.append(message)
        self._output(f"SecurityService: ALERT - {message}")

    def on_motion(self, event: MotionDetected) -> None:
        self._record(event, event.location)
        self._output(f"SecurityService: Motion recorded in {event.location}.")
        if self._state.mode is Mode.AWAY:
            self._alert("Motion detected while system is in AWAY mode.")

    def on_door(self, event: DoorOpened) -> None:
        self._record(event, event.door)
        label = event.door.replace("_", " ").capitalize()
        self._output(f"SecurityService: {label} opening recorded.")
        if self._state.mode is Mode.AWAY:
            self._alert(f"{label} opened while system is in AWAY mode.")

    def on_smoke(self, event: SmokeDetected) -> None:
        self._record(event, event.location)
        self._output(
            f"SecurityService: Smoke emergency recorded for {event.location}."
        )
