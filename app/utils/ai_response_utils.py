# ai_response_utils.py
import json
import re
from typing import Any, Dict, List


class AIResponseAnalyzer:
    """AI 回應分析器 - 支援多語言問題檢測"""

    # 多語言問題關鍵字
    QUESTION_INDICATORS = {
        # 中文繁體
        "zh_tw": [
            "您希望",
            "您想要",
            "您需要",
            "您偏好",
            "請問",
            "想知道",
            "可以告訴我",
            "選擇",
            "考慮",
            "您可以",
            "您願意",
            "建議您",
            "您覺得",
            "您認為",
            "有沒有",
            "是否",
            "要不要",
            "菜系名稱",
            "距離",
            "範圍",
        ],
        # 中文簡體
        "zh_cn": [
            "您希望",
            "您想要",
            "您需要",
            "您偏好",
            "请问",
            "想知道",
            "可以告诉我",
            "选择",
            "考虑",
            "您可以",
            "您愿意",
            "建议您",
            "您觉得",
            "您认为",
            "有没有",
            "是否",
            "要不要",
            "菜系名称",
            "距离",
            "范围",
        ],
        # 英文
        "en": [
            "would you like",
            "do you want",
            "do you need",
            "do you prefer",
            "can you tell me",
            "please let me know",
            "would you prefer",
            "are you looking for",
            "what kind of",
            "which type",
            "how about",
            "could you",
            "would you mind",
            "what about",
            "have you considered",
            "would you be interested",
            "are you interested in",
            "cuisine type",
        ],
    }

    # 多語言缺少資訊關鍵字
    MISSING_INFO_INDICATORS = {
        "zh_tw": [
            "缺少",
            "需要更多",
            "請提供",
            "沒有提到",
            "不清楚",
            "需要確認",
            "請指定",
            "請說明",
            "需要知道",
            "請補充",
            "資訊不足",
        ],
        "zh_cn": [
            "缺少",
            "需要更多",
            "请提供",
            "没有提到",
            "不清楚",
            "需要确认",
            "请指定",
            "请说明",
            "需要知道",
            "请补充",
            "信息不足",
        ],
        "en": [
            "missing",
            "need more",
            "please provide",
            "not mentioned",
            "unclear",
            "need to confirm",
            "please specify",
            "require",
            "incomplete",
            "additional information",
            "more details",
            "clarification needed",
        ],
    }

    # 通用問號符號
    QUESTION_MARKS = ["？", "?", "¿", "؟"]

    # 英文問句正則表達式模式
    ENGLISH_QUESTION_PATTERNS = [
        r"\b(what|where|when|why|how|which|who)\b.*[?\？]",
        r"\b(do|does|did|can|could|would|will|should|may|might)\s+you\b",
        r"\bare you\b.*[?\？]",
        r"\bis there\b.*[?\？]",
        r"\bhave you\b.*[?\？]",
    ]

    @classmethod
    def check_if_has_follow_up_questions(cls, ai_response: str) -> bool:
        """檢查 AI 回應是否包含追加問題 - 支援多語言"""
        if not ai_response or not isinstance(ai_response, str):
            return False

        ai_response_lower = ai_response.lower().strip()

        # 1. 檢查問號
        if cls._has_question_marks(ai_response):
            return True

        # 2. 檢查問題關鍵字
        if cls._has_question_indicators(ai_response_lower):
            return True

        # 3. 檢查缺少資訊關鍵字
        if cls._has_missing_info_indicators(ai_response_lower):
            return True

        # 4. 檢查英文問句結構
        if cls._has_english_question_patterns(ai_response_lower):
            return True

        return False

    @classmethod
    def _has_question_marks(cls, text: str) -> bool:
        """檢查是否包含問號"""
        return any(mark in text for mark in cls.QUESTION_MARKS)

    @classmethod
    def _has_question_indicators(cls, text_lower: str) -> bool:
        """檢查是否包含問題關鍵字"""
        for lang_indicators in cls.QUESTION_INDICATORS.values():
            for indicator in lang_indicators:
                if indicator.lower() in text_lower:
                    return True
        return False

    @classmethod
    def _has_missing_info_indicators(cls, text_lower: str) -> bool:
        """檢查是否包含缺少資訊關鍵字"""
        for lang_indicators in cls.MISSING_INFO_INDICATORS.values():
            for indicator in lang_indicators:
                if indicator.lower() in text_lower:
                    return True
        return False

    @classmethod
    def _has_english_question_patterns(cls, text_lower: str) -> bool:
        """檢查英文問句結構"""
        for pattern in cls.ENGLISH_QUESTION_PATTERNS:
            if re.search(pattern, text_lower):
                return True
        return False

    @classmethod
    def analyze_response_type(cls, ai_response: str) -> Dict[str, Any]:
        """分析 AI 回應類型，提供更詳細的資訊"""
        result = {
            "has_follow_up_questions": cls.check_if_has_follow_up_questions(
                ai_response
            ),
            "has_question_marks": cls._has_question_marks(ai_response),
            "has_question_indicators": cls._has_question_indicators(
                ai_response.lower()
            ),
            "has_missing_info": cls._has_missing_info_indicators(ai_response.lower()),
            "has_english_questions": cls._has_english_question_patterns(
                ai_response.lower()
            ),
            "response_length": len(ai_response),
            "detected_languages": cls._detect_languages(ai_response),
        }
        return result

    @classmethod
    def _detect_languages(cls, text: str) -> List[str]:
        """簡單的語言檢測（基於關鍵字）"""
        detected = []
        text_lower = text.lower()

        language_features = {
            "zh": ["您", "我", "的", "了", "是", "在", "有", "和"],
            "en": ["the", "and", "or", "you", "your", "we", "can", "will"],
            "ja": ["です", "ます", "ている", "について", "から", "まで"],
            "ko": ["입니다", "있습니다", "합니다", "에서", "으로", "를"],
        }

        for lang, features in language_features.items():
            if any(feature in text_lower for feature in features):
                detected.append(lang)

        return detected


# 便利函數，向後兼容
def check_if_ai_has_follow_up_questions(ai_response: str) -> bool:
    """檢查 AI 回應是否包含追加問題的便利函數"""
    return AIResponseAnalyzer.check_if_has_follow_up_questions(ai_response)


def is_json_message(message: str) -> bool:
    """檢查消息是否為 JSON 格式

    Args:
        message: AI 回應的消息

    Returns:
        bool: 如果消息是 JSON 格式則返回 True
    """
    return message.strip().startswith("```json") and message.strip().endswith("```")


def extract_search_params(message: str) -> Dict[str, Any]:
    """從 JSON 消息中提取搜索參數

    Args:
        message: 包含 JSON 的消息字符串

    Returns:
        Dict[str, Any]: 解析出的搜索參數，解析失敗則返回空字典
    """
    try:
        # 提取 JSON 內容
        json_match = re.search(r"```json\n(.*?)\n```", message, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
            return json.loads(json_str)
        return {}
    except (json.JSONDecodeError, AttributeError):
        return {}


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


def get_ai_analysis_summary(collected_info: Dict) -> Dict[str, Any]:
    """獲取 AI 分析摘要"""
    return {
        "total_criteria": len(collected_info),
        "required_completed": _is_collection_complete(collected_info),
        "optional_criteria": {
            key: value
            for key, value in collected_info.items()
            if key not in ["radius", "cuisine"]
        },
        "completion_percentage": (len(collected_info) / 7 * 100),  # 假設最多7個標準
    }


def should_return_recommendations(ai_response: str) -> bool:
    """
    綜合判斷是否應該返回餐廳推薦
    結合 JSON 檢測和問題檢測

    Args:
        ai_response: AI 的回應文字

    Returns:
        bool: True 如果應該返回推薦，False 如果還在收集信息
    """
    # 如果是 JSON 格式且沒有追加問題，則返回推薦
    if is_json_message(ai_response):
        # 即使是 JSON，也要檢查是否還有問題
        return not AIResponseAnalyzer.check_if_has_follow_up_questions(ai_response)

    # 如果不是 JSON 格式，不返回推薦
    return False
