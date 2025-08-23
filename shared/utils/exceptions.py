class RestaurantSearchError(Exception):
    """餐廳搜尋基礎異常"""

    pass


class InvalidSearchCriteriaError(RestaurantSearchError):
    """無效搜尋條件異常"""

    pass


class AIServiceError(RestaurantSearchError):
    """AI 服務異常"""

    pass


class SessionNotFoundError(RestaurantSearchError):
    """會話未找到異常"""

    pass


class ValidationError(RestaurantSearchError):
    """驗證異常"""

    pass
