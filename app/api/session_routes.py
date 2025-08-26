# app/api/session_routes.py
import logging

from fastapi import APIRouter, Depends, HTTPException

from app.core.dependencies import get_session_service
from app.services.session_service import SessionService

router = APIRouter(prefix="/session", tags=["session"])
logger = logging.getLogger(__name__)


@router.get("/{user_id}/status")
async def get_session_status(
    user_id: str,
    session_service: SessionService = Depends(get_session_service),
):
    """獲取會話狀態"""
    try:
        user_session = session_service.get_or_create(user_id)

        # 安全地獲取會話狀態
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


@router.post("/{user_id}/clear")
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

        # 安全地清理會話
        _cleanup_session(user_session)

        return {
            "message": "會話已清除",
            "cleared_messages": message_count,
            "user_id": user_id,
        }
    except Exception as e:
        logger.error(f"清除會話失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{user_id}/history")
async def get_session_history(
    user_id: str,
    limit: int = 10,
    session_service: SessionService = Depends(get_session_service),
):
    """獲取會話歷史記錄"""
    try:
        user_session = session_service.get_or_create(user_id)

        # 獲取歷史記錄（如果有此功能）
        history = (
            user_session.get_recent_messages(limit)
            if hasattr(user_session, "get_recent_messages")
            else []
        )

        return {
            "user_id": user_id,
            "history": history,
            "total_messages": len(history),
        }
    except Exception as e:
        logger.error(f"獲取會話歷史失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{user_id}/reset")
async def reset_session_criteria(
    user_id: str,
    session_service: SessionService = Depends(get_session_service),
):
    """重置會話搜尋條件（保留歷史記錄）"""
    try:
        user_session = session_service.get_or_create(user_id)

        # 只重置搜尋條件，保留對話歷史
        if hasattr(user_session, "reset_search_criteria"):
            user_session.reset_search_criteria()

        return {
            "message": "會話搜尋條件已重置",
            "user_id": user_id,
        }
    except Exception as e:
        logger.error(f"重置會話條件失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _cleanup_session(user_session):
    """清理會話狀態"""
    if hasattr(user_session, "clear_history"):
        user_session.clear_history()
    if hasattr(user_session, "reset_search_criteria"):
        user_session.reset_search_criteria()
    if hasattr(user_session, "prepare_for_new_conversation"):
        user_session.prepare_for_new_conversation()
