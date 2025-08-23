# app/api/routes.py
import json
import logging
from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException

from app.ai.config.constants import SearchDefaults
from app.ai.core.dependencies import (
    get_ai_service,
    get_restaurant_service,
    get_session_service,
)
from app.ai.domain.restaurant_knowledge import RestaurantDomainKnowledge
from app.ai.models.requests import SearchRequest
from app.ai.models.responses import (
    HealthResponse,
    RestaurantResponse,
    SearchResponseModel,
)
from app.ai.prompts.enums import MessageRole
from app.ai.services.db_restaurant_service import DatabaseRestaurantService
from app.ai.services.gemini_ai_service import GeminiAIService
from app.ai.services.session_service import SessionService

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """健康檢查端點"""
    return HealthResponse(status="healthy", timestamp=datetime.now(), version="2.0.0")


@router.post("/search", response_model=SearchResponseModel)
async def search_restaurants(
    request: SearchRequest,
    restaurant_service: DatabaseRestaurantService = Depends(get_restaurant_service),
    ai_service: GeminiAIService = Depends(get_ai_service),
    session_service: SessionService = Depends(get_session_service),
):
    """搜尋餐廳端點"""
    user_session = None

    try:
        # 1. 獲取/創建會話
        user_session = session_service.get_or_create(request.user_id)
        logging.info(f"🔍 處理用戶 {request.user_id} 的搜尋請求")

        # 2. AI 分析用戶意圖
        ai_analysis = await _analyze_user_intent(ai_service, request, user_session)

        if not ai_analysis.get("success", False):
            return await _handle_analysis_failure(ai_service, user_session, request)

        # 3. 更新搜索條件 - 添加異常處理
        extracted_info = ai_analysis.get("extracted_info", {})
        safe_extracted_info = _safe_convert_extracted_info(extracted_info)

        try:
            user_session.update_search_criteria(**safe_extracted_info)
            user_session.add_message(MessageRole.USER, request.user_input)
        except Exception as e:
            logger.warning(f"更新搜索條件失敗: {e}")
            # 繼續執行，使用預設值

        # 4. 檢查是否需要更多信息
        missing_info = _get_missing_required_fields(user_session, ai_analysis)

        if missing_info:
            return await _request_more_info(
                ai_service, user_session, missing_info, request.user_input
            )

        # 5. 執行搜索
        search_result = await _execute_database_search(
            restaurant_service, user_session, request
        )

        # 6. 生成回應
        response = await _build_search_response(
            ai_service, search_result, user_session, request
        )

        # 7. 清理會話狀態
        _cleanup_session(user_session)

        return response

    except Exception as e:
        logger.error(
            f"搜尋失敗: {str(e)}", exc_info=True
        )  # 添加 exc_info 獲得完整錯誤堆疊
        if user_session:
            try:
                if hasattr(user_session, "prepare_for_new_conversation"):
                    user_session.prepare_for_new_conversation()
            except:
                pass  # 忽略清理錯誤

        return SearchResponseModel(
            type="error",
            message="搜尋過程中發生錯誤，請重新開始搜尋。",
            recommendations=[],
            criteria=None,
            missing_fields=[],
            metadata={"error": True, "conversation_reset": True},
        )


def _safe_convert_extracted_info(extracted_info: dict) -> dict:
    """安全轉換提取的信息"""
    safe_extracted_info = {}

    for key, value in extracted_info.items():
        try:
            if key == "radius":
                if value is not None:
                    safe_extracted_info[key] = (
                        int(float(value)) if isinstance(value, (str, float)) else value
                    )
            elif key == "price_level":
                if value is not None:
                    safe_extracted_info[key] = (
                        int(float(value)) if isinstance(value, (str, float)) else value
                    )
            elif key in ["rating_min", "latitude", "longitude"]:
                if value is not None:
                    safe_extracted_info[key] = (
                        float(value) if isinstance(value, (str, int)) else value
                    )
            elif key in ["cuisine", "query", "address"]:
                if value is not None:
                    safe_extracted_info[key] = str(value)
            else:
                safe_extracted_info[key] = value
        except (ValueError, TypeError) as e:
            logger.warning(f"轉換 {key}={value} 失敗: {e}")
            # 跳過無效值，繼續處理其他字段

    return safe_extracted_info


# 輔助函數
async def _analyze_user_intent(ai_service, request, user_session):
    """分析用戶意圖"""
    try:
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
    except Exception as e:
        logger.error(f"AI 意圖分析失敗: {e}")
        return {"success": False, "error": str(e)}


async def _handle_analysis_failure(ai_service, user_session, request):
    """處理AI分析失敗的情況"""
    try:
        logger.info("🔄 使用降級邏輯")
        user_session.add_message(MessageRole.USER, request.user_input)

        # 🔧 修正：檢查方法是否存在
        if hasattr(ai_service, "legacy_restaurant_search"):
            legacy_response = await ai_service.legacy_restaurant_search(
                user_session.get_messages_for_ai()
            )
        else:
            # 基本降級回應
            legacy_response = (
                "請告訴我您想要什麼類型的菜系和搜尋範圍（例如：5公里內的日式餐廳）"
            )
        # 嘗試解析為搜索參數
        try:
            search_params = json.loads(legacy_response)
            if "radius" in search_params and "cuisine" in search_params:
                safe_params = _safe_convert_extracted_info(search_params)
                user_session.update_search_criteria(**safe_params)
                return {
                    "success": True,
                    "confidence": 0.8,
                    "extracted_info": safe_params,
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
    try:
        # 🔧 修正：安全地獲取必需字段
        if hasattr(RestaurantDomainKnowledge, "REQUIRED_FIELDS"):
            required_fields = RestaurantDomainKnowledge.REQUIRED_FIELDS
        else:
            required_fields = ["cuisine", "radius"]  # 預設必需字段

        current_data = user_session.data.__dict__ if user_session.data else {}

        missing_required = [
            field
            for field in required_fields
            if field not in current_data or not current_data[field]
        ]

        missing_from_ai = ai_analysis.get("missing_info", [])
        confidence = ai_analysis.get("confidence", 0.0)

        return missing_required + (missing_from_ai if confidence < 0.8 else [])
    except Exception as e:
        logger.warning(f"檢查缺失字段失敗: {e}")
        return ["cuisine", "radius"]  # 返回基本必需字段


async def _request_more_info(ai_service, user_session, missing_info, user_input):
    """請求更多信息"""
    try:
        current_context = user_session.data.__dict__ if user_session.data else {}

        # 檢查 AI 服務是否有對應方法
        if hasattr(ai_service, "generate_follow_up_question"):
            follow_up = await ai_service.generate_follow_up_question(
                missing_info=missing_info,
                current_context=current_context,
                user_input=user_input,
            )
        else:
            # 生成基本的追問
            if "cuisine" in missing_info:
                follow_up = (
                    "請問您想要什麼類型的菜系呢？例如：日式、中式、義大利菜、韓式等。"
                )
            elif "radius" in missing_info:
                follow_up = "請問您希望在多遠的範圍內搜尋餐廳呢？例如：1公里、5公里等。"
            else:
                follow_up = "請提供更多詳細信息以幫助我為您找到合適的餐廳。"

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
    except Exception as e:
        logger.error(f"請求更多信息失敗: {e}")
        return SearchResponseModel(
            type="partial",
            message="請告訴我您想要的餐廳類型和搜尋範圍。",
            recommendations=[],
            criteria=None,
            missing_fields=missing_info,
            metadata={"error": True},
        )


async def _execute_database_search(
    restaurant_service: DatabaseRestaurantService, user_session, request
):
    """執行資料庫餐廳搜索"""
    try:
        # 處理位置資訊
        location_data = restaurant_service._process_location_input(request.location)
        search_info = user_session.data.__dict__ if user_session.data else {}

        # 構建資料庫搜索參數
        db_search_params: Dict[str, Any] = {"limit": 20}

        # 位置參數 - 修正潛在的 KeyError
        if location_data.get("type") == "coordinates":
            latitude = location_data.get("latitude")
            longitude = location_data.get("longitude")

            if latitude is not None and longitude is not None:
                try:
                    db_search_params["latitude"] = float(latitude)
                    db_search_params["longitude"] = float(longitude)

                    radius = search_info.get("radius", SearchDefaults.RADIUS)
                    db_search_params["radius_km"] = float(radius) / 1000.0
                except (ValueError, TypeError) as e:
                    logger.warning(f"座標轉換失敗: {e}")

        elif location_data.get("type") == "address":
            address = location_data.get("address")
            if address:
                db_search_params["address"] = str(address)

        # 搜尋條件 - 添加安全檢查
        cuisine = search_info.get("cuisine")
        if cuisine:
            db_search_params["cuisine"] = str(cuisine)

        price_level = search_info.get("price_level")
        if price_level is not None:
            try:
                price_level_int = int(float(price_level))
                price_map = {1: "budget", 2: "mid_range", 3: "high_mid", 4: "expensive"}
                db_search_params["price_range"] = price_map.get(
                    price_level_int, "mid_range"
                )
            except (ValueError, TypeError):
                logger.warning(f"價格等級轉換失敗: {price_level}")

        rating_min = search_info.get("rating_min")
        if rating_min is not None:
            try:
                db_search_params["min_rating"] = float(rating_min)
            except (ValueError, TypeError):
                logger.warning(f"評分轉換失敗: {rating_min}")

        # 關鍵字搜尋
        if request.user_input:
            db_search_params["query"] = str(request.user_input)

        logger.info(f"執行資料庫搜索，參數: {db_search_params}")

        # 執行資料庫搜索
        restaurants = await restaurant_service.repository.search_restaurants(
            **db_search_params
        )

        # 後處理餐廳資料
        restaurants = restaurant_service._post_process_restaurants(
            restaurants, location_data
        )

        return {
            "restaurants": restaurants,
            "search_params": db_search_params,
            "location_data": location_data,
            "search_info": search_info,
        }

    except Exception as e:
        logger.error(f"資料庫搜索失敗: {e}", exc_info=True)
        return {
            "restaurants": [],
            "search_params": {"limit": 20},
            "location_data": {"type": "none"},
            "search_info": {},
            "error": str(e),
        }


async def _build_search_response(ai_service, search_result, user_session, request):
    """構建搜索回應"""
    restaurants = search_result["restaurants"]
    search_params = search_result["search_params"]
    location_data = search_result["location_data"]
    search_info = search_result["search_info"]

    # AI 生成個性化回應
    message = None
    try:
        # 🔧 修正：檢查方法是否存在
        if hasattr(ai_service, "generate_search_response"):
            ai_response = await ai_service.generate_search_response(
                restaurants=restaurants,
                user_preferences=search_info,
                search_params=search_params,
                user_input=request.user_input,
            )
            message = ai_response.get("message") if ai_response else None
    except Exception as e:
        logger.warning(f"AI 回應生成失敗，使用預設訊息: {e}")

    # 使用預設訊息如果 AI 回應失敗
    if not message:
        if restaurants:
            message = f"為您找到 {len(restaurants)} 家符合條件的餐廳！"
        else:
            message = "抱歉，沒有找到符合條件的餐廳，請嘗試調整搜尋條件。"

    try:
        user_session.add_message(MessageRole.ASSISTANT, message)
    except Exception as e:
        logger.warning(f"添加消息到會話失敗: {e}")

    # 轉換為 API 格式
    restaurant_responses = []
    for r in restaurants:
        try:
            restaurant_responses.append(
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
            )
        except Exception as e:
            logger.warning(f"轉換餐廳回應失敗: {e}")

    # 判斷回應類型
    response_type = "success" if restaurants else "partial"

    return SearchResponseModel(
        type=response_type,
        message=message,
        recommendations=restaurant_responses,
        criteria=clean_search_info(search_info),
        missing_fields=[],
        metadata={
            "database_search": True,
            "conversation_status": "completed",
            "search_completed_at": datetime.now().isoformat(),
            "total_found": len(restaurants),
            "location_processed": location_data,
            "search_params_used": clean_search_info(search_params),
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


# 資料庫相關的新端點
@router.get("/restaurants/{restaurant_id}")
async def get_restaurant_detail(
    restaurant_id: str,
    restaurant_service: DatabaseRestaurantService = Depends(get_restaurant_service),
):
    """獲取餐廳詳細信息"""
    try:
        restaurant = await restaurant_service.repository.get_restaurant_by_id(
            restaurant_id
        )

        if not restaurant:
            raise HTTPException(status_code=404, detail="餐廳不存在")

        return RestaurantResponse(
            id=restaurant.id,
            name=restaurant.name,
            cuisine=restaurant.cuisine,
            distance_km=restaurant.distance_km or 0.0,
            rating=restaurant.rating,
            price_level=restaurant.price_level,
            tags=restaurant.tags,
            address=restaurant.address,
            phone=restaurant.phone,
            description=restaurant.description,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 獲取餐廳詳情失敗: {e}")
        raise HTTPException(status_code=500, detail="獲取餐廳詳情失敗")


@router.get("/cuisines/popular")
async def get_popular_cuisines(
    limit: int = 10,
    restaurant_service: DatabaseRestaurantService = Depends(get_restaurant_service),
):
    """獲取熱門菜系"""
    try:
        cuisines = await restaurant_service.repository.get_popular_cuisines(limit)
        return {
            "popular_cuisines": cuisines,
            "total": len(cuisines),
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"❌ 獲取熱門菜系失敗: {e}")
        raise HTTPException(status_code=500, detail="獲取熱門菜系失敗")


# 會話管理端點
@router.get("/session/{user_id}/status")
async def get_session_status(
    user_id: str,
    session_service: SessionService = Depends(get_session_service),
):
    """獲取會話狀態"""
    try:
        user_session = session_service.get_or_create(user_id)

        # 🔧 修正：安全地獲取會話狀態
        is_ready = (
            user_session.is_fresh_conversation()
            if hasattr(user_session, "is_fresh_conversation")
            else True
        )

        message_count = (
            user_session.get_message_count()
            if hasattr(user_session, "get_message_count")
            else 0
        )

        return {
            "user_id": user_id,
            "is_ready_for_new_search": is_ready,
            "message_count": message_count,
            "last_activity": user_session.updated_at.isoformat(),
        }
    except Exception as e:
        logger.error(f"獲取會話狀態失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/session/{user_id}/clear")
async def clear_session(
    user_id: str,
    session_service: SessionService = Depends(get_session_service),
):
    """清除會話"""
    try:
        user_session = session_service.get_or_create(user_id)

        message_count = (
            user_session.get_message_count()
            if hasattr(user_session, "get_message_count")
            else 0
        )

        # 🔧 修正：安全地清理會話
        if hasattr(user_session, "clear_history"):
            user_session.clear_history()
        if hasattr(user_session, "reset_search_criteria"):
            user_session.reset_search_criteria()

        return {
            "message": "會話已清除",
            "cleared_messages": message_count,
            "user_id": user_id,
        }
    except Exception as e:
        logger.error(f"清除會話失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))
