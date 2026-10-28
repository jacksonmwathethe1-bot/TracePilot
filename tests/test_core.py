import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from tracepilot.core import load_report, compare_reports
from tracepilot.report import render_report
ROOT = Path(__file__).resolve().parents[1]
class TracePilotTests(unittest.TestCase):
    def setUp(self):
        self.baseline = load_report(ROOT / "fixtures" / "baseline.xml")
        self.current = load_report(ROOT / "fixtures" / "current.xml")
        self.result = compare_reports(self.baseline, self.current)
    def test_detects_new_failure(self):
        self.assertEqual(self.result["summary"]["new_failures"], 1)
        self.assertEqual(
            self.result["new_failures"][0]["name"], "test_total"
        )
    def test_detects_persistent_failure(self):
        self.assertEqual(self.result["summary"]["persistent_failures"], 1)
    def test_detects_resolved_failure(self):
        self.assertEqual(self.result["summary"]["resolved_failures"], 0)
    def test_groups_matching_failure_signatures(self):
        self.assertEqual(self.result["summary"]["failure_groups"], 2)
    def test_generates_html_report(self):
        with tempfile.TemporaryDirectory() as directory:
            path = render_report(self.result, Path(directory) / "report.html")
            html = path.read_text(encoding="utf-8")
            self.assertIn("TracePilot", html)
            self.assertIn("test_total", html)
            self.assertIn("New failures", html)
    def test_rejects_empty_xml_report(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "empty.xml"
            path.write_text("<testsuites/>", encoding="utf-8")
            with self.assertRaises(ValueError):
                load_report(path)
if __name__ == "__main__":
    unittest.main()
