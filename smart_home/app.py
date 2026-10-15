"""Composition root: assemble services and register their subscriptions."""

from dataclasses import dataclass
from typing import Callable, Optional

from smart_home.event_bus import EventBus, Handler
from smart_home.events import DoorOpened, Event, MotionDetected, SmokeDetected
from smart_home.services.alarm_service import AlarmService
from smart_home.services.audit_service import AuditService
from smart_home.services.light_service import LightService
from smart_home.services.notification_service import NotificationService
from smart_home.services.security_service import SecurityService
from smart_home.state import SystemState


@dataclass
class SmartHomeApp:
    bus: EventBus
    state: SystemState
    lights: LightService
    security: SecurityService
    notifications: NotificationService
    alarm: AlarmService
    audit: Optional[AuditService]


def failing_smoke_consumer(event: SmokeDetected) -> None:
    """An opt-in demonstration fault, placed before the normal consumers."""
    raise RuntimeError("simulated consumer failure")


def create_application(
    output: Callable[[str], None] = print,
    *,
    audit: bool = False,
    demo_failure: bool = False,
) -> SmartHomeApp:
    def report_error(event: Event, handler: Handler, error: Exception) -> None:
        output(
            f"EventBus: Consumer {handler.__qualname__} failed while processing "
            f"{type(event).__name__}: {error}. Continuing delivery."
        )

    bus = EventBus(on_error=report_error)
    state = SystemState()
    lights = LightService(output)
    security = SecurityService(state, output)
    notifications = NotificationService(output)
    alarm = AlarmService(output)

    if demo_failure:
        bus.subscribe(SmokeDetected, failing_smoke_consumer)

    bus.subscribe(MotionDetected, lights.on_motion)
    bus.subscribe(MotionDetected, security.on_motion)
    bus.subscribe(DoorOpened, security.on_door)
    bus.subscribe(DoorOpened, notifications.on_door)
    bus.subscribe(SmokeDetected, alarm.on_smoke)
    bus.subscribe(SmokeDetected, notifications.on_smoke)
    bus.subscribe(SmokeDetected, security.on_smoke)

    audit_service = AuditService(output) if audit else None
    if audit_service is not None:
        for event_type in (MotionDetected, DoorOpened, SmokeDetected):
            bus.subscribe(event_type, audit_service.on_event)

    return SmartHomeApp(
        bus, state, lights, security, notifications, alarm, audit_service
    )
