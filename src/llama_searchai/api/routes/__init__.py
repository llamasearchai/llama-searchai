"""
Routes module for LlamaSearch AI API.
"""

from .personalization import router as personalization_router
from .search import router as search_router
from .vector import router as vector_router

__all__ = [
    "search_router",
    "vector_router",
    "personalization_router",
]
