"""
Vector route handlers for LlamaSearch AI API.
"""

from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Security, status
from llamasearchai.api.app import get_api_key
from llamasearchai.config.settings import settings
from llamasearchai.models.vector import (
    EmbedRequest,
    EmbedResponse,
    UpsertVectorsRequest,
    UpsertVectorsResponse,
    VectorSearchRequest,
    VectorSearchResponse,
)
from llamasearchai.services.vector import VectorService
from loguru import logger

# Create router
router = APIRouter(
    prefix="/api/v1/vector",
    tags=["vector"],
    dependencies=[Security(get_api_key)],
)

# Create service instance
vector_service = VectorService()


@router.post("/embed", response_model=EmbedResponse)
async def create_embeddings(request: EmbedRequest) -> EmbedResponse:
    """
    Create embeddings for the given text(s).

    Args:
        request: The embedding request containing the text to embed.

    Returns:
        EmbedResponse: The embeddings and metadata.
    """
    logger.info(f"Embed request received for model: {request.model or 'default'}")

    try:
        return await vector_service.create_embeddings(request)
    except Exception as e:
        logger.error(f"Error creating embeddings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating embeddings: {str(e)}",
        )


@router.post("/search", response_model=VectorSearchResponse)
async def vector_search(request: VectorSearchRequest) -> VectorSearchResponse:
    """
    Perform a vector similarity search.

    Args:
        request: The vector search request.

    Returns:
        VectorSearchResponse: The search results and metadata.
    """
    logger.info(f"Vector search request received for collection: {request.collection}")

    if not settings.VECTOR_DB_TYPE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Vector database is not configured. Please check API settings.",
        )

    try:
        return await vector_service.vector_search(request)
    except Exception as e:
        logger.error(f"Error performing vector search: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error performing vector search: {str(e)}",
        )


@router.post("/upsert", response_model=UpsertVectorsResponse)
async def upsert_vectors(request: UpsertVectorsRequest) -> UpsertVectorsResponse:
    """
    Upsert vectors into a collection.

    Args:
        request: The upsert request containing vectors to add or update.

    Returns:
        UpsertVectorsResponse: The result of the upsert operation.
    """
    logger.info(
        f"Upsert request received for collection: {request.collection} with {len(request.vectors)} vectors"
    )

    if not settings.VECTOR_DB_TYPE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Vector database is not configured. Please check API settings.",
        )

    try:
        return await vector_service.upsert_vectors(request)
    except Exception as e:
        logger.error(f"Error upserting vectors: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error upserting vectors: {str(e)}",
        )


@router.get("/collections", response_model=Dict[str, Any])
async def list_collections() -> Dict[str, Any]:
    """
    List all available vector collections.

    Returns:
        Dict with collections information.
    """
    logger.info("List collections request received")

    if not settings.VECTOR_DB_TYPE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Vector database is not configured. Please check API settings.",
        )

    try:
        return await vector_service.list_collections()
    except Exception as e:
        logger.error(f"Error listing collections: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing collections: {str(e)}",
        )
