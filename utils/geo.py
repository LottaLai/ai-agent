# app/utils/geo.py
import math
from typing import Optional, Tuple

from models.requests import LocationCoordinates


class GeoUtils:
    """地理位置工具類"""

    @staticmethod
    def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        使用 Haversine 公式計算兩點間距離（公里）

        Args:
            lat1, lon1: 第一個點的緯度和經度
            lat2, lon2: 第二個點的緯度和經度

        Returns:
            距離（公里）
        """
        # 將角度轉換為弧度
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

        # Haversine 公式
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        )
        c = 2 * math.asin(math.sqrt(a))

        # 地球半徑（公里）
        r = 6371
        return c * r

    @staticmethod
    def is_valid_coordinates(latitude: float, longitude: float) -> bool:
        """
        驗證座標是否有效

        Args:
            latitude: 緯度
            longitude: 經度

        Returns:
            是否有效
        """
        return (-90 <= latitude <= 90) and (-180 <= longitude <= 180)

    @staticmethod
    def parse_coordinates_string(coord_str: str) -> Optional[LocationCoordinates]:
        """
        從字串解析座標
        支援格式：
        - "25.0330,121.5654"
        - "25.0330, 121.5654"
        - "lat:25.0330,lng:121.5654"

        Args:
            coord_str: 座標字串

        Returns:
            LocationCoordinates 物件或 None
        """
        if not coord_str:
            return None

        try:
            # 移除空格
            coord_str = coord_str.replace(" ", "")

            # 處理 "lat:25.0330,lng:121.5654" 格式
            if "lat:" in coord_str and "lng:" in coord_str:
                parts = coord_str.split(",")
                lat_part = next(p for p in parts if p.startswith("lat:"))
                lng_part = next(p for p in parts if p.startswith("lng:"))

                latitude = float(lat_part.replace("lat:", ""))
                longitude = float(lng_part.replace("lng:", ""))
            else:
                # 處理 "25.0330,121.5654" 格式
                parts = coord_str.split(",")
                if len(parts) != 2:
                    return None

                latitude = float(parts[0])
                longitude = float(parts[1])

            if GeoUtils.is_valid_coordinates(latitude, longitude):
                return LocationCoordinates(latitude=latitude, longitude=longitude)

        except (ValueError, StopIteration):
            pass

        return None

    @staticmethod
    def get_bounding_box(
        center_lat: float, center_lon: float, radius_km: float
    ) -> Tuple[float, float, float, float]:
        """
        根據中心點和半徑計算邊界框

        Args:
            center_lat: 中心點緯度
            center_lon: 中心點經度
            radius_km: 半徑（公里）

        Returns:
            (min_lat, max_lat, min_lon, max_lon)
        """
        # 地球半徑（公里）
        earth_radius = 6371

        # 計算緯度差異
        lat_diff = radius_km / earth_radius * (180 / math.pi)

        # 計算經度差異（考慮緯度影響）
        lon_diff = (
            radius_km
            / earth_radius
            * (180 / math.pi)
            / math.cos(math.radians(center_lat))
        )

        min_lat = center_lat - lat_diff
        max_lat = center_lat + lat_diff
        min_lon = center_lon - lon_diff
        max_lon = center_lon + lon_diff

        return min_lat, max_lat, min_lon, max_lon

    @staticmethod
    def format_coordinates(coords: LocationCoordinates, precision: int = 4) -> str:
        """
        格式化座標為字串

        Args:
            coords: 座標物件
            precision: 小數點精度

        Returns:
            格式化的座標字串
        """
        return f"{coords.latitude:.{precision}f},{coords.longitude:.{precision}f}"
