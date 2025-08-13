"""
Data models and schemas
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class ChatMessage:
    """聊天訊息實體"""

    role: str
    content: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class SearchCriteria:
    """搜尋條件資料實體"""

    radius: Optional[int] = None
    cuisine: Optional[str] = None
    meals: Optional[str] = None
    try_new: bool = False
    created_at: datetime = field(default_factory=datetime.now)

    def is_complete(self) -> bool:
        return self.radius is not None and self.cuisine is not None

    def get_missing_fields(self) -> List[str]:
        missing = []
        if self.radius is None:
            missing.append("radius")
        if self.cuisine is None:
            missing.append("cuisine")
        return missing
