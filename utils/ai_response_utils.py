# utils/ai_response_utils.py

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
        ],
        # 日文
        "ja": [
            "いかがですか",
            "どうですか",
            "お聞かせください",
            "教えてください",
            "どちらが",
            "どのような",
            "ご希望",
            "お好み",
            "いかが",
            "よろしいですか",
            "どう思いますか",
        ],
        # 韓文
        "ko": [
            "어떻게 생각하세요",
            "원하시나요",
            "필요하신가요",
            "선호하시나요",
            "알려주세요",
            "어떤 종류",
            "어디를",
            "무엇을",
            "어떤 것을",
        ],
        # 西班牙文
        "es": [
            "te gustaria",
            "quieres",
            "necesitas",
            "prefieres",
            "puedes decirme",
            "que tipo de",
            "cual",
            "como te parece",
            "estas interesado",
            "te interesa",
        ],
        # 法文
        "fr": [
            "voulez-vous",
            "souhaitez-vous",
            "avez-vous besoin",
            "préférez-vous",
            "pouvez-vous me dire",
            "quel type de",
            "qu'est-ce que",
            "comment",
            "êtes-vous intéressé",
            "cela vous intéresse",
        ],
    }

    # 多語言缺少資訊關鍵字
    MISSING_INFO_INDICATORS = {
        # 中文繁體
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
            "詳細資料",
            "進一步說明",
        ],
        # 中文簡體
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
            "详细资料",
            "进一步说明",
        ],
        # 英文
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
            "further information",
            "clarification needed",
        ],
        # 日文
        "ja": [
            "不足",
            "もっと必要",
            "提供してください",
            "言及されていない",
            "不明確",
            "確認が必要",
            "指定してください",
            "必要",
            "詳細が必要",
            "もっと詳しく",
        ],
        # 韓文
        "ko": [
            "부족",
            "더 필요",
            "제공해주세요",
            "언급되지 않음",
            "불분명",
            "확인 필요",
            "지정해주세요",
            "필요",
            "자세한 정보",
            "추가 정보",
        ],
        # 西班牙文
        "es": [
            "falta",
            "necesito más",
            "por favor proporciona",
            "no mencionado",
            "no claro",
            "necesito confirmar",
            "por favor especifica",
            "información adicional",
            "más detalles",
        ],
        # 法文
        "fr": [
            "manque",
            "besoin de plus",
            "veuillez fournir",
            "pas mentionné",
            "pas clair",
            "besoin de confirmer",
            "veuillez spécifier",
            "informations supplémentaires",
            "plus de détails",
        ],
    }

    # 通用問號符號
    QUESTION_MARKS = ["？", "?", "¿", "؟"]  # 包含阿拉伯文問號

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
        """
        檢查 AI 回應是否包含追加問題 - 支援多語言

        Args:
            ai_response: AI 的回應文字

        Returns:
            bool: True 如果包含追加問題，False 否則
        """
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
        """
        分析 AI 回應類型，提供更詳細的資訊

        Args:
            ai_response: AI 的回應文字

        Returns:
            Dict: 包含分析結果的字典
        """
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

        # 檢查各語言的特徵詞彙
        language_features = {
            "zh": ["您", "我", "的", "了", "是", "在", "有", "和"],
            "en": ["the", "and", "or", "you", "your", "we", "can", "will"],
            "ja": ["です", "ます", "ている", "について", "から", "まで"],
            "ko": ["입니다", "있습니다", "합니다", "에서", "으로", "를"],
            "es": ["el", "la", "de", "que", "y", "es", "en", "un"],
            "fr": ["le", "de", "et", "à", "un", "il", "être", "et"],
        }

        for lang, features in language_features.items():
            if any(feature in text_lower for feature in features):
                detected.append(lang)

        return detected


# 便利函數，向後兼容
def check_if_ai_has_follow_up_questions(ai_response: str) -> bool:
    """
    檢查 AI 回應是否包含追加問題的便利函數

    Args:
        ai_response: AI 的回應文字

    Returns:
        bool: True 如果包含追加問題，False 否則
    """
    return AIResponseAnalyzer.check_if_has_follow_up_questions(ai_response)
