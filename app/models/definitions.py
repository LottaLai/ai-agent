from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from app.prompts.enums import ResponseType


@dataclass
class Restaurant:
    """餐廳資料模型"""
    restaurant_id: int
    name: str
    name_en: Optional[str] = None
    cuisine_type: Optional[Union[str, List[str]]] = None
    price_range: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    district: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    average_rating: Optional[float] = None
    total_reviews: Optional[int] = None
    total_visits: Optional[int] = None
    popularity_score: Optional[float] = None
    status: Optional[str] = None
    verified: Optional[bool] = None
    description: Optional[str] = None
    is_featured: Optional[bool] = None
    is_sponsored: Optional[bool] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    distance_km: Optional[float] = None  # 計算欄位

    def __post_init__(self):
        if self.average_rating and self.average_rating > 5:
            self.average_rating = self.average_rating / 2  # 可能是10分制轉5分制



@dataclass
class SearchResponse:
    """搜尋回應資料類別"""

    type: ResponseType
    message: str
    recommendations: List[Restaurant]
    criteria: Optional[Dict[str, Any]]
    missing_fields: List[str]
    metadata: Dict[str, Any]
