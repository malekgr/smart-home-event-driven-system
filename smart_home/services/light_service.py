"""Simulate lights that respond to motion."""

from typing import Callable, Dict

from smart_home.events import MotionDetected


class LightService:
    def __init__(self, output: Callable[[str], None] = print) -> None:
        self.lights: Dict[str, bool] = {}
        self._output = output

    def on_motion(self, event: MotionDetected) -> None:
        self.lights[event.location] = True
        label = event.location.replace("_", " ").capitalize()
        self._output(f"LightService: {label} light turned ON.")
