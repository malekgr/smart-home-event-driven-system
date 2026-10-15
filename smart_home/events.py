"""Immutable messages shared between producers and subscribers."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Union


def utc_now() -> datetime:
    """Capture an aware timestamp when the producer creates an event."""
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class MotionDetected:
    location: str
    timestamp: datetime = field(default_factory=utc_now)


@dataclass(frozen=True)
class DoorOpened:
    door: str
    timestamp: datetime = field(default_factory=utc_now)


@dataclass(frozen=True)
class SmokeDetected:
    location: str
    timestamp: datetime = field(default_factory=utc_now)


Event = Union[MotionDetected, DoorOpened, SmokeDetected]
