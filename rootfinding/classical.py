def opposite(x, y):
    return (x < 0 < y) or (y < 0 < x)


def bracket(a, b, fa, fb, x, fx):
    if fx == 0:
        return x, x, fx, fx
    if opposite(fa, fx):
        return a, x, fa, fx
    return x, b, fx, fb


def false_position(a, b, fa, fb):
    scale = max(abs(fa), abs(fb))
    left, right = abs(fa) / scale, abs(fb) / scale
    weight = left / (left + right)
    return min(b, max(a, (1 - weight) * a + weight * b))
