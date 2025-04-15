"""
Common models used across the LlamaSearch AI API.
"""

from typing import Any, Dict, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

# Define a generic type variable for paginated responses
T = TypeVar("T")


class ErrorResponse(BaseModel):
    """
    Error response model.

    Attributes:
        error: Error message.
        detail: Detailed error information.
        code: Error code.
    """

    error: str
    detail: Optional[str] = None
    code: str = "unknown_error"


class HealthResponse(BaseModel):
    """
    Health check response model.

    Attributes:
        status: Health status.
        version: API version.
        uptime: API uptime in seconds.
        services: Status of dependent services.
    """

    status: str
    version: str
    uptime: Optional[float] = None
    services: Optional[Dict[str, Dict[str, Any]]] = None


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Paginated response model.

    Attributes:
        items: List of items.
        total: Total number of items.
        page: Current page number.
        page_size: Number of items per page.
        pages: Total number of pages.
        has_more: Whether there are more pages.
    """

    items: List[T]
    total: int
    page: int = 1
    page_size: int
    pages: int
    has_more: bool

    class Config:
        """Pydantic model config."""

        schema_extra = {
            "example": {
                "items": [{"id": 1, "name": "Item 1"}, {"id": 2, "name": "Item 2"}],
                "total": 42,
                "page": 1,
                "page_size": 10,
                "pages": 5,
                "has_more": True,
            }
        }


class Metadata(BaseModel):
    """
    Metadata model.

    Attributes:
        processing_time: Processing time in milliseconds.
        timestamp: Timestamp when the request was processed.
        request_id: Unique request ID.
        source: Source of the data.
        version: API version.
    """

    processing_time: float = Field(..., description="Processing time in milliseconds")
    timestamp: str = Field(
        ..., description="ISO timestamp when the request was processed"
    )
    request_id: str = Field(..., description="Unique request ID")
    source: Optional[str] = Field(None, description="Source of the data")
    version: Optional[str] = Field(None, description="API version")

    class Config:
        """Pydantic model config."""

        schema_extra = {
            "example": {
                "processing_time": 152.34,
                "timestamp": "2023-07-01T12:34:56Z",
                "request_id": "abcd1234-ef56-7890-ab12-cd34ef567890",
                "source": "LlamaSearch AI",
                "version": "0.1.0",
            }
        }
