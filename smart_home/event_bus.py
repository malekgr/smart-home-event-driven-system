"""Synchronous publish/subscribe delivery with per-consumer error isolation."""

import logging
from typing import Callable, Dict, List, Optional, Type

from smart_home.events import Event


Handler = Callable[[Event], None]
ErrorHandler = Callable[[Event, Handler, Exception], None]


def log_consumer_error(event: Event, handler: Handler, error: Exception) -> None:
    logging.getLogger(__name__).error(
        "Consumer %s failed while processing %s: %s",
        handler.__qualname__, type(event).__name__, error,
    )


class EventBus:
    """Dispatch events to handlers registered for their exact event type.

    Subscribers execute in registration order before publish() returns. Each
    subscriber gets the same immutable event; an exception cannot stop delivery
    to the remaining subscribers. This bus needs no threads or external broker.
    """

    def __init__(self, on_error: Optional[ErrorHandler] = None) -> None:
        self._subscribers: Dict[Type[Event], List[Handler]] = {}
        self._on_error = on_error if on_error is not None else log_consumer_error

    def subscribe(self, event_type: Type[Event], handler: Handler) -> None:
        self._subscribers.setdefault(event_type, []).append(handler)

    def publish(self, event: Event) -> None:
        # Snapshot subscriptions so changes during delivery apply next time.
        for handler in tuple(self._subscribers.get(type(event), ())):
            try:
                handler(event)
            except Exception as error:
                self._on_error(event, handler, error)
