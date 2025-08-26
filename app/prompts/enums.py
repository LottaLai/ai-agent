from enum import Enum


class MessageRole:
    """訊息角色常數 - 類似 Android 的 Constants"""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class PromptType(Enum):
    """Prompt 類型枚舉 - 類似 Android 的 enum"""

    SMART_RESTAURANT_ANALYSIS = "smart_restaurant_analysis"

class ResponseType(Enum):
    """回應類型枚舉"""

    SUCCESS = "success"
    PARTIAL = "partial"
    ERROR = "error"


class RestaurantTag(Enum):
    """餐廳標籤枚舉"""

    CLASSIC = "經典"
    NEW_FLAVOR = "新口味"
    POPULAR = "熱門"
    BUDGET = "平價"
    PREMIUM = "高級"
