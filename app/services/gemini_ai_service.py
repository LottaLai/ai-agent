import json
from asyncio.log import logger
from typing import List

from google import genai

from app.builders.prompt_builder import SystemPromptBuilder
from app.core.setting import AISettings
from app.prompts.enums import PromptType
from app.repositories.interfaces.ai_service_interface import AIServiceInterface
from app.services.helper.gemini_api_helper import GeminiAPIHelper
from app.services.prompt_service import PromptService
from app.utils.response_formatter import ResponseFormatter


class GeminiAIService(AIServiceInterface):
    def __init__(self, config: AISettings):
        self.config = config
        self.config.validate()
        self.client = genai.Client(api_key=config.api_key)
        self.prompt_service = PromptService(SystemPromptBuilder())
        self.api_helper = GeminiAPIHelper(self.client, ResponseFormatter())
        logger.info(f"🚀 Gemini AI 服務初始化完成 - 模型: {config.model}")

    async def smart_analyze_user_input(self, user_input: str, context: dict) -> dict:
        """智能分析用戶輸入，總是回傳完整的搜尋參數"""
        try:
            # 構建智能分析的 system prompt
            system_prompt = self.prompt_service.build(
                PromptType.SMART_RESTAURANT_ANALYSIS,
                **context
            )

            # 準備用戶訊息，包含更多上下文
            enhanced_user_message = f"""
            用戶需求: "{user_input}"
            當前時間: {context.get('time', '18:00')}
            位置資訊: {context.get('location', '未指定')}

            請分析並回傳完整的搜尋參數。
            """

            # 呼叫 AI
            response_text = await self.api_helper.call_api(
                client=self.client,
                model=self.config.model,
                system_prompt=system_prompt,
                user_message=enhanced_user_message,
                temperature=0.1,  # 低溫度確保穩定輸出
                max_tokens=self.config.max_tokens,
                top_p=self.config.top_p,
                top_k=self.config.top_k,
            )

            # 解析 JSON 回應
            try:
                import json
                result = json.loads(response_text.strip())

                # 驗證必要欄位
                required_fields = ['cuisine', 'radius_meters', 'price_level', 'min_rating', 'try_new']
                for field in required_fields:
                    if field not in result:
                        # 補充預設值
                        defaults = {
                            'cuisine': '其他',
                            'radius_meters': 1000,
                            'price_level': 2,
                            'min_rating': 3.5,
                            'try_new': False
                        }
                        result[field] = defaults[field]

                logger.info(f"✅ 智能分析成功: {result}")
                return {
                    "success": True,
                    "search_params": result,
                    "confidence": result.get('confidence', 0.8)
                }

            except json.JSONDecodeError as e:
                logger.error(f"❌ JSON 解析失敗: {e}, 原始回應: {response_text}")
                # 回傳預設搜尋參數
                return self._get_fallback_params(user_input)

        except Exception as e:
            logger.error(f"❌ 智能分析失敗: {e}")
            return self._get_fallback_params(user_input)

    def _get_fallback_params(self, user_input: str) -> dict:
        """當 AI 分析失敗時的備用參數"""
        return {
            "success": True,
            "search_params": {
                "cuisine": "其他",
                "radius_meters": 1000,
                "price_level": 2,
                "min_rating": 3.5,
                "try_new": False,
                "dietary_requirements": [],
                "atmosphere": "",
                "confidence": 0.3
            },
            "confidence": 0.3,
            "fallback_used": True
        }
