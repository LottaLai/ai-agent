# app/services/location_handler.py
"""位置處理服務 - 精簡版"""

from typing import Any, Dict, Optional, Union

from ai.models.requests import LocationCoordinates
from shared.utils.geo import GeoUtils


class LocationHandler:
    """位置處理器 - 精簡版"""

    # 預設搜尋半徑（公里）
    DEFAULT_RADIUS = {"coordinates": 5.0, "address": 10.0, "none": 15.0}

    @staticmethod
    def process_location(
        location: Union[str, LocationCoordinates, None],
    ) -> Dict[str, Any]:
        """處理位置資訊，統一轉換為標準格式"""

        if location is None:
            return {"type": "none"}

        if isinstance(location, str):
            # 嘗試解析座標字串
            coords = GeoUtils.parse_coordinates_string(location)
            if coords:
                return {
                    "type": "coordinates",
                    "latitude": coords.latitude,
                    "longitude": coords.longitude,
                }
            return {"type": "address", "address": location}

        if isinstance(location, LocationCoordinates):
            return {
                "type": "coordinates",
                "latitude": location.latitude,
                "longitude": location.longitude,
            }

        return {"type": "unknown"}

    @staticmethod
    def get_search_radius_km(location_data: Dict[str, Any]) -> float:
        """根據位置類型決定搜尋半徑"""
        location_type = location_data.get("type", "none")
        return LocationHandler.DEFAULT_RADIUS.get(location_type, 15.0)

    @staticmethod
    def calculate_distance(
        location_data: Dict[str, Any], restaurant_lat: float, restaurant_lon: float
    ) -> Optional[float]:
        """計算餐廳與用戶位置的距離（公里）"""

        if location_data.get("type") != "coordinates":
            return None

        user_lat = location_data.get("latitude")
        user_lon = location_data.get("longitude")

        if user_lat is None or user_lon is None:
            return None

        return GeoUtils.calculate_distance(
            user_lat, user_lon, restaurant_lat, restaurant_lon
        )

    @staticmethod
    def format_location(location_data: Dict[str, Any]) -> str:
        """格式化位置顯示"""
        location_type = location_data.get("type")

        if location_type == "coordinates":
            lat = location_data.get("latitude")
            lon = location_data.get("longitude")
            return f"座標 ({lat:.4f}, {lon:.4f})"
        elif location_type == "address":
            return location_data.get("address", "未知地址")
        else:
            return "未指定位置"

    @staticmethod
    def is_valid_location(location_data: Dict[str, Any]) -> bool:
        """檢查位置資料是否有效"""
        location_type = location_data.get("type")

        if location_type == "coordinates":
            return (
                location_data.get("latitude") is not None
                and location_data.get("longitude") is not None
            )
        elif location_type == "address":
            return bool(location_data.get("address"))

        return location_type == "none"  # "none" 也是有效狀態


# 輔助類別：位置處理器（進階功能）
class LocationProcessor:
    """位置處理器 - 提供更高級的處理功能"""

    @staticmethod
    def process_location_input(
        location: Union[str, LocationCoordinates, None],
    ) -> Dict[str, Any]:
        """處理位置輸入並添加額外資訊"""
        location_data = LocationHandler.process_location(location)

        # 添加搜尋半徑
        location_data["search_radius_km"] = LocationHandler.get_search_radius_km(
            location_data
        )

        # 添加格式化顯示
        location_data["formatted"] = LocationHandler.format_location(location_data)

        # 添加有效性檢查
        location_data["is_valid"] = LocationHandler.is_valid_location(location_data)

        return location_data
