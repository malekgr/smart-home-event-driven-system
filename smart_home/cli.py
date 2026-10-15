"""Console command producer. Communication with consumers goes through the bus."""

import argparse
import sys
from typing import Callable, Optional, Sequence, TextIO

from smart_home.app import create_application
from smart_home.event_bus import EventBus
from smart_home.events import DoorOpened, MotionDetected, SmokeDetected
from smart_home.state import SystemState


HELP = (
    "Commands: mode home|away, motion <location>, door_open <door>, "
    "smoke <location>, help, exit. Use underscores for names with spaces."
)


class CommandProcessor:
    """Translate valid commands into state changes or published events."""

    def __init__(
        self, bus: EventBus, state: SystemState,
        output: Callable[[str], None] = print,
    ) -> None:
        self._bus = bus
        self._state = state
        self._output = output

    def process(self, line: str) -> bool:
        """Return False on exit, True when the command loop should continue."""
        parts = line.split()
        if not parts:
            return True
        command = parts[0].lower()
        if command in ("exit", "help"):
            if len(parts) != 1:
                self._output(f"Invalid input. Usage: {command}")
                return True
            if command == "exit":
                return False
            self._output(HELP)
            return True

        factories = {
            "motion": MotionDetected,
            "door_open": DoorOpened,
            "smoke": SmokeDetected,
        }
        if command not in ("mode", *factories):
            self._output(f"Unknown command: {parts[0]}. Type 'help' for commands.")
            return True
        if len(parts) != 2:
            argument = {"mode": "home|away", "door_open": "<door>"}.get(
                command, "<location>"
            )
            self._output(f"Invalid input. Usage: {command} {argument}")
            return True

        value = parts[1]
        if command == "mode":
            try:
                self._state.set_mode(value)
            except ValueError:
                self._output("Invalid mode. Use HOME or AWAY.")
            else:
                self._output(f"System mode changed to {self._state.mode.value}.")
        else:
            event = factories[command](value)
            self._output(f"Event Published: {type(event).__name__}")
            self._output(f"{'Door' if command == 'door_open' else 'Location'}: {value}")
            self._bus.publish(event)
            self._output("")
        return True


def run_console(
    processor: CommandProcessor, source: TextIO,
    output: Callable[[str], None] = print, *, interactive: bool = False,
) -> None:
    if interactive:
        output("Smart Home Monitoring System (HOME mode). Type 'help' for commands.")
    try:
        while True:
            if interactive:
                print("> ", end="", flush=True)
            line = source.readline()
            if not line or not processor.process(line):
                break
    except KeyboardInterrupt:
        output("")
    output("Program terminated.")


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Event-driven smart home simulation")
    parser.add_argument(
        "--audit", action="store_true",
        help="add an independent audit subscriber to all three event types",
    )
    parser.add_argument(
        "--demo-failure", action="store_true",
        help="fail a smoke subscriber to demonstrate continued event delivery",
    )
    args = parser.parse_args(argv)
    app = create_application(audit=args.audit, demo_failure=args.demo_failure)
    processor = CommandProcessor(app.bus, app.state)
    run_console(processor, sys.stdin, interactive=sys.stdin.isatty())
    return 0
