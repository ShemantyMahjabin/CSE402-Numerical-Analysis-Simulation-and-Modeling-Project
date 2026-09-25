import unittest

from rootfinding import solve
from rootfinding.expressions import expression
from rootfinding.problems import PROBLEMS


class AdaptiveBlendTests(unittest.TestCase):
    """Extension A: weighted blend of midpoint and false-position."""

    def test_first_iteration_matches_hand_calculation(self):
        # x**2-x-2 on [1,4]: m=2.5 (f=1.75), s=1.5 (f=-1.25).
        # w_m = |fs|/(|fm|+|fs|) = 1.25/3 = 5/12, w_s = 1.75/3 = 7/12.
        # x_new = (5/12)*2.5 + (7/12)*1.5 = 23/12.
        r = solve(lambda x: x * x - x - 2, 1, 4, method="adaptive", max_iterations=1)
        s = r.history[0]
        self.assertEqual(s.midpoint, 2.5)
        self.assertEqual(s.false_position, 1.5)
        self.assertAlmostEqual(s.root, 23 / 12, places=12)
        self.assertEqual(s.selected, "adaptive-blend")
        self.assertTrue(s.weights)

    def test_converges_on_all_examples(self):
        for name, p in PROBLEMS.items():
            f = expression(p.function)
            with self.subTest(name=name):
                r = solve(f, p.a, p.b, method="adaptive", stopping="residual", tol=1e-10)
                self.assertTrue(r.converged, r.reason)
                self.assertLess(r.residual, 1e-10)
                for s in r.history:
                    self.assertLessEqual(s.a, s.root)
                    self.assertLessEqual(s.root, s.b)
                    self.assertLessEqual(f(s.a) * f(s.b), 0)

    def test_no_derivative_required(self):
        r = solve(lambda x: x * x - 2, 0, 2, method="adaptive")
        self.assertTrue(r.converged)
        self.assertEqual(r.derivative_evaluations, 0)


class SafeguardedBlendTests(unittest.TestCase):
    """Extension B: three-way blend of midpoint, false-position, and Newton."""

    def test_first_iteration_matches_hand_calculation(self):
        # Newton from a=1: f(1)=-2, f'(1)=1 -> n=3, f(3)=4.
        # Inverse-residual weights over |f|=(1.75, 1.25, 4):
        # w_m=80/227, w_s=112/227, w_n=35/227 -> x_new=(200+168+105)/227=473/227.
        r = solve(lambda x: x * x - x - 2, 1, 4, method="safeguarded",
                  df=lambda x: 2 * x - 1, max_iterations=1)
        s = r.history[0]
        self.assertEqual(s.newton, 3)
        self.assertEqual(s.newton_status, "included in blend")
        self.assertAlmostEqual(s.root, 473 / 227, places=9)
        self.assertEqual(s.selected, "safeguarded-blend")

    def test_falls_back_to_adaptive_blend_when_newton_unsafe(self):
        # With a zero derivative, Newton is excluded (w_n=0), so the first
        # iteration must match the plain adaptive blend exactly.
        adaptive = solve(lambda x: x * x - x - 2, 1, 4, method="adaptive", max_iterations=1)
        safeguarded = solve(lambda x: x * x - x - 2, 1, 4, method="safeguarded",
                             df=lambda x: 0, max_iterations=1)
        self.assertEqual(adaptive.history[0].root, safeguarded.history[0].root)
        self.assertTrue(safeguarded.history[0].newton_status.startswith("skipped"))

    def test_requires_derivative(self):
        with self.assertRaises(ValueError):
            solve(lambda x: x * x - 2, 0, 2, method="safeguarded")

    def test_converges_on_all_examples(self):
        for name, p in PROBLEMS.items():
            f, df = expression(p.function), expression(p.derivative)
            with self.subTest(name=name):
                r = solve(f, p.a, p.b, df=df, method="safeguarded", stopping="residual", tol=1e-10)
                self.assertTrue(r.converged, r.reason)
                self.assertLess(r.residual, 1e-10)
                for s in r.history:
                    self.assertLessEqual(s.a, s.root)
                    self.assertLessEqual(s.root, s.b)
                    self.assertLessEqual(f(s.a) * f(s.b), 0)


if __name__ == "__main__":
    unittest.main()
