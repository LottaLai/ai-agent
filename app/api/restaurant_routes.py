# app/api/routes.py
import logging

from fastapi import APIRouter, Depends

from app.core.dependencies import (
    get_ai_service,
    get_restaurant_service,
    get_session_service,
)
from app.models.requests import SearchRequest
from app.models.responses import SearchResponseModel
from app.prompts.enums import MessageRole
from app.services.gemini_ai_service import GeminiAIService
from app.services.restaurant_service import RestaurantService
from app.services.session_service import SessionService

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/search", response_model=SearchResponseModel)
async def search_restaurants(
    request: SearchRequest,
    restaurant_service: RestaurantService = Depends(get_restaurant_service),
    ai_service: GeminiAIService = Depends(get_ai_service),
    session_service: SessionService = Depends(get_session_service),
):
    """簡化版餐廳搜尋 - 一次性獲取完整參數"""
    user_session = None

    try:
        # 1. 獲取/創建會話
        user_session = session_service.get_or_create(request.user_id)
        logging.info(f"🔍 處理用戶 {request.user_id} 的搜尋請求")

        # 2. 智能分析 - 一次性獲取完整參數
        context = {
            "location": request.location,
            "time": request.time,
            "user_id": request.user_id
        }

        analysis_result = await ai_service.smart_analyze_user_input(
            request.user_input,
            context
        )

        if not analysis_result.get("success", False):
            return SearchResponseModel(
                type="error",
                message="抱歉，無法理解您的需求，請重新描述。",
                recommendations=[],
                criteria=None,
                missing_fields=[],
                metadata={"analysis_failed": True}
            )

        # 3. 獲取完整搜尋參數
        search_params = analysis_result["search_params"]
        confidence = analysis_result.get("confidence", 0.8)

        # 4. 記錄會話
        user_session.add_message(MessageRole.USER, request.user_input)

        # 5. 執行搜尋
        search_result = await _execute_smart_search(
            restaurant_service,
            request,
            search_params
        )

        # 6. 生成回應
        response = await _build_smart_response(
            ai_service,
            restaurant_service,
            search_result,
            search_params,
            request,
            confidence
        )

        # 7. 記錄 AI 回應
        user_session.add_message(MessageRole.ASSISTANT, response.message)

        return response

    except Exception as e:
        logger.error(f"搜尋失敗: {str(e)}", exc_info=True)
        return SearchResponseModel(
            type="error",
            message="搜尋過程中發生錯誤，請重新嘗試。",
            recommendations=[],
            criteria=None,
            missing_fields=[],
            metadata={"error": True, "error_message": str(e)}
        )

async def _execute_smart_search(
    restaurant_service: RestaurantService,
    request: SearchRequest,
    search_params: dict
) -> dict:
    """執行智能搜尋"""
    try:
        # 處理位置
        location_data = restaurant_service._process_location_input(request.location)

        # 構建資料庫搜尋參數
        db_params = {
            "limit": 20,
            "cuisine": search_params["cuisine"] if search_params["cuisine"] != "其他" else None,
            "min_rating": search_params["min_rating"],
        }

        # 價格範圍轉換
        price_map = {1: "budget", 2: "mid_range", 3: "high_mid", 4: "expensive"}
        db_params["price_range"] = price_map.get(search_params["price_level"], "mid_range")

        # 位置參數
        if location_data.get("type") == "coordinates":
            db_params.update({
                "latitude": location_data["latitude"],
                "longitude": location_data["longitude"],
                "radius_km": search_params["radius_meters"] / 1000.0
            })
        elif location_data.get("type") == "address":
            db_params["address"] = location_data["address"]
            db_params["radius_km"] = search_params["radius_meters"] / 1000.0

        # 執行搜尋
        restaurants = await restaurant_service.db_restaurant_repo.search_restaurants(**db_params)

        # 後處理
        restaurants = restaurant_service._post_process_restaurants(restaurants, location_data)

        return {
            "restaurants": restaurants,
            "search_params": search_params,
            "db_params": db_params,
            "location_data": location_data
        }

    except Exception as e:
        logger.error(f"智能搜尋執行失敗: {e}")
        return {
            "restaurants": [],
            "search_params": search_params,
            "db_params": {},
            "location_data": {"type": "none"},
            "error": str(e)
        }

async def _build_smart_response(
    ai_service,
    restaurant_service,
    search_result: dict,
    search_params: dict,
    request: SearchRequest,
    confidence: float
) -> SearchResponseModel:
    """構建智能回應"""
    restaurants = search_result["restaurants"]

    # 生成個性化訊息
    if restaurants:
        if confidence > 0.8:
            message = f"根據您的需求，為您找到 {len(restaurants)} 家{search_params['cuisine']}餐廳"
        else:
            message = f"為您推薦 {len(restaurants)} 家餐廳，如果不符合需求請告訴我更具體的要求"
    else:
        message = "抱歉，沒有找到符合條件的餐廳。建議您擴大搜尋範圍或調整條件。"

    # 轉換餐廳資料
    restaurant_responses = []
    for r in restaurants :
        try:
            restaurant_responses.append(r)
        except Exception as e:
            logger.warning(f"轉換餐廳資料失敗: {e}")
            continue

    return SearchResponseModel(
        type="success" if restaurants else "partial",
        message=message,
        recommendations=restaurant_responses,
        criteria={
            "cuisine": search_params["cuisine"],
            "radius_meters": search_params["radius_meters"],
            "price_level": search_params["price_level"],
            "min_rating": search_params["min_rating"]
        },
        missing_fields=[],
        metadata={
            "ai_confidence": confidence,
            "search_completed": True,
            "total_found": len(restaurants),
            "search_params_used": search_params,
            "fallback_used": search_result.get("error") is not None
        }
    )

