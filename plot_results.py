#!/usr/bin/env python3
"""Generate PNG charts backing the project proposal's claims (for slides/reports).

This script is separate from the core project: main.py, stress_test.py, and
rootfinding/ stay dependency-free (standard library only), while this file
additionally requires matplotlib, used only for rendering these images.

Produces, by default into examples/plots/:

  01_iterations_by_method.png       Obj. 2: mean iterations, 13 benchmark problems
  02_function_evals_by_method.png   Obj. 2: mean f evaluations, same problems
  03_convergence_curve.png          Obj. 3: residual decay on the cosine example
  04_stress_success_rate.png        Obj. 4: success rate across the stress-test grid
  05_stress_work_by_curvature.png   Obj. 4: mean work, grouped by curvature strength
  06_stress_grid_heatmap.png        Obj. 4: pass/fail per (test case x method)
"""

import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from rootfinding import solve
from rootfinding.expressions import expression
from rootfinding.problems import PROBLEMS
from rootfinding.testfunctions import generate_cases

METHODS = ["bisection", "false-position", "base", "improved", "adaptive", "safeguarded"]
NEEDS_DERIVATIVE = {"improved", "safeguarded"}

# Fixed categorical color per method, identical across every chart (dataviz
# skill: "color follows the entity, never its rank"). Slots 1-6 of the
# validated default palette (references/palette.md), light mode.
COLORS = {
    "bisection": "#2a78d6",
    "false-position": "#eb6834",
    "base": "#1baf7a",
    "improved": "#eda100",
    "adaptive": "#e87ba4",
    "safeguarded": "#008300",
}
INK = "#0b0b0b"
SECONDARY_INK = "#52514e"
MUTED = "#898781"
GRID_COLOR = "#e1e0d9"
BASELINE = "#c3c2b7"
GOOD, CRITICAL = "#0ca30c", "#d03b3b"
SURFACE = "#fcfcfb"

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 11,
    "text.color": INK,
    "axes.edgecolor": BASELINE,
    "axes.labelcolor": SECONDARY_INK,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "figure.facecolor": SURFACE,
    "axes.facecolor": SURFACE,
    "savefig.facecolor": SURFACE,
})


def _style_axis(ax, y_grid=True):
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    if y_grid:
        ax.grid(axis="y", color=GRID_COLOR, linewidth=0.8, zorder=0)
        ax.set_axisbelow(True)


def _bar_chart(ax, labels, values, colors, ylabel, title, caption, value_fmt="{:.1f}"):
    bars = ax.bar(labels, values, color=colors, width=0.62, zorder=3)
    _style_axis(ax)
    ax.set_ylabel(ylabel, fontsize=10.5)
    ax.set_title(title, loc="left", fontsize=13, color=INK, pad=14)
    top = max(values) if values else 1
    ax.set_ylim(0, top * 1.2)
    for bar, value in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + top * 0.02,
                 value_fmt.format(value), ha="center", va="bottom",
                 fontsize=9.5, color=SECONDARY_INK)
    ax.tick_params(axis="x", labelrotation=18)
    ax.text(0, -0.22, caption, transform=ax.transAxes, fontsize=8.5, color=MUTED, ha="left")


def benchmark_records(tol=1e-10, max_iterations=200):
    records = []
    for name, p in PROBLEMS.items():
        f, df = expression(p.function), expression(p.derivative)
        for method in METHODS:
            result = solve(f, p.a, p.b, method=method,
                            df=df if method in NEEDS_DERIVATIVE else None,
                            tol=tol, max_iterations=max_iterations, stopping="residual")
            records.append({"problem": name, "method": method,
                             "iterations": result.iterations,
                             "function_evaluations": result.function_evaluations,
                             "converged": result.converged})
    return records


def stress_records(tol=1e-8, max_iterations=100, lam=1.0):
    records = []
    for case in generate_cases():
        parts = dict(item.split("=") for item in case.label.split(","))
        for method in METHODS:
            df = case.df if method in NEEDS_DERIVATIVE else None
            result = solve(case.f, case.a, case.b, method=method, df=df,
                            tol=tol, max_iterations=max_iterations, stopping="residual")
            records.append({
                "case": case.label, "position": parts["root"],
                "concavity": parts["concavity"], "curvature": parts["curvature"],
                "method": method, "converged": result.converged,
                "iterations": result.iterations,
                "work": result.function_evaluations + lam * result.derivative_evaluations,
            })
    return records


def plot_benchmark_metric(records, metric, ylabel, title, caption, filename, out_dir, value_fmt="{:.1f}"):
    fig, ax = plt.subplots(figsize=(9, 5.5))
    means = [sum(r[metric] for r in records if r["method"] == m) /
             sum(1 for r in records if r["method"] == m) for m in METHODS]
    _bar_chart(ax, METHODS, means, [COLORS[m] for m in METHODS], ylabel, title, caption, value_fmt)
    fig.tight_layout()
    fig.savefig(out_dir / filename, dpi=200, bbox_inches="tight")
    plt.close(fig)


def plot_convergence_curve(out_dir, tol=1e-12, max_iterations=30):
    fig, ax = plt.subplots(figsize=(9, 5.5))
    f, df = expression("x-cos(x)"), expression("1+sin(x)")
    floor = 1e-16
    for method in METHODS:
        result = solve(f, 0, 1, method=method, df=df if method in NEEDS_DERIVATIVE else None,
                        tol=tol, max_iterations=max_iterations, stopping="residual")
        xs = [s.iteration for s in result.history]
        ys = [max(s.residual, floor) for s in result.history]
        ax.plot(xs, ys, marker="o", markersize=5, linewidth=2, color=COLORS[method],
                label=f"{method} ({result.iterations} iter)", zorder=3)
    ax.set_yscale("log")
    _style_axis(ax)
    ax.set_xlabel("Iteration", fontsize=10.5)
    ax.set_ylabel("Residual |f(root)|  (log scale)", fontsize=10.5)
    ax.set_title("Objective 3 — residual decay on x - cos(x) over [0, 1]", loc="left",
                  fontsize=13, color=INK, pad=14)
    ax.legend(frameon=False, fontsize=9.5, loc="upper right")
    ax.text(0, -0.16, "tol=1e-12, stop=residual. Points at the floor (1e-16) mark an exact "
                       "floating-point root.", transform=ax.transAxes, fontsize=8.5, color=MUTED)
    fig.tight_layout()
    fig.savefig(out_dir / "03_convergence_curve.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def plot_stress_success_rate(records, out_dir):
    fig, ax = plt.subplots(figsize=(9, 5.5))
    rates = []
    for method in METHODS:
        rows = [r for r in records if r["method"] == method]
        rates.append(100 * sum(r["converged"] for r in rows) / len(rows))
    _bar_chart(ax, METHODS, rates, [COLORS[m] for m in METHODS], "Success rate (%)",
               "Objective 4 — convergence under controlled curvature stress",
               "12 test cases (root position x concavity x curvature strength); "
               "tol=1e-8, max 100 iterations.", value_fmt="{:.0f}%")
    ax.set_ylim(0, 115)
    fig.tight_layout()
    fig.savefig(out_dir / "04_stress_success_rate.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def plot_stress_work_by_curvature(records, out_dir):
    strengths = ["weak", "strong"]
    fig, ax = plt.subplots(figsize=(9.5, 5.5))
    n_methods = len(METHODS)
    width = 0.8 / n_methods
    x = range(len(strengths))
    for i, method in enumerate(METHODS):
        means = []
        for strength in strengths:
            rows = [r["work"] for r in records if r["method"] == method
                    and r["curvature"] == strength and r["converged"]]
            means.append(sum(rows) / len(rows) if rows else 0)
        offsets = [xi + (i - (n_methods - 1) / 2) * width for xi in x]
        bars = ax.bar(offsets, means, width=width * 0.9, color=COLORS[method], label=method, zorder=3)
        for bar, value in zip(bars, means):
            if value > 0:
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                        f"{value:.1f}", ha="center", va="bottom", fontsize=7.5, color=SECONDARY_INK)
    _style_axis(ax)
    ax.set_xticks(list(x))
    ax.set_xticklabels([s.capitalize() + " curvature" for s in strengths])
    ax.set_ylim(0, ax.get_ylim()[1] * 1.08)
    ax.set_ylabel("Mean work  =  Nf + lambda*Nf'  (lambda=1)", fontsize=10.5)
    ax.set_title("Objective 4 — work under weak vs. strong curvature", loc="left",
                  fontsize=13, color=INK, pad=45)
    ax.legend(frameon=False, fontsize=9, ncol=6, loc="lower center",
              bbox_to_anchor=(0.5, 1.0), columnspacing=1.4)
    ax.text(0, -0.14, "Mean over converged cases only; a method missing a bar failed to "
                       "converge on every case at that strength.",
            transform=ax.transAxes, fontsize=8.5, color=MUTED)
    fig.tight_layout()
    fig.savefig(out_dir / "05_stress_work_by_curvature.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def plot_stress_grid_heatmap(records, out_dir):
    cases = list(dict.fromkeys(r["case"] for r in records))
    grid = [[1 if any(r["case"] == case and r["method"] == method and r["converged"]
                       for r in records) else 0
             for method in METHODS] for case in cases]

    fig, ax = plt.subplots(figsize=(9, 7))
    cmap = matplotlib.colors.ListedColormap([CRITICAL, GOOD])
    ax.imshow(grid, cmap=cmap, vmin=0, vmax=1, aspect="auto")
    for i in range(len(cases)):
        for j in range(len(METHODS)):
            ax.text(j, i, "OK" if grid[i][j] else "FAIL", ha="center", va="center",
                    fontsize=8, color="white", fontweight="bold")
    ax.set_xticks(range(len(METHODS)))
    ax.set_xticklabels(METHODS, rotation=30, ha="right")
    ax.set_yticks(range(len(cases)))
    ax.set_yticklabels([c.replace("root=", "").replace(",concavity=", " / ")
                         .replace(",curvature=", " / ") for c in cases], fontsize=8.5)
    ax.set_xticks([x - 0.5 for x in range(1, len(METHODS))], minor=True)
    ax.set_yticks([y - 0.5 for y in range(1, len(cases))], minor=True)
    ax.grid(which="minor", color=SURFACE, linewidth=2)
    ax.tick_params(which="minor", length=0)
    for side in ax.spines.values():
        side.set_visible(False)
    ax.set_title("Objective 4 — convergence per test case (position / concavity / curvature)",
                 loc="left", fontsize=13, color=INK, pad=14)
    fig.tight_layout()
    fig.savefig(out_dir / "06_stress_grid_heatmap.png", dpi=200, bbox_inches="tight")
    plt.close(fig)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("examples/plots"))
    args = parser.parse_args(argv)
    args.output_dir.mkdir(parents=True, exist_ok=True)

    bench = benchmark_records()
    plot_benchmark_metric(bench, "iterations", "Mean iterations",
                           "Objective 2 — mean iterations across 13 benchmark problems",
                           "stop=residual, tol=1e-10.", "01_iterations_by_method.png", args.output_dir)
    plot_benchmark_metric(bench, "function_evaluations", "Mean f(x) evaluations",
                           "Objective 2 — mean function evaluations across 13 benchmark problems",
                           "stop=residual, tol=1e-10; counts actual cached evaluations.",
                           "02_function_evals_by_method.png", args.output_dir)
    plot_convergence_curve(args.output_dir)

    stress = stress_records()
    plot_stress_success_rate(stress, args.output_dir)
    plot_stress_work_by_curvature(stress, args.output_dir)
    plot_stress_grid_heatmap(stress, args.output_dir)

    print(f"Saved 6 charts to {args.output_dir}")


if __name__ == "__main__":
    main()
