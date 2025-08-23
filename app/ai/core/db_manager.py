# app/core/database.py
import asyncio
import logging
import os
from functools import lru_cache
from typing import Optional

import asyncpg


class DatabaseManager:
    """資料庫連接管理器"""

    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None

    async def init_connection(self, conn):
        """初始化資料庫連接，包含函數創建"""
        init_sql = """
        -- 創建距離計算函數
        CREATE OR REPLACE FUNCTION calculate_distance(
            lat1 NUMERIC, lon1 NUMERIC, lat2 NUMERIC, lon2 NUMERIC
        ) RETURNS NUMERIC AS $$
        DECLARE
            earth_radius NUMERIC := 6371; -- 地球半徑（公里）
            dlat NUMERIC;
            dlon NUMERIC;
            a NUMERIC;
            c NUMERIC;
        BEGIN
            -- 檢查輸入參數
            IF lat1 IS NULL OR lon1 IS NULL OR lat2 IS NULL OR lon2 IS NULL THEN
                RETURN NULL;
            END IF;

            -- 轉換為弧度
            dlat := radians(lat2 - lat1);
            dlon := radians(lon2 - lon1);

            -- Haversine 公式
            a := sin(dlat/2) * sin(dlat/2) +
                 cos(radians(lat1)) * cos(radians(lat2)) *
                 sin(dlon/2) * sin(dlon/2);
            c := 2 * asin(sqrt(a));

            -- 返回距離（公里）
            RETURN earth_radius * c;
        END;
        $$ LANGUAGE plpgsql IMMUTABLE;
        """

        # 添加重試邏輯處理併發更新錯誤
        max_retries = 3
        for attempt in range(max_retries):
            try:
                await conn.execute(init_sql)
                break
            except Exception as e:
                error_msg = str(e).lower()
                if ("tuple concurrently updated" in error_msg or
                    "could not serialize access" in error_msg) and attempt < max_retries - 1:
                    # 指數退避重試
                    await asyncio.sleep(0.1 * (attempt + 1))
                    continue
                raise

    async def create_pool(self) -> asyncpg.Pool:
        """創建資料庫連接池"""
        try:
            database_url = self._get_database_url()

            self.pool = await asyncpg.create_pool(
                database_url,
                min_size=2,  # 減少初始連接數避免併發問題
                max_size=10, # 減少最大連接數
                command_timeout=60,
                init=self.init_connection,
            )

            logging.info("✅ 資料庫連接池創建成功")
            return self.pool

        except Exception as e:
            logging.error(f"❌ 資料庫連接失敗: {e}")
            raise

    async def close_pool(self):
        """關閉資料庫連接池"""
        if self.pool:
            await self.pool.close()
            logging.info("資料庫連接池已關閉")

    def _get_database_url(self) -> str:
        """獲取資料庫連接 URL"""
        # 從環境變數獲取資料庫配置
        db_host = os.getenv("DB_HOST", "localhost")
        db_port = os.getenv("DB_PORT", "5432")
        db_name = os.getenv("DB_NAME", "postgres")
        db_user = os.getenv("DB_USER", "postgres")
        db_password = os.getenv("DB_PASSWORD", "")

        if not db_password:
            raise ValueError("資料庫密碼未設定，請設定 DB_PASSWORD 環境變數")

        return f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"


# 全域資料庫管理器實例
db_manager = DatabaseManager()


@lru_cache()
def get_database_manager() -> DatabaseManager:
    """獲取資料庫管理器實例"""
    return db_manager
