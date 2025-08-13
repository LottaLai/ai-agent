from enum import Enum


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
