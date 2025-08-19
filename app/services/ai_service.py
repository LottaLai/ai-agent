import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from google import genai
from google.genai import types

from app.ai.builders.prompt_builder import SystemPromptBuilder
from app.ai.config.prompt_config import PromptConfig
from app.constants.enums import MessageRole, PromptType
from app.models.data_models import ChatMessage
from app.models.user_session import UserSession
from app.utils.exceptions import AIServiceError
from app.utils.formatters import ResponseFormatter
from config.setting import AISettings

logger = logging.getLogger(__name__)


class AIServiceInterface(ABC):
    """AI 服務介面"""

    @abstractmethod
    async def generate_response(self, messages: List[ChatMessage]) -> str:
        """生成 AI 回應"""
        pass

    @abstractmethod
    async def analyze_user_intent(
        self, user_input: str, session_history: dict, context: dict
    ) -> dict:
        """分析用戶意圖"""
        pass

    @abstractmethod
    async def generate_follow_up_question(
        self, missing_info: list, current_context: dict, user_input: str
    ) -> str:
        """生成後續問題"""
        pass

    @abstractmethod
    async def generate_search_response(
        self,
        restaurants: list,
        user_preferences: dict,
        search_params: dict,
        user_input: str,
    ) -> dict:
        """生成搜尋結果回應"""
        pass


class GeminiAIService(AIServiceInterface):
    """Gemini AI 服務"""

    def __init__(self, config: AISettings):
        self.config = config
        # 驗證設定
        self.config.validate()

        # 初始化客戶端
        self.client = genai.Client(api_key=config.api_key)

        # 初始化 Prompt 建構器
        self.prompt_builder = SystemPromptBuilder()

        self.response_formatter = ResponseFormatter()

        logger.info(f"🚀 Gemini AI 服務初始化完成 - 模型: {config.model}")

    def _convert_messages_to_contents(
        self, messages: List[ChatMessage]
    ) -> List[Dict[str, Any]]:
        """轉換訊息格式給 Gemini API"""
        role_map = {
            MessageRole.SYSTEM: "model",  # 使用常數
            MessageRole.ASSISTANT: "model",
            MessageRole.USER: "user",
        }

        contents = []
        for msg in messages:
            # 跳過系統訊息，因為我們會用 system_instruction
            if msg.role == MessageRole.SYSTEM:
                continue

            contents.append(
                {
                    "role": role_map.get(msg.role, "user"),
                    "parts": [{"text": msg.content}],
                }
            )

        return contents

    async def _call_gemini_api(
        self,
        prompt_type: PromptType,
        user_message: str,
        custom_prompt: Optional[str] = None,
        **prompt_kwargs,
    ) -> str:
        """統一的 Gemini API 調用方法"""
        try:
            # 使用結構化 Prompt 或自定義 Prompt
            if custom_prompt:
                system_prompt = custom_prompt
            else:
                system_prompt = self.prompt_builder.build_prompt(
                    prompt_type, **prompt_kwargs
                )

            contents = [{"role": "user", "parts": [{"text": user_message}]}]

            # 根據 Prompt 類型使用對應的配置
            temperature = PromptConfig.TEMPERATURES.get(
                prompt_type, self.config.temperature
            )
            max_tokens = PromptConfig.MAX_TOKENS.get(
                prompt_type, self.config.max_tokens
            )

            generation_config = types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=temperature,
                max_output_tokens=max_tokens,
                top_p=self.config.top_p,
                top_k=self.config.top_k,
            )

            response = self.client.models.generate_content(
                model=self.config.model,
                config=generation_config,
                contents=contents,
            )

            if not response or not response.text:
                raise AIServiceError("AI 回應為空")

            logger.debug(f"使用 Prompt 類型: {prompt_type.value}, 溫度: {temperature}")

            return self.response_formatter.clean_ai_response(response.text.strip())

        except Exception as e:
            logger.error(f"❌ Gemini API 調用失敗: {e}")
            raise AIServiceError(f"AI 服務異常: {str(e)}")

    async def generate_response(self, messages: List[ChatMessage]) -> str:
        """生成一般對話 AI 回應"""
        try:
            # 轉換訊息格式
            contents = self._convert_messages_to_contents(messages)

            logger.info(f"📤 發送請求到 Gemini API - 訊息數: {len(contents)}")

            # 可以選擇使用原有的 SYSTEM_PROMPT 或新的結構化 Prompt
            # 為了向後兼容，這裡使用原有的 SYSTEM_PROMPT
            system_prompt = self.prompt_builder.get_legacy_prompt()

            # 配置生成參數
            generation_config = types.GenerateContentConfig(
                system_instruction=system_prompt,
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
            print(f"{response.usage_metadata=}")

            if not response or not response.text:
                raise AIServiceError("AI 回應為空")

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

    async def analyze_user_intent(
        self, user_input: str, session_history: dict, context: dict
    ) -> dict:
        """分析用戶意圖並提取餐廳搜尋參數"""
        try:
            user_message = f"""
            用戶輸入: "{user_input}"
            會話歷史: {json.dumps(session_history, ensure_ascii=False, indent=2)}
            上下文: {json.dumps(context, ensure_ascii=False, indent=2)}

            請分析這個用戶輸入並提取餐廳搜尋相關信息。
            """

            # 添加額外的上下文信息到 Prompt
            prompt_kwargs = {}
            if context.get("location"):
                prompt_kwargs["用戶位置"] = context["location"]
            if context.get("time"):
                prompt_kwargs["當前時間"] = context["time"]

            response_text = await self._call_gemini_api(
                PromptType.INTENT_ANALYSIS, user_message, **prompt_kwargs
            )

            # 嘗試解析 JSON 回應
            try:
                result = json.loads(response_text)
                logger.info(
                    f"🧠 AI 意圖分析成功 - 信心度: {result.get('confidence', 0)}"
                )
                return result
            except json.JSONDecodeError:
                logger.error(f"AI 回應不是有效的 JSON: {response_text}")
                return {
                    "success": False,
                    "confidence": 0.0,
                    "extracted_info": {},
                    "missing_info": ["所有必要信息"],
                    "user_intent": "無法解析用戶意圖",
                }

        except Exception as e:
            logger.error(f"❌ 用戶意圖分析失敗: {e}")
            return {
                "success": False,
                "confidence": 0.0,
                "extracted_info": {},
                "missing_info": ["所有必要信息"],
                "user_intent": "分析過程中出現錯誤",
            }

    async def generate_follow_up_question(
        self, missing_info: list, current_context: dict, user_input: str
    ) -> str:
        """生成後續問題來收集缺少的信息"""
        try:
            user_message = f"""
用戶原始輸入: "{user_input}"
目前已收集的信息: {json.dumps(current_context, ensure_ascii=False, indent=2)}
缺少的信息: {missing_info}

請生成一個自然的問題來收集最重要的缺少信息。
"""

            # 根據缺少的信息類型調整 Prompt
            prompt_kwargs = {}
            if "cuisine" in missing_info:
                prompt_kwargs["重點"] = "優先詢問料理類型偏好"
            elif "radius" in missing_info:
                prompt_kwargs["重點"] = "優先詢問距離範圍"
            elif "price_level" in missing_info:
                prompt_kwargs["重點"] = "優先詢問價位預算"

            question = await self._call_gemini_api(
                PromptType.FOLLOW_UP_QUESTION, user_message, **prompt_kwargs
            )

            logger.info(f"💭 生成後續問題成功")
            return question

        except Exception as e:
            logger.error(f"❌ 生成後續問題失敗: {e}")
            return "請告訴我您想要什麼類型的餐廳？"

    async def generate_search_response(
        self,
        restaurants: list,
        user_preferences: dict,
        search_params: dict,
        user_input: str,
    ) -> dict:
        """生成個性化的搜尋結果回應"""
        try:
            restaurant_summary = []
            for r in restaurants[:5]:  # 只取前 5 個做摘要
                restaurant_summary.append(
                    {
                        "name": getattr(r, "name", "未知"),
                        "cuisine": getattr(r, "cuisine", "未知"),
                        "rating": getattr(r, "rating", 0),
                        "price_level": getattr(r, "price_level", 0),
                        "distance_km": getattr(r, "distance_km", 0),
                    }
                )

            user_message = f"""
用戶原始需求: "{user_input}"
用戶偏好: {json.dumps(user_preferences, ensure_ascii=False, indent=2)}
搜尋參數: {json.dumps(search_params, ensure_ascii=False, indent=2)}
找到的餐廳數量: {len(restaurants)}
餐廳摘要: {json.dumps(restaurant_summary, ensure_ascii=False, indent=2)}

請生成個性化的回應訊息。
"""

            # 根據結果數量調整 Prompt
            prompt_kwargs = {}
            if len(restaurants) == 0:
                prompt_kwargs["情況"] = "沒有找到符合條件的餐廳"
            elif len(restaurants) > 20:
                prompt_kwargs["情況"] = "找到很多餐廳，需要幫助篩選"
            elif len(restaurants) < 5:
                prompt_kwargs["情況"] = "餐廳選擇較少"

            response_text = await self._call_gemini_api(
                PromptType.SEARCH_RESPONSE, user_message, **prompt_kwargs
            )

            try:
                result = json.loads(response_text)
                logger.info(f"💬 生成搜尋回應成功")
                return result
            except json.JSONDecodeError:
                logger.error(f"搜尋回應不是有效的 JSON: {response_text}")
                return {
                    "message": f"我為您找到了 {len(restaurants)} 家符合條件的餐廳！",
                    "highlights": ["根據您的偏好篩選"],
                    "suggestions": ["您可以查看詳細信息選擇最喜歡的"],
                }

        except Exception as e:
            logger.error(f"❌ 生成搜尋回應失敗: {e}")
            return {
                "message": f"我為您找到了 {len(restaurants)} 家餐廳！",
                "highlights": [],
                "suggestions": [],
            }

    # === 新增的便利方法 ===

    async def legacy_restaurant_search(self, messages: List[ChatMessage]) -> str:
        """使用原有邏輯的餐廳搜尋（向後兼容）"""
        try:
            contents = self._convert_messages_to_contents(messages)

            # 使用原有的 Prompt 邏輯
            response_text = await self._call_gemini_api(
                PromptType.LEGACY_RESTAURANT_SEARCH,
                contents[-1]["parts"][0]["text"] if contents else "",
            )

            logger.info(f"🔄 使用原有餐廳搜尋邏輯成功")
            return response_text

        except Exception as e:
            logger.error(f"❌ 原有餐廳搜尋失敗: {e}")
            raise AIServiceError(f"餐廳搜尋服務異常: {str(e)}")

    def update_prompt_template(self, prompt_type: PromptType, **updates):
        """動態更新 Prompt 模板（可用於 A/B 測試或配置調整）"""
        try:
            template = self.prompt_builder.templates.get(prompt_type)
            if template:
                for key, value in updates.items():
                    if hasattr(template, key):
                        setattr(template, key, value)
                logger.info(f"📝 更新 Prompt 模板: {prompt_type.value}")
            else:
                logger.warning(f"未找到 Prompt 模板: {prompt_type.value}")
        except Exception as e:
            logger.error(f"❌ 更新 Prompt 模板失敗: {e}")

    def get_prompt_preview(self, prompt_type: PromptType, **kwargs) -> str:
        """預覽生成的 Prompt（用於調試）"""
        try:
            return self.prompt_builder.build_prompt(prompt_type, **kwargs)
        except Exception as e:
            logger.error(f"❌ 預覽 Prompt 失敗: {e}")
            return f"無法預覽 Prompt: {e}"

    def switch_to_advanced_mode(self, enable: bool = True):
        """切換到高級模式（使用新的結構化 Prompt）"""
        if enable:
            logger.info("🔄 切換到高級 AI 模式")
            # 可以在這裡添加切換邏輯
        else:
            logger.info("🔄 切換到兼容模式")
            # 保持原有邏輯
