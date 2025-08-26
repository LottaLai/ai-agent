from asyncio.log import logger
from typing import Any, Dict, List, Optional

import asyncpg

from app.models.definitions import Restaurant


class DatabaseRestaurantRepository:
    """資料庫餐廳資料存取層"""

    def __init__(self, db_manager):
        self.db_manager = db_manager

    async def get_connection(self) -> asyncpg.Connection:
        """獲取資料庫連接"""
        if not self.db_manager.pool:
            await self.db_manager.create_pool()
        return await self.db_manager.pool.acquire()

    async def search_restaurants(
            self,
            latitude: Optional[float] = None,
            longitude: Optional[float] = None,
            radius_km: Optional[float] = None,
            address: Optional[str] = None,
            query: Optional[str] = None,
            cuisine: Optional[str] = None,  # 對應 cuisine_type
            price_range: Optional[str] = None,
            min_rating: Optional[float] = None,  # 對應 average_rating
            limit: int = 20,
            **kwargs
            ) -> List[Restaurant]:
        """多條件搜尋餐廳"""
        # SQL 查詢、條件組合、排序、轉換為 Restaurant 物件
        conn = None
        try:
            # 獲取資料庫連接
            conn = await self.get_connection()
            logger.info(f"🔍 開始 asyncpg 搜尋: cuisine={cuisine}, price_range={price_range}")

            # 構建 SQL 查詢
            sql_query, params = await self._build_search_query(
                latitude=latitude,
                longitude=longitude,
                radius_km=radius_km,
                address=address,
                query=query,
                cuisine=cuisine,
                price_range=price_range,
                min_rating=min_rating,
                limit=limit
            )

            logger.debug(f"🔄 執行 SQL: {sql_query}")
            logger.debug(f"📊 參數: {params}")

            # 執行查詢
            rows = await conn.fetch(sql_query, *params)

            # 轉換為 Restaurant 對象

            restaurants = []
            for row in rows:
                try:
                    restaurant = self._row_to_restaurant(row)
                    restaurants.append(restaurant)
                except Exception as e:
                    logger.error(f"❌ 轉換資料失敗: {e}")
                    continue

            logger.info(f"✅ asyncpg 搜尋完成: 找到 {len(restaurants)} 家餐廳")
            return restaurants

        except Exception as e:
            logger.error(f"❌ asyncpg 搜尋失敗: {e}", exc_info=True)
            return []

        finally:
            if conn:
                await self.db_manager.pool.release(conn)

    async def _build_search_query(
        self,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        radius_km: Optional[float] = None,
        address: Optional[str] = None,
        query: Optional[str] = None,
        cuisine: Optional[str] = None,
        price_range: Optional[str] = None,
        min_rating: Optional[float] = None,
        limit: int = 20
    ) -> tuple[str, list]:
        """構建 PostgreSQL 查詢語句"""

        # 基礎 SELECT 子句
        select_fields = ["*"]

        # 如果有座標，計算距離
        if latitude is not None and longitude is not None:
            distance_field = f"calculate_distance({latitude}, {longitude}, latitude, longitude) as distance_km"
            select_fields.append(distance_field)

        select_clause = ", ".join(select_fields)

        # WHERE 條件和參數
        where_conditions = []
        params = []
        param_counter = 1

        # 1. 菜系條件
        if cuisine and cuisine.strip():
            where_conditions.append(f"""
                    AND EXISTS (
                        SELECT 1 FROM unnest(cuisine_type) elem
                        WHERE LOWER(elem) LIKE LOWER(${param_counter})
                    )
                """)
            params.append(f"%{cuisine.strip()}%")
            param_counter += 1

        # 2. 價格範圍
        if price_range:
            # 處理價格範圍映射
            price_mapping = {
                "budget": ["$", "budget", "cheap", "low"],
                "mid_range": ["$$", "moderate", "mid", "medium"],
                "high_mid": ["$$$", "expensive", "high"],
                "expensive": ["$$$$", "luxury", "premium"]
            }

            if price_range.lower() in price_mapping:
                price_options = price_mapping[price_range.lower()]
                price_conditions = " OR ".join([f"price_range ILIKE ${param_counter + i}" for i in range(len(price_options))])
                where_conditions.append(f"({price_conditions})")
                params.extend([f"%{option}%" for option in price_options])
                param_counter += len(price_options)

        # 3. 評分條件 - 使用 average_rating
        if min_rating is not None and min_rating > 0:
            where_conditions.append(f"average_rating >= ${param_counter}")
            params.append(min_rating)
            param_counter += 1

        # 4. 文字搜尋 - 搜尋名稱和描述
        if query and query.strip():
            search_text = query.strip()
            text_condition = f"""(
                name ILIKE ${param_counter} OR
                name_en ILIKE ${param_counter} OR
                description ILIKE ${param_counter} OR
                address ILIKE ${param_counter} OR
                district ILIKE ${param_counter}
            )"""
            where_conditions.append(text_condition)
            params.append(f"%{search_text}%")
            param_counter += 1

        # 5. 距離條件
        if latitude is not None and longitude is not None and radius_km:
            where_conditions.append(
                f"calculate_distance({latitude}, {longitude}, latitude, longitude) <= ${param_counter}"
            )
            params.append(radius_km)
            param_counter += 1

        # 6. 地址搜尋
        elif address and address.strip():
            address_condition = f"""(
                address ILIKE ${param_counter} OR
                district ILIKE ${param_counter} OR
                city ILIKE ${param_counter}
            )"""
            where_conditions.append(address_condition)
            params.append(f"%{address.strip()}%")
            param_counter += 1

        # 構建完整查詢
        where_clause = ""
        if where_conditions:
            where_clause = "WHERE 1=1" + " AND ".join(where_conditions)

        # 排序子句
        if latitude is not None and longitude is not None:
            order_clause = """ORDER BY
                distance_km ASC,
                average_rating DESC NULLS LAST,
                popularity_score DESC NULLS LAST,
                total_reviews DESC NULLS LAST"""
        else:
            order_clause = """ORDER BY
                is_featured DESC NULLS LAST,
                popularity_score DESC NULLS LAST,
                average_rating DESC NULLS LAST,
                total_reviews DESC NULLS LAST"""

        # 限制子句
        limit = min(max(1, limit), 100)
        limit_clause = f"LIMIT {limit}"

        # 組合完整 SQL
        sql = f"""
        SELECT {select_clause}
        FROM restaurants
        {where_clause}
        {order_clause}
        {limit_clause}
        """
        return sql.strip(), params


    # # 其他輔助方法
    async def get_restaurant_by_id(self, restaurant_id: int) -> Optional[Restaurant]:
        """根據 ID 獲取餐廳"""
        conn = None
        try:
            conn = await self.get_connection()
            sql = "SELECT * FROM restaurants WHERE restaurant_id = $1"
            row = await conn.fetchrow(sql, restaurant_id)

            if row:
                return self._row_to_restaurant(row)
            return None

        except Exception as e:
            logger.error(f"❌ 獲取餐廳失敗: {e}")
            return None
        finally:
            if conn:
                await self.db_manager.pool.release(conn)

    async def get_restaurants_count(self) -> int:
        """獲取餐廳總數"""
        conn = None
        try:
            conn = await self.get_connection()
            result = await conn.fetchval("SELECT COUNT(*) FROM restaurants")
            return result or 0
        except Exception as e:
            logger.error(f"❌ 獲取餐廳數量失敗: {e}")
            return 0
        finally:
            if conn:
                await self.db_manager.pool.release(conn)

    async def get_cuisines(self) -> List[str]:
        """獲取所有可用的菜系類型"""
        conn = None
        try:
            conn = await self.get_connection()
            sql = """
            SELECT DISTINCT cuisine_type
            FROM restaurants
            WHERE EXISTS (
                SELECT 1 FROM unnest(cuisine_type) elem
                WHERE LOWER(elem) not LIKE LOWER('')
            )
            ORDER BY cuisine_type
            """
            rows = await conn.fetch(sql)
            return [row['cuisine_type'] for row in rows]

        except Exception as e:
            logger.error(f"❌ 獲取菜系列表失敗: {e}")
            return []
        finally:
            if conn:
                await self.db_manager.pool.release(conn)

    async def get_popular_restaurants(self, limit: int = 10) -> List[Restaurant]:
        """獲取熱門餐廳"""
        return await self.search_restaurants(limit=limit)  # 默認按人氣排序

    async def get_restaurants_by_district(self, district: str, limit: int = 20) -> List[Restaurant]:
        """根據區域獲取餐廳"""
        return await self.search_restaurants(address=district, limit=limit)

    def _row_to_restaurant(self, row) -> Restaurant:
        """安全的行轉換方法 - 自動填充缺失欄位"""
        try:
            # 使用 .get() 方法安全獲取欄位，缺失時使用默認值
            restaurant = Restaurant(
                restaurant_id=row.get('restaurant_id'),
                name=row.get('name') or row.get('restaurant_name') or f"餐廳 {row.get('restaurant_id', 'Unknown')}",
                name_en=row.get('name_en'),
                cuisine_type=row.get('cuisine_type'),
                price_range=row.get('price_range'),
                phone=row.get('phone'),
                address=row.get('address'),
                district=row.get('district'),
                city=row.get('city'),
                country=row.get('country'),
                latitude=float(row['latitude']) if row.get('latitude') is not None else None,
                longitude=float(row['longitude']) if row.get('longitude') is not None else None,
                average_rating=float(row['average_rating']) if row.get('average_rating') is not None else None,
                total_reviews=row.get('total_reviews'),
                total_visits=row.get('total_visits'),
                popularity_score=float(row['popularity_score']) if row.get('popularity_score') is not None else None,
                status=row.get('status'),
                verified=row.get('verified'),
                description=row.get('description'),
                is_featured=row.get('is_featured'),
                is_sponsored=row.get('is_sponsored'),
                created_at=row.get('created_at'),
                updated_at=row.get('updated_at'),
                distance_km=float(row['distance_km']) if row.get('distance_km') is not None else None
            )
            return restaurant

        except Exception as e:
            logger.error(f"❌ 轉換餐廳失敗: {e}")
            # 返回最基本的餐廳物件
            return Restaurant(
                restaurant_id=row.get('restaurant_id'),
                name=row.get('name', f"餐廳 {row.get('restaurant_id', 'Unknown')}")
            )
