import logging
from asyncio.log import logger
from dataclasses import asdict
from typing import Any, Dict, List, Optional, Union

from api.location_handler import LocationHandler
from models.data_models import ChatMessage, SearchCriteria
from models.definitions import Restaurant, SearchResponse
from models.enums import ResponseType, RestaurantTag
from models.requests import LocationCoordinates
from utils.geo import GeoUtils


class RestaurantRepository:
    """餐廳資料庫存取層"""

    def __init__(self):
        # 為測試資料添加座標和描述
        self.restaurants = [
            Restaurant(
                id="1",
                name="築地壽司",
                cuisine="日式",
                distance_km=2.5,
                rating=4.5,
                price_level=3,
                tags=["經典", "壽司"],
                address="台北市大安區忠孝東路四段100號",
                phone="02-1234-5678",
                latitude=25.0418,
                longitude=121.5440,
                description="正宗日式壽司，新鮮食材",
            ),
            Restaurant(
                id="2",
                name="新宿拉麵",
                cuisine="日式",
                distance_km=1.8,
                rating=4.2,
                price_level=2,
                tags=["新口味", "拉麵"],
                address="台北市信義區信義路五段7號",
                phone="02-2345-6789",
                latitude=25.0330,
                longitude=121.5654,
                description="創新日式拉麵，口味獨特",
            ),
            Restaurant(
                id="3",
                name="川味軒",
                cuisine="川菜",
                distance_km=3.2,
                rating=4.3,
                price_level=2,
                tags=["經典", "辣味"],
                address="台北市中山區南京東路二段76號",
                phone="02-3456-7890",
                latitude=25.0520,
                longitude=121.5347,
                description="道地川菜，香辣過癮",
            ),
            Restaurant(
                id="4",
                name="義式風情",
                cuisine="義大利菜",
                distance_km=2.8,
                rating=4.6,
                price_level=3,
                tags=["經典", "義式"],
                address="台北市大安區敦化南路一段187號",
                phone="02-4567-8901",
                latitude=25.0405,
                longitude=121.5487,
                description="正宗義大利料理，浪漫氛圍",
            ),
        ]

    def find_by_criteria(self, criteria: SearchCriteria) -> List[Restaurant]:
        """根據搜尋條件查找餐廳（原有方法）"""
        if not criteria.radius or not criteria.cuisine:
            return []

        distance_km = criteria.radius / 1000
        results = []

        for restaurant in self.restaurants:
            if (
                isinstance(restaurant.distance_km, (int, float))
                and restaurant.distance_km <= distance_km
                and restaurant.cuisine == criteria.cuisine
            ):
                tag_match = (
                    RestaurantTag.NEW_FLAVOR.value in restaurant.tags
                    if criteria.try_new
                    else RestaurantTag.CLASSIC.value in restaurant.tags
                )

                if tag_match:
                    results.append(restaurant)

        return sorted(results, key=lambda x: (x.distance_km, -x.rating))

    async def search_restaurants(
        self,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        radius_km: Optional[float] = None,
        address: Optional[str] = None,
        query: Optional[str] = None,
        cuisine: Optional[str] = None,
        **kwargs,
    ) -> List[Restaurant]:
        """多條件搜尋餐廳"""
        try:
            results = self.restaurants.copy()

            # 應用各種過濾條件
            if latitude is not None and longitude is not None and radius_km is not None:
                results = self._filter_by_coordinates(
                    results, latitude, longitude, radius_km
                )
            elif address:
                results = self._filter_by_address(results, address)
            elif query:
                results = self._filter_by_query(results, query)

            if cuisine:
                results = [r for r in results if r.cuisine == cuisine]

            return results

        except Exception as e:
            logger.error(f"餐廳搜尋錯誤: {e}", exc_info=True)
            return []

    def _filter_by_coordinates(
        self, restaurants: List[Restaurant], lat: float, lon: float, radius_km: float
    ) -> List[Restaurant]:
        """根據座標和半徑過濾餐廳"""
        filtered = []
        for restaurant in restaurants:
            if self._has_coordinates(restaurant):
                distance = GeoUtils.calculate_distance(
                    lat, lon, restaurant.latitude or 0, restaurant.longitude or 0
                )
                if distance <= radius_km:
                    # 創建副本以避免修改原始資料
                    restaurant_copy = self._copy_restaurant_with_distance(
                        restaurant, distance
                    )
                    filtered.append(restaurant_copy)
        return filtered

    def _filter_by_address(
        self, restaurants: List[Restaurant], address: str
    ) -> List[Restaurant]:
        """根據地址過濾餐廳"""
        address_lower = address.lower()
        return [
            restaurant
            for restaurant in restaurants
            if restaurant.address and address_lower in restaurant.address.lower()
        ]

    def _filter_by_query(
        self, restaurants: List[Restaurant], query: str
    ) -> List[Restaurant]:
        """根據關鍵字過濾餐廳"""
        query_lower = query.lower()
        filtered = []

        for restaurant in restaurants:
            searchable_fields = [
                restaurant.name or "",
                restaurant.cuisine or "",
                getattr(restaurant, "description", "") or "",
                " ".join(restaurant.tags or []),
            ]
            searchable_text = " ".join(searchable_fields).lower()

            if query_lower in searchable_text:
                filtered.append(restaurant)

        return filtered

    def _has_coordinates(self, restaurant: Restaurant) -> bool:
        """檢查餐廳是否有座標資訊"""
        return (
            hasattr(restaurant, "latitude")
            and hasattr(restaurant, "longitude")
            and restaurant.latitude is not None
            and restaurant.longitude is not None
        )

    def _copy_restaurant_with_distance(
        self, restaurant: Restaurant, distance: float
    ) -> Restaurant:
        """創建餐廳副本並設定距離"""
        # 這裡假設 Restaurant 是可以複製的
        # 如果不行，可能需要根據你的 Restaurant 類別調整
        restaurant_dict = restaurant.__dict__.copy()
        restaurant_dict["distance_km"] = round(distance, 2)
        return Restaurant(**restaurant_dict)


class LocationProcessor:
    """位置資訊處理器"""

    @staticmethod
    def process_location_input(
        location: Union[str, LocationCoordinates, None],
    ) -> Dict[str, Any]:
        """處理各種格式的位置輸入"""
        if location is None:
            return {"type": "none"}

        if isinstance(location, str):
            return LocationProcessor._process_string_location(location)
        elif isinstance(location, LocationCoordinates):
            return {
                "type": "coordinates",
                "latitude": location.latitude,
                "longitude": location.longitude,
                "source": "coordinates_object",
            }

        return {"type": "unknown", "raw": str(location)}

    @staticmethod
    def _process_string_location(location: str) -> Dict[str, Any]:
        """處理字串格式的位置"""
        # API 層轉換的座標格式
        if location.startswith("coords:"):
            coord_str = location.replace("coords:", "")
            parsed_coords = GeoUtils.parse_coordinates_string(coord_str)
            if parsed_coords:
                return {
                    "type": "coordinates",
                    "latitude": parsed_coords.latitude,
                    "longitude": parsed_coords.longitude,
                    "source": "api_converted",
                }

        # 直接座標字串
        parsed_coords = GeoUtils.parse_coordinates_string(location)
        if parsed_coords:
            return {
                "type": "coordinates",
                "latitude": parsed_coords.latitude,
                "longitude": parsed_coords.longitude,
                "source": "parsed_string",
            }

        # 普通地址字串
        return {"type": "address", "address": location, "source": "direct_input"}


class SearchParameterBuilder:
    """搜尋參數建構器"""

    @staticmethod
    def build_search_parameters(
        location_data: Dict[str, Any],
        user_input: str,
        time: str,
        ai_analysis: Optional[str] = None,  # 新增參數，AI 分析結果
    ) -> Dict[str, Any]:
        """構建搜尋參數"""
        search_radius = LocationHandler.get_search_radius_km(location_data)

        params = {
            "user_input": user_input,
            "time": time,
            "location_data": location_data,
            "search_radius_km": search_radius,
        }

        # 如果有 AI 分析結果，嘗試解析並優化搜尋條件
        if ai_analysis:
            try:
                import json

                ai_data = json.loads(ai_analysis)
                # 範例：AI 可能回傳 {"cuisine": "日式", "radius": 10}
                if isinstance(ai_data, dict):
                    if "cuisine" in ai_data:
                        params["cuisine"] = ai_data["cuisine"]
                    if "radius" in ai_data:
                        params["search_radius_km"] = ai_data["radius"]
                    if "keywords" in ai_data:
                        params["keywords"] = ai_data["keywords"]
            except Exception as e:
                import logging

                logging.warning(f"AI 分析結果解析失敗，忽略: {e}")

        # 如果有座標，添加邊界框
        if location_data.get("type") == "coordinates":
            bounding_box = GeoUtils.get_bounding_box(
                location_data["latitude"], location_data["longitude"], search_radius
            )
            params["bounding_box"] = {
                "min_lat": bounding_box[0],
                "max_lat": bounding_box[1],
                "min_lon": bounding_box[2],
                "max_lon": bounding_box[3],
            }

        return params


class ResponseBuilder:
    """回應建構器"""

    @staticmethod
    def build_response(
        restaurants: List[Restaurant],
        search_params: Dict[str, Any],
        location_data: Dict[str, Any],
    ) -> SearchResponse:
        """構建搜尋回應"""
        metadata = ResponseBuilder._build_metadata(
            restaurants, search_params, location_data
        )
        response_type, message = ResponseBuilder._determine_response_type_and_message(
            restaurants
        )
        criteria = ResponseBuilder._build_criteria(search_params, location_data)

        return SearchResponse(
            type=response_type,
            message=message,
            recommendations=restaurants,
            criteria=criteria,
            missing_fields=[],  # 可根據需求調整
            metadata=metadata,
        )

    @staticmethod
    def _build_metadata(
        restaurants: List[Restaurant],
        search_params: Dict[str, Any],
        location_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """構建元數據"""
        metadata = {
            "location_processing": {
                "input_type": location_data.get("source"),
                "processed_type": location_data.get("type"),
                "search_radius_km": search_params.get("search_radius_km"),
                "total_found": len(restaurants),
            }
        }

        location_type = location_data.get("type")
        if location_type == "coordinates":
            metadata["location_processing"]["coordinates"] = {
                "latitude": location_data.get("latitude"),
                "longitude": location_data.get("longitude"),
            }
            if "bounding_box" in search_params:
                metadata["location_processing"]["bounding_box"] = search_params[
                    "bounding_box"
                ]
        elif location_type == "address":
            metadata["location_processing"]["address"] = location_data.get("address")

        return metadata

    @staticmethod
    def _determine_response_type_and_message(restaurants: List[Restaurant]) -> tuple:
        """判斷回應類型和訊息"""
        if restaurants:
            return ResponseType.SUCCESS, f"為您找到 {len(restaurants)} 家符合條件的餐廳"
        else:
            return (
                ResponseType.PARTIAL,
                "抱歉，沒有找到符合條件的餐廳，請嘗試調整搜尋條件",
            )

    @staticmethod
    def _build_criteria(
        search_params: Dict[str, Any], location_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """構建搜尋條件"""
        criteria = {
            "user_input": search_params.get("user_input"),
            "time": search_params.get("time"),
            "location_type": location_data.get("type"),
        }

        location_type = location_data.get("type")
        if location_type == "coordinates":
            criteria["coordinates"] = {
                "latitude": location_data.get("latitude"),
                "longitude": location_data.get("longitude"),
            }
        elif location_type == "address":
            criteria["address"] = location_data.get("address")

        return criteria


class RestaurantSearchEngine:
    """餐廳搜尋引擎"""

    def __init__(self, restaurant_repo: RestaurantRepository):
        self.restaurant_repo = restaurant_repo

    async def search_restaurants(
        self, search_params: Dict[str, Any]
    ) -> List[Restaurant]:
        """執行餐廳搜尋"""
        location_data = search_params["location_data"]
        location_type = location_data.get("type")

        try:
            if location_type == "coordinates":
                return await self._search_by_coordinates(search_params)
            elif location_type == "address":
                return await self._search_by_address(search_params)
            else:
                return await self._search_without_location(search_params)
        except Exception as e:
            logger.error(f"搜尋執行錯誤: {e}", exc_info=True)
            return []

    async def _search_by_coordinates(
        self, search_params: Dict[str, Any]
    ) -> List[Restaurant]:
        """基於座標的搜尋"""
        location_data = search_params["location_data"]
        return await self.restaurant_repo.search_restaurants(
            latitude=location_data["latitude"],
            longitude=location_data["longitude"],
            radius_km=search_params["search_radius_km"],
        )

    async def _search_by_address(
        self, search_params: Dict[str, Any]
    ) -> List[Restaurant]:
        """基於地址的搜尋"""
        location_data = search_params["location_data"]
        address = location_data.get("address")

        if address:
            return await self.restaurant_repo.search_restaurants(
                address=address, radius_km=search_params["search_radius_km"]
            )
        return []

    async def _search_without_location(
        self, search_params: Dict[str, Any]
    ) -> List[Restaurant]:
        """無位置資訊的搜尋"""
        user_input = search_params.get("user_input", "")
        return await self.restaurant_repo.search_restaurants(query=user_input)


class RestaurantService:
    """餐廳服務主類別"""

    def __init__(
        self, ai_service, session_service, restaurant_repo: RestaurantRepository
    ):
        self.ai_service = ai_service
        self.session_service = session_service
        self.restaurant_repo = restaurant_repo
        self.search_engine = RestaurantSearchEngine(restaurant_repo)

    async def process_search_request(
        self,
        user_id: str,
        user_input: str,
        location: Union[str, LocationCoordinates, None],
        time: str,
        ai_analysis: Optional[str] = None,  # 新增參數，預設可為 None
    ) -> SearchResponse:
        """處理搜尋請求"""
        try:
            # 1. 處理位置資訊
            location_data = LocationProcessor.process_location_input(location)

            # 2. 構建搜尋參數
            search_params = SearchParameterBuilder.build_search_parameters(
                location_data, user_input, time, ai_analysis
            )

            # 3. 執行搜尋
            restaurants = await self.search_engine.search_restaurants(search_params)

            # 4. 後處理：計算距離和排序
            restaurants = self._post_process_restaurants(restaurants, location_data)

            # 5. 構建回應
            return ResponseBuilder.build_response(
                restaurants, search_params, location_data
            )

        except Exception as e:
            logger.error(f"搜尋請求處理失敗: {e}", exc_info=True)
            return ResponseBuilder.build_response([], {}, {"type": "error"})

    def _post_process_restaurants(
        self, restaurants: List[Restaurant], location_data: Dict[str, Any]
    ) -> List[Restaurant]:
        """後處理餐廳資料：計算距離和排序"""
        if location_data.get("type") == "coordinates":
            restaurants = self._calculate_distances(restaurants, location_data)
            restaurants = self._sort_by_distance(restaurants)
        return restaurants

    def _calculate_distances(
        self, restaurants: List[Restaurant], location_data: Dict[str, Any]
    ) -> List[Restaurant]:
        """計算餐廳距離"""
        user_lat = location_data.get("latitude", 0)
        user_lon = location_data.get("longitude", 0)

        for restaurant in restaurants:
            if hasattr(restaurant, "latitude") and hasattr(restaurant, "longitude"):
                if restaurant.latitude is not None and restaurant.longitude is not None:
                    distance = GeoUtils.calculate_distance(
                        user_lat, user_lon, restaurant.latitude, restaurant.longitude
                    )
                    restaurant.distance_km = round(distance, 2)
                else:
                    restaurant.distance_km = None

        return restaurants

    def _sort_by_distance(self, restaurants: List[Restaurant]) -> List[Restaurant]:
        """按距離排序"""
        return sorted(
            restaurants,
            key=lambda r: r.distance_km if r.distance_km is not None else float("inf"),
        )
