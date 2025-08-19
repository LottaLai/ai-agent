# app/api/routes.py
import json
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException

from app.ai.domain.restaurant_knowledge import RestaurantDomainKnowledge
from app.constants.defaults import SearchDefaults
from app.constants.enums import MessageRole
from app.models.requests import SearchRequest
from app.models.responses import HealthResponse, RestaurantResponse, SearchResponseModel
from app.services.ai_service import GeminiAIService
from app.services.restaurant_service import RestaurantService
from app.services.session_service import SessionService
from config.dependencies import (
    get_ai_service,
    get_restaurant_service,
    get_session_service,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(status="healthy", timestamp=datetime.now())


@router.post("/search", response_model=SearchResponseModel)
async def search_restaurants(
    request: SearchRequest,
    restaurant_service: RestaurantService = Depends(get_restaurant_service),
    ai_service: GeminiAIService = Depends(get_ai_service),
    session_service: SessionService = Depends(get_session_service),
):
    """搜尋餐廳端點"""
    user_session = None

    try:
        # 1. 獲取/創建會話
        user_session = session_service.get_or_create(request.user_id)

        # 2. AI 分析用戶意圖
        ai_analysis = await _analyze_user_intent(ai_service, request, user_session)

        if not ai_analysis.get("success", False):
            return await _handle_analysis_failure(ai_service, user_session, request)

        # 3. 更新搜索條件
        extracted_info = ai_analysis.get("extracted_info", {})
        user_session.update_search_criteria(**extracted_info)
        user_session.add_message(MessageRole.USER, request.user_input)

        # 4. 檢查是否需要更多信息
        missing_info = _get_missing_required_fields(user_session, ai_analysis)

        if missing_info:
            return await _request_more_info(
                ai_service, user_session, missing_info, request.user_input
            )

        # 5. 執行搜索
        search_result = await _execute_search(restaurant_service, user_session, request)

        # 6. 生成回應
        response = await _build_search_response(
            ai_service, search_result, user_session, request
        )

        # 7. 清理會話狀態
        _cleanup_session(user_session)

        return response

    except Exception as e:
        logger.error(f"搜尋失敗: {str(e)}")
        if user_session:
            user_session.prepare_for_new_conversation()

        return SearchResponseModel(
            type="error",
            message="搜尋過程中發生錯誤，請重新開始搜尋。",
            recommendations=[],
            criteria=None,
            missing_fields=[],
            metadata={"error": True, "conversation_reset": True},
        )


# 輔助函數
async def _analyze_user_intent(ai_service, request, user_session):
    """分析用戶意圖"""
    return await ai_service.analyze_user_intent(
        user_input=request.user_input,
        session_history={},
        context={
            "location": request.location,
            "time": request.time,
            "is_fresh_conversation": True,
            "conversation_id": f"{request.user_id}_{datetime.now().timestamp()}",
        },
    )


async def _handle_analysis_failure(ai_service, user_session, request):
    """處理AI分析失敗的情況"""
    try:
        logger.info("🔄 使用降級邏輯")
        user_session.add_message(MessageRole.USER, request.user_input)

        legacy_response = await ai_service.legacy_restaurant_search(
            user_session.get_messages_for_ai()
        )

        # 嘗試解析為搜索參數
        try:
            search_params = json.loads(legacy_response)
            if "radius" in search_params and "cuisine" in search_params:
                user_session.update_search_criteria(**search_params)
                return {
                    "success": True,
                    "confidence": 0.8,
                    "extracted_info": search_params,
                    "missing_info": [],
                }
        except json.JSONDecodeError:
            pass

        user_session.add_message(MessageRole.ASSISTANT, legacy_response)
        return SearchResponseModel(
            type="partial",
            message=legacy_response,
            recommendations=[],
            criteria=None,
            missing_fields=["需要更多信息"],
            metadata={"fallback_used": True},
        )

    except Exception as e:
        logger.error(f"降級邏輯失敗: {e}")
        return SearchResponseModel(
            type="error",
            message="抱歉，我現在無法理解您的需求，請重新描述您想要的餐廳類型。",
            recommendations=[],
            criteria=None,
            missing_fields=[],
            metadata={"ai_analysis_failed": True},
        )


def _get_missing_required_fields(user_session, ai_analysis):
    """檢查缺失的必填欄位"""

    required_fields = RestaurantDomainKnowledge.REQUIRED_FIELDS
    current_data = user_session.data.__dict__ if user_session.data else {}

    missing_required = [
        field
        for field in required_fields
        if field not in current_data or not current_data[field]
    ]

    missing_from_ai = ai_analysis.get("missing_info", [])
    confidence = ai_analysis.get("confidence", 0.0)

    return missing_required + (missing_from_ai if confidence < 0.8 else [])


async def _request_more_info(ai_service, user_session, missing_info, user_input):
    """請求更多信息"""
    current_context = user_session.data.__dict__ if user_session.data else {}

    follow_up = await ai_service.generate_follow_up_question(
        missing_info=missing_info,
        current_context=current_context,
        user_input=user_input,
    )

    user_session.add_message(MessageRole.ASSISTANT, follow_up)

    return SearchResponseModel(
        type="partial",
        message=follow_up or "請提供更多信息以幫助我找到合適的餐廳。",
        recommendations=[],
        criteria=None,
        missing_fields=missing_info,
        metadata={
            "needs_more_info": True,
            "session_message_count": user_session.get_message_count(),
        },
    )


async def _execute_search(restaurant_service, user_session, request):
    """執行餐廳搜索"""
    from app.services.restaurant_service import LocationProcessor

    location_data = LocationProcessor.process_location_input(request.location)
    search_info = user_session.data.__dict__ if user_session.data else {}

    search_params = {
        "location_data": location_data,
        "search_radius_km": search_info.get("radius", SearchDefaults.RADIUS) / 1000,
        "cuisine": search_info.get("cuisine"),
        "price_level": search_info.get("price_level"),
        "rating_min": search_info.get("rating_min"),
        "try_new": search_info.get("try_new", SearchDefaults.TRY_NEW),
        "dietary_restrictions": search_info.get("dietary_restrictions"),
        "atmosphere": search_info.get("atmosphere"),
        "group_size": search_info.get("group_size"),
        "user_input": request.user_input,
        "time": request.time,
    }

    restaurants = await restaurant_service.search_engine.search_restaurants(
        search_params
    )
    restaurants = restaurant_service._post_process_restaurants(
        restaurants, location_data
    )

    return {
        "restaurants": restaurants,
        "search_params": search_params,
        "location_data": location_data,
        "search_info": search_info,
    }


async def _build_search_response(ai_service, search_result, user_session, request):
    """構建搜索回應"""
    import datetime as dt

    from app.services.restaurant_service import ResponseBuilder

    restaurants = search_result["restaurants"]
    search_params = search_result["search_params"]
    location_data = search_result["location_data"]
    search_info = search_result["search_info"]

    # AI 生成個性化回應
    ai_response = await ai_service.generate_search_response(
        restaurants=restaurants,
        user_preferences=search_info,
        search_params=search_params,
        user_input=request.user_input,
    )

    # 構建回應
    response = ResponseBuilder.build_response(restaurants, search_params, location_data)

    if ai_response and ai_response.get("message"):
        response.message = ai_response["message"]

    user_session.add_message(MessageRole.ASSISTANT, response.message)

    # 轉換為 API 格式
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
        for r in restaurants
    ]

    return SearchResponseModel(
        type=response.type.value,
        message=response.message,
        recommendations=restaurant_responses,
        criteria=response.criteria,
        missing_fields=[],
        metadata={
            **response.metadata,
            "conversation_status": "completed",
            "search_completed_at": datetime.now().isoformat(),
        },
    )


def clean_search_info(search_info):
    """清理 search_info 中的時間物件"""
    import datetime as dt

    if not isinstance(search_info, dict):
        return search_info

    cleaned = {}
    for key, value in search_info.items():
        if isinstance(value, dt.datetime):
            cleaned[key] = value.isoformat()
        elif isinstance(value, dt.time):
            cleaned[key] = value.strftime("%H:%M:%S")
        elif isinstance(value, dt.date):
            cleaned[key] = value.isoformat()
        elif isinstance(value, dict):
            cleaned[key] = clean_search_info(value)  # 遞迴處理巢狀字典
        elif isinstance(value, list):
            cleaned[key] = [
                clean_search_info(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            cleaned[key] = value

    return cleaned


def _cleanup_session(user_session):
    """清理會話狀態"""
    user_session.clear_history()
    user_session.reset_search_criteria()
    user_session.prepare_for_new_conversation()


# 會話管理端點（簡化版）
@router.get("/session/{user_id}/status")
async def get_session_status(
    user_id: str,
    session_service: SessionService = Depends(get_session_service),
):
    """獲取會話狀態"""
    try:
        user_session = session_service.get_or_create(user_id)
        return {
            "user_id": user_id,
            "is_ready_for_new_search": user_session.is_fresh_conversation(),
            "message_count": user_session.get_message_count(),
            "last_activity": user_session.updated_at.isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/session/{user_id}/clear")
async def clear_session(
    user_id: str,
    session_service: SessionService = Depends(get_session_service),
):
    """清除會話"""
    try:
        user_session = session_service.get_or_create(user_id)
        message_count = user_session.get_message_count()

        user_session.clear_history()
        user_session.reset_search_criteria()

        return {
            "message": "會話已清除",
            "cleared_messages": message_count,
            "user_id": user_id,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
