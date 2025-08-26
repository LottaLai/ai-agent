from app.prompts.enums import PromptType
from app.prompts.templates.prompt_templates import PromptTemplateRegistry


class SystemPromptBuilder:
    """系統 Prompt 建構器 - 類似 Android 的 Builder Pattern"""

    def __init__(self):
        self.templates = PromptTemplateRegistry.get_templates()

    def build_prompt(self, prompt_type: PromptType, **kwargs) -> str:
        """建構指定類型的 System Prompt - 類似 Android 的 build() 方法"""
        template = self.templates.get(prompt_type)
        if not template:
            raise ValueError(f"未支援的 Prompt 類型: {prompt_type}")

        prompt_parts = [f"角色：{template.role}", f"\n任務：{template.task}"]

        # 添加領域知識
        if template.domain_knowledge:
            prompt_parts.append("\n領域知識：")
            self._add_domain_knowledge(prompt_parts, template.domain_knowledge)

        prompt_parts.append(f"\n輸出格式：\n{template.output_format}")

        # 添加規則
        prompt_parts.append("\n規則：")
        for i, rule in enumerate(template.rules, 1):
            prompt_parts.append(f"{i}. {rule}")

        # 添加約束條件
        if template.constraints:
            prompt_parts.append("\n約束條件：")
            for i, constraint in enumerate(template.constraints, 1):
                prompt_parts.append(f"{i}. {constraint}")

        # 添加範例
        if template.examples:
            prompt_parts.append("\n問題範例：")
            for i, example in enumerate(template.examples, 1):
                prompt_parts.append(f"{i}. {example}")

        # 添加額外參數
        if kwargs:
            prompt_parts.append("\n額外說明：")
            for key, value in kwargs.items():
                prompt_parts.append(f"- {key}: {value}")

        return "\n".join(prompt_parts)

    def _add_domain_knowledge(self, prompt_parts: list, domain_knowledge: dict):
        """添加領域知識 - 私有輔助方法"""
        for key, value in domain_knowledge.items():
            if key == "distance_conversion":
                prompt_parts.append("\n距離單位轉換規則：")
                for example in value["conversion_examples"]:
                    prompt_parts.append(f"- {example}")
            elif key == "cuisine_mapping":
                prompt_parts.append("\n菜系類型對應：")
                for standard_name, variants in value.items():
                    prompt_parts.append(f"- {'/'.join(variants)} → \"{standard_name}\"")
            elif key == "required_fields":
                prompt_parts.append(f"\n必填欄位：{', '.join(value)}")
            elif key == "optional_fields":
                prompt_parts.append(f"\n選填欄位：{', '.join(value)}")
