import csv
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


PROJECT = Path(__file__).resolve().parents[1]


class CommandLineTests(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, str(PROJECT / "main.py"), *args],
                              cwd=PROJECT, capture_output=True, text=True)

    def test_comparison_exports(self):
        with tempfile.TemporaryDirectory() as directory:
            run = self.run_cli("--mode", "both", "--example", "cosine", "--stop", "residual",
                               "--output-dir", directory)
            self.assertEqual(run.returncode, 0, run.stderr)
            records = json.loads((Path(directory) / "results.json").read_text())
            self.assertEqual([r["method"] for r in records], ["base", "improved"])
            self.assertTrue(all(r["converged"] for r in records))
            self.assertTrue(all(abs(r["root"] - 0.7390851332151607) < 1e-7 for r in records))
            with (Path(directory) / "iterations.csv").open() as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(len(rows), sum(r["iterations"] for r in records))

    def test_custom_endpoint_export(self):
        with tempfile.TemporaryDirectory() as directory:
            run = self.run_cli("--mode", "base", "--function", "x", "--a", "0", "--b", "1",
                               "--output-dir", directory)
            self.assertEqual(run.returncode, 0, run.stderr)
            record = json.loads((Path(directory) / "results.json").read_text())[0]
            self.assertEqual(record["iterations"], 0)
            self.assertEqual(record["history"], [])
            with (Path(directory) / "iterations.csv").open() as stream:
                reader = csv.DictReader(stream)
                self.assertEqual(list(reader), [])
                self.assertIn("newton_status", reader.fieldnames)

    def test_missing_derivative_and_invalid_bracket(self):
        for args in (("--function", "x**2-2", "--a", "0", "--b", "2"),
                     ("--mode", "base", "--function", "x**2+1", "--a", "-1", "--b", "1")):
            run = self.run_cli(*args)
            self.assertEqual(run.returncode, 2)
            self.assertTrue(run.stderr)
            self.assertNotIn("Traceback", run.stderr)

    def test_nonconvergence_exit_code(self):
        run = self.run_cli("--mode", "base", "--example", "sqrt3", "--max-iterations", "1")
        self.assertEqual(run.returncode, 1)
        self.assertIn("NOT CONVERGED", run.stdout)


if __name__ == "__main__":
    unittest.main()
