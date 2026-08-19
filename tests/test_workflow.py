from app.demo_bank import DemoBankService
from app.models import ActionStatus, DemoSession
from app.telemetry import TraceRecorder
from app.workflow import BankingWorkflow


def session() -> DemoSession:
    return DemoSession(session_id="test-session", access_token="test-token")


def workflow() -> BankingWorkflow:
    return BankingWorkflow(DemoBankService(), TraceRecorder())


def test_balance_uses_synthetic_account() -> None:
    result = workflow().handle(session(), "What is my balance?")
    assert result["data"]["account_id"] == "demo-checking-001"
    assert "synthetic" in result["reply"].lower()


def test_transfer_is_preview_only_until_approval() -> None:
    active = session()
    preview = workflow().handle(active, "Transfer $25 to Alex Demo")
    assert preview["approval"]["status"] == ActionStatus.PREVIEW.value
    assert active.pending_action is not None


def test_approval_records_simulation_and_clears_pending_action() -> None:
    active = session()
    engine = workflow()
    engine.handle(active, "Send $18.50 to Jordan Example")
    result = engine.handle(active, "approve")
    assert result["result"]["status"] == ActionStatus.APPROVED.value
    assert result["result"]["simulation_reference"].startswith("SIM-")
    assert active.pending_action is None
    assert "No money moved" in result["reply"]


def test_transfer_limit_is_enforced_in_code() -> None:
    result = workflow().handle(session(), "Transfer $999 to Alex Demo")
    assert "between" in result["reply"]
    assert "approval" not in result


def test_no_pending_action_cannot_be_approved() -> None:
    result = workflow().handle(session(), "confirm")
    assert result == {"reply": "There is no pending action to approve."}

