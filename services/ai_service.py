import logging
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from google import genai
from google.genai import types

from config.constants import SYSTEM_PROMPT
from config.setting import AISettings
from models.data_models import ChatMessage
from models.user_session import UserSession
from utils.exceptions import AIServiceError

logger = logging.getLogger(__name__)


class AIServiceInterface(ABC):
    """AI 服務介面"""

    @abstractmethod
    async def generate_response(self, messages: List[ChatMessage]) -> str:
        """生成 AI 回應"""
        pass


class GeminiAIService(AIServiceInterface):
    """Gemini AI 服務"""

    def __init__(self, config: AISettings):
        self.config = config
        # 驗證設定
        self.config.validate()

        # 初始化客戶端
        self.client = genai.Client(api_key=config.api_key)

        logger.info(f"🚀 Gemini AI 服務初始化完成 - 模型: {config.model}")

    def _convert_messages_to_contents(
        self, messages: List[ChatMessage]
    ) -> List[Dict[str, Any]]:
        """轉換訊息格式給 Gemini API"""
        role_map = {
            "system": "model",  # Gemini 中系統訊息用 model 角色
            "assistant": "model",
            "user": "user",
        }

        contents = []
        for msg in messages:
            # 跳過系統訊息，因為我們會用 system_instruction
            if msg.role == "system":
                continue

            contents.append(
                {
                    "role": role_map.get(msg.role, "user"),
                    "parts": [{"text": msg.content}],
                }
            )

        return contents

    async def generate_response(self, messages: List[ChatMessage]) -> str:
        """生成 AI 回應"""
        try:
            # 轉換訊息格式
            contents = self._convert_messages_to_contents(messages)

            logger.info(f"📤 發送請求到 Gemini API - 訊息數: {len(contents)}")
            logger.debug(f"請求內容預覽: {contents[:2] if contents else '無內容'}")

            # 配置生成參數
            generation_config = types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=self.config.temperature,
                max_output_tokens=self.config.max_tokens,
                top_p=self.config.top_p,
                top_k=self.config.top_k,
            )

            # 調用 API
            response = self.client.models.generate_content(
                model=self.config.model,
                config=generation_config,
                contents=contents,
            )

            # 檢查回應
            if not response:
                raise AIServiceError("AI 服務無回應")

            if not response.text:
                logger.error(f"AI 回應為空 - 完整回應: {response}")
                raise AIServiceError("AI 回應內容為空")

            response_text = response.text.strip()
            logger.info(f"📥 AI 回應成功 - 長度: {len(response_text)} 字符")
            logger.debug(f"回應內容預覽: {response_text[:100]}...")

            return response_text

        except Exception as e:
            logger.error(f"❌ AI 服務調用失敗: {type(e).__name__}: {e}")

            # 更詳細的錯誤處理
            if "API_KEY" in str(e).upper():
                raise AIServiceError("API Key 無效或未設定")
            elif "QUOTA" in str(e).upper():
                raise AIServiceError("API 配額已用完")
            elif "MODEL" in str(e).upper():
                raise AIServiceError(f"模型 '{self.config.model}' 不可用")
            else:
                raise AIServiceError(f"AI 服務異常: {str(e)}")


# class SessionService:
#     def __init__(self, session_timeout: int = 3600):
#         self.sessions: Dict[str, UserSession] = {}
#         self.session_timeout = session_timeout

#     def get_session(self, user_id: str) -> UserSession:
#         """獲取或創建用戶會話"""
#         if user_id not in self.sessions:
#             self.sessions[user_id] = UserSession(user_id=user_id)
#             logging.info(f"為用戶 {user_id} 創建新會話")
#         return self.sessions[user_id]

#     def clear_session(self, user_id: str) -> bool:
#         """
#         完全移除用戶會話
#         Returns True if session existed and was removed, False otherwise
#         """
#         removed = self.sessions.pop(user_id, None)
#         if removed:
#             logging.info(f"已移除用戶 {user_id} 的會話")
#             return True
#         return False

#     def clear_session_history(self, user_id: str) -> bool:
#         """
#         只清除用戶會話的歷史記錄，保留會話對象和搜索條件
#         Returns True if session exists, False otherwise
#         """
#         if user_id in self.sessions:
#             self.sessions[user_id].clear_history()
#             logging.info(f"已清除用戶 {user_id} 的會話歷史")
#             return True
#         return False

#     def rollback_session_messages(
#         self, user_id: str, count: int = 1
#     ) -> List[ChatMessage]:
#         """
#         回滾用戶會話的最後 N 條訊息

#         Args:
#             user_id: 用戶ID
#             count: 要回滾的訊息數量

#         Returns:
#             List[ChatMessage]: 被回滾的訊息列表
#         """
#         if user_id in self.sessions:
#             rolled_back = self.sessions[user_id].rollback_last_messages(count)
#             if rolled_back:
#                 logging.info(f"為用戶 {user_id} 回滾了 {len(rolled_back)} 條訊息")
#             return rolled_back
#         return []

#     def session_exists(self, user_id: str) -> bool:
#         """檢查用戶會話是否存在"""
#         return user_id in self.sessions

#     def get_session_info(self, user_id: str) -> Dict:
#         """
#         獲取會話資訊

#         Returns:
#             dict: 會話資訊字典
#         """
#         if user_id not in self.sessions:
#             return {"exists": False}

#         session = self.sessions[user_id]
#         return {
#             "exists": True,
#             "user_id": session.user_id,
#             "message_count": session.get_message_count(),
#             "created_at": session.created_at.isoformat(),
#             "updated_at": session.updated_at.isoformat(),
#             "is_empty": session.is_empty(),
#             "has_recent_activity": session.has_recent_activity(),
#             "conversation_duration_minutes": session.get_conversation_duration() / 60,
#             "search_criteria": (
#                 session.data.__dict__
#                 if hasattr(session.data, "__dict__")
#                 else str(session.data)
#             ),
#         }

#     def get_all_sessions_info(self) -> List[Dict]:
#         """
#         獲取所有會話的資訊

#         Returns:
#             List[Dict]: 所有會話的資訊列表
#         """
#         return [self.get_session_info(user_id) for user_id in self.sessions.keys()]

#     def cleanup_inactive_sessions(self, inactive_minutes: int = 0) -> int:
#         """
#         清理不活躍的會話

#         Args:
#             inactive_minutes: 不活躍的時間閾值（分鐘），如果為 None 則使用 session_timeout

#         Returns:
#             int: 被清理的會話數量
#         """
#         if inactive_minutes is None:
#             inactive_minutes = self.session_timeout / 60

#         cutoff_time = datetime.now() - timedelta(minutes=inactive_minutes)
#         inactive_users = []

#         for user_id, session in self.sessions.items():
#             if session.updated_at < cutoff_time:
#                 inactive_users.append(user_id)

#         # 移除不活躍的會話
#         for user_id in inactive_users:
#             self.clear_session(user_id)

#         if inactive_users:
#             logging.info(f"清理了 {len(inactive_users)} 個不活躍會話")

#         return len(inactive_users)

#     def get_active_session_count(self) -> int:
#         """獲取活躍會話數量"""
#         return len(self.sessions)

#     def update_session_search_criteria(self, user_id: str, **kwargs) -> bool:
#         """
#         更新用戶會話的搜索條件

#         Args:
#             user_id: 用戶ID
#             **kwargs: 要更新的搜索條件

#         Returns:
#             bool: 更新成功返回 True，會話不存在返回 False
#         """
#         if user_id in self.sessions:
#             self.sessions[user_id].update_search_criteria(**kwargs)
#             logging.info(f"已更新用戶 {user_id} 的搜索條件")
#             return True
#         return False

#     def reset_session_search_criteria(self, user_id: str) -> bool:
#         """
#         重置用戶會話的搜索條件

#         Args:
#             user_id: 用戶ID

#         Returns:
#             bool: 重置成功返回 True，會話不存在返回 False
#         """
#         if user_id in self.sessions:
#             self.sessions[user_id].reset_search_criteria()
#             logging.info(f"已重置用戶 {user_id} 的搜索條件")
#             return True
#         return False

#     def get_session_summary(self, user_id: str) -> Optional[Dict]:
#         """
#         獲取會話摘要

#         Args:
#             user_id: 用戶ID

#         Returns:
#             Dict: 會話摘要，如果會話不存在返回 None
#         """
#         if user_id in self.sessions:
#             return self.sessions[user_id].get_session_summary()
#         return None

#     def export_session_data(self, user_id: str) -> Optional[Dict]:
#         """
#         導出會話資料

#         Args:
#             user_id: 用戶ID

#         Returns:
#             Dict: 完整的會話資料，如果會話不存在返回 None
#         """
#         if user_id in self.sessions:
#             return self.sessions[user_id].to_dict()
#         return None

#     def get_statistics(self) -> Dict:
#         """
#         獲取服務統計資料

#         Returns:
#             Dict: 統計資料
#         """
#         if not self.sessions:
#             return {
#                 "total_sessions": 0,
#                 "active_sessions": 0,
#                 "average_messages_per_session": 0,
#                 "total_messages": 0,
#             }

#         total_messages = sum(
#             session.get_message_count() for session in self.sessions.values()
#         )
#         active_sessions = sum(
#             1 for session in self.sessions.values() if session.has_recent_activity()
#         )

#         return {
#             "total_sessions": len(self.sessions),
#             "active_sessions": active_sessions,
#             "average_messages_per_session": total_messages / len(self.sessions),
#             "total_messages": total_messages,
#             "oldest_session": min(
#                 session.created_at for session in self.sessions.values()
#             ),
#             "newest_session": max(
#                 session.created_at for session in self.sessions.values()
#             ),
#         }
