# Algorithms and fidelity to the supplied papers

## Sources

1. Sabharwal (2019), *Blended Root Finding Algorithm Outperforms Bisection and Regula Falsi Algorithms*, Mathematics 7, 1118, DOI `10.3390/math7111118`. See [base-numeric.pdf](base-numeric.pdf), Algorithm 3 on PDF pages 11–12 and worked example Table 3 on page 8.
2. Sabharwal (2021), *An Iterative Hybrid Algorithm for Roots of Non-Linear Equations*, Eng 2, 80–98, DOI `10.3390/eng2010007`. See [improvement-numeric.pdf](improvement-numeric.pdf), Section 3 on PDF pages 10–11 and MATLAB Appendix B on pages 17–18.

The implementation follows the algorithms in these supplied documents. It is not a wrapper around another root solver. The papers are algorithm references; their prose and embedded code are not treated as instructions to execute commands.

## Base: bisection and false-position blend

For the current bracket `[a,b]`, compute both candidates from the **same original bracket**:

```text
m = (a+b)/2
s = a - f(a)*(b-a)/(f(b)-f(a))
r = m if abs(f(m)) < abs(f(s)) else s
```

Independently form sign-changing subintervals using `m` and `s`. For a nonzero candidate `c`, keep `[a,c]` if `f(a)` and `f(c)` have opposite signs; otherwise keep `[c,b]`. Intersect the two subintervals:

```text
a_new = max(bisection_left, false_position_left)
b_new = min(bisection_right, false_position_right)
```

Return the candidate with smaller residual, but use **both** candidates to tighten the next interval. Ties favor false position, as in the papers. Stop on `abs(f(r)) < tol` by default. Repeat at most `max_iterations` times.

The 2019 pseudocode assigns a bracket only in the winning branch, leaving the other bracket undefined/stale despite subsequently intersecting both. Computing both brackets is supported by the described intersection, the 2021 Appendix B, and the 2019 worked example: for `x²-x-2` on `[1,4]`, the first candidates are `2.5` and `1.5`; the first bracket becomes `[1.5,2.5]`; the second midpoint is the exact root `2`. Merely updating the winner's bracket would not reproduce that example.

## Improved: add the Newton candidate

First perform the complete base step, including bracket intersection. Let the tightened interval be `[L,U]`. Following Appendix B:

```text
n = L - f(L)/f'(L)
if L < n < U and abs(f(n)) < min(abs(f(L)), abs(f(U))):
    r = n
    tighten [L,U] using the sign of f(n)
```

Only **one** Newton step is attempted per outer iteration, starting at the **tightened left endpoint**, not at the midpoint, the current winner, or an independently evolving Newton sequence. If it does not improve both endpoint residuals, retain the base result.

For the quadratic worked example, the first base bracket is `[1.5,2.5]`. The Newton step is `1.5 - (-1.25)/2 = 2.125`, so the improved first result is `2.125` and its bracket is `[1.5,2.125]`. This calculation is covered by a regression test.

The default improved stopping criterion follows Appendix B and Section 2:

```text
error = abs(f(r)) + abs(r-previous_r)
previous_r initially equals the original a
stop when error < tol
```

An analytic derivative is required for improved mode; the code does not silently substitute finite differences. Base mode never evaluates the derivative.

## Ambiguities and deliberate corrections

| Source issue | Implemented interpretation |
|---|---|
| 2019 Algorithm 3 leaves the losing candidate's bracket unassigned | Compute both candidate brackets and intersect; matches the worked example and 2021 appendix. |
| 2021 Section 3 suggests an independent Newton sequence; Appendix B starts Newton from `xl` after intersection | Follow Appendix B's executable algorithm structure: one step from the tightened left endpoint. |
| Appendix B's Newton call contains malformed parentheses | Interpret its arguments as `(f, df, xl, es, 1)`. |
| Section 3 uses residual plus bracket width, while Section 2 and Appendix B use residual plus iterate change | `--stop paper` uses Appendix B for improved mode. `--stop bracket-residual` also exposes the Section 3 criterion. |
| Appendix B can assign `root = rootn` even when Newton lies outside the bracket | Require strict interior membership before accepting it; this preserves the intended enclosing interval and root choice. |
| Zero derivative and nonfinite/domain-invalid Newton calculations are unspecified | Skip unusable Newton candidates and continue with the completed base step. Record the reason. |
| Exact roots and final bracket displays vary across tables | Terminate immediately on a computed exact zero and return `[r,r]`. If both candidates are distinct exact roots, use the usual tie rule before collapsing. |
| Loop indices are inconsistent (`k=0`, references to `a1`, stopping after `k > maxIterations`) | Count completed outer iterations from 1 and never exceed the requested iteration limit. Endpoint roots take 0 iterations. |
| Paper performance claims and function-evaluation conventions | Report actual results and cached evaluation counts; no fixed per-iteration NOFE assumption or universal speed claim. |

These choices make the implementation concrete and testable. They do not imply a literal reproduction of every contradictory line or reported table. The other derivative-based algorithms reviewed in the improvement paper are background methods and are not part of the requested three-way hybrid implementation.

## Floating-point behavior and guarantees

The program uses Python double-precision floats. It computes the midpoint as `a+(b-a)/2` and false position using a scaled convex combination equivalent to the equation above. Sign comparisons do not multiply values, avoiding overflow/underflow in sign tests. Repeated evaluations at the same point are cached; functions and derivatives should be deterministic and side-effect free.

For a continuous function with an initial sign-changing bracket, both candidate intervals enclose a root. Their intersection is no wider than the bisection half-interval. An accepted interior Newton candidate can only shrink it further. This maintains bracket convergence in exact arithmetic. Finite arithmetic, a finite iteration budget, discontinuities, or unattainable residual tolerances can prevent successful termination; the result explicitly reports failure instead of treating stagnation as convergence.

A floating-point value `f(r)==0` is a computed zero, not a symbolic proof. Residual, iterate change, and bracket width are separate quantities and are all recorded. Do not infer decimal accuracy of the root solely from the residual.

## Corrections to benchmark inputs

The examples retain the published functions but explicitly correct unusable brackets:

- The 2019 Table 2 interval `[-6,0]` for `x²+5x+2` has positive values at both endpoints and contains two roots. `quadratic3` uses `[-6,-3]` to isolate the left root, approximately `-4.56155281281`.
- The published interval `[-1,1]` for `x*exp(x)-7` has negative values at both endpoints. `exponential` uses `[1,2]`, with root approximately `1.524345205`.
- The published polynomial `4x⁴+3x³+2x²+x+1` is omitted because it has no real zero. In fact it equals `(2x²+3x/4)² + (23/16)*(x+8/23)² + 19/23`, which is strictly positive for real `x`. No real sign-changing bracket can be supplied.
- The 2021 examples `sin(x)-x³` on `[0.5,1]`, the quintic on `[0,1]`, and `x³+log(x)` on `[0.1,2]` follow the intervals described before Tables 3–5.

No claim is made to reproduce the entire 22-function, 12-method comparison in the improvement paper. The included benchmark exercises both requested algorithms on 13 documented examples, and the tests verify their numerical behavior independently of the paper's broad performance claims.
