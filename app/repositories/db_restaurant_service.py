# app/services/db_restaurant_service.py
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import asyncpg

from app.models.definitions import Restaurant, SearchResponse
from app.models.enums import ResponseType
from app.models.requests import LocationCoordinates
from app.utils.geo import GeoUtils


class DatabaseRestaurantRepository:
    """資料庫餐廳資料存取層"""

    def __init__(self, db_pool: asyncpg.Pool):
        self.db_pool = db_pool

    async def search_restaurants(
        self,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        radius_km: Optional[float] = None,
        address: Optional[str] = None,
        query: Optional[str] = None,
        cuisine: Optional[str] = None,
        price_range: Optional[str] = None,
        min_rating: Optional[float] = None,
        limit: int = 20,
        **kwargs,
    ) -> List[Restaurant]:
        """多條件搜尋餐廳"""

        async with self.db_pool.acquire() as conn:
            try:
                # 基礎 SQL 查詢
                base_query = """
                SELECT
                    r.restaurant_id,
                    r.name,
                    r.name_en,
                    r.cuisine_type,
                    r.address,
                    r.phone,
                    r.latitude,
                    r.longitude,
                    r.average_rating,
                    r.price_range,
                    r.description,
                    r.short_description,
                    r.featured_image_url,
                    r.total_reviews,
                    r.opening_hours,
                    r.accepts_reservations,
                    COALESCE(
                        CASE
                            WHEN $1::NUMERIC IS NOT NULL AND $2::NUMERIC IS NOT NULL
                            THEN calculate_distance($1, $2, r.latitude, r.longitude)
                            ELSE NULL
                        END,
                        0
                    ) as distance_km
                FROM restaurants r
                WHERE r.status = 'active'
                """

                params: List[Any] = [latitude, longitude]
                param_count = 2
                conditions = []

                # 地理位置條件
                if (
                    latitude is not None
                    and longitude is not None
                    and radius_km is not None
                ):
                    param_count += 1
                    conditions.append(
                        f"""
                        r.latitude IS NOT NULL
                        AND r.longitude IS NOT NULL
                        AND calculate_distance($1, $2, r.latitude, r.longitude) <= ${param_count}
                    """
                    )
                    params.append(radius_km)

                # 地址搜尋
                if address:
                    param_count += 1
                    conditions.append(f"r.address ILIKE ${param_count}")
                    params.append(f"%{address}%")

                # 菜系搜尋
                if cuisine:
                    param_count += 1
                    conditions.append(f"${param_count} = ANY(r.cuisine_type)")
                    params.append(cuisine)

                # 價格範圍
                if price_range:
                    param_count += 1
                    conditions.append(f"r.price_range = ${param_count}")
                    params.append(price_range)

                # 最低評分
                if min_rating:
                    param_count += 1
                    conditions.append(f"r.average_rating >= ${param_count}")
                    params.append(min_rating)

                # 關鍵字搜尋
                if query:
                    param_count += 1
                    conditions.append(
                        f"""
                        (r.name ILIKE ${param_count}
                         OR r.description ILIKE ${param_count}
                         OR r.short_description ILIKE ${param_count}
                         OR EXISTS (
                             SELECT 1 FROM unnest(r.cuisine_type) AS ct
                             WHERE ct ILIKE ${param_count}
                         ))
                    """
                    )
                    params.append(f"%{query}%")

                # 組合條件
                if conditions:
                    base_query += " AND " + " AND ".join(conditions)

                # 排序和限制
                base_query += """
                ORDER BY
                    CASE WHEN distance_km > 0 THEN distance_km ELSE 999 END ASC,
                    r.average_rating DESC,
                    r.total_reviews DESC
                LIMIT $""" + str(
                    param_count + 1
                )
                params.append(limit)

                # 執行查詢
                rows = await conn.fetch(base_query, *params)

                restaurants = []
                for row in rows:
                    # 獲取餐廳標籤
                    tags = await self._get_restaurant_tags(conn, row["restaurant_id"])

                    restaurant = Restaurant(
                        id=str(row["restaurant_id"]),
                        name=row["name"],
                        cuisine=(
                            ", ".join(row["cuisine_type"])
                            if row["cuisine_type"]
                            else ""
                        ),
                        distance_km=(
                            float(row["distance_km"]) if row["distance_km"] else None
                        ),
                        rating=(
                            float(row["average_rating"])
                            if row["average_rating"]
                            else 0.0
                        ),
                        price_level=self._convert_price_range_to_level(
                            row["price_range"]
                        ),
                        tags=tags,
                        address=row["address"],
                        phone=row["phone"],
                        description=row["description"] or row["short_description"],
                        latitude=float(row["latitude"]) if row["latitude"] else None,
                        longitude=float(row["longitude"]) if row["longitude"] else None,
                    )
                    restaurants.append(restaurant)

                return restaurants

            except Exception as e:
                logging.error(f"資料庫搜尋錯誤: {e}")
                return []

    async def _get_restaurant_tags(
        self, conn: asyncpg.Connection, restaurant_id: int
    ) -> List[str]:
        """獲取餐廳標籤"""
        try:
            query = """
            SELECT rt.tag_name
            FROM restaurant_tag_assignments rta
            JOIN restaurant_tags rt ON rta.tag_id = rt.tag_id
            WHERE rta.restaurant_id = $1 AND rta.is_verified = true
            ORDER BY rta.relevance_score DESC
            """
            rows = await conn.fetch(query, restaurant_id)
            return [row["tag_name"] for row in rows]
        except Exception as e:
            logging.error(f"獲取餐廳標籤錯誤: {e}")
            return []

    def _convert_price_range_to_level(self, price_range: str) -> int:
        """將價格範圍轉換為等級"""
        price_map = {
            "budget": 1,
            "low_mid": 2,
            "mid_range": 2,
            "high_mid": 3,
            "expensive": 4,
            "luxury": 4,
        }
        return price_map.get(price_range, 2)

    async def get_restaurant_by_id(self, restaurant_id: str) -> Optional[Restaurant]:
        """根據 ID 獲取餐廳詳細資訊"""
        async with self.db_pool.acquire() as conn:
            try:
                query = """
                SELECT
                    r.restaurant_id, r.name, r.name_en, r.cuisine_type,
                    r.address, r.phone, r.latitude, r.longitude,
                    r.average_rating, r.price_range, r.description,
                    r.short_description, r.featured_image_url, r.total_reviews,
                    r.opening_hours, r.accepts_reservations, r.website_url,
                    r.email, r.gallery_images, r.menu_pdf_url
                FROM restaurants r
                WHERE r.restaurant_id = $1 AND r.status = 'active'
                """

                row = await conn.fetchrow(query, int(restaurant_id))
                if not row:
                    return None

                tags = await self._get_restaurant_tags(conn, row["restaurant_id"])

                return Restaurant(
                    id=str(row["restaurant_id"]),
                    name=row["name"],
                    cuisine=(
                        ", ".join(row["cuisine_type"]) if row["cuisine_type"] else ""
                    ),
                    distance_km=None,
                    rating=(
                        float(row["average_rating"]) if row["average_rating"] else 0.0
                    ),
                    price_level=self._convert_price_range_to_level(row["price_range"]),
                    tags=tags,
                    address=row["address"],
                    phone=row["phone"],
                    description=row["description"] or row["short_description"],
                    latitude=float(row["latitude"]) if row["latitude"] else None,
                    longitude=float(row["longitude"]) if row["longitude"] else None,
                )

            except Exception as e:
                logging.error(f"獲取餐廳詳情錯誤: {e}")
                return None

    async def get_popular_cuisines(self, limit: int = 10) -> List[Dict[str, Any]]:
        """獲取熱門菜系"""
        async with self.db_pool.acquire() as conn:
            try:
                query = """
                SELECT
                    unnest(cuisine_type) as cuisine,
                    COUNT(*) as restaurant_count,
                    AVG(average_rating) as avg_rating
                FROM restaurants
                WHERE status = 'active' AND cuisine_type IS NOT NULL
                GROUP BY unnest(cuisine_type)
                ORDER BY restaurant_count DESC, avg_rating DESC
                LIMIT $1
                """
                rows = await conn.fetch(query, limit)
                return [
                    {
                        "cuisine": row["cuisine"],
                        "restaurant_count": row["restaurant_count"],
                        "avg_rating": (
                            float(row["avg_rating"]) if row["avg_rating"] else 0.0
                        ),
                    }
                    for row in rows
                ]
            except Exception as e:
                logging.error(f"獲取熱門菜系錯誤: {e}")
                return []


class DatabaseRestaurantService:
    """資料庫餐廳服務"""

    def __init__(self, ai_service, session_service, db_pool: asyncpg.Pool):
        self.ai_service = ai_service
        self.session_service = session_service
        self.repository = DatabaseRestaurantRepository(db_pool)

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
            restaurants = await self.repository.search_restaurants(**db_search_params)

            # 5. 後處理結果
            restaurants = self._post_process_restaurants(restaurants, location_data)

            # 6. 構建回應
            return self._build_response(restaurants, search_params, location_data)

        except Exception as e:
            logging.error(f"搜尋請求處理失敗: {e}")
            return self._build_error_response()

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
