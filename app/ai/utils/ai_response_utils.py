# ai_response_utils.py
import json
import re
from typing import Any, Dict, List

from ai.utils.response_formatter import ResponseFormatter


def analyze_user_input(user_input: str, session_data: Dict) -> Dict[str, Any]:
    """分析用戶輸入並返回 AI 回應

    Args:
        user_input: 用戶的輸入文本
        session_data: 會話數據，包含已收集的信息

    Returns:
        Dict[str, Any]: 包含分析結果的字典
    """

    # 初始化已收集信息
    session_data.setdefault("collected_info", {})
    collected_info = session_data["collected_info"]

    # 檢查距離信息
    if "radius" not in collected_info:
        radius = _extract_radius_from_input(user_input)
        if radius:
            collected_info["radius"] = radius
        else:
            return {
                "is_complete": False,
                "message": "請問您希望搜索多大範圍內的餐廳？(例如: 5 km)",
                "missing_fields": ["radius"],
            }

    # 檢查菜系信息
    if "cuisine" not in collected_info:
        cuisine = _extract_cuisine_from_input(user_input)
        if cuisine:
            collected_info["cuisine"] = cuisine
        else:
            return {
                "is_complete": False,
                "message": "菜系名稱？",
                "missing_fields": ["cuisine"],
            }

    # 檢查其他可選參數
    _extract_optional_params(user_input, collected_info)

    # 如果信息收集完成，生成最終結果
    if _is_collection_complete(collected_info):
        return {
            "is_complete": True,
            "message": _generate_final_json_message(collected_info),
            "missing_fields": [],
            "search_params": collected_info,
        }

    # 確定還需要什麼信息
    missing_fields = _get_missing_required_fields(collected_info)
    return {
        "is_complete": False,
        "message": _generate_question_for_missing_field(missing_fields[0]),
        "missing_fields": missing_fields,
    }


def _extract_radius_from_input(user_input: str) -> int:
    """從用戶輸入中提取距離信息"""
    distance_keywords = ["km", "公里", "kilometer", "meter", "米", "m"]

    if any(keyword in user_input.lower() for keyword in distance_keywords):
        # 提取數字
        numbers = re.findall(r"\d+(?:\.\d+)?", user_input)
        if numbers:
            distance = float(numbers[0])
            # 如果是公里，轉換為米
            if any(
                km_word in user_input.lower() for km_word in ["km", "公里", "kilometer"]
            ):
                return int(distance * 1000)
            else:
                return int(distance)

    return 0


def _extract_cuisine_from_input(user_input: str) -> str:
    """從用戶輸入中提取菜系信息"""
    cuisine_keywords = {
        "chinese": ["中式", "中菜", "chinese", "中國菜", "中餐"],
        "japanese": ["日式", "日菜", "japanese", "日本菜", "日餐"],
        "italian": ["義式", "義大利", "italian", "義大利菜", "意大利"],
        "sichuan": ["川菜", "sichuan", "四川菜", "川式"],
        "korean": ["韓式", "韓菜", "korean", "韓國菜", "韓餐"],
        "thai": ["泰式", "泰菜", "thai", "泰國菜", "泰餐"],
        "vietnamese": ["越式", "越菜", "vietnamese", "越南菜", "越餐"],
    }

    user_input_lower = user_input.lower()
    for cuisine_type, keywords in cuisine_keywords.items():
        if any(keyword in user_input_lower for keyword in keywords):
            return cuisine_type

    return ""


def _extract_optional_params(user_input: str, collected_info: Dict) -> None:
    """提取可選參數"""
    # 提取價格偏好
    if "price_preference" not in collected_info:
        price_keywords = {
            "budget": ["便宜", "實惠", "cheap", "budget", "省錢"],
            "mid_range": ["中等", "一般", "moderate", "中價"],
            "expensive": ["高檔", "昂貴", "expensive", "奢華", "高級"],
        }

        user_input_lower = user_input.lower()
        for price_level, keywords in price_keywords.items():
            if any(keyword in user_input_lower for keyword in keywords):
                collected_info["price_preference"] = price_level
                break

    # 提取評分要求
    rating_match = re.search(r"評分.*?(\d+(?:\.\d+)?)", user_input)
    if rating_match and "min_rating" not in collected_info:
        collected_info["min_rating"] = float(rating_match.group(1))

    # 提取是否嘗新偏好
    if "try_new" not in collected_info:
        if any(word in user_input.lower() for word in ["新", "new", "嘗試", "新鮮"]):
            collected_info["try_new"] = True
        elif any(
            word in user_input.lower() for word in ["熟悉", "familiar", "經典", "傳統"]
        ):
            collected_info["try_new"] = False


def _is_collection_complete(collected_info: Dict) -> bool:
    """檢查是否收集完必要信息"""
    required_fields = ["radius", "cuisine"]
    return all(field in collected_info for field in required_fields)


def _get_missing_required_fields(collected_info: Dict) -> List[str]:
    """獲取缺失的必要字段"""
    required_fields = ["radius", "cuisine"]
    return [field for field in required_fields if field not in collected_info]


def _generate_question_for_missing_field(field: str) -> str:
    """為缺失的字段生成問題"""
    questions = {
        "radius": "請問您希望搜索多大範圍內的餐廳？(例如: 5 km)",
        "cuisine": "菜系名稱？",
        "price_preference": "您希望的價格範圍是？(便宜/中等/高檔)",
        "min_rating": "最低評分要求？(例如: 4.0分以上)",
    }
    return questions.get(field, "還需要更多信息")


def _generate_final_json_message(collected_info: Dict) -> str:
    """生成最終的 JSON 格式消息"""
    # 構建搜索參數
    search_params = {
        "radius": collected_info["radius"],
        "cuisine": collected_info["cuisine"],
        "try_new": collected_info.get("try_new", False),
    }

    # 添加可選參數
    if "price_preference" in collected_info:
        search_params["price_preference"] = collected_info["price_preference"]

    if "min_rating" in collected_info:
        search_params["min_rating"] = collected_info["min_rating"]

    # 格式化 JSON
    json_str = json.dumps(search_params, indent=2, ensure_ascii=False)
    return f"```json\n{json_str}\n```"
