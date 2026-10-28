import tempfile
import unittest
from pathlib import Path
from tracepilot.flaky import analyze_reports, render_flaky_report
class FlakyDetectionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.run1 = self.root / "run1.xml"
        self.run2 = self.root / "run2.xml"
        self.run1.write_text("""<testsuite>
          <testcase classname="demo.Checks" name="sometimesFails"/>
          <testcase classname="demo.Checks" name="alwaysPasses"/>
          <testcase classname="demo.Checks" name="alwaysFails">
            <failure message="broken"/>
          </testcase>
          <testcase classname="demo.Checks" name="skipped">
            <skipped/>
          </testcase>
        </testsuite>""", encoding="utf-8")
        self.run2.write_text("""<testsuite>
          <testcase classname="demo.Checks" name="sometimesFails">
            <failure message="intermittent"/>
          </testcase>
          <testcase classname="demo.Checks" name="alwaysPasses"/>
          <testcase classname="demo.Checks" name="alwaysFails">
            <failure message="still broken"/>
          </testcase>
          <testcase classname="demo.Checks" name="skipped">
            <skipped/>
          </testcase>
        </testsuite>""", encoding="utf-8")
    def tearDown(self):
        self.tmp.cleanup()
    def test_detects_mixed_pass_and_failure(self):
        result = analyze_reports([self.run1, self.run2])
        flaky = next(r for r in result["results"] if r["test"].endswith("sometimesFails"))
        self.assertEqual(flaky["status"], "FLAKY")
        self.assertEqual(flaky["passes"], 1)
        self.assertEqual(flaky["failures"], 1)
        self.assertEqual(flaky["failure_rate"], 50.0)
    def test_stable_pass_is_not_flaky(self):
        result = analyze_reports([self.run1, self.run2])
        item = next(r for r in result["results"] if r["test"].endswith("alwaysPasses"))
        self.assertEqual(item["status"], "PASSING")
    def test_consistent_failure_is_not_flaky(self):
        result = analyze_reports([self.run1, self.run2])
        item = next(r for r in result["results"] if r["test"].endswith("alwaysFails"))
        self.assertEqual(item["status"], "CONSISTENTLY FAILING")
    def test_skipped_tests_are_not_counted_as_passes(self):
        result = analyze_reports([self.run1, self.run2])
        item = next(r for r in result["results"] if r["test"].endswith("skipped"))
        self.assertEqual(item["status"], "SKIPPED ONLY")
        self.assertIsNone(item["failure_rate"])
    def test_requires_two_reports(self):
        with self.assertRaises(ValueError):
            analyze_reports([self.run1])
    def test_invalid_xml_is_rejected(self):
        bad = self.root / "bad.xml"
        bad.write_text("<not-closed>", encoding="utf-8")
        with self.assertRaises(ValueError):
            analyze_reports([bad, self.run2])
    def test_html_report_is_generated(self):
        result = analyze_reports([self.run1, self.run2])
        output = render_flaky_report(result, self.root / "report.html")
        content = output.read_text(encoding="utf-8")
        self.assertIn("Flaky Test Analysis", content)
        self.assertIn("sometimesFails", content)
        self.assertIn("50.0%", content)
if __name__ == "__main__":
    unittest.main()
