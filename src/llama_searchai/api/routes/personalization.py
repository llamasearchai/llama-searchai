"""
Personalization route handlers for LlamaSearch AI API.
"""

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Path, Query, Security, status
from llamasearchai.api.app import get_api_key
from llamasearchai.config.settings import settings
from llamasearchai.models.personalization import (
    PersonalizationRequest,
    PersonalizationResponse,
    UserFeedbackRequest,
    UserFeedbackResponse,
    UserPreference,
    UserProfile,
)
from llamasearchai.services.personalization import PersonalizationService
from loguru import logger

# Create router
router = APIRouter(
    prefix="/api/v1/personalization",
    tags=["personalization"],
    dependencies=[Security(get_api_key)],
)

# Create service instance
personalization_service = PersonalizationService()


@router.post("/rerank", response_model=PersonalizationResponse)
async def personalize_content(
    request: PersonalizationRequest,
) -> PersonalizationResponse:
    """
    Personalize content for a specific user.

    Args:
        request: The personalization request with user ID and content to personalize.

    Returns:
        PersonalizationResponse: The personalized content and metadata.
    """
    logger.info(f"Personalization request received for user: {request.user_id}")

    if not settings.PERSONALIZATION_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Personalization is not enabled. Please check API settings.",
        )

    try:
        return await personalization_service.personalize_content(request)
    except Exception as e:
        logger.error(f"Error personalizing content: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error personalizing content: {str(e)}",
        )


@router.get("/profile/{user_id}", response_model=UserProfile)
async def get_user_profile(
    user_id: str = Path(..., description="User ID to retrieve profile for"),
) -> UserProfile:
    """
    Get a user's profile.

    Args:
        user_id: The ID of the user to get the profile for.

    Returns:
        UserProfile: The user's profile.
    """
    logger.info(f"User profile request received for user: {user_id}")

    if not settings.PERSONALIZATION_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Personalization is not enabled. Please check API settings.",
        )

    try:
        return await personalization_service.get_user_profile(user_id)
    except Exception as e:
        logger.error(f"Error retrieving user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving user profile: {str(e)}",
        )


@router.put("/profile/{user_id}", response_model=UserProfile)
async def update_user_profile(
    user_profile: UserProfile,
    user_id: str = Path(..., description="User ID to update profile for"),
) -> UserProfile:
    """
    Update a user's profile.

    Args:
        user_id: The ID of the user to update the profile for.
        user_profile: The new profile data.

    Returns:
        UserProfile: The updated user profile.
    """
    logger.info(f"User profile update received for user: {user_id}")

    if not settings.PERSONALIZATION_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Personalization is not enabled. Please check API settings.",
        )

    # Ensure the path parameter matches the body
    if user_id != user_profile.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User ID in path does not match user ID in profile",
        )

    try:
        return await personalization_service.update_user_profile(user_id, user_profile)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error updating user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating user profile: {str(e)}",
        )


@router.post("/feedback", response_model=UserFeedbackResponse)
async def submit_user_feedback(request: UserFeedbackRequest) -> UserFeedbackResponse:
    """
    Submit user feedback for a search result or other item.

    Args:
        request: The feedback request with user ID, item ID, and feedback.

    Returns:
        UserFeedbackResponse: Confirmation of the feedback submission.
    """
    logger.info(
        f"User feedback received from user: {request.user_id} for item: {request.item_id}"
    )

    if not settings.PERSONALIZATION_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Personalization is not enabled. Please check API settings.",
        )

    try:
        return await personalization_service.submit_user_feedback(request)
    except Exception as e:
        logger.error(f"Error submitting user feedback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error submitting user feedback: {str(e)}",
        )


@router.get("/preferences/{user_id}", response_model=List[UserPreference])
async def get_user_preferences(
    user_id: str = Path(..., description="User ID to retrieve preferences for"),
    category: Optional[str] = Query(None, description="Filter preferences by category"),
) -> List[UserPreference]:
    """
    Get a user's preferences.

    Args:
        user_id: The ID of the user to get preferences for.
        category: Optional category to filter preferences by.

    Returns:
        List[UserPreference]: The user's preferences.
    """
    logger.info(f"User preferences request received for user: {user_id}")

    if not settings.PERSONALIZATION_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Personalization is not enabled. Please check API settings.",
        )

    try:
        return await personalization_service.get_user_preferences(user_id, category)
    except Exception as e:
        logger.error(f"Error retrieving user preferences: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving user preferences: {str(e)}",
        )
