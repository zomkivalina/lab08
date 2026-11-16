# Лабораторна робота №8. Алгебраїчні типи даних «по-Python'івськи»

**Студентка:** Зьомків А. І., група ФЕП-21
**Варіант:** 6 — «Стани замовлення»

## Модель (варіант 6)
Стани замовлення — sum type з незмінних `@dataclass(frozen=True)` вузлів:

```python
type OrderState = Created | Paid | Shipped | Delivered | Cancelled
type Event      = Pay | Ship | Deliver | Cancel
type EventKind  = Literal["pay", "ship", "deliver", "cancel"]
```

Дозволені переходи:

```
Created --pay--> Paid --ship--> Shipped --deliver--> Delivered
   |               |
 cancel          cancel (повернення всієї суми)
   v               v
Cancelled       Cancelled
```
Усе інше заборонено (`InvalidTransition`): оплата з сумою ≤ 0, відправлення без ТТН,
скасування вже відправленого, будь-яка подія в кінцевому стані.

## Файли
- `model.py` — ADT станів і подій, `Literal` (`EventKind`, `PaymentMethod`, `StatusName`),
  `Protocol HasOrderId`, виняток `InvalidTransition`;
- `evaluator.py` — чиста `transition(state, event)` на `match/case`, `apply_events`
  (reduce), `history` (accumulate), `run_tolerant`, `allowed_events`, `is_terminal`,
  статистика `revenue_and_refunds`, `status_counts`;
- `pretty.py` — `render_state`, `render_event`, `Protocol Renderable`, `Timeline`,
  а також `pretty_expr` для базової частини;
- `expr.py`, `eval_.py` — базова частина: `Expr = Num | Add | Mul`, `eval_expr` через
  `match`, захист від переповнення `EvalOverflow`;
- `main.py` — демонстрація, `tests/` — pytest.

## Запуск
```bash
python -m venv .venv
.venv\Scripts\activate          # Windows (Linux/macOS: source .venv/bin/activate)
pip install -r requirements.txt

python main.py
pytest -v
mypy --strict .
black --check .
ruff check .
```
Потрібен Python 3.12+ (оператор `type`).
