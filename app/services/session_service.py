import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from app.models.data_models import ChatMessage
from app.models.user_session import UserSession
from shared.utils.session_interface import SessionInterface


class SessionService:
    """會話業務邏輯層 - 精簡版"""

    def __init__(
        self, repository: SessionInterface, session_timeout: int = 3600
    ):
        self.repo = repository
        self.session_timeout = session_timeout
        self.logger = logging.getLogger(__name__)

    # === 核心會話操作 ===
    def get_or_create(self, user_id: str) -> UserSession:
        """獲取或創建用戶會話"""
        session = self.repo.get(user_id)
        if not session:
            session = UserSession(user_id=user_id)
            self.repo.save(session)
            self.logger.info(f"創建新會話: {user_id}")
        return session

    def clear_session(self, user_id: str) -> bool:
        """清除整個會話"""
        return self.repo.delete(user_id)

    # === 會話內容管理 ===
    def clear_history(self, user_id: str) -> bool:
        """清除會話歷史"""
        return self._execute_session_operation(
            user_id, lambda session: session.clear_history()
        )

    def rollback_messages(self, user_id: str, count: int = 1) -> List[ChatMessage]:
        """回滾訊息"""
        session = self.repo.get(user_id)
        if not session:
            return []

        rolled_back = session.rollback_last_messages(count)
        self.repo.save(session)
        return rolled_back

    # === 搜索條件管理 ===
    def update_search_criteria(self, user_id: str, **kwargs) -> bool:
        """更新搜索條件"""
        return self._execute_session_operation(
            user_id, lambda session: session.update_search_criteria(**kwargs)
        )

    def reset_search_criteria(self, user_id: str) -> bool:
        """重置搜索條件"""
        return self._execute_session_operation(
            user_id, lambda session: session.reset_search_criteria()
        )

    # === 會話信息查詢 ===
    def get_session_summary(self, user_id: str) -> Optional[Dict]:
        """獲取會話摘要"""
        session = self.repo.get(user_id)
        return session.get_session_summary() if session else None

    def export_session_data(self, user_id: str) -> Optional[Dict]:
        """導出會話數據"""
        session = self.repo.get(user_id)
        return session.to_dict() if session else None

    # === 批量操作 ===
    def get_all_sessions_info(self) -> List[Dict]:
        """獲取所有會話信息"""
        return [
            session.get_session_summary() for session in self.repo.list_all().values()
        ]

    def cleanup_inactive(self, inactive_minutes: Optional[int] = None) -> int:
        """清理不活躍的會話"""
        cutoff_minutes = inactive_minutes or (self.session_timeout // 60)
        cutoff_time = datetime.now() - timedelta(minutes=cutoff_minutes)

        removed_count = 0
        for user_id, session in list(self.repo.list_all().items()):
            if session.updated_at < cutoff_time:
                self.repo.delete(user_id)
                removed_count += 1

        return removed_count

    def get_statistics(self) -> Dict:
        """獲取統計信息"""
        sessions = self.repo.list_all()
        total_sessions = len(sessions)
        total_messages = sum(
            session.get_message_count() for session in sessions.values()
        )

        return {
            "total_sessions": total_sessions,
            "total_messages": total_messages,
            "average_messages_per_session": (
                total_messages / total_sessions if total_sessions > 0 else 0
            ),
        }

    # === 私有輔助方法 ===
    def _execute_session_operation(self, user_id: str, operation) -> bool:
        """執行會話操作的通用方法"""
        session = self.repo.get(user_id)
        if not session:
            return False

        operation(session)
        self.repo.save(session)
        return True

    def _cleanup_expired_sessions(self) -> None:
        """清理過期會話（內部使用）"""
        cutoff_time = datetime.now() - timedelta(seconds=self.session_timeout)

        for user_id, session in list(self.repo.list_all().items()):
            if session.updated_at < cutoff_time:
                self.repo.delete(user_id)
