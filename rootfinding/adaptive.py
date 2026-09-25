"""Adaptive weighted blends beyond hard candidate selection.

Implements the two extensions proposed in the project's "Beyond Hard
Selection: Adaptive Blending of Root-Finding Methods" proposal, on top of
the base blend in base.py and the classical primitives in classical.py:

- `adaptive_step` (Extension A): instead of hard-selecting whichever of the
  bisection midpoint or false-position point has the smaller residual (as
  base.py does), form a convex combination of both, weighted by their
  relative residuals, and take that as the next iterate.
- `safeguarded_step` (Extension B): the same idea extended with a third,
  Newton-Raphson candidate computed from the current left endpoint. The
  Newton candidate is included in the blend only when it is safe (finite,
  nonzero derivative) and lies strictly inside the current bracket;
  otherwise its weight is zero and the step reduces exactly to Extension A.

Both functions reuse `base.select_and_intersect` to fold every candidate's
own sub-bracket into the next bracket, exactly as the base algorithm does.
This is not an optional safety net: stress-testing (rootfinding/
testfunctions.py, stress_test.py) showed that on strongly asymmetric
functions the false-position candidate can sit almost exactly on top of
one endpoint (a residual near zero, but almost no progress toward the
root). A blend that only trusted per-candidate residuals to also drive the
*bracket* update stagnated on those cases; using the full base
intersection guarantees the bracket still contracts by at least half each
iteration (the bisection contribution) regardless of how skewed the
weights are, while the weighted point is still used as the reported root
and as one further tightening candidate. See ALGORITHMS.md.

Weighting itself uses inverse-residual weighting: for candidates with
residuals r_1..r_n (all > 0; an exact-zero residual is handled as an
immediate root via select_and_intersect, before any weighting happens),
the weight of candidate i is

    w_i = (1/r_i) / sum_j(1/r_j)

so a candidate with a smaller residual is trusted more, and the weights
always sum to 1.
"""

import math

from .base import select_and_intersect
from .classical import bracket, false_position as false_position_candidate


def _weights(residuals):
    """Inverse-residual weights for a list of strictly positive residuals."""
    inverse = [1.0 / r for r in residuals]
    total = sum(inverse)
    return [w / total for w in inverse]


def adaptive_step(a, b, fa, fb, evaluate):
    """Extension A: weighted blend of the midpoint and false-position point.

    Returns (root, f_root, selected, new_a, new_b, new_fa, new_fb,
    midpoint, false_position, weights_description).
    """
    midpoint = a + (b - a) / 2
    fm = evaluate(midpoint)
    false_position = false_position_candidate(a, b, fa, fb)
    fs = evaluate(false_position)

    candidates = [(midpoint, fm, "bisection"), (false_position, fs, "false-position")]
    hard_root, hard_fr, hard_selected, left, right, f_left, f_right = select_and_intersect(
        a, b, fa, fb, candidates)
    if hard_fr == 0:
        return (hard_root, hard_fr, hard_selected, left, right, f_left, f_right,
                midpoint, false_position, "exact candidate")

    w_m, w_s = _weights([abs(fm), abs(fs)])
    weights = f"m={w_m:.4f},s={w_s:.4f}"
    x_blend = min(right, max(left, w_m * midpoint + w_s * false_position))

    fx = evaluate(x_blend)
    if fx == 0:
        return (x_blend, fx, "adaptive-blend", x_blend, x_blend, fx, fx,
                midpoint, false_position, weights)
    new_a, new_b, new_fa, new_fb = bracket(left, right, f_left, f_right, x_blend, fx)
    return (x_blend, fx, "adaptive-blend", new_a, new_b, new_fa, new_fb,
            midpoint, false_position, weights)


def safeguarded_step(a, b, fa, fb, evaluate, df):
    """Extension B: three-way blend of midpoint, false-position, and Newton.

    The Newton candidate is computed from the current left endpoint `a`
    (not a post-selection tightened endpoint, unlike improved.py), so all
    three candidates come from the same bracket every iteration. It is
    included in the blend only if the derivative is safe and the candidate
    lies strictly inside (a, b); otherwise its weight is 0 and this reduces
    to the same blend as `adaptive_step`.

    Returns (root, f_root, selected, new_a, new_b, new_fa, new_fb,
    midpoint, false_position, newton, newton_status, weights_description).
    """
    midpoint = a + (b - a) / 2
    fm = evaluate(midpoint)
    false_position = false_position_candidate(a, b, fa, fb)
    fs = evaluate(false_position)

    newton = None
    fn = None
    newton_status = "not used"
    try:
        derivative = float(df(a))
        if not math.isfinite(derivative) or derivative == 0:
            newton_status = "skipped: zero or nonfinite derivative"
        else:
            proposal = a - fa / derivative
            if not math.isfinite(proposal):
                newton_status = "skipped: nonfinite Newton candidate"
            else:
                newton = proposal
                if not a < newton < b:
                    newton_status = "rejected: outside open bracket"
                else:
                    fn = evaluate(newton)
                    newton_status = "accepted: exact root" if fn == 0 else "included in blend"
    except (ValueError, TypeError, ArithmeticError) as exc:
        newton_status = f"skipped: {exc}"

    candidates = [(midpoint, fm, "bisection"), (false_position, fs, "false-position")]
    newton_included = fn is not None and newton_status in ("accepted: exact root", "included in blend")
    if newton_included:
        candidates.append((newton, fn, "newton"))

    hard_root, hard_fr, hard_selected, left, right, f_left, f_right = select_and_intersect(
        a, b, fa, fb, candidates)
    if hard_fr == 0:
        return (hard_root, hard_fr, hard_selected, left, right, f_left, f_right,
                midpoint, false_position, newton, newton_status, "exact candidate")

    if newton_included:
        w_m, w_s, w_n = _weights([abs(fm), abs(fs), abs(fn)])
        x_blend = w_m * midpoint + w_s * false_position + w_n * newton
    else:
        w_m, w_s = _weights([abs(fm), abs(fs)])
        w_n = 0.0
        x_blend = w_m * midpoint + w_s * false_position
    weights = f"m={w_m:.4f},s={w_s:.4f},n={w_n:.4f}"
    x_blend = min(right, max(left, x_blend))

    fx = evaluate(x_blend)
    if fx == 0:
        return (x_blend, fx, "safeguarded-blend", x_blend, x_blend, fx, fx,
                midpoint, false_position, newton, newton_status, weights)
    new_a, new_b, new_fa, new_fb = bracket(left, right, f_left, f_right, x_blend, fx)
    return (x_blend, fx, "safeguarded-blend", new_a, new_b, new_fa, new_fb,
            midpoint, false_position, newton, newton_status, weights)
