"""Check the actual entry point and documented sample files end to end."""

from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]


class CliTests(unittest.TestCase):
    def run_app(self, filename, *flags):
        return subprocess.run(
            [sys.executable, str(ROOT / "main.py"), *flags],
            input=(ROOT / "data" / filename).read_text(),
            text=True, capture_output=True, cwd=str(ROOT), timeout=10,
        )

    def test_sample_matches_checked_in_expected_output(self):
        result = self.run_app("sample_input.txt")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        self.assertEqual(
            result.stdout, (ROOT / "data" / "sample_output.txt").read_text()
        )

    def test_home_file_has_emergency_but_no_security_alert(self):
        result = self.run_app("home_input.txt")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("ALERT", result.stdout)
        self.assertIn("FIRE ALARM ACTIVATED", result.stdout)
        self.assertIn("EMERGENCY - Smoke detected in garage", result.stdout)

    def test_mode_switch_file_has_exactly_two_security_alerts(self):
        result = self.run_app("mode_switch_input.txt")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.count("SecurityService: ALERT"), 2)
        self.assertIn("FIRE ALARM ACTIVATED", result.stdout)

    def test_invalid_input_recovers_and_processes_valid_event(self):
        result = self.run_app("invalid_input.txt")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Invalid mode", result.stdout)
        self.assertIn("Unknown command", result.stdout)
        self.assertEqual(result.stdout.count("Event Published:"), 1)
        self.assertIn("Living room light turned ON", result.stdout)
        self.assertTrue(result.stdout.endswith("Program terminated.\n"))

    def test_both_demonstration_flags_work_together(self):
        result = self.run_app("sample_input.txt", "--audit", "--demo-failure")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stderr, "")
        self.assertEqual(result.stdout.count("AuditService:"), 3)
        self.assertIn("simulated consumer failure", result.stdout)
        self.assertIn("FIRE ALARM ACTIVATED", result.stdout)
        self.assertIn("EMERGENCY - Smoke detected in kitchen", result.stdout)
        self.assertIn("Smoke emergency recorded for kitchen", result.stdout)


if __name__ == "__main__":
    unittest.main()
