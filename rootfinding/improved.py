"""Newton-Raphson refinement added on top of the base blend.

Implements the single-Newton-step improvement from the 2021 paper
(Sabharwal, *An Iterative Hybrid Algorithm for Roots of Non-Linear
Equations*, Appendix B). See ALGORITHMS.md, "Improved: add the Newton
candidate", for why the step starts at the tightened left endpoint and why
it is only accepted when it improves both endpoint residuals.
"""

import math

from .classical import bracket


def newton_step(a, b, fa, fb, root, fr, selected, evaluate, df):
    """Attempt one Newton step from the tightened left endpoint `a`.

    Returns the possibly-updated (a, b, fa, fb, root, fr, selected), the
    raw Newton candidate (or None), a human-readable status string, and the
    number of derivative evaluations attempted (always 1 here).
    """
    newton = None
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
                    if abs(fn) < min(abs(fa), abs(fb)):
                        root, fr, selected = newton, fn, "newton"
                        a, b, fa, fb = bracket(a, b, fa, fb, newton, fn)
                        newton_status = "accepted"
                    else:
                        newton_status = "rejected: residual did not improve both endpoints"
    except (ValueError, TypeError, ArithmeticError) as exc:
        newton_status = f"skipped: {exc}"
    return a, b, fa, fb, root, fr, selected, newton, newton_status
