"""Parameterized test-function family for controlled stress-testing."""

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class TestCase:
    label: str
    a: float
    b: float
    root: float
    curvature: float

    @property
    def f(self):
        r, c = self.root, self.curvature
        return lambda x: (x - r) * math.exp(c * (x - r))

    @property
    def df(self):
        r, c = self.root, self.curvature
        return lambda x: math.exp(c * (x - r)) * (1 + c * (x - r))


ROOT_POSITIONS = {"left": 0.2, "center": 0.5, "right": 0.8}
CONCAVITY_SIGNS = {"up": 1.0, "down": -1.0}
CURVATURE_STRENGTHS = {"weak": 1.0, "strong": 4.0}


def generate_cases(interval=(-2.0, 2.0)):
    """Enumerate the full grid: root position x concavity sign x curvature strength."""
    lo, hi = interval
    width = hi - lo
    cases = []
    for pos_name, fraction in ROOT_POSITIONS.items():
        root = lo + fraction * width
        for sign_name, sign in CONCAVITY_SIGNS.items():
            for strength_name, magnitude in CURVATURE_STRENGTHS.items():
                label = f"root={pos_name},concavity={sign_name},curvature={strength_name}"
                cases.append(TestCase(label, lo, hi, root, sign * magnitude))
    return cases
