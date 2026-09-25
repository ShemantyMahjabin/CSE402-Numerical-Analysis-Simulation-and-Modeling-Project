import math
import unittest

from rootfinding import solve
from rootfinding.expressions import expression
from rootfinding.problems import PROBLEMS


class PaperAlgorithmTests(unittest.TestCase):
    def test_base_worked_example(self):
        r = solve(lambda x: x*x-x-2, 1, 4, tol=1e-5)
        self.assertTrue(r.converged)
        self.assertEqual(r.iterations, 2)
        self.assertEqual(r.root, 2)
        first, second = r.history
        self.assertEqual(first.midpoint, 2.5)
        self.assertEqual(first.false_position, 1.5)
        self.assertEqual((first.root, first.a, first.b), (1.5, 1.5, 2.5))
        self.assertEqual(second.midpoint, 2)
        self.assertAlmostEqual(second.false_position, 23/12)

    def test_improvement_appendix_first_iteration(self):
        r = solve(lambda x: x*x-x-2, 1, 4, method="improved",
                  df=lambda x: 2*x-1, max_iterations=1)
        s = r.history[0]
        # Intersection [1.5, 2.5], Newton from LEFT: 1.5 - (-1.25)/2.
        self.assertEqual(s.newton, 2.125)
        self.assertEqual((s.root, s.a, s.b), (2.125, 1.5, 2.125))
        self.assertEqual(s.selected, "newton")
        self.assertEqual(s.error, abs(2.125**2-2.125-2) + 1.125)
        self.assertFalse(r.converged)

    def test_classical_reference_counts(self):
        for method, count in [("bisection", 19), ("false-position", 15)]:
            r = solve(lambda x: x*x-x-2, 1, 4, method=method, tol=1e-5)
            self.assertEqual(r.iterations, count)

    def test_examples_and_bracket_invariants(self):
        for name, p in PROBLEMS.items():
            f, df = expression(p.function), expression(p.derivative)
            for method in ("base", "improved"):
                with self.subTest(name=name, method=method):
                    r = solve(f, p.a, p.b, df=df, method=method, stopping="residual", tol=1e-10)
                    self.assertTrue(r.converged, r.reason)
                    self.assertLess(r.residual, 1e-10)
                    for s in r.history:
                        self.assertLessEqual(s.input_a, s.a)
                        self.assertLessEqual(s.a, s.root)
                        self.assertLessEqual(s.root, s.b)
                        self.assertLessEqual(s.b, s.input_b)
                        self.assertLessEqual(f(s.a) * f(s.b), 0)
                        self.assertLessEqual(s.b-s.a, (s.input_b-s.input_a)/2 + 1e-14)

    def test_known_roots(self):
        for method in ("base", "improved"):
            r = solve(lambda x: x*x-2, 0, 2, method=method, df=lambda x: 2*x, tol=1e-12)
            self.assertAlmostEqual(r.root, math.sqrt(2), places=11)

    def test_two_distinct_exact_candidates(self):
        r = solve(lambda x: (x-0.25)*(x-0.5)**2, 0, 1)
        self.assertEqual(r.root, 0.25)
        self.assertEqual((r.a, r.b), (0.25, 0.25))

    def test_bad_derivatives_fall_back(self):
        for derivative in (lambda x: 0, lambda x: float("nan"), lambda x: 1e-300,
                           lambda x: 1/0):
            r = solve(lambda x: x*x-2, 0, 2, method="improved", df=derivative)
            self.assertTrue(r.converged)
            self.assertTrue(any(s.newton_status.startswith(("skipped", "rejected")) for s in r.history))

    def test_endpoint_and_invalid_inputs(self):
        self.assertEqual(solve(lambda x: x, 0, 1).iterations, 0)
        for a, b in [(1, 1), (2, 1), (float("nan"), 2), (float("-inf"), 2)]:
            with self.assertRaises(ValueError):
                solve(lambda x: x, a, b)
        for kwargs in ({"tol": 0}, {"tol": float("nan")}, {"max_iterations": 0},
                       {"max_iterations": 1.5}, {"method": "improved"}):
            with self.assertRaises(ValueError):
                solve(lambda x: x*x-2, 0, 2, **kwargs)
        with self.assertRaises(ValueError):
            solve(lambda x: x*x+1, -1, 1)
        with self.assertRaises(ValueError):
            solve(math.log, -1, 2)
        with self.assertRaises(ValueError):
            solve(lambda x: float("nan"), -1, 1)

    def test_sign_checks_do_not_underflow(self):
        r = solve(lambda x: 1e-200*(x-0.3), 0, 1, tol=1e-210)
        self.assertTrue(r.converged)
        self.assertAlmostEqual(r.root, 0.3)

    def test_float_resolution_and_iteration_cap(self):
        r = solve(lambda x: x*x-2, 1, 2, max_iterations=1, tol=1e-15)
        self.assertFalse(r.converged)
        self.assertEqual(r.reason, "maximum iterations reached")
        a, b = 1.0, math.nextafter(1.0, 2.0)
        r = solve(lambda x: -1 if x == a else 1, a, b)
        self.assertFalse(r.converged)
        self.assertEqual(r.reason, "floating-point resolution exhausted")

    def test_stopping_choices(self):
        for rule in ("residual", "step-residual", "bracket-residual"):
            r = solve(lambda x: x*x-2, 0, 2, stopping=rule)
            s = r.history[-1]
            expected = s.residual
            if rule == "step-residual":
                expected += s.step_size
            elif rule == "bracket-residual":
                expected += s.b-s.a
            self.assertEqual(r.error, expected)

    def test_evaluation_counts(self):
        calls, derivatives = [], []
        def f(x):
            calls.append(x)
            return x*x-2
        def df(x):
            derivatives.append(x)
            return 2*x
        r = solve(f, 0, 2, df=df, method="improved")
        self.assertEqual(r.function_evaluations, len(calls))
        self.assertEqual(r.derivative_evaluations, len(derivatives))
        self.assertEqual(len(calls), len(set(calls)))


class ExpressionTests(unittest.TestCase):
    def test_valid(self):
        self.assertAlmostEqual(expression("sin(pi/2)+x**2+log(e)")(3), 11)

    def test_invalid(self):
        for source in ("__import__('os')", "x.__class__", "[x][0]", "x^2", "y+1", "2x", "sin(x, x)"):
            with self.subTest(source=source), self.assertRaises(ValueError):
                expression(source)


if __name__ == "__main__":
    unittest.main()
