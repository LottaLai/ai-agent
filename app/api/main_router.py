# app/api/main_router.py 或者放在 app/api/__init__.py

from datetime import datetime

from fastapi import APIRouter

from app.models.responses import HealthResponse

from . import restaurant_routes, session_routes

# 創建主路由器
api_router = APIRouter()

# 包含所有子路由
api_router.include_router(restaurant_routes.router, tags=["restaurant"])
api_router.include_router(session_routes.router, tags=["session"])

# 健康檢查端點
@api_router.get("/health")
async def health_check():
    """API 健康檢查"""
    return {"status": "healthy", "service": "restaurant-search-api"}

# 根路徑健康檢查
@api_router.get("/", response_model=HealthResponse)
async def root():
    """根路徑 - 健康檢查"""
    return HealthResponse(status="healthy", timestamp=datetime.now())
