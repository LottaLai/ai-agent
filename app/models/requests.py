# app/models/requests.py
from typing import Optional, Union

from pydantic import BaseModel, Field, validator


class LocationCoordinates(BaseModel):
    """座標位置模型"""

    latitude: float = Field(..., description="緯度", ge=-90, le=90)
    longitude: float = Field(..., description="經度", ge=-180, le=180)

    class Config:
        json_schema_extra = {"example": {"latitude": 25.0330, "longitude": 121.5654}}


class SearchRequest(BaseModel):
    """搜尋請求模型"""

    user_id: str = Field(..., description="用戶 ID")
    user_input: str = Field(..., description="用戶輸入")
    location: Optional[Union[str, LocationCoordinates]] = Field(
        None, description="位置 - 可以是地址字串或經緯度座標"
    )
    time: str = Field("", description="時間，格式: HH:MM")

    @validator("location", pre=True)
    def validate_location(cls, v):
        """驗證位置格式"""
        if v is None or v == "":
            return None

        # 如果是字典且包含 latitude 和 longitude，轉換為 LocationCoordinates
        if isinstance(v, dict) and "latitude" in v and "longitude" in v:
            return LocationCoordinates(**v)

        # 如果是字串，保持原樣
        if isinstance(v, str):
            return v

        # 如果已經是 LocationCoordinates，直接返回
        if isinstance(v, LocationCoordinates):
            return v

        return v

    def get_location_type(self) -> str:
        """取得位置類型"""
        if self.location is None:
            return "none"
        elif isinstance(self.location, str):
            return "address"
        elif isinstance(self.location, LocationCoordinates):
            return "coordinates"
        return "unknown"

    def get_coordinates(self) -> Optional[LocationCoordinates]:
        """取得座標（如果有的話）"""
        if isinstance(self.location, LocationCoordinates):
            return self.location
        return None

    def get_address(self) -> Optional[str]:
        """取得地址（如果有的話）"""
        if isinstance(self.location, str):
            return self.location
        return None

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "name": "使用地址搜尋",
                    "value": {
                        "user_id": "user123",
                        "user_input": "我想要找一家義大利餐廳",
                        "location": "台北市信義區",
                        "time": "18:00",
                    },
                },
                {
                    "name": "使用座標搜尋",
                    "value": {
                        "user_id": "user123",
                        "user_input": "我想要找一家義大利餐廳",
                        "location": {"latitude": 25.0330, "longitude": 121.5654},
                        "time": "18:00",
                    },
                },
            ]
        }
