import json
import re
from typing import Any, Dict


class ResponseFormatter:
    """回應格式化工具"""

    @staticmethod
    def clean_ai_response(raw_text: str) -> str:
        """清理 AI 回應中的格式標記"""
        if not raw_text:
            return ""

        # 移除 markdown 代碼塊標記
        cleaned = re.sub(r"^```json\s*|```$", "", raw_text.strip(), flags=re.IGNORECASE)
        return cleaned.strip()

    @staticmethod
    def parse_json_safely(text: str) -> Dict[str, Any]:
        """安全解析 JSON"""
        try:
            return json.loads(text)
        except (json.JSONDecodeError, ValueError):
            return {}
