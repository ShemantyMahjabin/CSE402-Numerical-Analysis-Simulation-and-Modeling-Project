"""Selected paper examples; brackets are explicitly validated by the solver."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Problem:
    function: str
    derivative: str
    a: float
    b: float
    source: str


PROBLEMS = {
    "quadratic": Problem("x**2-x-2", "2*x-1", 1, 4, "2019 Table 3"),
    "sqrt3": Problem("x**2-3", "2*x", 1, 2, "2019 Table 2"),
    "sqrt5": Problem("x**2-5", "2*x", 2, 7, "2019 Table 2"),
    "sqrt10": Problem("x**2-10", "2*x", 3, 4, "2019 Table 2"),
    "quadratic2": Problem("x**2+2*x-7", "2*x+2", 1, 3, "2019 Table 2"),
    "quadratic3": Problem("x**2+5*x+2", "2*x+5", -6, -3,
                          "2019 Table 2; corrected bracket isolating the left root"),
    "cuberoot2": Problem("x**3-2", "3*x**2", 0, 2, "2019 Table 2"),
    "exponential": Problem("x*exp(x)-7", "(x+1)*exp(x)", 1, 2,
                           "2019 Table 2; corrected sign-changing bracket"),
    "cosine": Problem("x-cos(x)", "1+sin(x)", 0, 1, "2019 Table 2"),
    "sine_product": Problem("x*sin(x)-1", "sin(x)+x*cos(x)", 0, 2, "2019 Table 2"),
    "sine_cubic": Problem("sin(x)-x**3", "cos(x)-3*x**2", 0.5, 1, "2021 Table 3"),
    "quintic": Problem("0.7*x**5-8*x**4+44*x**3-90*x**2+82*x-25",
                       "3.5*x**4-32*x**3+132*x**2-180*x+82", 0, 1, "2021 Table 4"),
    "log_cubic": Problem("x**3+log(x)", "3*x**2+1/x", 0.1, 2, "2021 Table 5"),
}
