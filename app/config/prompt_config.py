from app.prompts.enums import PromptType


class PromptConfig:
    """Prompt 配置 - 類似 Android 的 Configuration"""

    # 溫度設定 - 類似 Android 的 theme attributes
    TEMPERATURES = {
        PromptType.SMART_RESTAURANT_ANALYSIS: 0.1
    }

    # Token 限制 - 類似 Android 的 dimension resources
    MAX_TOKENS = {
        PromptType.SMART_RESTAURANT_ANALYSIS: 1000
    }

    @classmethod
    def get_temperature(cls, prompt_type: PromptType) -> float:
        """獲取指定類型的溫度設定"""
        return cls.TEMPERATURES.get(prompt_type, 0.5)

    @classmethod
    def get_max_tokens(cls, prompt_type: PromptType) -> int:
        """獲取指定類型的Token限制"""
        return cls.MAX_TOKENS.get(prompt_type, 500)
