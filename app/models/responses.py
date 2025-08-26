# app/models/responses.py
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from app.models.definitions import Restaurant


class SearchResponseModel(BaseModel):
    """搜尋回應模型"""

    type: str
    message: str
    recommendations: List[Restaurant] = []
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
