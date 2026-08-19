from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Transaction:
    merchant: str
    amount: float
    category: str
    date: str


class DemoBankService:
    """Read-only synthetic data plus simulated actions; never connects to a bank."""

    ACCOUNT_ID = "demo-checking-001"
    CURRENCY = "USD"

    def __init__(self) -> None:
        self._transactions = (
            Transaction("Northwind Market", -42.18, "Groceries", "2026-08-18"),
            Transaction("Salary — Demo Employer", 3200.00, "Income", "2026-08-15"),
            Transaction("City Metro", -18.50, "Transport", "2026-08-14"),
            Transaction("Cloud Cafe", -11.90, "Dining", "2026-08-13"),
        )

    def balance(self) -> dict[str, object]:
        return {"account_id": self.ACCOUNT_ID, "available": 4820.64, "currency": self.CURRENCY}

    def transactions(self) -> list[dict[str, object]]:
        return [transaction.__dict__ for transaction in self._transactions]

    def spending_summary(self) -> dict[str, float]:
        totals: dict[str, float] = {}
        for transaction in self._transactions:
            if transaction.amount < 0:
                totals[transaction.category] = round(
                    totals.get(transaction.category, 0.0) + abs(transaction.amount), 2
                )
        return totals

