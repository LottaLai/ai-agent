# app/services/location_handler.py
"""
位置處理服務 - 在 RestaurantService 中使用
"""
from typing import Any, Dict, Optional, Union

from models.requests import LocationCoordinates
from utils.geo import GeoUtils


class LocationHandler:
    """位置處理器"""

    @staticmethod
    def process_location(
        location: Union[str, LocationCoordinates, None],
    ) -> Dict[str, Any]:
        """
        處理位置資訊，統一轉換為標準格式

        Args:
            location: 位置資訊（字串地址或座標物件）

        Returns:
            標準化的位置資訊字典
        """
        if location is None:
            return {"type": "none"}

        if isinstance(location, str):
            # 檢查是否為座標字串格式
            parsed_coords = GeoUtils.parse_coordinates_string(location)
            if parsed_coords:
                return {
                    "type": "coordinates",
                    "latitude": parsed_coords.latitude,
                    "longitude": parsed_coords.longitude,
                    "formatted": GeoUtils.format_coordinates(parsed_coords),
                }
            else:
                return {"type": "address", "address": location, "formatted": location}

        elif isinstance(location, LocationCoordinates):
            return {
                "type": "coordinates",
                "latitude": location.latitude,
                "longitude": location.longitude,
                "formatted": GeoUtils.format_coordinates(location),
            }

        else:
            return {"type": "unknown", "raw": str(location)}

    @staticmethod
    def get_search_radius_km(location_data: Dict[str, Any]) -> float:
        """
        根據位置類型決定搜尋半徑

        Args:
            location_data: 處理後的位置資訊

        Returns:
            搜尋半徑（公里）
        """
        if location_data.get("type") == "coordinates":
            return 5.0  # 座標搜尋使用較小半徑
        elif location_data.get("type") == "address":
            return 10.0  # 地址搜尋使用較大半徑
        else:
            return 15.0  # 無位置資訊時使用更大半徑

    @staticmethod
    def calculate_restaurant_distance(
        location_data: Dict[str, Any], restaurant_lat: float, restaurant_lon: float
    ) -> Optional[float]:
        """
        計算餐廳與用戶位置的距離

        Args:
            location_data: 處理後的位置資訊
            restaurant_lat: 餐廳緯度
            restaurant_lon: 餐廳經度

        Returns:
            距離（公里）或 None
        """
        if location_data.get("type") == "coordinates":
            user_lat = location_data.get("latitude")
            user_lon = location_data.get("longitude")

            if user_lat is not None and user_lon is not None:
                return GeoUtils.calculate_distance(
                    user_lat, user_lon, restaurant_lat, restaurant_lon
                )

        return None


# 在 RestaurantService 中的使用範例
class RestaurantServiceExample:
    """餐廳服務範例 - 展示如何處理位置"""

    async def process_search_request(
        self,
        user_id: str,
        user_input: str,
        location: Union[str, LocationCoordinates, None],
        time: str,
    ):
        """
        處理搜尋請求

        Args:
            user_id: 用戶ID
            user_input: 用戶輸入
            location: 位置資訊（可能是字串或座標物件）
            time: 時間
        """
        # 1. 處理位置資訊
        location_data = LocationHandler.process_location(location)
        print(f"處理後的位置資訊: {location_data}")

        # 2. 根據位置類型調整搜尋策略
        search_radius = LocationHandler.get_search_radius_km(location_data)
        print(f"搜尋半徑: {search_radius} 公里")

        # 3. 如果有座標，可以計算距離
        if location_data.get("type") == "coordinates":
            # 示例餐廳座標（台北101附近）
            restaurant_lat, restaurant_lon = 25.0340, 121.5645
            distance = LocationHandler.calculate_restaurant_distance(
                location_data, restaurant_lat, restaurant_lon
            )
            if distance:
                print(f"餐廳距離: {distance:.2f} 公里")

        # 4. 執行搜尋邏輯...
        # 這裡可以根據 location_data 的類型執行不同的搜尋邏輯

        return {
            "location_processed": location_data,
            "search_radius": search_radius,
            "user_input": user_input,
            "time": time,
        }


# 使用範例
if __name__ == "__main__":
    import asyncio

    async def test_location_handling():
        service = RestaurantServiceExample()

        # 測試地址
        print("=== 測試地址 ===")
        result1 = await service.process_search_request(
            "user123", "找義大利餐廳", "台北市信義區", "18:00"
        )
        print(result1)
        print()

        # 測試座標
        print("=== 測試座標 ===")
        coords = LocationCoordinates(latitude=25.0330, longitude=121.5654)
        result2 = await service.process_search_request(
            "user123", "找義大利餐廳", coords, "18:00"
        )
        print(result2)
        print()

        # 測試座標字串
        print("=== 測試座標字串 ===")
        result3 = await service.process_search_request(
            "user123", "找義大利餐廳", "25.0330,121.5654", "18:00"
        )
        print(result3)

    asyncio.run(test_location_handling())
