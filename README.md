# Numerical root finding: base project and improvement

Python implementation of the two supplied papers:

- **Base:** Chaman Lal Sabharwal, *Blended Root Finding Algorithm Outperforms Bisection and Regula Falsi Algorithms* (2019), Section 3, Algorithm 3. Source: [base-numeric.pdf](base-numeric.pdf).
- **Improvement:** Chaman Lal Sabharwal, *An Iterative Hybrid Algorithm for Roots of Non-Linear Equations* (2021), Section 3 and Appendix B. Source: [improvement-numeric.pdf](improvement-numeric.pdf).

The base method combines bisection and false position. The improved method adds a Newton–Raphson candidate. Both can run independently or in the same comparison. See [ALGORITHMS.md](ALGORITHMS.md) for the equations, source ambiguities, and explicit implementation choices.

## 1. Setup

Use **Python 3.9 or newer**. The program and tests use only the Python standard library; no packages, MATLAB, internet connection, or PDF reader are needed to run them.

Open a terminal in this project folder:

```bash
cd /Users/farihanisraq/Documents/4-1/Numeric/project
python3 --version
python3 main.py
```

On Windows, use `python` or `py` in place of `python3`, and change to your own project path.

The default run solves `x**2-x-2 = 0` on `[1, 4]`, using both methods with tolerance `1e-7`. Expected summary (spacing may differ):

```text
Problem         Method                        Root    |f(root)|  Iter f calls df calls Status
quadratic       base                             2   0.0000e+00     2       6        0 OK
quadratic       improved                         2   0.0000e+00     4      13        3 OK
```

Each summary row is followed by the stopping rule, error, final bracket, and termination reason. By default, each method uses its own paper's stopping rule; use a common `--stop` when comparing iteration counts.

## 2. Run without or with the improvement

**Without improvement:**

```bash
python3 main.py --mode base --example quadratic --tol 1e-5 --trace
```

This reproduces the base paper's two-iteration worked example:

| Iteration | Midpoint | False-position candidate | Selected root | Residual | Updated bracket |
|---|---:|---:|---:|---:|---|
| 1 | 2.5 | 1.5 | 1.5 | 1.25 | [1.5, 2.5] |
| 2 | 2 | 1.916666666667 | 2 | 0 | [2, 2] |

An exactly evaluated root is returned with a collapsed bracket; this final-bracket convention differs from the paper's display.

**With improvement:**

```bash
python3 main.py --mode improved --example cosine --stop residual --trace
```

Expected result: approximately `0.739085133231`, residual `2.5808e-11`, 2 iterations. The analytic derivative is included with every built-in example.

**Compare the base and improvement under the same stopping criterion:**

```bash
python3 main.py --mode both --example cosine --stop residual
```

Expected: base takes 5 iterations and improved takes 2, with both residuals below `1e-7`.

**Also compare classical bisection and false position:**

```bash
python3 main.py --mode all --example quadratic --tol 1e-5 --stop residual
```

| Method | Approximate root | Iterations | Actual f calls | Actual derivative calls |
|---|---:|---:|---:|---:|
| bisection | 2.00000190735 | 19 | 21 | 0 |
| false-position | 1.99999838939 | 15 | 17 | 0 |
| base | 2 | 2 | 6 | 0 |
| improved | 2.0000000000007865 | 3 | 11 | 3 |

The improvement is not faster on every input. Here the base hits the exact root in two iterations. Counts also change with stopping criteria and floating-point rounding; these results do not assert universal superiority or reproduce all tables in the papers.

## 3. Supply your own input

Inputs are a real function `f(x)`, interval endpoints `a < b`, a positive tolerance, and an iteration limit. For improved mode, also supply its analytic derivative `f'(x)`.

Base mode needs no derivative:

```bash
python3 main.py --mode base --function 'x**3-2' --a 0 --b 2 --tol 1e-10
```

Expected root: approximately `1.259921049895`.

Improved mode:

```bash
python3 main.py --mode improved --function 'x-cos(x)' --derivative '1+sin(x)' --a 0 --b 1 --tol 1e-7 --stop residual
```

Both modes, using identical input and stopping rule:

```bash
python3 main.py --mode both --function 'x**3+log(x)' --derivative '3*x**2+1/x' --a 0.1 --b 2 --stop residual --trace
```

Expected root: approximately `0.70470949`.

Expression syntax:

- Use `x` as the variable, `**` for powers, and explicit multiplication (`2*x`, not `2x`).
- Supported operators: `+`, `-`, `*`, `/`, `**`, parentheses, unary signs.
- Functions: `sin`, `cos`, `tan`, `asin`, `acos`, `atan`, `sinh`, `cosh`, `tanh`, `exp`, `log`, `log10`, `sqrt`, `expm1`, `log1p`, `abs`. Each takes one argument.
- `log` is the natural logarithm; angles are in radians. Constants: `pi`, `e`.
- Write `sin(x)`, not `math.sin(x)`. Quote expressions so the shell preserves them. On Windows Command Prompt use double quotes.
- Write an equation `g(x)=h(x)` as the expression `g(x)-h(x)`.

The function must be continuous and finite on the interval, with opposite signs at its endpoints (or an exact endpoint root). A sign change across a discontinuity does not establish a root. Continuity and correctness of the supplied derivative cannot be checked automatically. The program finds **one** root, and does not search for a bracket or all roots. An even-multiplicity root may have no sign-changing bracket.

## 4. Options and outputs

```bash
python3 main.py --help
python3 main.py --list-examples
```

| Option | Meaning / default |
|---|---|
| `--mode` | `base`, `improved`, `both` (default), `all`, `bisection`, `false-position`, `adaptive`, `safeguarded`, `extended` |
| `--example` | Built-in problem; default `quadratic` |
| `--function` | Custom expression; requires `--a` and `--b` |
| `--derivative` | Required for custom `improved`, `both`, and `all` runs |
| `--a`, `--b` | Custom bounds; optionally override a built-in example's bounds |
| `--tol` | Positive error threshold; default `1e-7` |
| `--max-iterations` | Positive iteration limit; default `100` |
| `--stop` | `paper` (default), `residual`, `step-residual`, `bracket-residual` |
| `--trace` | Print every iteration and Newton acceptance/rejection reason |
| `--output-dir` | Save machine-readable results and iteration history |
| `--benchmark` | Run all 13 examples; cannot be combined with custom inputs |

Stopping rules use strict `< tol`:

| Rule | Measured error |
|---|---|
| `residual` | `abs(f(root))` |
| `step-residual` | `abs(f(root)) + abs(root - previous_root)` |
| `bracket-residual` | `abs(f(root)) + (b-a)` |
| `paper` | Residual for base/classical methods; step-residual for improved (Appendix B) |

The initial `previous_root` is the original left endpoint. An exact floating-point evaluation `f(root) == 0` terminates immediately for every rule, even if the combined error is still above tolerance. The termination reason makes this explicit. A small residual is not the same as a guaranteed small distance to the true root. Use the bracket to assess positional uncertainty, assuming continuity and a valid sign change.

Save results:

```bash
python3 main.py --mode both --example cosine --stop residual --trace --output-dir outputs/cosine
```

This creates:

- **`results.json`**: a list of results, including the function, derivative, original bounds, tolerance, stopping rule, final root, signed function value, residual, measured error, bracket, iteration count, actual evaluation counts, convergence flag, reason, and full history.
- **`iterations.csv`**: one row per iteration with problem, method, input bounds, midpoint, false-position candidate, Newton candidate, selected method, root, signed function value, residual, step size, measured error, new bounds, and Newton status. Blank candidate cells mean that candidate was not generated. An endpoint root has no iteration rows.

Existing `results.json` and `iterations.csv` in the selected output directory are overwritten. Use separate directories to keep separate runs. Example reports from actual runs are included in [examples/quadratic](examples/quadratic/) and [examples/benchmark](examples/benchmark/).

Function values are cached for the entire solve. `f calls` counts actual evaluations, including initial endpoints; `df calls` counts attempted derivative evaluations, including unsuccessful attempts. These are measured counts, not a theoretical constant multiplied by the number of iterations.

Exit codes: `0` = all solves converged, `1` = iteration limit or floating-point resolution reached, `2` = invalid input or output-file error. A nonconverged result is labeled `NOT CONVERGED` and is still available for inspection/export.

## 5. Run the benchmark and tests

```bash
python3 main.py --benchmark --mode both --stop residual --output-dir outputs/benchmark
python3 -m unittest discover -s tests -v
```

The benchmark includes ten usable examples from the base paper and three from Tables 3–5 of the improvement paper. All 26 base/improved runs should converge at the default tolerance. Some original table brackets are invalid; corrections and the omitted polynomial are explained in [ALGORITHMS.md](ALGORITHMS.md).

Tests check the paper's worked example and classical iteration counts, an independently calculated Newton update, reference roots, bracket preservation and contraction, stopping criteria, function-call accounting, invalid inputs, Newton fallback, floating-point exhaustion, and CLI exports/error reporting.

## 6. Use from another Python file

```python
from rootfinding import solve

def f(x):
    return x*x - 2

def df(x):
    return 2*x

use_improvement = True  # Set False to run the base algorithm.
result = solve(
    f, 0, 2,
    method="improved" if use_improvement else "base",
    df=df if use_improvement else None,
    tol=1e-10,
    stopping="residual",
    max_iterations=100,
)
print(result.root)        # Approximately 1.41421356237
print(result.converged)
print(result.iterations)
print(result.to_dict())   # Includes the complete iteration history.
```

## 7. Extensions: adaptive blending and controlled stress-testing

Beyond reproducing the two papers, this project adds its own extensions
(see the project proposal, "Beyond Hard Selection: Adaptive Blending of
Root-Finding Methods"):

- **`--mode adaptive`**: instead of hard-selecting whichever of the
  bisection midpoint or false-position point has the smaller residual
  (what `base` does), blend both with residual-adaptive weights and take
  that blend as the next iterate.
- **`--mode safeguarded`**: the same idea with a third Newton-Raphson
  candidate folded in, included only when it is safe and lies inside the
  current bracket. Requires `--derivative`/`df`, like `improved`.
- **`--mode extended`** runs both; **`--mode all`** now also includes them
  alongside the classical and paper methods.

```bash
python3 main.py --mode extended --example cosine --stop residual --trace
```

See ALGORITHMS.md for the weighting formula and why both extensions reuse
the base algorithm's bracket-intersection safety net.

**Proposal-proof charts** (`plot_results.py`): generates PNG charts for
slides/reports, backing the above with data (this script alone needs
matplotlib; everything else stays standard-library-only):

```bash
python3 plot_results.py --output-dir examples/plots
```

Produces six images: mean iterations and function evaluations per method
over the 13 benchmark problems, a log-scale residual-decay curve for all
six methods on one example, stress-test success rate, mean work by
curvature strength, and a pass/fail heatmap over the full stress-test
grid. See [examples/plots](examples/plots/) for a saved set.

**Controlled stress-test** (`stress_test.py`): a separate script that
builds a parameterized family of test functions varying root position,
concavity direction, and curvature strength, and runs every method on all
of them under identical settings:

```bash
python3 stress_test.py --tol 1e-8 --output-dir outputs/stress
```

It reports success rate, mean iterations, actual `f`/`f'` call counts, a
combined work metric `Nf + lambda*Nf'` (`--lambda`, default `1.0`), mean
bracket contraction, and runtime per method, and can save per-case records
and the summary as JSON/CSV. Classical `false-position` is expected to
underperform (even fail to converge within the iteration budget) on the
strongly asymmetric cases in this grid — that is the known pathology the
base, improved, adaptive, and safeguarded methods are all designed to
avoid, not a bug in the harness.

## Project files

```text
main.py                    Command-line interface
stress_test.py             Controlled stress-test harness (Objective 4)
plot_results.py            PNG charts for slides/reports (needs matplotlib)
rootfinding/solver.py      Orchestrates validation, iteration, and stopping rules
rootfinding/classical.py   Bisection and false-position primitives
rootfinding/base.py        Blended candidate selection (2019 Algorithm 3)
rootfinding/improved.py    Newton-Raphson refinement (2021 Appendix B)
rootfinding/adaptive.py    Adaptive/safeguarded blend extensions (project proposal)
rootfinding/testfunctions.py  Parameterized stress-test function family
rootfinding/expressions.py  Restricted arithmetic-expression interpreter
rootfinding/problems.py    Built-in functions, derivatives, and intervals
tests/                     Algorithm and command-line tests
examples/                  Saved results from verified runs
README.md                  Setup, commands, input/output guide
ALGORITHMS.md              Paper mapping and implementation decisions
```
