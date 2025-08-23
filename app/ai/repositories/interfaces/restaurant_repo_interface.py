from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from ai.models.data_models import SearchCriteria
from ai.models.definitions import Restaurant


class RestaurantRepositoryInterface(ABC):
    """餐廳資料存取介面"""

    @abstractmethod
    def find_by_criteria(self, criteria: SearchCriteria) -> List[Restaurant]:
        """根據條件搜尋餐廳"""
        pass

    @abstractmethod
    def get_by_id(self, restaurant_id: str) -> Optional[Restaurant]:
        """根據 ID 取得餐廳"""
        pass
