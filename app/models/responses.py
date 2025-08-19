# app/models/responses.py
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class RestaurantResponse(BaseModel):
    """餐廳回應模型"""

    id: str
    name: str
    cuisine: str
    distance_km: float
    rating: float
    price_level: int
    tags: List[str]
    address: Optional[str] = None
    phone: Optional[str] = None
    description: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "id": "rest001",
                "name": "義式風情餐廳",
                "cuisine": "義大利菜",
                "distance_km": 1.2,
                "rating": 4.5,
                "price_level": 3,
                "tags": ["浪漫", "約會", "正宗"],
                "address": "台北市信義區信義路五段7號",
                "phone": "02-2345-6789",
                "description": "正宗義大利料理，浪漫用餐環境",
            }
        }


class SearchResponseModel(BaseModel):
    """搜尋回應模型"""

    type: str
    message: Optional[str] = None
    recommendations: List[RestaurantResponse] = []
    criteria: Optional[Dict[str, Any]] = None
    missing_fields: List[str] = []
    metadata: Dict[str, Any] = {}

    class Config:
        json_schema_extra = {
            "example": {
                "type": "success",
                "message": "為您找到 3 家符合條件的餐廳",
                "recommendations": [
                    {
                        "id": "rest001",
                        "name": "義式風情餐廳",
                        "cuisine": "義大利菜",
                        "distance_km": 1.2,
                        "rating": 4.5,
                        "price_level": 3,
                        "tags": ["浪漫", "約會", "正宗"],
                    }
                ],
                "criteria": {"cuisine": "義大利菜", "location": "台北市信義區"},
                "missing_fields": [],
                "metadata": {"search_time": "2024-01-15T18:00:00", "total_found": 3},
            }
        }


class HealthResponse(BaseModel):
    """健康檢查回應"""

    status: str
    timestamp: datetime
    version: str = "1.0.0"

    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2024-01-15T18:00:00.000Z",
                "version": "1.0.0",
            }
        }
