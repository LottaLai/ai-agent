# app/api/routes.py
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException

from api.location_handler import LocationHandler
from core.dependencies import (
    get_ai_service,
    get_restaurant_service,
    get_session_service,
)
from models.requests import LocationCoordinates, SearchRequest
from models.responses import HealthResponse, RestaurantResponse, SearchResponseModel
from services.ai_service import GeminiAIService
from services.restaurant_service import RestaurantService
from services.session_service import SessionService
from utils.ai_response_utils import check_if_ai_has_follow_up_questions

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """健康檢查端點"""
    return HealthResponse(status="healthy", timestamp=datetime.now())


@router.post("/search", response_model=SearchResponseModel)
async def search_restaurants(
    request: SearchRequest,
    restaurant_service: RestaurantService = Depends(get_restaurant_service),
    ai_service: GeminiAIService = Depends(get_ai_service),
    session_service: SessionService = Depends(get_session_service),
):
    """搜尋餐廳端點 - 整合 AI 服務"""
    user_session = None
    try:
        # 1. 取得用戶會話
        user_session = session_service.get_or_create(request.user_id)

        # 2. 將新的用戶輸入加入會話歷史
        from models.data_models import ChatMessage

        user_session.add_message("user", request.user_input)

        # 3. 準備 AI 對話歷史（包含系統提示和過往對話）
        messages_for_ai = user_session.get_messages_for_ai()

        # 4. 調用 AI 服務生成回應
        logging.info(f"調用 AI 服務處理用戶請求: {request.user_input}")
        ai_response = await ai_service.generate_response(messages_for_ai)

        # 5. 將 AI 回應加入會話歷史
        user_session.add_message("assistant", ai_response)

        # 6. 解析 AI 回應並調用餐廳服務
        # 這裡需要解析 AI 回應來提取搜尋條件
        response = await restaurant_service.process_search_request(
            user_id=request.user_id,
            user_input=request.user_input,
            location=request.location,
            time=request.time,
            ai_analysis=ai_response,  # 傳遞 AI 分析結果
        )

        # 7. 檢查是否 AI 提供了建議且沒有追加問題
        has_recommendations = (
            response.recommendations and len(response.recommendations) > 0
        )
        has_follow_up_questions = check_if_ai_has_follow_up_questions(ai_response)

        if has_recommendations and not has_follow_up_questions:
            # AI 提供了建議且沒有追加問題，清除對話歷史
            logging.info(f"用戶 {request.user_id} 獲得餐廳建議，清除對話歷史")
            user_session.clear_history()

        # 7. 轉換為 API 回應格式
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

        result = SearchResponseModel(
            type=response.type.value,
            message=ai_response,
            recommendations=restaurant_responses,
            criteria=response.criteria,
            missing_fields=response.missing_fields,
            metadata={
                **response.metadata,
                "ai_processed": True,
                "session_message_count": len(user_session.history),
                "history_cleared": has_recommendations and not has_follow_up_questions,
            },
        )
        return result

    except Exception as e:
        logging.error(f"搜尋餐廳時發生錯誤: {str(e)}")
        if user_session:
            # 發生錯誤時也清除最後添加的消息，避免錯誤狀態保留
            user_session.rollback_last_messages(2)  # 回滾用戶消息和AI回應
        raise


@router.delete("/sessions/{user_id}")
async def clear_user_session(
    user_id: str, session_service: SessionService = Depends(get_session_service)
):
    """清除用戶會話"""
    try:
        success = session_service.clear_session(user_id)
        if success:
            return {"message": f"用戶 {user_id} 的會話已清除"}
        else:
            raise HTTPException(status_code=404, detail="會話不存在或清除失敗")
    except Exception as e:
        logging.error(f"清除會話失敗: {e}")
        raise HTTPException(status_code=500, detail="清除會話失敗")
