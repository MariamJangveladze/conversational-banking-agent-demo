import pytest

from app.sessions import SessionRegistry


def test_session_requires_matching_token() -> None:
    registry = SessionRegistry()
    active = registry.create()
    with pytest.raises(PermissionError):
        registry.authorized(active.session_id, "wrong-token")


def test_session_turn_budget_is_enforced() -> None:
    registry = SessionRegistry(max_turns=1)
    active = registry.create()
    registry.authorized(active.session_id, active.access_token)
    with pytest.raises(PermissionError):
        registry.authorized(active.session_id, active.access_token)


def test_registry_capacity_is_bounded() -> None:
    registry = SessionRegistry(max_sessions=1)
    registry.create()
    with pytest.raises(RuntimeError):
        registry.create()

