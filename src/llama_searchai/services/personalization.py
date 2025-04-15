"""
Personalization service module for LlamaSearch AI.

This module implements the business logic for personalization-related operations,
such as managing user profiles and personalizing content.
"""

import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import uuid4

from llamasearchai.config.settings import settings
from llamasearchai.models.common import Metadata
from llamasearchai.models.personalization import (
    PersonalizationMetadata,
    PersonalizationRequest,
    PersonalizationResponse,
    PersonalizationResult,
    PrivacyLevel,
    UserFeedbackRequest,
    UserFeedbackResponse,
    UserPreference,
    UserProfile,
)
from loguru import logger


class PersonalizationService:
    """
    Service class for handling personalization operations.

    This class implements user profile management and content personalization
    with various privacy levels and personalization algorithms.
    """

    def __init__(self):
        """Initialize the personalization service."""
        self._personalization_enabled = settings.PERSONALIZATION_ENABLED
        self._default_privacy_level = settings.PRIVACY_LEVEL
        self._redis_url = settings.REDIS_URL

        # Mock storage for development
        self._user_profiles = {}
        self._user_preferences = {}
        self._user_feedback = {}

        # In a full implementation, this would initialize a database connection
        # for storing user profiles and preferences

        logger.info(
            f"PersonalizationService initialized with privacy level: {self._default_privacy_level}"
        )

    async def personalize_content(
        self, request: PersonalizationRequest
    ) -> PersonalizationResponse:
        """
        Personalize content for a specific user.

        Args:
            request: The personalization request.

        Returns:
            The personalized content with metadata.

        Raises:
            ValueError: If personalization is not enabled.
        """
        if not self._personalization_enabled:
            raise ValueError("Personalization is not enabled")

        # Record start time
        start_time = time.time()

        # Get user profile
        user_id = request.user_id
        profile = await self.get_user_profile(user_id)

        # Make a copy of the content to personalize
        personalized_content = list(request.content)

        # Personalization results
        personalization_results = []

        # Apply personalization to each item
        for i, item in enumerate(personalized_content):
            # Get original score or default to 0.5
            original_score = item.get("score", 0.5)

            # In a real implementation, this would apply sophisticated personalization
            # algorithms based on the user profile and content

            # For development, apply a simple personalization based on interests
            personalized_score = original_score
            explanation = {}

            if "topics_of_interest" in profile:
                # Check for topic matches in title or metadata
                title = item.get("title", "").lower()
                topic_score = 0.0
                matched_topics = []

                for topic in profile["topics_of_interest"]:
                    if topic.lower() in title:
                        topic_score += 0.1
                        matched_topics.append(topic)

                # Apply topic boost (max 0.3)
                topic_boost = min(topic_score, 0.3)
                personalized_score += topic_boost

                if matched_topics:
                    explanation["topic_relevance"] = topic_boost
                    explanation["matched_topics"] = matched_topics

            # Apply recency bias - prefer newer content
            if "timestamp" in item:
                try:
                    item_date = datetime.fromisoformat(item["timestamp"])
                    days_old = (datetime.now() - item_date).days
                    recency_boost = max(0.0, 0.2 - (days_old * 0.01))
                    personalized_score += recency_boost
                    explanation["recency_boost"] = recency_boost
                except (ValueError, TypeError):
                    pass

            # Check past history if available
            if "search_history" in profile:
                # Look for similar searches
                history_match = 0.0
                for history_item in profile["search_history"]:
                    query = history_item.get("query", "").lower()
                    if query and query in title:
                        history_match += 0.05

                personalized_score += min(history_match, 0.15)
                if history_match > 0:
                    explanation["history_match"] = min(history_match, 0.15)

            # Ensure score is between 0 and 1
            personalized_score = max(0.0, min(1.0, personalized_score))

            # Calculate rank change (this is simplified)
            rank_change = 0
            if i > 0 and personalized_score > personalized_content[i - 1].get(
                "score", 0
            ):
                rank_change = -1
            elif i < len(
                personalized_content
            ) - 1 and personalized_score < personalized_content[i + 1].get("score", 0):
                rank_change = 1

            # Create result
            result = PersonalizationResult(
                id=item.get("id", f"item-{i}"),
                original_score=original_score,
                personalized_score=personalized_score,
                rank_change=rank_change,
                explanation=explanation,
            )
            personalization_results.append(result)

            # Update the score in the content
            personalized_content[i]["score"] = personalized_score

        # Sort content by personalized score
        personalized_content.sort(key=lambda x: x.get("score", 0), reverse=True)

        # Calculate processing time
        processing_time = time.time() - start_time

        # Get profile age for metadata
        profile_age_days = 0.0
        if profile.get("created_at"):
            try:
                created_at = datetime.fromisoformat(profile["created_at"])
                profile_age_days = (datetime.now() - created_at).days
            except (ValueError, TypeError):
                profile_age_days = 30.0  # Default

        # Calculate profile completeness
        profile_completeness = self._calculate_profile_completeness(profile)

        # Create metadata
        privacy_level = PrivacyLevel(
            profile.get("privacy_level", self._default_privacy_level)
        )
        metadata = PersonalizationMetadata(
            processing_time=processing_time,
            request_id=str(uuid4()),
            timestamp=datetime.utcnow().isoformat(),
            version="0.1.0",
            source="llamasearch-api",
            user_profile_age_days=profile_age_days,
            features_used=list(
                set(
                    key
                    for result in personalization_results
                    for key in result.explanation or {}
                )
            ),
            model_version="personalization-v1",
            profile_completeness=profile_completeness,
            privacy_level=privacy_level,
        )

        # Return the response
        return PersonalizationResponse(
            results=personalization_results,
            content=personalized_content,
            metadata=metadata,
        )

    async def get_user_profile(self, user_id: str) -> UserProfile:
        """
        Get a user's profile.

        Args:
            user_id: The user ID to get the profile for.

        Returns:
            The user profile.
        """
        if not self._personalization_enabled:
            raise ValueError("Personalization is not enabled")

        # Check if profile exists in mock storage
        if user_id in self._user_profiles:
            return self._user_profiles[user_id]

        # In production, fetch from database
        # For development, create a mock profile
        created_date = datetime.utcnow() - timedelta(days=30)
        profile = UserProfile(
            user_id=user_id,
            preferences={
                "theme": "dark",
                "results_per_page": 20,
                "safe_search": True,
            },
            topics_of_interest=["AI", "machine learning", "Python", "data science"],
            search_history=[
                {
                    "query": "fastapi tutorial",
                    "timestamp": (datetime.utcnow() - timedelta(days=1)).isoformat(),
                },
                {
                    "query": "vector database python",
                    "timestamp": (datetime.utcnow() - timedelta(days=3)).isoformat(),
                },
                {
                    "query": "machine learning datasets",
                    "timestamp": (datetime.utcnow() - timedelta(days=5)).isoformat(),
                },
            ],
            embedding=[0.1, 0.2, 0.3, 0.4, 0.5],  # Example embedding
            privacy_level=PrivacyLevel(self._default_privacy_level),
            created_at=created_date,
            updated_at=datetime.utcnow() - timedelta(days=1),
        )

        # Store in mock storage
        self._user_profiles[user_id] = profile

        return profile

    async def update_user_profile(
        self, user_id: str, profile: UserProfile
    ) -> UserProfile:
        """
        Update a user's profile.

        Args:
            user_id: The user ID to update the profile for.
            profile: The new profile data.

        Returns:
            The updated user profile.

        Raises:
            ValueError: If the user IDs don't match.
        """
        if not self._personalization_enabled:
            raise ValueError("Personalization is not enabled")

        # Ensure the user ID matches
        if user_id != profile.user_id:
            raise ValueError("User ID in path does not match user ID in profile")

        # Update the updated_at timestamp
        profile.updated_at = datetime.utcnow()

        # In production, save to database
        # For development, save to mock storage
        self._user_profiles[user_id] = profile

        return profile

    async def submit_user_feedback(
        self, request: UserFeedbackRequest
    ) -> UserFeedbackResponse:
        """
        Submit user feedback for a search result or other item.

        Args:
            request: The feedback request.

        Returns:
            The feedback response.
        """
        if not self._personalization_enabled:
            raise ValueError("Personalization is not enabled")

        # Record start time
        start_time = time.time()

        # In production, save to database
        # For development, save to mock storage
        user_id = request.user_id
        if user_id not in self._user_feedback:
            self._user_feedback[user_id] = []

        # Add timestamp if not present
        feedback_data = request.dict()
        if "timestamp" not in feedback_data:
            feedback_data["timestamp"] = datetime.utcnow().isoformat()

        # Generate a feedback ID
        feedback_id = str(uuid4())
        feedback_data["feedback_id"] = feedback_id

        # Store the feedback
        self._user_feedback[user_id].append(feedback_data)

        # Calculate processing time
        processing_time = time.time() - start_time

        # Create metadata
        metadata = Metadata(
            processing_time=processing_time,
            request_id=str(uuid4()),
            timestamp=datetime.utcnow().isoformat(),
            version="0.1.0",
            source="llamasearch-api",
        )

        # Return the response
        return UserFeedbackResponse(
            status="success",
            feedback_id=feedback_id,
            message="Feedback recorded successfully",
            metadata=metadata,
        )

    async def get_user_preferences(
        self, user_id: str, category: Optional[str] = None
    ) -> List[UserPreference]:
        """
        Get a user's preferences.

        Args:
            user_id: The user ID to get preferences for.
            category: Optional category to filter preferences by.

        Returns:
            The user's preferences.
        """
        if not self._personalization_enabled:
            raise ValueError("Personalization is not enabled")

        # Check if preferences exist in mock storage
        if user_id in self._user_preferences:
            preferences = self._user_preferences[user_id]
        else:
            # In production, fetch from database
            # For development, create mock preferences
            preferences = [
                UserPreference(
                    key="theme",
                    value="dark",
                    category="ui",
                    timestamp=datetime.utcnow() - timedelta(days=10),
                ),
                UserPreference(
                    key="results_per_page",
                    value=20,
                    category="search",
                    timestamp=datetime.utcnow() - timedelta(days=5),
                ),
                UserPreference(
                    key="safe_search",
                    value=True,
                    category="search",
                    timestamp=datetime.utcnow() - timedelta(days=15),
                ),
                UserPreference(
                    key="notifications_enabled",
                    value=False,
                    category="notifications",
                    timestamp=datetime.utcnow() - timedelta(days=2),
                ),
            ]

            # Store in mock storage
            self._user_preferences[user_id] = preferences

        # Filter by category if provided
        if category:
            return [p for p in preferences if p.category == category]

        return preferences

    def _calculate_profile_completeness(self, profile: Dict[str, Any]) -> float:
        """
        Calculate the completeness of a user profile.

        Args:
            profile: The user profile.

        Returns:
            Completeness score between 0 and 1.
        """
        # Define the fields that contribute to completeness
        fields = [
            "preferences",
            "topics_of_interest",
            "search_history",
            "embedding",
        ]

        # Count how many fields are populated
        populated = sum(1 for field in fields if field in profile and profile[field])

        # Calculate completeness
        completeness = populated / len(fields)

        # Adjust based on the size/quality of each field
        if "preferences" in profile and profile["preferences"]:
            completeness += min(0.1, len(profile["preferences"]) * 0.02)

        if "topics_of_interest" in profile and profile["topics_of_interest"]:
            completeness += min(0.1, len(profile["topics_of_interest"]) * 0.02)

        if "search_history" in profile and profile["search_history"]:
            completeness += min(0.1, len(profile["search_history"]) * 0.01)

        # Ensure completeness is between 0 and 1
        return max(0.0, min(1.0, completeness))
