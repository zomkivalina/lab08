"""Текстове представлення: вирази, стани, події та історія замовлення."""

from typing import Protocol

from expr import Add, Expr, Mul, Num
from model import (
    Cancel,
    Cancelled,
    Created,
    Deliver,
    Delivered,
    Event,
    OrderState,
    Paid,
    Pay,
    Ship,
    Shipped,
)

# ---------- Вирази ----------


def pretty_expr(e: Expr) -> str:
    """Дужки лише там, де потрібні: сума всередині добутку."""
    match e:
        case Num(value=v):
            return str(v)
        case Add(left=l, right=r):
            return f"{pretty_expr(l)} + {pretty_expr(r)}"
        case Mul(left=l, right=r):
            return f"{_factor(l)} * {_factor(r)}"


def _factor(e: Expr) -> str:
    match e:
        case Add():
            return f"({pretty_expr(e)})"
        case _:
            return pretty_expr(e)


# ---------- Стани та події ----------

ICONS = {
    "created": "○",
    "paid": "₴",
    "shipped": "⇢",
    "delivered": "✓",
    "cancelled": "✗",
}


def render_state(s: OrderState) -> str:
    match s:
        case Created():
            details = "очікує оплати"
        case Paid(amount=amount, method=method):
            details = f"оплачено {amount} грн ({method})"
        case Shipped(tracking=tracking, amount=amount):
            details = f"відправлено, ТТН {tracking}, {amount} грн"
        case Delivered(amount=amount):
            details = f"доставлено, {amount} грн"
        case Cancelled(reason=reason, refund=refund):
            details = f"скасовано: {reason}; повернення {refund} грн"
    return f"{ICONS[s.status]} #{s.order_id} {s.status:<9} {details}"


def render_event(e: Event) -> str:
    match e:
        case Pay(amount=amount, method=method):
            return f"pay({amount}, {method})"
        case Ship(tracking=tracking):
            return f"ship({tracking})"
        case Deliver():
            return "deliver()"
        case Cancel(reason=reason):
            return f"cancel({reason!r})"


class Renderable(Protocol):
    """Структурний контракт: будь-що з методом render() -> str."""

    def render(self) -> str: ...


def render_all(items: list[Renderable]) -> str:
    return "\n".join(item.render() for item in items)


class Timeline:
    """Історія одного замовлення; відповідає Renderable без наслідування."""

    def __init__(self, states: list[OrderState]) -> None:
        self.states = tuple(states)

    def render(self) -> str:
        return "\n".join(f"  {render_state(s)}" for s in self.states)
