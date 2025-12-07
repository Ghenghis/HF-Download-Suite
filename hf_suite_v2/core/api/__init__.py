"""
API module for HF Download Suite.

Provides high-level API wrappers for:
- HuggingFace Hub API
- ModelScope API
- Repository information retrieval
- File listing and metadata
"""

from .huggingface import HuggingFaceAPI
from .modelscope import ModelScopeAPI
from .base import BaseAPI, APIError
from .cache import APICache, get_cache, cached, TTL_SEARCH, TTL_REPO_INFO, TTL_FILE_LIST

__all__ = [
    "HuggingFaceAPI",
    "ModelScopeAPI",
    "BaseAPI",
    "APIError",
    "APICache",
    "get_cache",
    "cached",
    "TTL_SEARCH",
    "TTL_REPO_INFO",
    "TTL_FILE_LIST",
]
