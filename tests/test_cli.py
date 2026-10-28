import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
BASELINE = ROOT / "fixtures" / "baseline.xml"
CURRENT = ROOT / "fixtures" / "current.xml"
class TracePilotCliTests(unittest.TestCase):
    def run_cli(self, *args):
        env = os.environ.copy()
        env["PYTHONPATH"] = str(SRC) + os.pathsep + env.get("PYTHONPATH", "")
        return subprocess.run(
            [
                sys.executable, "-m", "tracepilot",
                str(BASELINE), str(CURRENT), *args
            ],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
        )
    def test_default_run_generates_report_successfully(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = Path(tmp) / "report.html"
            result = self.run_cli("--out", str(report))
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(report.exists())
            self.assertIn("New failures:      1", result.stdout)
    def test_new_failure_gate_returns_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.run_cli(
                "--out", str(Path(tmp) / "report.html"),
                "--fail-on", "new",
            )
            self.assertEqual(result.returncode, 1)
            self.assertIn("CI GATE: FAILED", result.stderr)
    def test_any_failure_gate_returns_one_for_persistent_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.run_cli(
                "--out", str(Path(tmp) / "report.html"),
                "--fail-on", "any",
            )
            self.assertEqual(result.returncode, 1)
    def test_json_output_is_valid(self):
        with tempfile.TemporaryDirectory() as tmp:
            json_path = Path(tmp) / "comparison.json"
            result = self.run_cli(
                "--out", str(Path(tmp) / "report.html"),
                "--json-out", str(json_path),
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            data = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertEqual(data["summary"]["new_failures"], 1)
            self.assertEqual(data["summary"]["persistent_failures"], 1)
    def test_missing_input_returns_two(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.run_cli(
                str(Path(tmp) / "missing.xml"),
                "--out", str(Path(tmp) / "report.html"),
            )
            self.assertEqual(result.returncode, 2)
            self.assertIn("TracePilot", result.stderr)
if __name__ == "__main__":
    unittest.main()
