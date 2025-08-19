# app/core/dependencies.py
import logging
from functools import lru_cache
from typing import Optional

from fastapi import HTTPException

from config.setting import get_ai_settings
from config.config import get_config
from app.repositories.in_memory_repo import InMemorySessionRepository
from app.services.ai_service import GeminiAIService
from app.services.restaurant_service import RestaurantRepository, RestaurantService
from app.services.session_service import SessionService

# 全域服務實例
_ai_service: Optional[GeminiAIService] = None
_session_service: Optional[SessionService] = None
_restaurant_repo: Optional[RestaurantRepository] = None
_restaurant_service: Optional[RestaurantService] = None


async def setup_dependencies():
    """初始化所有服務依賴"""
    global _ai_service, _session_service, _restaurant_repo, _restaurant_service

    try:
        config = get_config()

        # 初始化服務
        _ai_service = GeminiAIService(config.ai)
        _repo = InMemorySessionRepository(session_timeout=3600)
        _session_service = SessionService(_repo)
        _restaurant_repo = RestaurantRepository()
        _restaurant_service = RestaurantService(
            _ai_service, _session_service, _restaurant_repo
        )

        logging.info("服務依賴初始化成功")

    except Exception as e:
        logging.error(f"服務依賴初始化失敗: {e}")
        raise


def get_restaurant_service() -> RestaurantService:
    """依賴注入：取得餐廳服務實例"""
    if _restaurant_service is None:
        raise HTTPException(status_code=500, detail="服務未初始化")
    return _restaurant_service


@lru_cache()
def get_ai_service() -> GeminiAIService:
    """取得 AI 服務實例"""
    ai_settings = get_ai_settings()
    return GeminiAIService(ai_settings)


@lru_cache()
def get_session_service() -> SessionService:
    """取得會話服務實例"""
    repo = InMemorySessionRepository(session_timeout=3600)
    return SessionService(repository=repo)


def get_restaurant_repository() -> RestaurantRepository:
    """依賴注入：取得餐廳資料庫實例"""
    if _restaurant_repo is None:
        raise HTTPException(status_code=500, detail="餐廳資料庫未初始化")
    return _restaurant_repo
