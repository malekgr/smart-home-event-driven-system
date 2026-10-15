"""Simulate notifications without contacting an external service."""

from typing import Callable, List

from smart_home.events import DoorOpened, SmokeDetected


class NotificationService:
    def __init__(self, output: Callable[[str], None] = print) -> None:
        self.notifications: List[str] = []
        self._output = output

    def on_door(self, event: DoorOpened) -> None:
        label = event.door.replace("_", " ").capitalize()
        message = f"Notification sent - {label} was opened."
        self.notifications.append(message)
        self._output(f"NotificationService: {message}")

    def on_smoke(self, event: SmokeDetected) -> None:
        message = f"EMERGENCY - Smoke detected in {event.location}."
        self.notifications.append(message)
        self._output(f"NotificationService: {message}")
