from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from evaluator import (
    allowed_events,
    apply_events,
    history,
    is_terminal,
    order_ids,
    revenue_and_refunds,
    run_tolerant,
    status_counts,
    transition,
)
from model import (
    Cancel,
    Cancelled,
    Created,
    Deliver,
    Delivered,
    Event,
    InvalidTransition,
    OrderState,
    Paid,
    Pay,
    Ship,
    Shipped,
)
from pretty import Timeline, render_all, render_event, render_state

D = Decimal
PAID = Paid(1, D("100.00"), "card")
SHIPPED = Shipped(1, D("100.00"), "TTN1")
DELIVERED = Delivered(1, D("100.00"), "TTN1")

# ---------- коректні переходи ----------


@pytest.mark.parametrize(
    ("state", "event", "expected"),
    [
        (Created(1), Pay(D("100.00"), "card"), PAID),
        (Created(1), Cancel("x"), Cancelled(1, "x", D("0.00"))),
        (PAID, Ship("TTN1"), SHIPPED),
        (PAID, Cancel("y"), Cancelled(1, "y", D("100.00"))),
        (SHIPPED, Deliver(), DELIVERED),
    ],
)
def test_valid_transitions(
    state: OrderState, event: Event, expected: OrderState
) -> None:
    assert transition(state, event) == expected


# ---------- заборонені переходи ----------


@pytest.mark.parametrize(
    ("state", "event", "fragment"),
    [
        (Created(1), Ship("TTN"), "не підходить"),
        (Created(1), Deliver(), "не підходить"),
        (Created(1), Pay(D("0"), "cash"), "> 0"),
        (Created(1), Pay(D("-5"), "cash"), "> 0"),
        (PAID, Pay(D("1"), "card"), "не підходить"),
        (PAID, Ship(""), "номер відправлення"),
        (PAID, Deliver(), "не підходить"),
        (SHIPPED, Cancel("пізно"), "в дорозі"),
        (SHIPPED, Ship("TTN2"), "не підходить"),
        (DELIVERED, Cancel("z"), "кінцевий"),
        (Cancelled(1, "x", D("0")), Pay(D("1"), "card"), "кінцевий"),
    ],
)
def test_invalid_transitions(state: OrderState, event: Event, fragment: str) -> None:
    with pytest.raises(InvalidTransition, match=fragment) as info:
        transition(state, event)
    assert info.value.state is state and info.value.event is event


# ---------- послідовності подій ----------


def test_full_happy_path_and_history() -> None:
    events: list[Event] = [Pay(D("100.00"), "card"), Ship("TTN1"), Deliver()]
    assert apply_events(Created(1), events) == DELIVERED
    assert history(Created(1), events) == [Created(1), PAID, SHIPPED, DELIVERED]


def test_empty_event_list() -> None:
    assert apply_events(Created(7), []) == Created(7)
    assert history(Created(7), []) == [Created(7)]


def test_apply_events_stops_on_first_error() -> None:
    with pytest.raises(InvalidTransition):
        apply_events(Created(1), [Pay(D("1"), "cash"), Deliver()])


def test_run_tolerant_skips_invalid() -> None:
    events: list[Event] = [Deliver(), Pay(D("50.00"), "cash"), Cancel("так треба")]
    final, errors = run_tolerant(Created(3), events)
    assert final == Cancelled(3, "так треба", D("50.00"))
    assert len(errors) == 1 and "deliver" in errors[0]


def test_states_are_immutable_and_inputs_untouched() -> None:
    start = Created(1)
    paid = transition(start, Pay(D("10"), "card"))
    assert start == Created(1) and paid is not start
    with pytest.raises(FrozenInstanceError):
        start.order_id = 2  # type: ignore[misc]


# ---------- допоміжні функції ----------


def test_allowed_events_and_terminal() -> None:
    assert allowed_events(Created(1)) == {"pay", "cancel"}
    assert allowed_events(PAID) == {"ship", "cancel"}
    assert allowed_events(SHIPPED) == {"deliver"}
    assert is_terminal(DELIVERED) and is_terminal(Cancelled(1, "x", D("0")))
    assert not is_terminal(PAID)


def test_statistics_over_many_orders() -> None:
    states: list[OrderState] = [
        DELIVERED,
        Delivered(2, D("50.50"), "T"),
        Cancelled(3, "x", D("30.00")),
        Cancelled(4, "y", D("0.00")),
        Created(5),
    ]
    assert revenue_and_refunds(states) == (D("150.50"), D("30.00"))
    assert status_counts(states) == {"delivered": 2, "cancelled": 2, "created": 1}
    assert revenue_and_refunds([]) == (D("0.00"), D("0.00"))


def test_protocol_has_order_id() -> None:
    assert order_ids([Created(1), PAID, Cancelled(9, "x", D("0"))]) == [1, 1, 9]


def test_every_transition_respects_allowed_events() -> None:
    """Узгодженість: подія з allowed_events не дає InvalidTransition."""
    samples: dict[str, Event] = {
        "pay": Pay(D("1"), "card"),
        "ship": Ship("T"),
        "deliver": Deliver(),
        "cancel": Cancel("c"),
    }
    for state in (Created(1), PAID, SHIPPED, DELIVERED):
        for kind, event in samples.items():
            if kind in allowed_events(state):
                transition(state, event)
            else:
                with pytest.raises(InvalidTransition):
                    transition(state, event)


# ---------- рендер ----------


def test_render() -> None:
    assert render_state(PAID) == "₴ #1 paid      оплачено 100.00 грн (card)"
    assert render_event(Cancel("x")) == "cancel('x')"
    assert render_event(Pay(D("5"), "cash")) == "pay(5, cash)"
    text = render_all([Timeline([Created(1), PAID])])
    assert text.count("\n") == 1 and "#1 created" in text
