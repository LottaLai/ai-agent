import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from models.data_models import ChatMessage
from models.user_session import UserSession
from repositories.session_repo_interface import SessionRepositoryInterface


class SessionService:
    """會話業務邏輯層"""

    def __init__(
        self, repository: SessionRepositoryInterface, session_timeout: int = 3600
    ):
        self.repo = repository
        self.session_timeout = int(session_timeout)  # 確保是 int 秒數

    def get_or_create(self, user_id: str) -> UserSession:
        session = self.repo.get(user_id)
        if not session:
            session = UserSession(user_id=user_id)
            self.repo.save(session)
            logging.info(f"創建新會話: {user_id}")
        return session

    def clear_session(self, user_id: str) -> bool:
        return self.repo.delete(user_id)

    def clear_history(self, user_id: str) -> bool:
        session = self.repo.get(user_id)
        if not session:
            return False
        session.clear_history()
        self.repo.save(session)
        return True

    def rollback_messages(self, user_id: str, count: int = 1) -> List[ChatMessage]:
        session = self.repo.get(user_id)
        if not session:
            return []
        rolled_back = session.rollback_last_messages(count)
        self.repo.save(session)
        return rolled_back

    def update_search_criteria(self, user_id: str, **kwargs) -> bool:
        session = self.repo.get(user_id)
        if not session:
            return False
        session.update_search_criteria(**kwargs)
        self.repo.save(session)
        return True

    def reset_search_criteria(self, user_id: str) -> bool:
        session = self.repo.get(user_id)
        if not session:
            return False
        session.reset_search_criteria()
        self.repo.save(session)
        return True

    def get_session_summary(self, user_id: str) -> Optional[Dict]:
        session = self.repo.get(user_id)
        return session.get_session_summary() if session else None

    def export_session_data(self, user_id: str) -> Optional[Dict]:
        session = self.repo.get(user_id)
        return session.to_dict() if session else None

    def get_all_sessions_info(self) -> List[Dict]:
        return [s.get_session_summary() for s in self.repo.list_all().values()]

    def cleanup_inactive(self, inactive_minutes: Optional[int] = None) -> int:
        # None → 預設 session_timeout 換算分鐘
        minutes_val: int = int(
            inactive_minutes
            if inactive_minutes is not None
            else self.session_timeout // 60
        )
        cutoff = datetime.now() - timedelta(minutes=minutes_val)
        removed = 0
        for uid, session in list(self.repo.list_all().items()):
            if session.updated_at < cutoff:
                self.repo.delete(uid)
                removed += 1
        return removed

    def _cleanup_expired_sessions(self) -> None:
        """內部：清理過期的會話"""
        cutoff = datetime.now() - timedelta(seconds=int(self.session_timeout))
        for uid, session in list(self.repo.list_all().items()):
            if session.updated_at < cutoff:
                self.repo.delete(uid)

    def get_statistics(self) -> Dict:
        sessions = self.repo.list_all()
        total = len(sessions)
        total_messages = sum(s.get_message_count() for s in sessions.values())
        return {
            "total_sessions": total,
            "total_messages": total_messages,
            "average_messages_per_session": total_messages / total if total else 0,
        }
