"""Чисті функції над станами замовлення: усе через match/case."""

from collections import Counter
from collections.abc import Iterable, Iterator
from decimal import Decimal
from functools import reduce
from itertools import accumulate

from model import (
    Cancel,
    Cancelled,
    Created,
    Deliver,
    Delivered,
    Event,
    EventKind,
    HasOrderId,
    InvalidTransition,
    OrderState,
    Paid,
    Pay,
    Ship,
    Shipped,
    StatusName,
)

ZERO = Decimal("0.00")


def transition(state: OrderState, event: Event) -> OrderState:
    """Один крок автомата станів. Повертає НОВИЙ стан або кидає InvalidTransition."""
    match state, event:
        case Created(order_id=oid), Pay(amount=amount, method=method) if amount > 0:
            return Paid(oid, amount, method)
        case Created(), Pay():
            raise InvalidTransition(state, event, "сума оплати має бути > 0")
        case Created(order_id=oid), Cancel(reason=reason):
            return Cancelled(oid, reason, refund=ZERO)
        case Paid(order_id=oid, amount=amount), Ship(tracking=tracking) if tracking:
            return Shipped(oid, amount, tracking)
        case Paid(), Ship():
            raise InvalidTransition(state, event, "потрібен номер відправлення")
        case Paid(order_id=oid, amount=amount), Cancel(reason=reason):
            return Cancelled(oid, reason, refund=amount)  # повертаємо всю суму
        case Shipped(order_id=oid, amount=amount, tracking=tracking), Deliver():
            return Delivered(oid, amount, tracking)
        case Shipped(), Cancel():
            raise InvalidTransition(state, event, "посилка вже в дорозі")
        case Delivered() | Cancelled(), _:
            raise InvalidTransition(state, event, "кінцевий стан")
        case _:
            raise InvalidTransition(state, event, "подія не підходить до стану")


def apply_events(state: OrderState, events: Iterable[Event]) -> OrderState:
    """Згортка подій: reduce(transition, events, state)."""
    return reduce(transition, events, state)


def history(state: OrderState, events: Iterable[Event]) -> list[OrderState]:
    """Усі проміжні стани, починаючи з початкового."""
    steps: Iterator[OrderState] = accumulate(events, transition, initial=state)
    return list(steps)


def run_tolerant(
    state: OrderState, events: Iterable[Event]
) -> tuple[OrderState, list[str]]:
    """Застосувати події, пропускаючи некоректні; повертає стан і список відмов."""

    def step(
        acc: tuple[OrderState, list[str]], event: Event
    ) -> tuple[OrderState, list[str]]:
        current, errors = acc
        try:
            return transition(current, event), errors
        except InvalidTransition as exc:
            return current, [*errors, str(exc)]

    start: tuple[OrderState, list[str]] = (state, [])
    return reduce(step, events, start)


def allowed_events(state: OrderState) -> frozenset[EventKind]:
    match state:
        case Created():
            return frozenset({"pay", "cancel"})
        case Paid():
            return frozenset({"ship", "cancel"})
        case Shipped():
            return frozenset({"deliver"})
        case Delivered() | Cancelled():
            return frozenset()


def is_terminal(state: OrderState) -> bool:
    return not allowed_events(state)


def revenue_and_refunds(states: Iterable[OrderState]) -> tuple[Decimal, Decimal]:
    """Виручка — лише доставлені; повернення — скасовані після оплати."""

    def add(acc: tuple[Decimal, Decimal], s: OrderState) -> tuple[Decimal, Decimal]:
        earned, refunded = acc
        match s:
            case Delivered(amount=amount):
                return earned + amount, refunded
            case Cancelled(refund=refund):
                return earned, refunded + refund
            case _:
                return acc

    return reduce(add, states, (ZERO, ZERO))


def status_counts(states: Iterable[OrderState]) -> dict[StatusName, int]:
    return dict(Counter(s.status for s in states))


def order_ids(items: Iterable[HasOrderId]) -> list[int]:
    """Працює з будь-якими об'єктами, що відповідають Protocol HasOrderId."""
    return [item.order_id for item in items]
