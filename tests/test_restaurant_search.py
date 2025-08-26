from services.db_restaurant_service import DatabaseRestaurantService

# async def test_restaurant_search():
#     """測試餐廳搜尋功能"""
#     try:
#         service = DatabaseRestaurantService()

#         # 測試 1: 基本搜尋
#         print("🧪 測試基本搜尋...")
#         restaurants = await service.search_restaurants(limit=5)
#         print(f"✅ 找到 {len(restaurants)} 家餐廳")

#         # 測試 2: 條件搜尋
#         print("🧪 測試條件搜尋...")
#         restaurants = await service.search_restaurants(
#             cuisine="中式",
#             min_rating=4.0,
#             limit=3
#         )
#         print(f"✅ 中式餐廳: {len(restaurants)} 家")

#         # 測試 3: 地理位置搜尋
#         print("🧪 測試地理搜尋...")
#         restaurants = await service.search_restaurants(
#             latitude=25.033,
#             longitude=121.565,
#             radius_km=2.0,
#             limit=3
#         )
#         print(f"✅ 附近餐廳: {len(restaurants)} 家")

#         for r in restaurants:
#             print(f"  - {r.name}: {r.rating}⭐, {r.distance_km}km")

#     except Exception as e:
#         print(f"❌ 測試失敗: {e}")

# if __name__ == "__main__":
#     import asyncio
#     asyncio.run(test_restaurant_search())
