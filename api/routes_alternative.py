# app/api/routes_alternative.py
"""
替代方案：在 API 層處理位置資訊
"""
import logging
from datetime import datetime
from typing import Union

from fastapi import APIRouter, Depends, HTTPException

from api.location_handler import LocationHandler
from core.dependencies import get_restaurant_service
from models.requests import LocationCoordinates, SearchRequest
from models.responses import RestaurantResponse, SearchResponseModel
from services.restaurant_service import RestaurantService

router = APIRouter()


@router.post("/search", response_model=SearchResponseModel)
async def search_restaurants_v2(
    request: SearchRequest, service: RestaurantService = Depends(get_restaurant_service)
):
    """搜尋餐廳端點 - 方案2：API層處理位置"""
    try:
        # 在 API 層處理位置資訊
        location_data = LocationHandler.process_location(request.location)

        location_for_service = _convert_location_for_service(location_data)

        # 如果服務層需要特定格式，可以在這裡轉換
        if hasattr(service, "process_search_request_v2"):
            # 新版本的服務方法，接受處理過的位置資料
            response = await service.process_search_request(
                user_id=request.user_id,
                user_input=request.user_input,
                location=location_for_service,  # 傳遞處理過的位置資料
                time=request.time,
            )
        else:
            # 舊版本兼容，傳遞原始位置或轉換為字串
            location_for_service = _convert_location_for_legacy_service(location_data)
            response = await service.process_search_request(
                user_id=request.user_id,
                user_input=request.user_input,
                location=location_for_service,
                time=request.time,
            )

        # 轉換為 API 回應格式
        restaurant_responses = [
            RestaurantResponse(
                id=r.id,
                name=r.name,
                cuisine=r.cuisine,
                distance_km=r.distance_km or 0.0,
                rating=r.rating,
                price_level=r.price_level,
                tags=r.tags,
                address=r.address,
                phone=r.phone,
                description=r.description,
            )
            for r in response.recommendations
        ]

        return SearchResponseModel(
            type=response.type.value,
            message=response.message,
            recommendations=restaurant_responses,
            criteria=response.criteria,
            missing_fields=response.missing_fields,
            metadata={
                **response.metadata,
                "location_data": location_data,  # 包含處理過的位置資訊
            },
        )

    except Exception as e:
        logging.error(f"搜尋請求處理失敗: {e}")
        raise HTTPException(status_code=500, detail="內部伺服器錯誤")


def _convert_location_for_legacy_service(location_data: dict) -> str:
    """
    將處理過的位置資料轉換為舊版服務能接受的格式

    Args:
        location_data: 處理過的位置資料

    Returns:
        適合舊版服務的位置字串
    """
    location_type = location_data.get("type")

    if location_type == "address":
        return location_data.get("address", "")
    elif location_type == "coordinates":
        # 轉換為座標字串格式
        lat = location_data.get("latitude")
        lon = location_data.get("longitude")
        return f"{lat},{lon}" if lat is not None and lon is not None else ""
    else:
        return ""


def _convert_location_for_service(
    location_data: dict,
) -> Union[str, LocationCoordinates, None]:
    loc_type = location_data.get("type")

    if loc_type == "coordinates":
        latitude = location_data.get("latitude")
        longitude = location_data.get("longitude")
        if latitude is not None and longitude is not None:
            return LocationCoordinates(latitude=latitude, longitude=longitude)
        return None
    elif loc_type == "address":
        return location_data.get("address")
    elif loc_type == "none":
        return None
    else:
        return None


# 增強版的搜尋端點，提供更多位置相關資訊
@router.post("/search/enhanced", response_model=SearchResponseModel)
async def search_restaurants_enhanced(
    request: SearchRequest, service: RestaurantService = Depends(get_restaurant_service)
):
    """增強版搜尋端點 - 提供詳細的位置處理資訊"""
    try:
        # 處理位置資訊
        location_data = LocationHandler.process_location(request.location)
        search_radius = LocationHandler.get_search_radius_km(location_data)

        # 記錄詳細的位置資訊
        location_info = {
            "original_input": request.location,
            "processed_data": location_data,
            "search_radius_km": search_radius,
            "location_type": location_data.get("type"),
        }

        # 如果是座標，添加邊界框資訊
        if location_data.get("type") == "coordinates":
            from utils.geo import GeoUtils

            min_lat, max_lat, min_lon, max_lon = GeoUtils.get_bounding_box(
                location_data["latitude"], location_data["longitude"], search_radius
            )
            location_info["bounding_box"] = {
                "min_lat": min_lat,
                "max_lat": max_lat,
                "min_lon": min_lon,
                "max_lon": max_lon,
            }

        # 呼叫服務
        response = await service.process_search_request(
            user_id=request.user_id,
            user_input=request.user_input,
            location=request.location,
            time=request.time,
        )

        # 如果有座標資訊，計算每個餐廳的精確距離
        restaurant_responses = []
        for r in response.recommendations:
            restaurant_response = RestaurantResponse(
                id=r.id,
                name=r.name,
                cuisine=r.cuisine,
                distance_km=r.distance_km or 0,
                rating=r.rating,
                price_level=r.price_level,
                tags=r.tags,
                address=r.address,
                phone=r.phone,
                description=r.description,
            )

            # 如果有座標和餐廳座標，重新計算精確距離
            if (
                location_data.get("type") == "coordinates"
                and hasattr(r, "latitude")
                and hasattr(r, "longitude")
            ):
                precise_distance = LocationHandler.calculate_restaurant_distance(
                    location_data, r.latitude or 0.0, r.longitude or 0.0
                )
                if precise_distance is not None:
                    restaurant_response.distance_km = round(precise_distance, 2)

            restaurant_responses.append(restaurant_response)

        return SearchResponseModel(
            type=response.type.value,
            message=response.message,
            recommendations=restaurant_responses,
            criteria=response.criteria,
            missing_fields=response.missing_fields,
            metadata={**response.metadata, "location_info": location_info},
        )

    except Exception as e:
        logging.error(f"增強版搜尋請求處理失敗: {e}")
        raise HTTPException(status_code=500, detail="內部伺服器錯誤")
