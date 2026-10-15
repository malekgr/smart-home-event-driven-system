"""Exercise business state and the console producer through the real bus."""

from datetime import datetime, timezone
from io import StringIO
import unittest

from smart_home.app import create_application
from smart_home.cli import CommandProcessor, run_console
from smart_home.events import DoorOpened, MotionDetected, SmokeDetected
from smart_home.state import Mode


class SystemTests(unittest.TestCase):
    def setUp(self):
        self.output = []
        self.app = create_application(self.output.append)
        self.commands = CommandProcessor(
            self.app.bus, self.app.state, self.output.append
        )

    def test_default_mode_is_home(self):
        self.assertIs(self.app.state.mode, Mode.HOME)

    def test_home_motion_turns_on_only_target_light_without_alert(self):
        self.commands.process("motion living_room")
        self.assertEqual(self.app.lights.lights, {"living_room": True})
        self.assertEqual(len(self.app.security.records), 1)
        self.assertEqual(self.app.security.records[0].location, "living_room")
        self.assertEqual(self.app.security.alerts, [])
        self.assertEqual(self.app.notifications.notifications, [])
        self.assertFalse(self.app.alarm.active)

    def test_away_motion_records_and_alerts(self):
        self.commands.process("mode away")
        self.commands.process("motion hallway")
        self.assertTrue(self.app.lights.lights["hallway"])
        self.assertEqual(self.app.security.records[0].event_type, "MotionDetected")
        self.assertIs(self.app.security.records[0].mode, Mode.AWAY)
        self.assertEqual(self.app.security.alerts, [
            "Motion detected while system is in AWAY mode."
        ])

    def test_door_notifies_and_records_in_both_modes(self):
        for mode in Mode:
            with self.subTest(mode=mode):
                app = create_application(lambda message: None)
                app.state.set_mode(mode.value)
                app.bus.publish(DoorOpened("front_door"))
                self.assertEqual(app.security.records[0].location, "front_door")
                self.assertEqual(app.security.records[0].event_type, "DoorOpened")
                self.assertEqual(app.notifications.notifications, [
                    "Notification sent - Front door was opened."
                ])
                self.assertEqual(len(app.security.alerts), int(mode is Mode.AWAY))
                if mode is Mode.AWAY:
                    self.assertIn("Front door opened", app.security.alerts[0])
                self.assertEqual(app.lights.lights, {})

    def test_smoke_activates_all_three_consumers_in_both_modes(self):
        for mode in Mode:
            with self.subTest(mode=mode):
                app = create_application(lambda message: None)
                app.state.set_mode(mode.value)
                app.bus.publish(SmokeDetected("kitchen"))
                self.assertTrue(app.alarm.active)
                self.assertEqual(app.alarm.locations, ["kitchen"])
                self.assertEqual(app.notifications.notifications, [
                    "EMERGENCY - Smoke detected in kitchen."
                ])
                self.assertEqual(app.security.records[0].event_type, "SmokeDetected")
                self.assertEqual(app.security.records[0].location, "kitchen")
                self.assertIs(app.security.records[0].mode, mode)
                self.assertEqual(app.lights.lights, {})

    def test_mode_switch_affects_subsequent_events(self):
        for command in (
            "motion hall", "mode away", "motion hall",
            "door_open front_door", "mode home", "door_open front_door",
        ):
            self.commands.process(command)
        self.assertEqual([record.mode for record in self.app.security.records], [
            Mode.HOME, Mode.AWAY, Mode.AWAY, Mode.HOME,
        ])
        self.assertEqual(len(self.app.security.alerts), 2)

    def test_security_preserves_original_event_timestamp_for_every_type(self):
        timestamp = datetime(2026, 10, 15, 12, 0, tzinfo=timezone.utc)
        events = [
            MotionDetected("hall", timestamp), DoorOpened("door", timestamp),
            SmokeDetected("kitchen", timestamp),
        ]
        for event in events:
            self.app.bus.publish(event)
        self.assertEqual(len(self.app.security.records), 3)
        for record in self.app.security.records:
            self.assertEqual(record.timestamp, timestamp)
        self.assertIsNotNone(MotionDetected("hall").timestamp.utcoffset())

    def test_failure_demo_still_activates_alarm_notifies_and_records(self):
        app = create_application(self.output.append, demo_failure=True)
        app.bus.publish(SmokeDetected("kitchen"))
        self.assertIn("simulated consumer failure", self.output[0])
        self.assertIn("FIRE ALARM ACTIVATED", self.output[1])
        self.assertTrue(app.alarm.active)
        self.assertEqual(len(app.notifications.notifications), 1)
        self.assertEqual(len(app.security.records), 1)

    def test_audit_extension_works_with_existing_command_producer(self):
        app = create_application(self.output.append, audit=True)
        commands = CommandProcessor(app.bus, app.state, self.output.append)
        for command in ("motion hall", "door_open door", "smoke kitchen"):
            commands.process(command)
        self.assertEqual([type(event) for event in app.audit.events], [
            MotionDetected, DoorOpened, SmokeDetected,
        ])
        self.assertTrue(app.lights.lights["hall"])
        self.assertTrue(app.alarm.active)
        self.assertEqual(len(app.security.records), 3)

    def test_repeated_motion_keeps_light_on_and_records_each_event(self):
        self.commands.process("motion hallway")
        self.commands.process("motion hallway")
        self.assertEqual(self.app.lights.lights, {"hallway": True})
        self.assertEqual(len(self.app.security.records), 2)

    def test_invalid_commands_do_not_publish_or_change_mode(self):
        self.commands.process("mode away")
        for command in (
            "mode vacation", "mode", "mode home extra", "motion",
            "motion living room", "door_open", "smoke", "unknown kitchen",
            "exit extra", "help extra",
        ):
            with self.subTest(command=command):
                self.assertTrue(self.commands.process(command))
        self.assertIs(self.app.state.mode, Mode.AWAY)
        self.assertEqual(self.app.security.records, [])
        self.assertEqual(self.app.lights.lights, {})
        self.assertFalse(self.app.alarm.active)

    def test_blank_help_and_case_insensitive_commands(self):
        self.assertTrue(self.commands.process("   "))
        self.assertTrue(self.commands.process("help"))
        self.assertIn("Commands:", self.output[-1])
        self.commands.process("  MODE AwAy  ")
        self.commands.process("MOTION Living_Room")
        self.assertIs(self.app.state.mode, Mode.AWAY)
        self.assertTrue(self.app.lights.lights["Living_Room"])

    def test_exit_stops_before_later_commands(self):
        run_console(
            self.commands, StringIO("motion hall\nexit\nsmoke kitchen\n"),
            self.output.append,
        )
        self.assertEqual(len(self.app.security.records), 1)
        self.assertFalse(self.app.alarm.active)
        self.assertEqual(self.output[-1], "Program terminated.")

    def test_eof_terminates_without_exit_command(self):
        run_console(self.commands, StringIO("motion hall\n"), self.output.append)
        self.assertEqual(len(self.app.security.records), 1)
        self.assertEqual(self.output[-1], "Program terminated.")


if __name__ == "__main__":
    unittest.main()
