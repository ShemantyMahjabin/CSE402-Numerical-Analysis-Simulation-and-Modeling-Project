"""Orchestrates the classical, base, and improved root finders.

See ALGORITHMS.md for source locations and resolutions of paper
inconsistencies. The per-method logic itself lives in classical.py
(bisection/false-position primitives), base.py (blended candidate
selection), and improved.py (the Newton refinement).
"""

from dataclasses import asdict, dataclass
import math
from typing import Callable, Optional

from .adaptive import adaptive_step, safeguarded_step
from .base import candidates_for, select_and_intersect
from .classical import opposite
from .improved import newton_step


@dataclass(frozen=True)
class Step:
    iteration: int
    input_a: float
    input_b: float
    midpoint: Optional[float]
    false_position: Optional[float]
    newton: Optional[float]
    selected: str
    root: float
    f_root: float
    residual: float
    step_size: float
    error: float
    a: float
    b: float
    newton_status: str
    weights: str = ""


@dataclass(frozen=True)
class Result:
    method: str
    root: float
    f_root: float
    residual: float
    error: float
    a: float
    b: float
    iterations: int
    function_evaluations: int
    derivative_evaluations: int
    converged: bool
    reason: str
    stopping: str
    history: tuple[Step, ...]

    def to_dict(self):
        return asdict(self)


def solve(f: Callable[[float], float], a: float, b: float, *,
          method: str = "base", df: Optional[Callable[[float], float]] = None,
          tol: float = 1e-7, max_iterations: int = 100,
          stopping: str = "paper") -> Result:
    """Find one real root in a continuous, sign-changing interval.

    method: base, improved, bisection, false-position, adaptive, or
            safeguarded. adaptive and safeguarded are project extensions
            (see ALGORITHMS.md) that replace base's/improved's hard
            candidate selection with a residual-weighted blend; safeguarded
            adds a Newton term to adaptive's midpoint/false-position blend.
    stopping: paper (base/adaptive residual, improved/safeguarded
              residual+step), residual, step-residual, or bracket-residual.
    An analytic derivative is required for improved and safeguarded. Domain
    errors in f are reported; unusable Newton steps are skipped without
    losing the bracket.
    Nonconvergence returns a Result with converged=False, never silent success.
    """
    if method not in {"base", "improved", "bisection", "false-position", "adaptive", "safeguarded"}:
        raise ValueError("Unknown method")
    if stopping not in {"paper", "residual", "step-residual", "bracket-residual"}:
        raise ValueError("Unknown stopping rule")
    if not callable(f) or (method in ("improved", "safeguarded") and not callable(df)):
        raise ValueError("A callable f is required; improved and safeguarded also require df")
    a, b, tol = float(a), float(b), float(tol)
    if not (math.isfinite(a) and math.isfinite(b) and a < b):
        raise ValueError("Bounds must be finite and satisfy a < b")
    if not math.isfinite(b - a):
        raise ValueError("Interval width must be finite; rescale the problem")
    if not math.isfinite(tol) or tol <= 0:
        raise ValueError("Tolerance must be finite and positive")
    if isinstance(max_iterations, bool) or not isinstance(max_iterations, int) or max_iterations < 1:
        raise ValueError("max_iterations must be a positive integer")
    rule = (("step-residual" if method in ("improved", "safeguarded") else "residual")
            if stopping == "paper" else stopping)
    cache = {}
    function_evaluations = 0
    derivative_evaluations = 0
    history = []

    def evaluate(x):
        nonlocal function_evaluations
        if x not in cache:
            function_evaluations += 1
            try:
                value = float(f(x))
            except (ValueError, TypeError, ArithmeticError) as exc:
                raise ValueError(f"Cannot evaluate f at x={x:.17g}: {exc}") from exc
            if not math.isfinite(value):
                raise ValueError(f"f({x:.17g}) must be finite")
            cache[x] = value
        return cache[x]

    def finish(root, fr, error, converged, reason):
        return Result(method, root, fr, abs(fr), error, a, b, len(history),
                      function_evaluations, derivative_evaluations, converged,
                      reason, rule, tuple(history))

    fa, fb = evaluate(a), evaluate(b)
    if fa == 0 or fb == 0:
        root = a if fa == 0 else b
        a = b = root
        return finish(root, 0.0, 0.0, True, "exact endpoint root")
    if not opposite(fa, fb):
        raise ValueError("Root not bracketed: f(a) and f(b) must have opposite signs")
    previous = a  # Appendix B: rold = xl.
    for iteration in range(1, max_iterations + 1):
        input_a, input_b = a, b
        newton = None
        newton_status = "not used"
        weights = ""

        if method == "adaptive":
            (root, fr, selected, a, b, fa, fb, midpoint, false_position,
             weights) = adaptive_step(a, b, fa, fb, evaluate)
        elif method == "safeguarded":
            # Unlike improved's sequential Newton step, all three candidates
            # here are generated from the SAME current bracket [a, b] and
            # blended together; see adaptive.py.
            derivative_evaluations += 1
            (root, fr, selected, a, b, fa, fb, midpoint, false_position,
             newton, newton_status, weights) = safeguarded_step(a, b, fa, fb, evaluate, df)
        else:
            candidates, midpoint, false_position = candidates_for(method, a, b, fa, fb, evaluate)
            root, fr, selected, a, b, fa, fb = select_and_intersect(a, b, fa, fb, candidates)

            if method == "improved" and fr != 0:
                # Appendix B uses ONE Newton step starting at the tightened LEFT
                # endpoint each iteration, not an independent Newton trajectory.
                derivative_evaluations += 1
                a, b, fa, fb, root, fr, selected, newton, newton_status = newton_step(
                    a, b, fa, fb, root, fr, selected, evaluate, df)

        step_size = abs(root - previous)
        error = abs(fr)
        if rule == "step-residual":
            error += step_size
        elif rule == "bracket-residual":
            error += b - a
        history.append(Step(iteration, input_a, input_b, midpoint, false_position,
                            newton, selected, root, fr, abs(fr), step_size, error,
                            a, b, newton_status, weights))
        if fr == 0:
            return finish(root, fr, error, True, "exact root (floating-point evaluation)")
        if error < tol:
            return finish(root, fr, error, True, "tolerance reached")
        if (a == input_a and b == input_b) or math.nextafter(a, b) == b:
            return finish(root, fr, error, False, "floating-point resolution exhausted")
        previous = root
    return finish(root, fr, error, False, "maximum iterations reached")
