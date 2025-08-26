# app/services/db_restaurant_service.py
import logging
from typing import Any, Dict, List

from app.models.definitions import Restaurant, SearchResponse
from app.prompts.enums import ResponseType
from app.repositories.database_restaurant_repo import DatabaseRestaurantRepository
from shared.utils.geo import GeoUtils


class DatabaseRestaurantService:
    """資料庫餐廳服務"""

    def __init__(self, ai_service, session_service, repository: DatabaseRestaurantRepository):
        self.ai_service = ai_service
        self.session_service = session_service
        self.repository = repository

    def _post_process_restaurants(
        self, restaurants: List[Restaurant], location_data: Dict[str, Any]
    ) -> List[Restaurant]:
        """後處理餐廳資料"""
        # 如果有座標資訊，重新計算精確距離
        if location_data.get("type") == "coordinates":
            user_lat = location_data["latitude"]
            user_lon = location_data["longitude"]

            for restaurant in restaurants:
                if restaurant.latitude and restaurant.longitude:
                    distance = GeoUtils.calculate_distance(
                        user_lat, user_lon, restaurant.latitude, restaurant.longitude
                    )
                    restaurant.distance_km = round(distance, 2)

        return restaurants


    def _build_error_response(self) -> SearchResponse:
        """構建錯誤回應"""
        return SearchResponse(
            type=ResponseType.ERROR,
            message="搜尋服務發生錯誤，請稍後再試",
            recommendations=[],
            criteria=None,
            missing_fields=[],
            metadata={"error": True},
        )
