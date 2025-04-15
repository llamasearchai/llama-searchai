"""
Search-related models for LlamaSearch AI.
"""

import enum
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Union

from pydantic import BaseModel, Field, HttpUrl

from .common import Metadata


class SearchResultType(str, enum.Enum):
    """Type of search result."""

    WEB = "web"
    IMAGE = "image"
    VIDEO = "video"
    NEWS = "news"
    DOCUMENT = "document"
    SOCIAL = "social"
    PRODUCT = "product"
    OTHER = "other"


class SearchIntent(str, enum.Enum):
    """Intent of a search query."""

    INFORMATIONAL = "informational"  # Seeking information
    NAVIGATIONAL = "navigational"  # Looking for a specific site
    TRANSACTIONAL = "transactional"  # Wants to buy/download something
    COMMERCIAL = "commercial"  # Researching products
    LOCAL = "local"  # Looking for local services
    VISUAL = "visual"  # Looking for images/videos
    NEWS = "news"  # Looking for recent news
    UNDEFINED = "undefined"  # Intent unclear


class SearchLocality(str, enum.Enum):
    """Locality of a search query."""

    GLOBAL = "global"  # No specific location
    LOCAL = "local"  # Specific location
    REGIONAL = "regional"  # Specific region
    NATIONAL = "national"  # Specific country
    UNDEFINED = "undefined"  # Locality unclear


class Query(BaseModel):
    """
    Search query model.

    Attributes:
        text: The raw query text.
        intent: The classified intent of the query.
        locality: The locality type of the query.
        language: The language of the query.
        query_id: A unique identifier for the query.
        timestamp: When the query was created.
        processed_text: Query text after preprocessing.
        parameters: Additional query parameters.
        context: Contextual information for the query.
    """

    text: str
    intent: SearchIntent = SearchIntent.UNDEFINED
    locality: SearchLocality = SearchLocality.UNDEFINED
    language: str = "en"
    query_id: Optional[str] = None
    timestamp: Optional[datetime] = None
    processed_text: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)
    context: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        """Pydantic model config."""

        schema_extra = {
            "example": {
                "text": "best restaurants in new york",
                "intent": "local",
                "locality": "local",
                "language": "en",
                "query_id": "q123456",
                "timestamp": "2023-07-01T12:34:56Z",
                "processed_text": "best restaurants new york",
                "parameters": {"include_ratings": True},
                "context": {"user_location": "Brooklyn"},
            }
        }


class SearchResult(BaseModel):
    """
    Search result model.

    Attributes:
        title: The title of the search result.
        url: The URL of the search result.
        snippet: A text snippet or description.
        provider: The search provider that returned this result.
        rank: The original rank position from the provider.
        timestamp: When the result was retrieved.
        metadata: Additional provider-specific metadata.
        content_type: The type of content.
        is_ad: Whether the result is marked as an advertisement.
        cached_url: URL to a cached version of the page.
        attribution: Attribution information for proper sourcing.
        dark_pattern_flags: Set of detected dark patterns if any.
        result_id: A unique identifier for this result.
    """

    title: str
    url: HttpUrl
    snippet: str
    provider: str
    rank: int
    timestamp: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    content_type: SearchResultType = SearchResultType.WEB
    is_ad: bool = False
    cached_url: Optional[HttpUrl] = None
    attribution: Optional[Dict[str, str]] = None
    dark_pattern_flags: Set[str] = Field(default_factory=set)
    result_id: Optional[str] = None

    class Config:
        """Pydantic model config."""

        schema_extra = {
            "example": {
                "title": "Best restaurants in NYC 2023 - Zagat",
                "url": "https://www.zagat.com/best-restaurants-nyc-2023",
                "snippet": "Explore the top-rated restaurants in New York City for 2023...",
                "provider": "Google",
                "rank": 1,
                "timestamp": "2023-07-01T12:34:56Z",
                "metadata": {"rank_score": 0.95},
                "content_type": "web",
                "is_ad": False,
                "cached_url": "https://webcache.example.com/doc/12345",
                "attribution": {"source": "Zagat", "license": "Standard"},
                "dark_pattern_flags": ["countdown_timer"],
                "result_id": "r123456",
            }
        }


class SearchRequest(BaseModel):
    """
    Search request model.

    Attributes:
        query: The search query text or Query object.
        num_results: Number of results to return.
        providers: Optional list of providers to use.
        parameters: Additional search parameters.
    """

    query: Union[str, Query]
    num_results: int = 10
    providers: Optional[List[str]] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        """Pydantic model config."""

        schema_extra = {
            "example": {
                "query": "best restaurants in new york",
                "num_results": 10,
                "providers": ["Google", "Bing"],
                "parameters": {"include_images": True, "filter_ads": True},
            }
        }


class BiasAnalysis(BaseModel):
    """
    Bias analysis model.

    Attributes:
        provider_bias: Analysis of provider bias.
        commercial_bias: Analysis of commercial bias.
        source_bias: Analysis of source bias.
        dark_patterns: Analysis of dark patterns.
    """

    provider_bias: Dict[str, Any] = Field(default_factory=dict)
    commercial_bias: Dict[str, Any] = Field(default_factory=dict)
    source_bias: Dict[str, Any] = Field(default_factory=dict)
    dark_patterns: Dict[str, Any] = Field(default_factory=dict)


class SearchMetadata(Metadata):
    """
    Search metadata model.

    Attributes:
        query_processing_time: Time taken to process the query in milliseconds.
        engine_selection_time: Time taken to select engines in milliseconds.
        engines_used: List of search engines used.
        result_counts: Count of results from each engine.
        aggregation_strategy: Strategy used for result aggregation.
        deduplication_stats: Statistics about deduplication.
        bias_analysis: Results of bias detection.
    """

    query_processing_time: float = 0.0
    engine_selection_time: float = 0.0
    engines_used: List[str] = Field(default_factory=list)
    result_counts: Dict[str, int] = Field(default_factory=dict)
    aggregation_strategy: str = "default"
    deduplication_stats: Dict[str, Any] = Field(default_factory=dict)
    bias_analysis: Optional[BiasAnalysis] = None


class SearchResponse(BaseModel):
    """
    Search response model.

    Attributes:
        results: List of search results.
        metadata: Metadata about the search.
        query: The processed query.
    """

    results: List[SearchResult]
    metadata: SearchMetadata
    query: Query
