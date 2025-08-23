from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from app.ai.models.requests import LocationCoordinates
from app.ai.prompts.enums import ResponseType


@dataclass
class Restaurant:
    """餐廳資料模型"""

    id: str
    name: str
    cuisine: str
    rating: float
    price_level: int
    tags: List[str]
    address: Optional[str] = None
    phone: Optional[str] = None
    description: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    distance_km: Optional[float] = None


@dataclass
class SearchResponse:
    """搜尋回應資料類別"""

    type: ResponseType
    message: str
    recommendations: List[Restaurant]
    criteria: Optional[Dict[str, Any]]
    missing_fields: List[str]
    metadata: Dict[str, Any]


@dataclass
class LocationData:
    """位置資料模型"""

    type: str  # "coordinates", "address", "none"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: Optional[str] = None
    source: Optional[str] = None
    formatted: Optional[str] = None


@dataclass
class SearchParameters:
    """搜尋參數模型"""

    user_input: str
    time: str
    location_data: LocationData
    search_radius_km: float
    bounding_box: Optional[Dict[str, float]] = None


@dataclass
class BoundingBox:
    """邊界框模型"""

    min_lat: float
    max_lat: float
    min_lon: float
    max_lon: float


# 類型別名
RestaurantList = List[Restaurant]
LocationInput = Union[str, "LocationCoordinates", None]
SearchResult = SearchResponse
