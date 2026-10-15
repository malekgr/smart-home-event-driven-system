"""Verify routing, extension, and failure isolation independently of services."""

import unittest

from smart_home.event_bus import EventBus
from smart_home.events import DoorOpened, MotionDetected, SmokeDetected


class EventBusTests(unittest.TestCase):
    def test_only_matching_subscribers_receive_the_same_event(self):
        bus = EventBus()
        first, second, doors = [], [], []
        bus.subscribe(MotionDetected, first.append)
        bus.subscribe(MotionDetected, second.append)
        bus.subscribe(DoorOpened, doors.append)
        event = MotionDetected("hallway")

        bus.publish(event)

        self.assertIs(first[0], event)
        self.assertIs(second[0], event)
        self.assertEqual(doors, [])

    def test_failure_preserves_delivery_order_and_future_publications(self):
        errors, delivered = [], []
        bus = EventBus(on_error=lambda event, handler, error: errors.append(
            (event, handler, error)
        ))

        def failing_handler(event):
            raise RuntimeError("consumer unavailable")

        bus.subscribe(SmokeDetected, failing_handler)
        bus.subscribe(SmokeDetected, lambda event: delivered.append(("alarm", event)))
        bus.subscribe(SmokeDetected, lambda event: delivered.append(("security", event)))
        events = [SmokeDetected("kitchen"), SmokeDetected("garage")]
        for event in events:
            bus.publish(event)

        self.assertEqual(delivered, [
            ("alarm", events[0]), ("security", events[0]),
            ("alarm", events[1]), ("security", events[1]),
        ])
        self.assertEqual(len(errors), 2)
        self.assertIs(errors[0][0], events[0])
        self.assertIs(errors[0][1], failing_handler)
        self.assertIsInstance(errors[0][2], RuntimeError)

    def test_new_consumer_joins_existing_event(self):
        bus = EventBus()
        original, added = [], []
        bus.subscribe(MotionDetected, original.append)
        bus.publish(MotionDetected("before"))
        bus.subscribe(MotionDetected, added.append)
        event = MotionDetected("after")

        bus.publish(event)

        self.assertEqual(len(original), 2)
        self.assertEqual(added, [event])

    def test_subscription_changes_apply_to_next_publication(self):
        bus = EventBus()
        received = []

        def register_consumer(event):
            bus.subscribe(MotionDetected, received.append)

        bus.subscribe(MotionDetected, register_consumer)
        bus.publish(MotionDetected("first"))
        self.assertEqual(received, [])
        second = MotionDetected("second")
        bus.publish(second)
        self.assertEqual(received, [second])

    def test_event_without_subscribers_is_allowed(self):
        EventBus().publish(DoorOpened("front_door"))


if __name__ == "__main__":
    unittest.main()
