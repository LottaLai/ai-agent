import logging
from asyncio.log import logger
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from app.models.definitions import Restaurant, SearchResponse
from app.models.requests import LocationCoordinates
from app.prompts.enums import ResponseType
from shared.utils.geo import GeoUtils


class RestaurantService:
    """餐廳服務主類別"""

    def __init__(
        self, ai_service, session_service, db_restaurant_repo
    ):
        self.ai_service = ai_service
        self.session_service = session_service
        self.db_restaurant_repo = db_restaurant_repo

    def _process_location_input(
        self, location: Union[str, LocationCoordinates, None]
    ) -> Dict[str, Any]:
        """處理位置輸入"""
        if location is None:
            return {"type": "none"}

        if isinstance(location, str):
            # 嘗試解析座標字串
            parsed_coords = GeoUtils.parse_coordinates_string(location)
            if parsed_coords:
                return {
                    "type": "coordinates",
                    "latitude": parsed_coords.latitude,
                    "longitude": parsed_coords.longitude,
                }
            else:
                return {"type": "address", "address": location}

        elif isinstance(location, LocationCoordinates):
            return {
                "type": "coordinates",
                "latitude": location.latitude,
                "longitude": location.longitude,
            }

        return {"type": "unknown", "raw": str(location)}

    async def process_search_request(
        self,
        user_id: str,
        user_input: str,
        location: Union[str, LocationCoordinates, None],
        time: str,
        ai_analysis: Optional[str] = None,
    ) -> SearchResponse:
        """處理搜尋請求"""
        try:
            # 1. 處理位置資訊
            location_data = self._process_location_input(location)

            # 2. 解析 AI 分析結果
            search_params = self._parse_ai_analysis(ai_analysis, user_input)

            # 3. 構建搜尋參數
            db_search_params = self._build_database_search_params(
                location_data, search_params, time
            )

            # 4. 執行資料庫搜尋
            restaurants = await self.db_restaurant_repo.search_restaurants(**db_search_params)

            # 5. 後處理結果
            # restaurants = self._post_process_restaurants(restaurants, location_data)

            # 6. 構建回應
            return self._build_response(restaurants, search_params, location_data)

        except Exception as e:
            logging.error(f"搜尋請求處理失敗: {e}")
            return self._build_error_response()


    def _parse_ai_analysis(
        self, ai_analysis: Optional[str], user_input: str
    ) -> Dict[str, Any]:
        """解析 AI 分析結果"""
        search_params = {"user_input": user_input}

        if ai_analysis:
            try:
                import json
                ai_data = json.loads(ai_analysis)
                if isinstance(ai_data, dict):
                    search_params.update(ai_data)
            except Exception as e:
                logging.warning(f"AI 分析結果解析失敗: {e}")

        return search_params


    def _build_database_search_params(
        self, location_data: Dict[str, Any], search_params: Dict[str, Any], time: str
    ) -> Dict[str, Any]:
        """構建資料庫搜尋參數"""
        db_params = {
            "limit": 20,
        }

        # 位置參數
        if location_data.get("type") == "coordinates":
            db_params.update(
                {
                    "latitude": location_data["latitude"],
                    "longitude": location_data["longitude"],
                    "radius_km": search_params.get("radius", 5000) / 1000,  # 轉換為公里
                }
            )
        elif location_data.get("type") == "address":
            db_params["address"] = location_data["address"]

        # 搜尋條件
        if "cuisine" in search_params:
            db_params["cuisine"] = search_params["cuisine"]

        if "price_range" in search_params:
            db_params["price_range"] = search_params["price_range"]

        if "min_rating" in search_params:
            db_params["min_rating"] = search_params["min_rating"]

        # 關鍵字搜尋
        if "query" in search_params:
            db_params["query"] = search_params["query"]
        elif "user_input" in search_params:
            db_params["query"] = search_params["user_input"]

        return db_params

    def _build_response(
        self,
        restaurants: List[Restaurant],
        search_params: Dict[str, Any],
        location_data: Dict[str, Any],
    ) -> SearchResponse:
        """構建搜尋回應"""
        if restaurants:
            response_type = ResponseType.SUCCESS
            message = f"為您找到 {len(restaurants)} 家符合條件的餐廳"
        else:
            response_type = ResponseType.PARTIAL
            message = "抱歉，沒有找到符合條件的餐廳，請嘗試調整搜尋條件"

        metadata = {
            "search_params": search_params,
            "location_data": location_data,
            "total_found": len(restaurants),
            "timestamp": datetime.now().isoformat(),
        }

        return SearchResponse(
            type=response_type,
            message=message,
            recommendations=restaurants,
            criteria=search_params,
            missing_fields=[],
            metadata=metadata,
        )

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
