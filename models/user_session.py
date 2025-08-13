from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from models.data_models import ChatMessage, SearchCriteria


@dataclass
class UserSession:
    """用戶會話實體"""

    user_id: str
    data: SearchCriteria = field(default_factory=SearchCriteria)
    history: List[ChatMessage] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def add_message(self, role: str, content: str):
        """添加訊息到會話歷史"""
        self.history.append(ChatMessage(role=role, content=content))
        self.updated_at = datetime.now()

    def clear_history(self):
        """清除所有會話歷史"""
        self.history.clear()
        self.updated_at = datetime.now()

    def get_messages_for_ai(self):
        """獲取適合 AI 處理的訊息格式"""
        return self.history

    def rollback_last_messages(self, count: int = 1) -> List[ChatMessage]:
        """
        回滾最後 N 條訊息

        Args:
            count: 要回滾的訊息數量

        Returns:
            List[ChatMessage]: 被回滾的訊息列表
        """
        if count <= 0:
            return []

        # 確保不會回滾超過現有訊息數量
        actual_count = min(count, len(self.history))

        # 取出要回滾的訊息
        rolled_back_messages = self.history[-actual_count:] if actual_count > 0 else []

        # 從歷史中移除這些訊息
        self.history = (
            self.history[:-actual_count] if actual_count > 0 else self.history
        )

        # 更新時間戳
        self.updated_at = datetime.now()

        return rolled_back_messages

    def get_last_messages(self, count: int = 1) -> List[ChatMessage]:
        """
        獲取最後 N 條訊息（不移除）

        Args:
            count: 要獲取的訊息數量

        Returns:
            List[ChatMessage]: 最後的訊息列表
        """
        if count <= 0:
            return []
        return self.history[-count:] if self.history else []

    def get_message_count(self) -> int:
        """獲取訊息總數"""
        return len(self.history)

    def get_last_user_message(self) -> Optional[ChatMessage]:
        """獲取最後一條用戶訊息"""
        for message in reversed(self.history):
            if message.role == "user":
                return message
        return None

    def get_last_assistant_message(self) -> Optional[ChatMessage]:
        """獲取最後一條助手訊息"""
        for message in reversed(self.history):
            if message.role == "assistant":
                return message
        return None

    def remove_message_by_index(self, index: int) -> Optional[ChatMessage]:
        """
        根據索引移除訊息

        Args:
            index: 訊息在歷史中的索引

        Returns:
            ChatMessage: 被移除的訊息，如果索引無效則返回 None
        """
        if 0 <= index < len(self.history):
            removed_message = self.history.pop(index)
            self.updated_at = datetime.now()
            return removed_message
        return None

    def is_empty(self) -> bool:
        """檢查會話歷史是否為空"""
        return len(self.history) == 0

    def get_messages_by_role(self, role: str) -> List[ChatMessage]:
        """
        根據角色獲取訊息

        Args:
            role: 訊息角色 (user, assistant, system 等)

        Returns:
            List[ChatMessage]: 指定角色的訊息列表
        """
        return [msg for msg in self.history if msg.role == role]

    def get_conversation_duration(self) -> float:
        """
        獲取會話持續時間（秒）

        Returns:
            float: 從創建到最後更新的時間差（秒）
        """
        return (self.updated_at - self.created_at).total_seconds()

    def has_recent_activity(self, minutes: int = 30) -> bool:
        """
        檢查是否有最近的活動

        Args:
            minutes: 檢查最近多少分鐘內的活動

        Returns:
            bool: True 如果在指定時間內有活動
        """
        time_diff = (datetime.now() - self.updated_at).total_seconds()
        return time_diff <= (minutes * 60)

    def update_search_criteria(self, **kwargs):
        """
        更新搜索條件

        Args:
            **kwargs: 要更新的搜索條件字段
        """
        for key, value in kwargs.items():
            if hasattr(self.data, key):
                setattr(self.data, key, value)
        self.updated_at = datetime.now()

    def reset_search_criteria(self):
        """重置搜索條件"""
        self.data = SearchCriteria()
        self.updated_at = datetime.now()

    def to_dict(self) -> dict:
        """
        轉換為字典格式，方便序列化

        Returns:
            dict: 會話資料的字典表示
        """
        return {
            "user_id": self.user_id,
            "data": (
                self.data.__dict__ if hasattr(self.data, "__dict__") else str(self.data)
            ),
            "history": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": (
                        msg.timestamp.isoformat() if hasattr(msg, "timestamp") else None
                    ),
                }
                for msg in self.history
            ],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "message_count": len(self.history),
            "conversation_duration": self.get_conversation_duration(),
        }

    def get_session_summary(self) -> dict:
        """
        獲取會話摘要資訊

        Returns:
            dict: 會話摘要
        """
        user_messages = self.get_messages_by_role("user")
        assistant_messages = self.get_messages_by_role("assistant")

        return {
            "user_id": self.user_id,
            "total_messages": len(self.history),
            "user_messages": len(user_messages),
            "assistant_messages": len(assistant_messages),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "duration_minutes": self.get_conversation_duration() / 60,
            "is_active": self.has_recent_activity(),
            "has_search_criteria": bool(self.data),
            "last_user_input": user_messages[-1].content if user_messages else None,
            "last_assistant_response": (
                assistant_messages[-1].content if assistant_messages else None
            ),
        }

    def __str__(self) -> str:
        return f"UserSession(user_id={self.user_id}, messages={len(self.history)}, updated={self.updated_at})"

    def __repr__(self) -> str:
        return self.__str__()
