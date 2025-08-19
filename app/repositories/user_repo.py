from abc import ABC, abstractmethod
from typing import Any, Dict


class UserRepositoryInterface(ABC):
    """用戶資料存取介面"""

    @abstractmethod
    def get_preferences(self, user_id: str) -> Dict[str, Any]:
        """取得用戶偏好"""
        pass

    @abstractmethod
    def update_preferences(self, user_id: str, preferences: Dict[str, Any]) -> bool:
        """更新用戶偏好"""
        pass


class InMemoryUserRepository(UserRepositoryInterface):
    """記憶體用戶資料庫"""

    def __init__(self):
        self.user_preferences: Dict[str, Dict[str, Any]] = {}

    def get_preferences(self, user_id: str) -> Dict[str, Any]:
        """取得用戶偏好"""
        return self.user_preferences.get(user_id, {})

    def update_preferences(self, user_id: str, preferences: Dict[str, Any]) -> bool:
        """更新用戶偏好"""
        try:
            self.user_preferences[user_id] = preferences
            return True
        except Exception:
            return False
