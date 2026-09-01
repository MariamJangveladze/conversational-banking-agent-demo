from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any


def utc_now() -> datetime:
    return datetime.now(UTC)


class ActionStatus(str, Enum):
    PREVIEW = "preview"
    APPROVED = "approved"
    CANCELLED = "cancelled"


@dataclass
class PendingAction:
    action_id: str
    action_type: str
    summary: str
    payload: dict[str, Any]
    status: ActionStatus = ActionStatus.PREVIEW


@dataclass
class DemoSession:
    session_id: str
    access_token: str
    created_at: datetime = field(default_factory=utc_now)
    last_seen_at: datetime = field(default_factory=utc_now)
    turn_count: int = 0
    pending_action: PendingAction | None = None
