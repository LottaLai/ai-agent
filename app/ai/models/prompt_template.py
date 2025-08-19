from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class PromptTemplate:
    """Prompt 模板數據類 - 類似 Android 的 Data Class"""

    role: str
    task: str
    output_format: str
    rules: List[str]
    examples: Optional[List[str]] = None
    constraints: Optional[List[str]] = None
    domain_knowledge: Optional[Dict[str, Any]] = None
