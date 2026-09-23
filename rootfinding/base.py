"""Blended bisection / false-position candidate selection.

Implements the per-iteration candidate generation, selection, and bracket
intersection from the 2019 paper's Algorithm 3. See ALGORITHMS.md, "Base:
bisection and false-position blend", for the equations and the worked
example this logic reproduces. Also used, unmodified, as the first half of
each improved-method iteration (see improved.py).
"""

from .classical import bracket, false_position as false_position_candidate


def candidates_for(method, a, b, fa, fb, evaluate):
    """Generate this iteration's midpoint and/or false-position candidates."""
    candidates = []
    midpoint = false_position = None
    if method != "false-position":
        midpoint = a + (b - a) / 2
        candidates.append((midpoint, evaluate(midpoint), "bisection"))
    if method != "bisection":
        false_position = false_position_candidate(a, b, fa, fb)
        candidates.append((false_position, evaluate(false_position), "false-position"))
    return candidates, midpoint, false_position


def select_and_intersect(a, b, fa, fb, candidates):
    """Pick the smaller-residual candidate and intersect both candidate brackets.

    Ties favor false position, as in the papers. Both candidate brackets are
    computed and intersected even though only one candidate wins the
    residual comparison; see ALGORITHMS.md for why this matches the paper's
    worked example.
    """
    root, fr, selected = min(reversed(candidates), key=lambda item: abs(item[1]))
    if fr == 0:
        # Two candidates can be distinct exact roots; choose the winner
        # before intersecting their otherwise disjoint singleton brackets.
        return root, fr, selected, root, root, fr, fr
    brackets = [bracket(a, b, fa, fb, x, fx) for x, fx, _ in candidates]
    left = max(brackets, key=lambda interval: interval[0])
    right = min(brackets, key=lambda interval: interval[1])
    new_a, new_fa = left[0], left[2]
    new_b, new_fb = right[1], right[3]
    return root, fr, selected, new_a, new_b, new_fa, new_fb
