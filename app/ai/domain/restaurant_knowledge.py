# 領域知識常數
class RestaurantDomainKnowledge:
    """餐廳領域知識"""

    # 距離單位轉換規則
    DISTANCE_CONVERSION_RULES = {
        "keywords_to_meters": {
            "km": 1000,
            "公里": 1000,
            "kilometer": 1000,
            "公尺": 1,
            "米": 1,
            "m": 1,
            "meter": 1,
        },
        "conversion_examples": [
            "用戶說 '3 公里' → radius 應該是 3000",
            "用戶說 '500 米' → radius 應該是 500",
        ],
    }

    # 菜系類型對應
    CUISINE_MAPPING = {
        "中式": ["中式", "中菜", "中國菜", "chinese"],
        "日式": ["日式", "日菜", "日本菜", "japanese"],
        "義大利菜": ["義式", "義大利菜", "italian"],
        "川菜": ["川菜", "四川菜", "sichuan"],
        "韓式": ["韓式", "韓菜", "korean"],
        "泰式": ["泰式", "泰菜", "thai"],
        "美式": ["美式", "美國菜", "american"],
        "法式": ["法式", "法國菜", "french"],
        "印度菜": ["印度菜", "印度料理", "indian"],
        "越南菜": ["越南菜", "越式", "vietnamese"],
        "港式": ["港式", "港菜", "粤菜", "cantonese"],
    }

    # 必填欄位定義
    REQUIRED_FIELDS = ["radius", "cuisine"]
    OPTIONAL_FIELDS = [
        "try_new",
        "price_level",
        "rating_min",
        "atmosphere",
        "group_size",
    ]

    # JSON 格式範例
    JSON_FORMAT_EXAMPLE = {"radius": 2000, "cuisine": "日式", "try_new": False}
