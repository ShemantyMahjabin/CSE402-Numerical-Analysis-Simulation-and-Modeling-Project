#!/usr/bin/env python3
"""Controlled stress-test harness (Objective 4 of the project proposal).

Runs every method over a parameterized grid of test functions that vary
root position, concavity direction, and curvature strength (see
rootfinding/testfunctions.py), and reports accuracy, work, and robustness
metrics for a fair comparison:

- success rate and mean iterations
- Nf and Nf' (actual function/derivative evaluation counts)
- work = Nf + lambda * Nf' (lambda models a derivative costing more or
  less than one function evaluation; default 1.0)
- bracket contraction: final bracket width / initial interval width
- wall-clock runtime
"""

import argparse
import csv
import json
from pathlib import Path
import sys
import time

from rootfinding import solve
from rootfinding.testfunctions import generate_cases

METHODS = ["bisection", "false-position", "base", "improved", "adaptive", "safeguarded"]
NEEDS_DERIVATIVE = {"improved", "safeguarded"}


def run(cases, methods, tol, max_iterations, lam):
    records = []
    for case in cases:
        width = case.b - case.a
        for method in methods:
            df = case.df if method in NEEDS_DERIVATIVE else None
            start = time.perf_counter()
            result = solve(case.f, case.a, case.b, method=method, df=df,
                            tol=tol, max_iterations=max_iterations, stopping="residual")
            elapsed = time.perf_counter() - start
            records.append({
                "case": case.label,
                "method": method,
                "converged": result.converged,
                "iterations": result.iterations,
                "residual": result.residual,
                "function_evaluations": result.function_evaluations,
                "derivative_evaluations": result.derivative_evaluations,
                "work": result.function_evaluations + lam * result.derivative_evaluations,
                "bracket_contraction": (result.b - result.a) / width,
                "runtime": elapsed,
            })
    return records


def summarize(records, methods):
    summary = []
    metrics = ["iterations", "function_evaluations", "derivative_evaluations", "work",
               "bracket_contraction", "runtime"]
    for method in methods:
        rows = [r for r in records if r["method"] == method]
        n = len(rows)
        if n == 0:
            continue
        converged = sum(1 for r in rows if r["converged"])
        entry = {"method": method, "cases": n, "success_rate": converged / n}
        for metric in metrics:
            entry[f"mean_{metric}"] = sum(r[metric] for r in rows) / n
        summary.append(entry)
    return summary


def print_summary(summary):
    header = (f"{'Method':16} {'Success':>8} {'Iter':>7} {'Nf':>7} {'Nf-prime':>9} "
              f"{'Work':>8} {'Contraction':>12} {'Runtime(ms)':>12}")
    print(header)
    for row in summary:
        print(f"{row['method']:16} {row['success_rate'] * 100:7.1f}% "
              f"{row['mean_iterations']:7.2f} {row['mean_function_evaluations']:7.2f} "
              f"{row['mean_derivative_evaluations']:9.2f} {row['mean_work']:8.2f} "
              f"{row['mean_bracket_contraction']:12.6f} {row['mean_runtime'] * 1000:12.4f}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--methods", nargs="+", choices=METHODS, default=METHODS)
    parser.add_argument("--tol", type=float, default=1e-10)
    parser.add_argument("--max-iterations", type=int, default=100)
    parser.add_argument("--lambda", dest="lam", type=float, default=1.0,
                         help="Cost weight for a derivative evaluation in work = Nf + lambda*Nf'")
    parser.add_argument("--interval", type=float, nargs=2, default=(-2.0, 2.0),
                         metavar=("LOW", "HIGH"))
    parser.add_argument("--output-dir", type=Path, help="Save per-case records and the summary")
    args = parser.parse_args(argv)

    cases = generate_cases(tuple(args.interval))
    records = run(cases, args.methods, args.tol, args.max_iterations, args.lam)
    summary = summarize(records, args.methods)
    print_summary(summary)

    if args.output_dir:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        (args.output_dir / "stress_records.json").write_text(json.dumps(records, indent=2) + "\n")
        (args.output_dir / "stress_summary.json").write_text(json.dumps(summary, indent=2) + "\n")
        with (args.output_dir / "stress_records.csv").open("w", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(records[0].keys()))
            writer.writeheader()
            writer.writerows(records)
        print(f"Saved records and summary to {args.output_dir}")

    return 0 if all(r["converged"] for r in records) else 1


if __name__ == "__main__":
    sys.exit(main())
