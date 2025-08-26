from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from app.models.data_models import SearchCriteria
from app.models.definitions import Restaurant
from app.prompts.enums import RestaurantTag
from app.repositories.interfaces.restaurant_repo_interface import (
    RestaurantRepositoryInterface,
)


class InMemoryRestaurantRepository(RestaurantRepositoryInterface):
    """記憶體餐廳資料庫"""

    def __init__(self, restaurants_data: List[Dict[str, Any]]):
        self.restaurants = [
            Restaurant(
                id=str(idx),
                name=r.get("name", ""),
                cuisine=r.get("cuisine", ""),
                distance_km=r.get("distance_km", 0),
                rating=r.get("rating", 0),
                price_level=r.get("price_level", 1),
                tags=r.get("tags", []),
                address=r.get("address"),
                phone=r.get("phone"),
                description=r.get("description"),
            )
            for idx, r in enumerate(restaurants_data)
        ]

    def find_by_criteria(self, criteria: SearchCriteria) -> List[Restaurant]:
        """根據條件搜尋餐廳"""
        if not criteria.radius or not criteria.cuisine:
            return []

        distance_km = criteria.radius / 1000
        results = []

        for restaurant in self.restaurants:
            # 基本條件篩選
            if (
                restaurant.distance_km
                or 0 <= distance_km
                and restaurant.cuisine == criteria.cuisine
            ):

                # 根據 try_new 篩選標籤
                if criteria.try_new:
                    if RestaurantTag.NEW_FLAVOR.value in restaurant.tags:
                        results.append(restaurant)
                else:
                    if RestaurantTag.CLASSIC.value in restaurant.tags:
                        results.append(restaurant)

        return sorted(results, key=lambda x: (x.distance_km, -x.rating))

    def get_by_id(self, restaurant_id: str) -> Optional[Restaurant]:
        """根據 ID 取得餐廳"""
        try:
            idx = int(restaurant_id)
            if 0 <= idx < len(self.restaurants):
                return self.restaurants[idx]
        except (ValueError, IndexError):
            pass
        return None
