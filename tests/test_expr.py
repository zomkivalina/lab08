import pytest

from eval_ import LIMIT, EvalOverflow, eval_expr
from expr import Add, Mul, Num
from pretty import pretty_expr


def test_eval_basic() -> None:
    assert eval_expr(Num(7)) == 7
    assert eval_expr(Add(Num(2), Num(3))) == 5
    assert eval_expr(Mul(Num(4), Num(5))) == 20


def test_eval_nested() -> None:
    e = Mul(Add(Num(2), Num(3)), Add(Num(4), Mul(Num(5), Num(6))))
    assert eval_expr(e) == 170
    assert pretty_expr(e) == "(2 + 3) * (4 + 5 * 6)"


def test_pretty_without_extra_parentheses() -> None:
    assert pretty_expr(Add(Num(1), Mul(Num(2), Num(3)))) == "1 + 2 * 3"
    assert pretty_expr(Mul(Mul(Num(1), Num(2)), Num(3))) == "1 * 2 * 3"


def test_overflow() -> None:
    big = Num(LIMIT)
    assert eval_expr(big) == LIMIT
    with pytest.raises(EvalOverflow):
        eval_expr(Mul(big, Num(2)))
    with pytest.raises(EvalOverflow):
        eval_expr(Num(-LIMIT - 1))


def test_nodes_are_hashable_and_comparable() -> None:
    assert Add(Num(1), Num(2)) == Add(Num(1), Num(2))
    assert len({Num(1), Num(1), Num(2)}) == 2
