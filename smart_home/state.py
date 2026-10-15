"""The single source of truth for the system's operating mode."""

from dataclasses import dataclass
from enum import Enum


class Mode(Enum):
    HOME = "HOME"
    AWAY = "AWAY"


@dataclass
class SystemState:
    mode: Mode = Mode.HOME

    def set_mode(self, value: str) -> None:
        # Construct before assigning: invalid modes leave the state unchanged.
        self.mode = Mode(value.upper())
