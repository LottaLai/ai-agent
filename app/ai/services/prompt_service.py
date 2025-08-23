import logging
from typing import Any

from app.ai.builders.prompt_builder import SystemPromptBuilder
from app.ai.prompts.enums import PromptType

logger = logging.getLogger(__name__)

class PromptService:
    """封裝 Prompt 生成功能"""

    def __init__(self, builder: SystemPromptBuilder):
        self.builder = builder

    def build(self, prompt_type: PromptType, **kwargs) -> str:
        """
        根據 PromptType 和可選參數生成 Prompt。
        """
        try:
            return self.builder.build_prompt(prompt_type, **kwargs)
        except Exception as e:
            logger.error(f"❌ 生成 Prompt 失敗: {e}")
            return f"無法生成 Prompt: {e}"

    def get_legacy_prompt(self) -> str:
        """
        取得舊版 SYSTEM_PROMPT，向後兼容使用。
        """
        try:
            return self.builder.get_legacy_prompt()
        except Exception as e:
            logger.error(f"❌ 取得 legacy Prompt 失敗: {e}")
            return ""

    def update_template(self, prompt_type: PromptType, **updates):
        """
        動態更新模板，用於 A/B 測試或微調。
        """
        try:
            template = self.builder.templates.get(prompt_type)
            if template:
                for key, value in updates.items():
                    if hasattr(template, key):
                        setattr(template, key, value)
                logger.info(f"📝 更新 Prompt 模板: {prompt_type.value}")
            else:
                logger.warning(f"未找到 Prompt 模板: {prompt_type.value}")
        except Exception as e:
            logger.error(f"❌ 更新 Prompt 模板失敗: {e}")

    def preview(self, prompt_type: PromptType, **kwargs) -> str:
        """
        預覽生成的 Prompt（可用於調試）
        """
        try:
            return self.builder.build_prompt(prompt_type, **kwargs)
        except Exception as e:
            logger.error(f"❌ 預覽 Prompt 失敗: {e}")
            return f"無法預覽 Prompt: {e}"
