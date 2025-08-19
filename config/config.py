# app/core/config.py
from functools import lru_cache

from config.setting import Config


@lru_cache()
def get_config() -> Config:
    """
    取得配置實例 (使用 LRU cache 確保單例)
    """
    return Config()
