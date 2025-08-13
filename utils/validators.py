import re
from typing import Union


class Validators:
    """驗證工具類"""

    @staticmethod
    def validate_user_id(user_id: str) -> bool:
        if not user_id or not isinstance(user_id, str):
            return False
        return len(user_id.strip()) > 0

    @staticmethod
    def validate_radius(radius: Union[int, str]) -> bool:
        try:
            r = int(radius) if isinstance(radius, str) else radius
            return 100 <= r <= 50000
        except (ValueError, TypeError):
            return False

    @staticmethod
    def validate_cuisine(cuisine: str) -> bool:
        if not cuisine or not isinstance(cuisine, str):
            return False
        return len(cuisine.strip()) > 0
