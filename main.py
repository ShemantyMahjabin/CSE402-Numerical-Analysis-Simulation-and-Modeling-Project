#!/usr/bin/env python3
"""Command-line runner for the base and improved numerical projects."""

import argparse
import csv
from dataclasses import fields as dataclass_fields
import json
from pathlib import Path
import sys

from rootfinding import Step, solve
from rootfinding.expressions import expression
from rootfinding.problems import PROBLEMS


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["base", "improved", "both", "all", "bisection", "false-position"], default="both")
    parser.add_argument("--example", choices=PROBLEMS, default=None)
    parser.add_argument("--function", help="Quoted expression, e.g. 'x**2-x-2'")
    parser.add_argument("--derivative", help="Analytic derivative expression; required for custom improved runs")
    parser.add_argument("--a", type=float, help="Left endpoint")
    parser.add_argument("--b", type=float, help="Right endpoint")
    parser.add_argument("--tol", type=float, default=1e-7)
    parser.add_argument("--max-iterations", type=int, default=100)
    parser.add_argument("--stop", choices=["paper", "residual", "step-residual", "bracket-residual"], default="paper")
    parser.add_argument("--trace", action="store_true", help="Print per-iteration details")
    parser.add_argument("--output-dir", type=Path, help="Save results.json and iterations.csv")
    parser.add_argument("--benchmark", action="store_true", help="Run all included paper examples")
    parser.add_argument("--list-examples", action="store_true")
    args = parser.parse_args(argv)
    if args.list_examples:
        for name, p in PROBLEMS.items():
            print(f"{name:15} f(x)={p.function}  [{p.a}, {p.b}]  ({p.source})")
        return 0
    if args.benchmark and any(v is not None for v in (args.function, args.derivative, args.example, args.a, args.b)):
        parser.error("--benchmark cannot be combined with custom inputs or --example")
    if args.example and args.function:
        parser.error("Choose --example or --function")
    if args.derivative and not args.function:
        parser.error("--derivative requires --function; examples already include derivatives")
    if args.function and (args.a is None or args.b is None):
        parser.error("Custom functions require both --a and --b")
    methods = {"both": ["base", "improved"],
               "all": ["bisection", "false-position", "base", "improved"]}.get(args.mode, [args.mode])
    if args.function and "improved" in methods and not args.derivative:
        parser.error("Supply --derivative when a custom function is run with improvement")
    if args.benchmark:
        inputs = [(name, p.function, p.derivative, p.a, p.b) for name, p in PROBLEMS.items()]
    elif args.function:
        inputs = [("custom", args.function, args.derivative, args.a, args.b)]
    else:
        name = args.example or "quadratic"
        p = PROBLEMS[name]
        inputs = [(name, p.function, p.derivative,
                   p.a if args.a is None else args.a, p.b if args.b is None else args.b)]
    records = []
    print(f"{'Problem':15} {'Method':15} {'Root':>18} {'|f(root)|':>12} {'Iter':>5} {'f calls':>7} {'df calls':>8} Status")
    try:
        for name, source, derivative, a, b in inputs:
            f = expression(source)
            df = expression(derivative) if derivative else None
            for method in methods:
                result = solve(f, a, b, method=method, df=df, tol=args.tol,
                               max_iterations=args.max_iterations, stopping=args.stop)
                records.append({"problem": name, "function": source,
                                "derivative": derivative if method == "improved" else None,
                                "input_a": a, "input_b": b, "tolerance": args.tol,
                                "max_iterations": args.max_iterations, **result.to_dict()})
                status = "OK" if result.converged else "NOT CONVERGED"
                print(f"{name:15} {method:15} {result.root:18.12g} {result.residual:12.4e} "
                      f"{result.iterations:5d} {result.function_evaluations:7d} {result.derivative_evaluations:8d} {status}")
                print(f"  stop={result.stopping}; error={result.error:.6g}; "
                      f"bracket=[{result.a:.12g}, {result.b:.12g}]; {result.reason}")
                if args.trace:
                    for s in result.history:
                        print(f"  {s.iteration:3d}: m={s.midpoint!s} s={s.false_position!s} n={s.newton!s}\n"
                              f"       selected={s.selected}; root={s.root:.12g}; |f|={s.residual:.6g}; "
                              f"step={s.step_size:.6g}; error={s.error:.6g}; "
                              f"bracket=[{s.a:.12g}, {s.b:.12g}]; Newton: {s.newton_status}")
        if args.output_dir:
            args.output_dir.mkdir(parents=True, exist_ok=True)
            (args.output_dir / "results.json").write_text(json.dumps(records, indent=2, allow_nan=False) + "\n")
            # Endpoint roots have no iteration rows; always emit the same CSV header.
            fields = ["problem", "method"] + [field.name for field in dataclass_fields(Step)]
            with (args.output_dir / "iterations.csv").open("w", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=fields)
                writer.writeheader()
                for record in records:
                    for step in record["history"]:
                        writer.writerow({"problem": record["problem"], "method": record["method"], **step})
            print(f"Saved {args.output_dir / 'results.json'} and {args.output_dir / 'iterations.csv'}")
    except (ValueError, OverflowError, OSError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    return 0 if all(r["converged"] for r in records) else 1


if __name__ == "__main__":
    sys.exit(main())
