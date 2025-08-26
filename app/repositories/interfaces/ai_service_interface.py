from abc import ABC, abstractmethod

class AIServiceInterface(ABC):
    """AI 服務介面"""

    @abstractmethod
    async def smart_analyze_user_input(self, user_input: str, context: dict
    ) -> dict:
        """智能分析用戶輸入，總是回傳完整的搜尋參數"""
        pass
