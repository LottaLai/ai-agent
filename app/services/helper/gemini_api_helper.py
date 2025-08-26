from typing import Any, Dict, List

from google.genai import types

from app.models.data_models import ChatMessage
from app.prompts.enums import MessageRole
from shared.utils.exceptions import AIServiceError


class GeminiAPIHelper:
    def __init__(self, client, response_formatter):
        self.client = client
        self.response_formatter = response_formatter

    def convert_messages(self, messages: List[ChatMessage]) -> List[Dict[str, Any]]:
        role_map = {MessageRole.SYSTEM: "model", MessageRole.ASSISTANT: "model", MessageRole.USER: "user"}
        return [
            {"role": role_map.get(msg.role, "user"), "parts": [{"text": msg.content}]}
            for msg in messages if msg.role != MessageRole.SYSTEM
        ]

    async def call_api(
        self, client, model: str, system_prompt: str, user_message: str, temperature: float, max_tokens: int, top_p: float, top_k: int
    ) -> str:
        contents = [{"role": "user", "parts": [{"text": user_message}]}]
        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=temperature,
            max_output_tokens=max_tokens,
            top_p=top_p,
            top_k=top_k,
        )
        response = self.client.models.generate_content(model=model, config=config, contents=contents)
        if not response or not response.text:
            raise AIServiceError("AI 回應為空")
        return self.response_formatter.clean_json_response(response.text.strip())
