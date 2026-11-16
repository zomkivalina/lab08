"""Демонстрація: автомат станів замовлення (варіант 6) і базові вирази."""

from decimal import Decimal

from eval_ import eval_expr
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
from expr import Add, Mul, Num
from model import (
    Cancel,
    Created,
    Deliver,
    Event,
    InvalidTransition,
    OrderState,
    Pay,
    Ship,
)
from pretty import Timeline, pretty_expr, render_all, render_event, render_state

D = Decimal

SCENARIOS: dict[int, list[Event]] = {
    101: [Pay(D("1250.00"), "card"), Ship("20450001234567"), Deliver()],
    102: [Pay(D("640.00"), "transfer"), Cancel("немає на складі")],
    103: [Cancel("клієнт передумав")],
    104: [Pay(D("2990.00"), "cash"), Ship("20450007654321")],
}


def main() -> None:
    print("=== ВАРІАНТ 6: ІСТОРІЯ СТАНІВ ЗАМОВЛЕНЬ ===")
    timelines = [Timeline(history(Created(oid), evs)) for oid, evs in SCENARIOS.items()]
    print(render_all(list(timelines)))

    finals = [apply_events(Created(oid), evs) for oid, evs in SCENARIOS.items()]
    print("\n=== ПІДСУМКОВІ СТАНИ ===")
    for s in finals:
        allowed = ", ".join(sorted(allowed_events(s))) or "— (кінцевий)"
        print(f"  {render_state(s)}\n      дозволені події: {allowed}")
    earned, refunded = revenue_and_refunds(finals)
    print(f"  виручка (доставлені): {earned} грн, повернення: {refunded} грн")
    print(f"  статуси: {status_counts(finals)}")
    print(f"  order_ids (Protocol HasOrderId): {order_ids(finals)}")

    print("\n=== ЗАБОРОНЕНІ ПЕРЕХОДИ ===")
    cases: list[tuple[OrderState, Event]] = [
        (finals[3], Cancel("пізно")),  # уже відправлено
        (finals[3], Pay(D("1"), "card")),
        (Created(105), Pay(D("0"), "card")),
        (Created(105), Deliver()),
        (finals[0], Cancel("повернення")),  # кінцевий стан
    ]
    for state, event in cases:
        try:
            transition(state, event)
        except InvalidTransition as exc:
            print(f"  {render_event(event):<22} -> {exc}")
    print(f"  is_terminal(доставлене): {is_terminal(finals[0])}")

    print("\n=== run_tolerant: некоректні події пропускаються ===")
    noisy: list[Event] = [
        Ship("x"),
        Pay(D("500.00"), "card"),
        Deliver(),
        Ship("20450000000001"),
        Cancel("запізно"),
        Deliver(),
    ]
    final, errors = run_tolerant(Created(106), noisy)
    print(f"  події: {', '.join(map(render_event, noisy))}")
    print(f"  результат: {render_state(final)}")
    for err in errors:
        print(f"  відхилено: {err}")

    print("\n=== БАЗОВА ЧАСТИНА: Expr = Num | Add | Mul ===")
    e = Mul(Add(Num(2), Num(3)), Add(Num(4), Mul(Num(5), Num(6))))
    print(f"  {pretty_expr(e)} = {eval_expr(e)}")


if __name__ == "__main__":
    main()
