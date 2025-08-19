import os
from dataclasses import dataclass
from functools import lru_cache


@dataclass
class AISettings:
    """AI 服務設定"""

    api_key: str
    model: str = "gemini-2.0-flash-lite"  # 注意：正確的模型名稱
    max_tokens: int = 1000
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 40

    def validate(self) -> None:
        """驗證設定"""
        if not self.api_key:
            raise ValueError("AI API Key 不能為空")

        if self.temperature < 0 or self.temperature > 2:
            raise ValueError("Temperature 必須在 0-2 之間")

        if self.max_tokens <= 0:
            raise ValueError("max_tokens 必須大於 0")

        print(f"✅ AI 設定驗證通過 - 模型: {self.model}")


@lru_cache()
def get_ai_settings() -> AISettings:
    """取得 AI 設定"""
    return AISettings(
        api_key=os.getenv("GEMINI_API_KEY", ""),
        model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash-exp"),
        max_tokens=int(os.getenv("GEMINI_MAX_TOKENS", "1000")),
        temperature=float(os.getenv("GEMINI_TEMPERATURE", "0.7")),
        top_p=float(os.getenv("GEMINI_TOP_P", "0.9")),
        top_k=int(os.getenv("GEMINI_TOP_K", "40")),
    )


@dataclass
class AppSettings:
    """應用程式設定"""

    debug: bool = False
    log_level: str = "INFO"
    session_timeout: int = 3600
    host: str = "0.0.0.0"
    port: int = 8000


class Config:
    """配置管理類"""

    def __init__(self):
        self.ai = AISettings(
            api_key=os.getenv("GEMINI_API_KEY", ""),
            model=os.getenv("AI_MODEL", "gemini-2.5-flash"),
        )
        self.app = AppSettings(
            debug=os.getenv("DEBUG", "false").lower() == "true",
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            host=os.getenv("HOST", "0.0.0.0"),
            port=int(os.getenv("PORT", "8000")),
        )

    def validate(self) -> bool:
        """驗證配置"""
        if not self.ai.api_key:
            raise ValueError("GEMINI_API_KEY 環境變數未設定")
        return True
