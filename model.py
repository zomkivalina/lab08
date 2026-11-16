"""Варіант 6: стани замовлення та події як алгебраїчні типи даних (ADT)."""

from dataclasses import dataclass
from decimal import Decimal
from typing import ClassVar, Literal, Protocol

type PaymentMethod = Literal["card", "cash", "transfer"]
type EventKind = Literal["pay", "ship", "deliver", "cancel"]
type StatusName = Literal["created", "paid", "shipped", "delivered", "cancelled"]

# ---------- Стани (sum type) ----------


@dataclass(frozen=True, slots=True)
class Created:
    order_id: int
    status: ClassVar[StatusName] = "created"


@dataclass(frozen=True, slots=True)
class Paid:
    order_id: int
    amount: Decimal
    method: PaymentMethod
    status: ClassVar[StatusName] = "paid"


@dataclass(frozen=True, slots=True)
class Shipped:
    order_id: int
    amount: Decimal
    tracking: str
    status: ClassVar[StatusName] = "shipped"


@dataclass(frozen=True, slots=True)
class Delivered:
    order_id: int
    amount: Decimal
    tracking: str
    status: ClassVar[StatusName] = "delivered"


@dataclass(frozen=True, slots=True)
class Cancelled:
    order_id: int
    reason: str
    refund: Decimal  # скільки повернути клієнту (0, якщо ще не платив)
    status: ClassVar[StatusName] = "cancelled"


type OrderState = Created | Paid | Shipped | Delivered | Cancelled

# ---------- Події (sum type) ----------


@dataclass(frozen=True, slots=True)
class Pay:
    amount: Decimal
    method: PaymentMethod
    kind: ClassVar[EventKind] = "pay"


@dataclass(frozen=True, slots=True)
class Ship:
    tracking: str
    kind: ClassVar[EventKind] = "ship"


@dataclass(frozen=True, slots=True)
class Deliver:
    kind: ClassVar[EventKind] = "deliver"


@dataclass(frozen=True, slots=True)
class Cancel:
    reason: str
    kind: ClassVar[EventKind] = "cancel"


type Event = Pay | Ship | Deliver | Cancel

# ---------- Структурний контракт ----------


class HasOrderId(Protocol):
    """Будь-що з номером замовлення: усі стани підходять без наслідування."""

    @property
    def order_id(self) -> int: ...


class InvalidTransition(Exception):
    """Перехід заборонено бізнес-правилами."""

    def __init__(self, state: OrderState, event: Event, why: str) -> None:
        super().__init__(f"{state.status} --{event.kind}--> заборонено: {why}")
        self.state = state
        self.event = event
