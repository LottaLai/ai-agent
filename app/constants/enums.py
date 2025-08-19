from enum import Enum


class MessageRole:
    """訊息角色常數 - 類似 Android 的 Constants"""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class PromptType(Enum):
    """Prompt 類型枚舉 - 類似 Android 的 enum"""

    INTENT_ANALYSIS = "intent_analysis"
    FOLLOW_UP_QUESTION = "follow_up_question"
    SEARCH_RESPONSE = "search_response"
    GENERAL_CHAT = "general_chat"
    LEGACY_RESTAURANT_SEARCH = "legacy_restaurant_search"
