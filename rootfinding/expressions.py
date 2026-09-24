"""Small arithmetic expression interpreter; no eval or executable Python input."""

import ast
import math
import operator

FUNCTIONS = {name: getattr(math, name) for name in
             ("sin", "cos", "tan", "asin", "acos", "atan", "sinh", "cosh",
              "tanh", "exp", "log", "log10", "sqrt", "expm1", "log1p")}
FUNCTIONS["abs"] = abs
CONSTANTS = {"pi": math.pi, "e": math.e}
OPERATORS = {ast.Add: operator.add, ast.Sub: operator.sub,
             ast.Mult: operator.mul, ast.Div: operator.truediv, ast.Pow: operator.pow}


def expression(source):
    """Compile a real expression using x, math functions, and + - * / **."""
    if len(source) > 2000:
        raise ValueError("Expression is too long")
    try:
        tree = ast.parse(source, mode="eval")
    except (SyntaxError, RecursionError) as exc:
        raise ValueError("Invalid expression; use x**2 for powers and explicit multiplication") from exc
    if sum(1 for _ in ast.walk(tree)) > 300:
        raise ValueError("Expression is too complex")

    def compile_node(node):
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            value = float(node.value)
            return lambda x: value
        if isinstance(node, ast.Name):
            if node.id == "x":
                return lambda x: x
            if node.id in CONSTANTS:
                return lambda x: CONSTANTS[node.id]
        if isinstance(node, ast.BinOp) and type(node.op) in OPERATORS:
            left, right = compile_node(node.left), compile_node(node.right)
            op = OPERATORS[type(node.op)]
            return lambda x: op(left(x), right(x))
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            operand = compile_node(node.operand)
            sign = -1 if isinstance(node.op, ast.USub) else 1
            return lambda x: sign * operand(x)
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id in FUNCTIONS and len(node.args) == 1 and not node.keywords):
            fn, argument = FUNCTIONS[node.func.id], compile_node(node.args[0])
            return lambda x: fn(argument(x))
        raise ValueError("Unsupported expression. Use x, numbers, + - * / **, and named math functions")

    return compile_node(tree.body)
