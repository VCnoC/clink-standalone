"""Session management for clink continuation support.

Provides conversation continuation through continuation_id tracking.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from threading import Lock
from typing import Any

logger = logging.getLogger("clink.session")


@dataclass
class SessionEntry:
    """A single session entry tracking conversation state."""

    session_id: str
    cli_name: str
    role_name: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_accessed: datetime = field(default_factory=datetime.utcnow)
    turn_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    def touch(self) -> None:
        """Update last access time and increment turn count."""
        self.last_accessed = datetime.utcnow()
        self.turn_count += 1


class SessionManager:
    """Manages conversation sessions for continuation support.

    Sessions are tracked by continuation_id and automatically expire
    after a configurable TTL (default: 1 hour).
    """

    def __init__(self, ttl_minutes: int = 60, max_sessions: int = 100) -> None:
        self._sessions: dict[str, SessionEntry] = {}
        self._lock = Lock()
        self._ttl = timedelta(minutes=ttl_minutes)
        self._max_sessions = max_sessions

    def create_session(
        self,
        cli_name: str,
        role_name: str,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Create a new session and return its ID."""
        session_id = str(uuid.uuid4())

        with self._lock:
            self._cleanup_expired()

            # Evict oldest if at capacity
            if len(self._sessions) >= self._max_sessions:
                self._evict_oldest()

            self._sessions[session_id] = SessionEntry(
                session_id=session_id,
                cli_name=cli_name,
                role_name=role_name,
                metadata=metadata or {},
            )
            logger.debug(f"Created session {session_id} for {cli_name}/{role_name}")

        return session_id

    def get_session(self, session_id: str) -> SessionEntry | None:
        """Retrieve a session by ID, updating access time."""
        with self._lock:
            self._cleanup_expired()

            entry = self._sessions.get(session_id)
            if entry is None:
                return None

            entry.touch()
            return entry

    def get_or_create_session(
        self,
        continuation_id: str | None,
        cli_name: str,
        role_name: str,
        metadata: dict[str, Any] | None = None,
    ) -> tuple[str, SessionEntry, bool]:
        """Get existing session or create new one.

        Returns:
            Tuple of (session_id, session_entry, is_new_session)
        """
        if continuation_id:
            existing = self.get_session(continuation_id)
            if existing:
                return continuation_id, existing, False
            logger.debug(f"Session {continuation_id} not found, creating new")

        new_id = self.create_session(cli_name, role_name, metadata)
        entry = self._sessions[new_id]
        return new_id, entry, True

    def delete_session(self, session_id: str) -> bool:
        """Delete a session by ID."""
        with self._lock:
            if session_id in self._sessions:
                del self._sessions[session_id]
                logger.debug(f"Deleted session {session_id}")
                return True
            return False

    def list_sessions(self) -> list[SessionEntry]:
        """List all active sessions."""
        with self._lock:
            self._cleanup_expired()
            return list(self._sessions.values())

    def _cleanup_expired(self) -> None:
        """Remove expired sessions (must be called with lock held)."""
        now = datetime.utcnow()
        expired = [
            sid
            for sid, entry in self._sessions.items()
            if now - entry.last_accessed > self._ttl
        ]
        for sid in expired:
            del self._sessions[sid]
            logger.debug(f"Expired session {sid}")

    def _evict_oldest(self) -> None:
        """Evict oldest session (must be called with lock held)."""
        if not self._sessions:
            return
        oldest_id = min(
            self._sessions.keys(),
            key=lambda sid: self._sessions[sid].last_accessed,
        )
        del self._sessions[oldest_id]
        logger.debug(f"Evicted oldest session {oldest_id}")


# Global session manager instance
_SESSION_MANAGER: SessionManager | None = None


def get_session_manager() -> SessionManager:
    """Get the global session manager instance."""
    global _SESSION_MANAGER
    if _SESSION_MANAGER is None:
        _SESSION_MANAGER = SessionManager()
    return _SESSION_MANAGER
