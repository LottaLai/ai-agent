# app/core/dependencies.py
import logging
from functools import lru_cache
from typing import Optional

import asyncpg
from ai.core.db_manager import get_database_manager
from ai.core.setting import get_ai_settings, get_config
from ai.repositories.database_restaurant_repo import DatabaseRestaurantRepository
from ai.services.db_restaurant_service import DatabaseRestaurantService
from ai.services.gemini_ai_service import GeminiAIService
from ai.services.session_service import SessionService
from fastapi import HTTPException

from shared.utils.in_memory_repo import InMemorySessionRepository

# 全域服務實例
_ai_service: Optional[GeminiAIService] = None
_session_service: Optional[SessionService] = None
_restaurant_service: Optional[DatabaseRestaurantService] = None
_db_pool: Optional[asyncpg.Pool] = None
_db_restaurant_repo: Optional[DatabaseRestaurantRepository] = None


async def setup_dependencies():
    """初始化所有服務依賴"""
    global _ai_service, _session_service, _restaurant_service, _db_pool

    try:
        config = get_config()

        # 1. 初始化資料庫連接池
        db_manager = get_database_manager()
        _db_pool = await db_manager.create_pool()
        logging.info("✅ 資料庫連接池初始化成功")

        _db_restaurant_repo = DatabaseRestaurantRepository(_db_pool)
        # 2. 初始化 AI 服務
        _ai_service = GeminiAIService(config.ai)
        logging.info("✅ AI 服務初始化成功")

        # 3. 初始化會話服務
        session_repo = InMemorySessionRepository(session_timeout=3600)
        _session_service = SessionService(session_repo)
        logging.info("✅ 會話服務初始化成功")

        # 4. 初始化餐廳服務（使用資料庫）
        _restaurant_service = DatabaseRestaurantService(
            _ai_service, _session_service, _db_restaurant_repo
        )
        logging.info("✅ 餐廳服務（資料庫版）初始化成功")

        logging.info("🎉 所有服務依賴初始化完成")

    except Exception as e:
        logging.error(f"❌ 服務依賴初始化失敗: {e}")
        raise


async def cleanup_dependencies():
    """清理服務依賴"""
    global _db_pool

    try:
        if _db_pool:
            await _db_pool.close()
            logging.info("資料庫連接池已關閉")
    except Exception as e:
        logging.error(f"清理依賴時發生錯誤: {e}")


def get_restaurant_service() -> DatabaseRestaurantService:
    """依賴注入：取得餐廳服務實例"""
    if _restaurant_service is None:
        raise HTTPException(status_code=500, detail="餐廳服務未初始化")
    return _restaurant_service


@lru_cache()
def get_ai_service() -> GeminiAIService:
    """取得 AI 服務實例"""
    if _ai_service is None:
        ai_settings = get_ai_settings()
        return GeminiAIService(ai_settings)
    return _ai_service


@lru_cache()
def get_session_service() -> SessionService:
    """取得會話服務實例"""
    if _session_service is None:
        repo = InMemorySessionRepository(session_timeout=3600)
        return SessionService(repository=repo)
    return _session_service


def get_database_pool() -> asyncpg.Pool:
    """取得資料庫連接池"""
    if _db_pool is None:
        raise HTTPException(status_code=500, detail="資料庫連接池未初始化")
    return _db_pool
