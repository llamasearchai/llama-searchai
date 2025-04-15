"""
Search route handlers for LlamaSearch AI API.
"""

from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query, Security, status
from llamasearchai.api.app import get_api_key
from llamasearchai.config.settings import settings
from llamasearchai.models.search import Query as SearchQuery
from llamasearchai.models.search import (
    SearchRequest,
    SearchResponse,
)
from llamasearchai.services.search import SearchService
from loguru import logger

# Create router
router = APIRouter(
    prefix="/api/v1/search",
    tags=["search"],
    dependencies=[Security(get_api_key)],
)

# Create service instance
search_service = SearchService()


@router.post("/", response_model=SearchResponse)
async def search(request: SearchRequest) -> SearchResponse:
    """
    Perform a metasearch query across configured search engines.

    Args:
        request: The search request containing the query and parameters.

    Returns:
        SearchResponse: The search results and metadata.
    """
    logger.info(
        f"Search request received: {request.query.text if isinstance(request.query, SearchQuery) else request.query}"
    )

    if not settings.GOOGLE_API_KEY and not settings.BING_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="No search providers are configured. Please check API settings.",
        )

    try:
        return await search_service.search(request)
    except Exception as e:
        logger.error(f"Error performing search: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error performing search: {str(e)}",
        )


@router.get("/analyze", response_model=SearchQuery)
async def analyze_query(
    query: str = Query(..., description="The search query to analyze"),
) -> SearchQuery:
    """
    Analyze a search query to determine intent, locality, and other characteristics.

    Args:
        query: The search query text to analyze.

    Returns:
        SearchQuery: The analyzed query with metadata.
    """
    logger.info(f"Query analysis request received: {query}")

    try:
        return await search_service.analyze_query(query)
    except Exception as e:
        logger.error(f"Error analyzing query: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing query: {str(e)}",
        )


@router.get("/trends", response_model=Dict[str, List[str]])
async def get_search_trends(
    category: Optional[str] = Query(None, description="Category to filter trends"),
    limit: int = Query(
        10, ge=1, le=50, description="Number of trending items to return"
    ),
) -> Dict[str, List[str]]:
    """
    Get current trending search queries.

    Args:
        category: Optional category to filter trending topics.
        limit: Maximum number of trending items to return per category.

    Returns:
        Dict of category names to lists of trending searches.
    """
    logger.info(f"Trend request received: category={category}, limit={limit}")

    try:
        return await search_service.get_trends(category, limit)
    except Exception as e:
        logger.error(f"Error getting trends: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting trends: {str(e)}",
        )
