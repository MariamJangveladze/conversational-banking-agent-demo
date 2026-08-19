from __future__ import annotations

import secrets
import threading
from datetime import timedelta

from app.models import DemoSession, utc_now


class SessionRegistry:
    def __init__(self, max_sessions: int = 100, ttl_minutes: int = 30, max_turns: int = 40) -> None:
        self._sessions: dict[str, DemoSession] = {}
        self._session_locks: dict[str, threading.Lock] = {}
        self._lock = threading.Lock()
        self.max_sessions = max_sessions
        self.ttl = timedelta(minutes=ttl_minutes)
        self.max_turns = max_turns

    def create(self) -> DemoSession:
        with self._lock:
            self._evict_expired()
            if len(self._sessions) >= self.max_sessions:
                raise RuntimeError("session_capacity_reached")
            session = DemoSession(session_id=secrets.token_urlsafe(18), access_token=secrets.token_urlsafe(32))
            self._sessions[session.session_id] = session
            self._session_locks[session.session_id] = threading.Lock()
            return session

    def authorized(self, session_id: str, access_token: str) -> tuple[DemoSession, threading.Lock]:
        with self._lock:
            session = self._sessions.get(session_id)
            lock = self._session_locks.get(session_id)
            if session is None or lock is None or not secrets.compare_digest(session.access_token, access_token):
                raise PermissionError("invalid_session")
            if utc_now() - session.last_seen_at > self.ttl or session.turn_count >= self.max_turns:
                self._sessions.pop(session_id, None)
                self._session_locks.pop(session_id, None)
                raise PermissionError("expired_session")
            session.turn_count += 1
            session.last_seen_at = utc_now()
            return session, lock

    def _evict_expired(self) -> None:
        cutoff = utc_now() - self.ttl
        expired = [key for key, value in self._sessions.items() if value.last_seen_at < cutoff]
        for key in expired:
            self._sessions.pop(key, None)
            self._session_locks.pop(key, None)

