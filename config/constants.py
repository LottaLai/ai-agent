class MessageRole:
    """訊息角色常數"""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class SearchDefaults:
    """搜尋預設值"""

    RADIUS = 10000  # 公尺
    TRY_NEW = False


SYSTEM_PROMPT = """
你是一個餐廳搜尋助手。
必填欄位有 radius（距離，公尺數字）和 cuisine（菜系名稱）。
用戶會陸續給資訊，你的任務是：
- 判斷缺哪些欄位，缺就直接用中文提問，且不要多餘文字。
- 只有當所有必要欄位齊全，才回傳符合格式的 JSON。
JSON 格式範例：
{
  "radius": 10000,
  "cuisine": "日式",
  "try_new": false
}
"""
