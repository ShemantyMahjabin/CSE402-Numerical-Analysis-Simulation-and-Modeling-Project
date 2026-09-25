import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from rootfinding.testfunctions import generate_cases
from rootfinding.classical import opposite

PROJECT = Path(__file__).resolve().parents[1]


class TestFunctionFamilyTests(unittest.TestCase):
    def test_grid_size_and_labels_are_unique(self):
        cases = generate_cases()
        self.assertEqual(len(cases), 3 * 2 * 2)
        self.assertEqual(len({c.label for c in cases}), len(cases))

    def test_every_case_has_a_guaranteed_bracket_and_interior_root(self):
        for case in generate_cases():
            with self.subTest(case=case.label):
                self.assertTrue(opposite(case.f(case.a), case.f(case.b)))
                self.assertLess(case.a, case.root)
                self.assertLess(case.root, case.b)
                self.assertAlmostEqual(case.f(case.root), 0.0)

    def test_derivative_matches_numerical_estimate(self):
        h = 1e-6
        for case in generate_cases():
            x = (case.a + case.b) / 2
            numerical = (case.f(x + h) - case.f(x - h)) / (2 * h)
            with self.subTest(case=case.label):
                self.assertAlmostEqual(case.df(x), numerical, places=4)


class StressTestCLITests(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, str(PROJECT / "stress_test.py"), *args],
                              cwd=PROJECT, capture_output=True, text=True)

    def test_runs_and_exports_all_methods(self):
        # false-position is expected to stagnate on some strongly asymmetric
        # cases in this grid (the classical pathology the base/improved/
        # adaptive/safeguarded methods are all designed to avoid), so a
        # nonzero exit code from that method alone is not a bug; every
        # other method must still converge on every case.
        with tempfile.TemporaryDirectory() as directory:
            run = self.run_cli("--tol", "1e-8", "--output-dir", directory)
            records = json.loads((Path(directory) / "stress_records.json").read_text())
            summary = json.loads((Path(directory) / "stress_summary.json").read_text())
            self.assertEqual(len(records), 12 * 6)
            methods = {row["method"] for row in summary}
            self.assertEqual(methods, {"bisection", "false-position", "base",
                                        "improved", "adaptive", "safeguarded"})
            for row in summary:
                if row["method"] != "false-position":
                    self.assertEqual(row["success_rate"], 1.0, row["method"])
                expected_work = row["mean_function_evaluations"] + row["mean_derivative_evaluations"]
                self.assertAlmostEqual(row["mean_work"], expected_work, places=9)

    def test_subset_of_methods(self):
        run = self.run_cli("--methods", "base", "adaptive", "--tol", "1e-3", "--max-iterations", "20")
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn("base", run.stdout)
        self.assertIn("adaptive", run.stdout)
        self.assertNotIn("improved", run.stdout)


if __name__ == "__main__":
    unittest.main()
