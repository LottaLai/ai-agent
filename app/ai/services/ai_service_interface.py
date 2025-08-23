from abc import ABC, abstractmethod
from typing import List

from app.ai.models.data_models import ChatMessage


class AIServiceInterface(ABC):
    """AI 服務介面"""

    @abstractmethod
    async def generate_response(self, messages: List[ChatMessage]) -> str:
        """生成一般對話回應"""
        pass

    @abstractmethod
    async def analyze_user_intent(
        self, user_input: str, session_history: dict, context: dict
    ) -> dict:
        """分析用戶意圖"""
        pass

    @abstractmethod
    async def generate_follow_up_question(
        self, missing_info: list, current_context: dict, user_input: str
    ) -> str:
        """生成後續問題以收集缺失信息"""
        pass

    @abstractmethod
    async def generate_search_response(
        self,
        restaurants: list,
        user_preferences: dict,
        search_params: dict,
        user_input: str,
    ) -> dict:
        """生成個性化的搜尋結果回應"""
        pass
