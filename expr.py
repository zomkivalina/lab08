"""Базова частина: AST арифметичних виразів Expr = Num | Add | Mul."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Num:
    value: int


@dataclass(frozen=True, slots=True)
class Add:
    left: "Expr"
    right: "Expr"


@dataclass(frozen=True, slots=True)
class Mul:
    left: "Expr"
    right: "Expr"


type Expr = Num | Add | Mul
