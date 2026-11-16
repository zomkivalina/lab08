"""Базова частина: чистий eval_expr через match/case."""

from expr import Add, Expr, Mul, Num

LIMIT = 10**18


class EvalOverflow(ArithmeticError):
    """Проміжний результат вийшов за межу ±LIMIT."""


def _checked(x: int) -> int:
    if abs(x) > LIMIT:
        raise EvalOverflow(f"|{x}| > {LIMIT}")
    return x


def eval_expr(e: Expr) -> int:
    match e:
        case Num(value=v):
            return _checked(v)
        case Add(left=l, right=r):
            return _checked(eval_expr(l) + eval_expr(r))
        case Mul(left=l, right=r):
            return _checked(eval_expr(l) * eval_expr(r))
