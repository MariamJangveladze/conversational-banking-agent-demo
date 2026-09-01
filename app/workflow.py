from __future__ import annotations

import re
import secrets
from collections.abc import Callable

from app.demo_bank import DemoBankService
from app.models import ActionStatus, DemoSession, PendingAction
from app.telemetry import Timer, Trace, TraceRecorder

TRANSFER_RE = re.compile(
    r"(?:send|transfer)\s+\$?(?P<amount>\d+(?:\.\d{1,2})?)\s+(?:to\s+)?"
    r"(?P<recipient>[a-z][a-z .'-]{1,40}?)"
    r"(?=\s+(?:please|and|then|show|hurry|do|now|right)\b|[,.!?]|$)",
    re.IGNORECASE,
)


class BankingWorkflow:
    """Deterministic policy boundary around all demo capabilities."""

    def __init__(
        self,
        bank: DemoBankService,
        traces: TraceRecorder,
        intent_classifier: Callable[[str], object] | None = None,
    ) -> None:
        self.bank = bank
        self.traces = traces
        self.intent_classifier = intent_classifier

    def handle(self, session: DemoSession, message: str) -> dict[str, object]:
        normalized = message.strip()
        lowered = normalized.lower()
        proposed_intent = None
        if self.intent_classifier is not None:
            proposed_intent = str(getattr(self.intent_classifier(normalized), "intent", "help"))
        with Timer() as timer:
            if lowered in {"approve", "confirm"}:
                response = self._approve(session)
            elif lowered in {"cancel", "reject"}:
                response = self._cancel(session)
            elif match := TRANSFER_RE.search(normalized):
                response = self._preview_transfer(session, match)
            elif "balance" in lowered or proposed_intent == "balance":
                balance = self.bank.balance()
                response = {
                    "reply": f"Your synthetic available balance is ${balance['available']:,.2f} {balance['currency']}.",
                    "data": balance,
                }
            elif "transaction" in lowered or "activity" in lowered or proposed_intent == "transactions":
                response = {"reply": "Here are the latest synthetic transactions.", "data": self.bank.transactions()}
            elif "spending" in lowered or "spent" in lowered or proposed_intent == "spending":
                response = {"reply": "Here is your synthetic spending summary.", "data": self.bank.spending_summary()}
            else:
                response = {
                    "reply": "Try asking for balance, transactions, spending, or: transfer $25 to Alex Demo.",
                    "suggestions": ["Show my balance", "Recent transactions", "Spending summary"],
                }

        model = "bedrock-intent-classifier" if self.intent_classifier else "deterministic-router"
        self.traces.record(Trace(operation="chat_turn", latency_ms=timer.latency_ms, model=model))
        return response

    def _preview_transfer(self, session: DemoSession, match: re.Match[str]) -> dict[str, object]:
        amount = round(float(match.group("amount")), 2)
        recipient = match.group("recipient").strip().title()
        if amount <= 0 or amount > 500:
            return {"reply": "Demo transfers must be between $0.01 and $500.00."}
        action = PendingAction(
            action_id=secrets.token_urlsafe(10),
            action_type="simulated_transfer",
            summary=f"Simulate transfer of ${amount:,.2f} to {recipient}",
            payload={"amount": amount, "recipient": recipient, "currency": "USD"},
        )
        session.pending_action = action
        return {
            "reply": "I prepared a simulation only. Review it, then choose Approve or Cancel.",
            "approval": self._public_action(action),
        }

    def _approve(self, session: DemoSession) -> dict[str, object]:
        action = session.pending_action
        if action is None or action.status is not ActionStatus.PREVIEW:
            return {"reply": "There is no pending action to approve."}
        action.status = ActionStatus.APPROVED
        session.pending_action = None
        return {
            "reply": "Approved and recorded as a simulation. No money moved.",
            "result": {**self._public_action(action), "simulation_reference": f"SIM-{action.action_id}"},
        }

    def _cancel(self, session: DemoSession) -> dict[str, object]:
        action = session.pending_action
        if action is None:
            return {"reply": "There is no pending action to cancel."}
        action.status = ActionStatus.CANCELLED
        session.pending_action = None
        return {"reply": "The simulated action was cancelled.", "result": self._public_action(action)}

    @staticmethod
    def _public_action(action: PendingAction) -> dict[str, object]:
        return {
            "action_id": action.action_id,
            "type": action.action_type,
            "summary": action.summary,
            "status": action.status.value,
            "payload": action.payload,
        }
