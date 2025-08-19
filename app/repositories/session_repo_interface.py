from abc import ABC, abstractmethod
from typing import Dict, Optional

from app.models.user_session import UserSession


class SessionRepositoryInterface(ABC):
    """會話儲存介面"""

    @abstractmethod
    def get(self, user_id: str) -> Optional[UserSession]:
        pass

    @abstractmethod
    def save(self, session: UserSession) -> None:
        pass

    @abstractmethod
    def delete(self, user_id: str) -> bool:
        pass

    @abstractmethod
    def list_all(self) -> Dict[str, UserSession]:
        pass
