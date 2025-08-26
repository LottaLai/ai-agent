from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from app.models.data_models import ChatMessage, SearchCriteria


@dataclass
class UserSession:
    """用戶會話實體 - 精簡版"""

    user_id: str
    data: SearchCriteria = field(default_factory=SearchCriteria)
    history: List[ChatMessage] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    # === 核心訊息操作 ===
    def add_message(self, role: str, content: str):
        """添加訊息到會話歷史"""
        self.history.append(ChatMessage(role=role, content=content))
        self._update_timestamp()

    def clear_history(self):
        """清除所有會話歷史"""
        self.history.clear()
        self._update_timestamp()

    # === 訊息查詢 ===
    def get_message_count(self) -> int:
        """獲取訊息總數"""
        return len(self.history)

    def get_last_messages(self, count: int = 1) -> List[ChatMessage]:
        """獲取最後 N 條訊息"""
        return self.history[-count:] if count > 0 and self.history else []

    def get_recent_messages(self, limit: int = 10) -> List[dict]:
        """獲取最近的 N 條訊息，返回字典格式（適用於API響應）"""
        recent_messages = self.get_last_messages(limit)
        return [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": getattr(msg, "timestamp", None),
            }
            for msg in recent_messages
        ]

    def get_messages_by_role(self, role: str) -> List[ChatMessage]:
        """根據角色獲取訊息"""
        return [msg for msg in self.history if msg.role == role]

    # === 搜索條件管理 ===
    def update_search_criteria(self, **kwargs):
        """更新搜索條件"""
        for key, value in kwargs.items():
            if hasattr(self.data, key):
                setattr(self.data, key, value)
        self._update_timestamp()

    def reset_search_criteria(self):
        """重置搜索條件"""
        self.data = SearchCriteria()
        self._update_timestamp()

    # === 會話狀態管理 ===
    def prepare_for_new_conversation(self):
        """準備新對話 - 清除所有上下文"""
        self.clear_history()
        self.reset_search_criteria()
        self.add_message("system", "新對話開始")

    def is_fresh_conversation(self) -> bool:
        """檢查是否為全新對話"""
        return len(self.get_messages_by_role("user")) == 0

    # === 實用工具方法 ===
    def get_conversation_duration(self) -> float:
        """獲取會話持續時間（秒）"""
        return (self.updated_at - self.created_at).total_seconds()

    def has_recent_activity(self, minutes: int = 30) -> bool:
        """檢查是否有最近的活動"""
        time_diff = (datetime.now() - self.updated_at).total_seconds()
        return time_diff <= (minutes * 60)

    # === 進階操作（可選） ===
    def rollback_last_messages(self, count: int = 1) -> List[ChatMessage]:
        """回滾最後 N 條訊息"""
        if count <= 0:
            return []

        actual_count = min(count, len(self.history))
        rolled_back = self.history[-actual_count:] if actual_count > 0 else []
        self.history = (
            self.history[:-actual_count] if actual_count > 0 else self.history
        )
        self._update_timestamp()

        return rolled_back

    # === 序列化 ===
    def get_session_summary(self) -> dict:
        """獲取會話摘要"""
        user_msgs = self.get_messages_by_role("user")
        assistant_msgs = self.get_messages_by_role("assistant")

        return {
            "user_id": self.user_id,
            "total_messages": len(self.history),
            "user_messages": len(user_msgs),
            "assistant_messages": len(assistant_msgs),
            "duration_minutes": self.get_conversation_duration() / 60,
            "is_active": self.has_recent_activity(),
            "is_fresh": self.is_fresh_conversation(),
            "last_user_input": user_msgs[-1].content if user_msgs else None,
            "last_assistant_response": (
                assistant_msgs[-1].content if assistant_msgs else None
            ),
        }

    def to_dict(self) -> dict:
        """轉換為字典格式"""
        return {
            "user_id": self.user_id,
            "data": (
                self.data.__dict__ if hasattr(self.data, "__dict__") else str(self.data)
            ),
            "history": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": getattr(msg, "timestamp", None),
                }
                for msg in self.history
            ],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "message_count": len(self.history),
        }

    # === 私有輔助方法 ===
    def _update_timestamp(self):
        """更新時間戳"""
        self.updated_at = datetime.now()
