import tempfile
import unittest
from pathlib import Path
from tracepilot.history import save_run, list_runs, get_run
def sample(name, failures=0):
    return {
        "baseline": "baseline.xml",
        "current": name,
        "summary": {"new_failures": failures},
        "new_failures": [],
        "persistent_failures": [],
        "resolved_failures": [],
        "new_tests": [],
        "removed_tests": [],
        "failure_groups": [],
    }
class HistoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = str(Path(self.tmp.name) / "history.sqlite3")
    def tearDown(self):
        self.tmp.cleanup()
    def test_save_and_retrieve(self):
        run_id = save_run(sample("current.xml", 2), self.db)
        self.assertEqual(get_run(run_id, self.db)["summary"]["new_failures"], 2)
    def test_newest_first(self):
        save_run(sample("first.xml"), self.db)
        save_run(sample("second.xml"), self.db)
        self.assertEqual(list_runs(self.db)[0]["current"], "second.xml")
    def test_limit(self):
        for i in range(4):
            save_run(sample(f"run-{i}.xml"), self.db)
        self.assertEqual(len(list_runs(self.db, 2)), 2)
    def test_invalid_limit(self):
        with self.assertRaises(ValueError):
            list_runs(self.db, 0)
    def test_missing_run(self):
        self.assertIsNone(get_run(999, self.db))
if __name__ == "__main__":
    unittest.main()
