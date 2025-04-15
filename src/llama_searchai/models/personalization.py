"""
Personalization-related models for LlamaSearch AI.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator

from .common import Metadata


class PrivacyLevel(str, Enum):
    """Privacy level enum for personalization."""

    HIGH = "high"  # Minimal data collection, local processing
    MEDIUM = "medium"  # Standard personalization, pseudonymized data
    LOW = "low"  # Enhanced personalization, more data collection
    NONE = "none"  # No privacy restrictions, full data collection


class UserPreference(BaseModel):
    """
    User preference model.

    Attributes:
        key: The preference key.
        value: The preference value.
        category: Optional category for the preference.
        timestamp: When the preference was created/updated.
    """

    key: str
    value: Any
    category: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class UserProfile(BaseModel):
    """
    User profile model.

    Attributes:
        user_id: Unique identifier for the user.
        preferences: User preferences.
        topics_of_interest: Topics the user is interested in.
        search_history: Recent search history.
        embedding: User embedding vector for similarity matching.
        privacy_level: User's privacy level setting.
        created_at: When the profile was created.
        updated_at: When the profile was last updated.
    """

    user_id: str
    preferences: Dict[str, Any] = Field(default_factory=dict)
    topics_of_interest: List[str] = Field(default_factory=list)
    search_history: List[Dict[str, Any]] = Field(default_factory=list, max_items=100)
    embedding: Optional[List[float]] = None
    privacy_level: PrivacyLevel = PrivacyLevel.MEDIUM
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    @validator("updated_at", pre=True, always=True)
    def set_updated_at(cls, v):
        """Always set updated_at to current time on updates."""
        return datetime.utcnow()

    class Config:
        """Pydantic model config."""

        schema_extra = {
            "example": {
                "user_id": "user123",
                "preferences": {
                    "theme": "dark",
                    "results_per_page": 20,
                    "safe_search": True,
                },
                "topics_of_interest": ["AI", "machine learning", "Python"],
                "search_history": [
                    {
                        "query": "fastapi tutorial",
                        "timestamp": "2023-06-15T10:30:00Z",
                    }
                ],
                "embedding": [0.1, 0.2, 0.3, 0.4, 0.5],
                "privacy_level": "medium",
                "created_at": "2023-01-15T00:00:00Z",
                "updated_at": "2023-06-20T14:25:00Z",
            }
        }


class SearchHistoryItem(BaseModel):
    """
    Search history item model.

    Attributes:
        query: The search query text.
        timestamp: When the search was performed.
        results_clicked: URLs of search results that were clicked.
        dwell_times: Dwell times for clicked results in seconds.
        device_info: Information about the device used.
        location: Optional location information.
    """

    query: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    results_clicked: List[str] = Field(default_factory=list)
    dwell_times: Dict[str, float] = Field(default_factory=dict)
    device_info: Dict[str, str] = Field(default_factory=dict)
    location: Optional[Dict[str, Any]] = None


class PersonalizationRequest(BaseModel):
    """
    Personalization request model.

    Attributes:
        user_id: The user ID to personalize for.
        content: The content to personalize (search results, recommendations, etc).
        context: Optional context information.
        parameters: Additional personalization parameters.
    """

    user_id: str
    content: List[Dict[str, Any]]
    context: Optional[Dict[str, Any]] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        """Pydantic model config."""

        schema_extra = {
            "example": {
                "user_id": "user123",
                "content": [
                    {
                        "id": "result1",
                        "title": "Introduction to FastAPI",
                        "url": "https://example.com/fastapi",
                        "score": 0.95,
                    },
                    {
                        "id": "result2",
                        "title": "Python Web Frameworks Comparison",
                        "url": "https://example.com/frameworks",
                        "score": 0.85,
                    },
                ],
                "context": {"query": "python web frameworks", "session_id": "sess123"},
                "parameters": {"rerank_strength": 0.7, "diversity_weight": 0.3},
            }
        }


class PersonalizationResult(BaseModel):
    """
    Personalization result item model.

    Attributes:
        id: Identifier for the content item.
        original_score: The original score before personalization.
        personalized_score: The score after personalization.
        explanation: Optional explanation of personalization factors.
    """

    id: str
    original_score: float
    personalized_score: float
    rank_change: int = 0
    explanation: Optional[Dict[str, float]] = None


class PersonalizationMetadata(Metadata):
    """
    Personalization metadata model.

    Attributes:
        user_profile_age_days: Age of the user profile in days.
        features_used: List of features used for personalization.
        model_version: Version of the personalization model.
        profile_completeness: How complete the user profile is (0-1).
        privacy_level: Privacy level applied during personalization.
    """

    user_profile_age_days: float
    features_used: List[str]
    model_version: str
    profile_completeness: float
    privacy_level: PrivacyLevel


class PersonalizationResponse(BaseModel):
    """
    Personalization response model.

    Attributes:
        results: List of personalized items.
        content: The reranked and personalized content.
        metadata: Metadata about the personalization.
    """

    results: List[PersonalizationResult]
    content: List[Dict[str, Any]]
    metadata: PersonalizationMetadata


class UserFeedbackRequest(BaseModel):
    """
    User feedback request model.

    Attributes:
        user_id: The user ID providing feedback.
        item_id: The ID of the item being rated/feedback.
        rating: Numeric rating (typically 1-5).
        feedback_text: Optional text feedback.
        source: Source of the feedback.
        context: Additional context information.
    """

    user_id: str
    item_id: str
    rating: Optional[float] = None
    feedback_text: Optional[str] = None
    source: str = "search"
    context: Dict[str, Any] = Field(default_factory=dict)

    @validator("rating")
    def validate_rating(cls, v):
        """Validate that rating is in a valid range."""
        if v is not None and (v < 1 or v > 5):
            raise ValueError("Rating must be between 1 and 5")
        return v

    class Config:
        """Pydantic model config."""

        schema_extra = {
            "example": {
                "user_id": "user123",
                "item_id": "result1",
                "rating": 4.5,
                "feedback_text": "Very helpful result, exactly what I was looking for",
                "source": "search",
                "context": {"query": "python web frameworks", "session_id": "sess123"},
            }
        }


class UserFeedbackResponse(BaseModel):
    """
    User feedback response model.

    Attributes:
        status: Status of the feedback submission.
        feedback_id: Unique ID for the submitted feedback.
        message: Optional message about the feedback submission.
        metadata: Metadata about the feedback submission.
    """

    status: str
    feedback_id: str
    message: Optional[str] = None
    metadata: Metadata
