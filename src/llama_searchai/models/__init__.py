"""Models module for LlamaSearch AI."""

# Import models for easier access
from .common import ErrorResponse, HealthResponse, PaginatedResponse
from .search import Query, SearchRequest, SearchResponse, SearchResult
from .vector import (
    EmbedRequest,
    EmbedResponse,
    VectorSearchRequest,
    VectorSearchResponse,
)

__all__ = [
    "ErrorResponse",
    "HealthResponse",
    "PaginatedResponse",
    "Query",
    "SearchRequest",
    "SearchResponse",
    "SearchResult",
    "EmbedRequest",
    "EmbedResponse",
    "VectorSearchRequest",
    "VectorSearchResponse",
]
