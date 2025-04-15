"""
Vector-related models for LlamaSearch AI.
"""

from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator

from .common import Metadata


class EmbedRequest(BaseModel):
    """
    Embedding request model.

    Attributes:
        text: Text or list of texts to embed.
        model: Optional embedding model to use.
        normalize: Whether to normalize the embeddings.
        parameters: Additional embedding parameters.
    """

    text: Union[str, List[str]]
    model: Optional[str] = None
    normalize: bool = True
    parameters: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        """Pydantic model config."""

        schema_extra = {
            "example": {
                "text": "How does photosynthesis work?",
                "model": "text-embedding-3-large",
                "normalize": True,
                "parameters": {"truncation": True},
            }
        }


class Embedding(BaseModel):
    """
    Embedding model.

    Attributes:
        vector: The embedding vector.
        text: The text that was embedded.
        model: The model used to create the embedding.
        dimensions: Number of dimensions in the embedding.
    """

    vector: List[float]
    text: str
    model: str
    dimensions: int

    @validator("dimensions", pre=True, always=True)
    def set_dimensions(cls, v, values):
        """Set dimensions from vector length if not provided."""
        if v is None and "vector" in values:
            return len(values["vector"])
        return v

    class Config:
        """Pydantic model config."""

        schema_extra = {
            "example": {
                "vector": [0.1, 0.2, 0.3, 0.4, 0.5],
                "text": "How does photosynthesis work?",
                "model": "text-embedding-3-large",
                "dimensions": 5,
            }
        }


class EmbeddingMetadata(Metadata):
    """
    Embedding metadata model.

    Attributes:
        model: The model used to create the embeddings.
        dimensions: Number of dimensions in the embeddings.
        normalized: Whether the embeddings are normalized.
        batch_size: Batch size used for processing.
    """

    model: str
    dimensions: int
    normalized: bool
    batch_size: Optional[int] = None


class EmbedResponse(BaseModel):
    """
    Embedding response model.

    Attributes:
        embeddings: List of embeddings.
        metadata: Metadata about the embeddings.
    """

    embeddings: List[Embedding]
    metadata: EmbeddingMetadata


class VectorSearchRequest(BaseModel):
    """
    Vector search request model.

    Attributes:
        query: Text query or vector to search with.
        collection: Vector collection to search in.
        num_results: Number of results to return.
        filter: Optional filter to apply to the search.
        parameters: Additional search parameters.
    """

    query: Union[str, List[float]]
    collection: str
    num_results: int = 10
    filter: Optional[Dict[str, Any]] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        """Pydantic model config."""

        schema_extra = {
            "example": {
                "query": "How does photosynthesis work?",
                "collection": "science_articles",
                "num_results": 5,
                "filter": {"category": {"$eq": "biology"}},
                "parameters": {"min_score": 0.7, "include_metadata": True},
            }
        }

    @validator("query")
    def validate_query(cls, v):
        """Validate that query is either a string or vector."""
        if isinstance(v, list):
            if not all(isinstance(x, (int, float)) for x in v):
                raise ValueError("Vector elements must be numbers")
        elif not isinstance(v, str):
            raise ValueError("Query must be either a string or a vector")
        return v


class VectorRecord(BaseModel):
    """
    Vector record model.

    Attributes:
        id: Unique identifier for the vector.
        vector: The vector data.
        score: Similarity score for search results.
        metadata: Additional metadata for the vector.
    """

    id: str
    vector: Optional[List[float]] = None
    score: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        """Pydantic model config."""

        schema_extra = {
            "example": {
                "id": "doc123",
                "vector": [0.1, 0.2, 0.3, 0.4, 0.5],
                "score": 0.92,
                "metadata": {
                    "title": "Photosynthesis: The Process Explained",
                    "url": "https://example.com/photosynthesis",
                    "timestamp": "2023-07-01T12:34:56Z",
                },
            }
        }


class VectorSearchMetadata(Metadata):
    """
    Vector search metadata model.

    Attributes:
        collection: The collection that was searched.
        index_type: Type of index used for search.
        vector_dimensions: Number of dimensions in the vectors.
        total_vectors_searched: Total number of vectors searched.
        filtered_vectors: Number of vectors filtered out.
    """

    collection: str
    index_type: str
    vector_dimensions: int
    total_vectors_searched: int
    filtered_vectors: int


class VectorSearchResponse(BaseModel):
    """
    Vector search response model.

    Attributes:
        results: List of vector records.
        metadata: Metadata about the search.
    """

    results: List[VectorRecord]
    metadata: VectorSearchMetadata


class UpsertVectorsRequest(BaseModel):
    """
    Upsert vectors request model.

    Attributes:
        collection: Vector collection to add to.
        vectors: List of vector records to add.
        create_collection: Whether to create the collection if it doesn't exist.
    """

    collection: str
    vectors: List[VectorRecord]
    create_collection: bool = False

    class Config:
        """Pydantic model config."""

        schema_extra = {
            "example": {
                "collection": "science_articles",
                "vectors": [
                    {
                        "id": "doc123",
                        "vector": [0.1, 0.2, 0.3, 0.4, 0.5],
                        "metadata": {
                            "title": "Photosynthesis: The Process Explained",
                            "url": "https://example.com/photosynthesis",
                            "timestamp": "2023-07-01T12:34:56Z",
                        },
                    }
                ],
                "create_collection": True,
            }
        }


class UpsertVectorsResponse(BaseModel):
    """
    Upsert vectors response model.

    Attributes:
        inserted_count: Number of vectors inserted.
        updated_count: Number of vectors updated.
        collection: Name of the collection.
        metadata: Operation metadata.
    """

    inserted_count: int
    updated_count: int
    collection: str
    metadata: Metadata
