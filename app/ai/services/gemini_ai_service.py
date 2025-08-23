import json
from asyncio.log import logger
from typing import List

from ai.builders.prompt_builder import SystemPromptBuilder
from ai.core.setting import AISettings
from ai.models.data_models import ChatMessage
from ai.prompts.enums import PromptType
from ai.services.ai_service_interface import AIServiceInterface
from ai.services.gemini_api_helper import GeminiAPIHelper
from ai.services.prompt_service import PromptService
from ai.utils.response_formatter import ResponseFormatter
from google import genai
from google.genai import types

from shared.utils.exceptions import AIServiceError


class GeminiAIService(AIServiceInterface):
    def __init__(self, config: AISettings):
        self.config = config
        self.config.validate()
        self.client = genai.Client(api_key=config.api_key)
        self.prompt_service = PromptService(SystemPromptBuilder())
        self.api_helper = GeminiAPIHelper(self.client, ResponseFormatter())
        logger.info(f"🚀 Gemini AI 服務初始化完成 - 模型: {config.model}")

    async def generate_response(self, messages: List[ChatMessage]) -> str:
        try:
            contents = self.api_helper.convert_messages(messages)
            system_prompt = self.prompt_service.get_legacy_prompt()
            return await self.api_helper.call_api(
                client=self.client,
                model=self.config.model,
                system_prompt=system_prompt,
                user_message=contents[-1]["parts"][0]["text"] if contents else "",
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                top_p=self.config.top_p,
                top_k=self.config.top_k,
            )
        except Exception as e:
            logger.error(f"❌ AI 服務調用失敗: {e}")
            raise AIServiceError(str(e))


    async def analyze_user_intent(self, user_input: str, session_history: dict, context: dict) -> dict:
        """
        分析用戶意圖並提取餐廳搜尋相關信息。
        """
        try:
            # 組裝輸入給 AI
            user_message = f"""
    用戶輸入: "{user_input}"
    會話歷史: {session_history}
    上下文: {context}

    請分析這個用戶輸入並提取餐廳搜尋相關信息。
    """

            # 根據上下文生成 Prompt
            prompt_kwargs = {}
            if "location" in context:
                prompt_kwargs["用戶位置"] = context["location"]
            if "time" in context:
                prompt_kwargs["當前時間"] = context["time"]

            system_prompt = self.prompt_service.build(
                prompt_type=PromptType.INTENT_ANALYSIS,
                **prompt_kwargs
            )

            # 呼叫 Gemini API
            response_text = await self.api_helper.call_api(
                client=self.client,
                model=self.config.model,
                system_prompt=system_prompt,
                user_message=user_message,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                top_p=self.config.top_p,
                top_k=self.config.top_k,
            )

            # 嘗試解析 JSON
            try:
                result = json.loads(response_text)
                return result
            except json.JSONDecodeError:
                return {
                    "success": False,
                    "confidence": 0.0,
                    "extracted_info": {},
                    "missing_info": ["所有必要信息"],
                    "user_intent": "無法解析用戶意圖",
                }

        except Exception as e:
            # 捕獲異常並返回預設值
            return {
                "success": False,
                "confidence": 0.0,
                "extracted_info": {},
                "missing_info": ["所有必要信息"],
                "user_intent": "分析過程中出現錯誤",
            }

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

            response_text = await self.api_helper.call_api(
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


    def update_prompt_template(self, prompt_type: PromptType, **updates):
        """動態更新 Prompt 模板（可用於 A/B 測試或配置調整）"""
        try:
            template = self.prompt_service.builder.templates.get(prompt_type)
            if template:
                for key, value in updates.items():
                    if hasattr(template, key):
                        setattr(template, key, value)
                logger.info(f"📝 更新 Prompt 模板: {prompt_type.value}")
            else:
                logger.warning(f"未找到 Prompt 模板: {prompt_type.value}")
        except Exception as e:
            logger.error(f"❌ 更新 Prompt 模板失敗: {e}")

    def switch_to_advanced_mode(self, enable: bool = True):
        """切換到高級模式（使用新的結構化 Prompt）"""
        if enable:
            logger.info("🔄 切換到高級 AI 模式")
            # 可以在這裡添加切換邏輯
        else:
            logger.info("🔄 切換到兼容模式")

    async def generate_follow_up_question(self, missing_info: List, current_context: dict, user_input: str) -> str:
        raise NotImplementedError

            # 保持原有邏輯
