import logging
from datetime import datetime

import uvicorn

# FastAPI 相關導入
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 假設的資料導入
from app.api.routes import router
from app.models.responses import HealthResponse


def create_application() -> FastAPI:
    """建立 FastAPI 應用程式實例"""

    app = FastAPI(
        title="餐廳搜尋助手 API",
        description="AI 驅動的智能餐廳搜尋服務",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # 設定 CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 生產環境應該限制來源
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 註冊路由
    app.include_router(router)

    # 設定事件處理器
    app.add_event_handler("startup", startup_event)
    app.add_event_handler("shutdown", shutdown_event)

    return app


async def startup_event():
    """應用程式啟動時初始化服務"""
    try:
        config = get_config()
        config.validate()

        # 設定日誌
        setup_logging(config.app.log_level)

        # 初始化服務依賴
        await setup_dependencies()

        logging.info("餐廳搜尋服務啟動成功")

    except Exception as e:
        logging.error(f"服務啟動失敗: {e}")
        raise


async def shutdown_event():
    """應用程式關閉時清理資源"""
    logging.info("餐廳搜尋服務正在關閉")


# 建立應用程式實例
app = create_application()


# 根路徑健康檢查
@app.get("/", response_model=HealthResponse)
async def root():
    """根路徑 - 健康檢查"""
    return HealthResponse(status="healthy", timestamp=datetime.now())


if __name__ == "__main__":
    config = get_config()
    uvicorn.run(
        "main:app",
        host=config.app.host,
        port=config.app.port,
        reload=config.app.debug,
        log_level=config.app.log_level.lower(),
    )
