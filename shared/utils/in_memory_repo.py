from datetime import datetime
from typing import Dict, Optional

from app.models.user_session import UserSession
from shared.utils.session_interface import SessionInterface


class InMemorySessionRepository(SessionInterface):
    """記憶體儲存會話"""

    def __init__(self, session_timeout: int = 3600):
        self.sessions: Dict[str, UserSession] = {}
        self.session_timeout = session_timeout

    def _cleanup_expired(self):
        now = datetime.now()
        expired = [
            uid
            for uid, s in self.sessions.items()
            if (now - s.updated_at).total_seconds() > self.session_timeout
        ]
        for uid in expired:
            del self.sessions[uid]

    def get(self, user_id: str) -> Optional[UserSession]:
        self._cleanup_expired()
        return self.sessions.get(user_id)

    def save(self, session: UserSession) -> None:
        self.sessions[session.user_id] = session

    def delete(self, user_id: str) -> bool:
        return self.sessions.pop(user_id, None) is not None

    def list_all(self) -> Dict[str, UserSession]:
        self._cleanup_expired()
        return dict(self.sessions)
