import json
import re
from typing import Any, Dict


class ResponseFormatter:
    """回應格式化工具"""

    @staticmethod
    def clean_json_response(raw_text: str) -> str:
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

    @staticmethod
    def is_json_message(message: str) -> bool:
        """檢查消息是否為 JSON 格式

        Args:
            message: AI 回應的消息

        Returns:
            bool: 如果消息是 JSON 格式則返回 True
        """
        return message.strip().startswith("```json") and message.strip().endswith("```")

    @staticmethod
    def extract_search_params(message: str) -> Dict[str, Any]:
        """從 JSON 消息中提取搜索參數，使用 ResponseFormatter"""
        try:
            # 提取 JSON 代碼塊
            json_match = re.search(r"```json\n(.*?)\n```", message, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                cleaned_str = ResponseFormatter.clean_json_response(json_str)
                return ResponseFormatter.parse_json_safely(cleaned_str)
            return {}
        except AttributeError:
            return {}

