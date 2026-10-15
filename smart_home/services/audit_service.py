"""Optional consumer demonstrating extension without changing the producer."""

from typing import Callable, List

from smart_home.events import Event


class AuditService:
    def __init__(self, output: Callable[[str], None] = print) -> None:
        self.events: List[Event] = []
        self._output = output

    def on_event(self, event: Event) -> None:
        self.events.append(event)
        self._output(
            f"AuditService: {type(event).__name__} received at "
            f"{event.timestamp.isoformat()}."
        )
