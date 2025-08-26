# app/utils/geo.py
import math
from typing import Optional, Tuple

from app.models.requests import LocationCoordinates


class GeoUtils:
    """地理位置工具類"""

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
