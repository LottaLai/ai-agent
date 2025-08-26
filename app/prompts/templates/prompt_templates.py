from typing import Dict

from app.models.prompt_template import PromptTemplate
from app.prompts.enums import PromptType


class PromptTemplateRegistry:
    """改進的 Prompt 模板註冊表"""

    @staticmethod
    def get_templates() -> Dict[PromptType, PromptTemplate]:
        return {
            PromptType.SMART_RESTAURANT_ANALYSIS: PromptTemplate(
                role="你是一個智能餐廳搜尋分析助手",
                task="""分析用戶的餐廳搜尋需求，智能提取和補充搜尋參數。
                重要：你必須總是回傳完整的搜尋參數，對於缺失的必要資訊使用合理的預設值。""",

                output_format="""嚴格按照以下 JSON 格式回傳：
                {
                    "cuisine": "菜系類型，必須是以下之一：中式|日式|韓式|泰式|義大利菜|法式|美式|印度菜|越南菜|川菜|粤菜|其他",
                    "radius_meters": 搜尋半徑數值(整數，單位：公尺),
                    "price_level": 價格等級(1-4，1=平價，2=中等，3=中高，4=高檔),
                    "min_rating": 最低評分(1.0-5.0),
                    "try_new": 是否嘗試新餐廳(true/false),
                    "dietary_requirements": ["素食", "清真", "無麩質等特殊需求"],
                    "atmosphere": "用餐氛圍偏好",
                    "confidence": 信心分數(0.0-1.0)
                }""",

                rules=[
                    "必須總是回傳完整的JSON，不可省略任何欄位",
                    "對於用戶未明確提及的必要參數，使用以下預設值：",
                    "- radius_meters: 1000 (1公里)",
                    "- price_level: 2 (中等價位)",
                    "- min_rating: 3.5",
                    "- try_new: false",
                    "根據用戶輸入的自然語言智能判斷菜系類型",
                    "自動處理距離單位轉換：km→公尺, 步行時間→距離",
                    "confidence 反映提取資訊的可靠程度，有明確需求時>0.8",
                    "回傳純 JSON，不要包含 ```json 標記"
                ],

                examples=[
                    "用戶：「找附近的日本料理」→ radius_meters: 1000, cuisine: 日式",
                    "用戶：「3公里內的便宜中餐」→ radius_meters: 3000, cuisine: 中式, price_level: 1",
                    "用戶：「走路10分鐘的高檔法國菜」→ radius_meters: 800, cuisine: 法式, price_level: 4",
                    "用戶：「想試試新的韓式料理，評分要高一點」→ cuisine: 韓式, try_new: true, min_rating: 4.0"
                ],

                constraints=[
                    "絕對不要詢問額外資訊，總是提供完整參數",
                    "使用邏輯推理補充缺失資訊",
                    "保持 JSON 格式嚴格正確",
                    "confidence < 0.5 時仍要提供最佳猜測"
                ],

                domain_knowledge={
                    "distance_hints": {
                        "附近/nearby": "1000公尺",
                        "走路5分鐘": "400公尺",
                        "走路10分鐘": "800公尺",
                        "走路15分鐘": "1200公尺",
                        "騎車範圍": "3000公尺",
                        "開車範圍": "10000公尺"
                    },
                    "price_hints": {
                        "便宜/平價/實惠": 1,
                        "一般/中等": 2,
                        "高檔/精緻/昂貴": 3,
                        "頂級/奢華": 4
                    },
                    "cuisine_intelligence": "使用自然語言理解，不依賴預定義對應表"
                }
            )
        }
