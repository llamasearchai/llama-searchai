"""
Notification route handlers for LlamaSearch AI API.
"""

from typing import List

from fastapi import APIRouter, Body, HTTPException, Query, Security, status
from llamasearchai.api.app import get_api_key
from llamasearchai.config.settings import settings
from llamasearchai.models.notification import Notification, NotificationResult
from llamasearchai.services.notification import NotificationService
from loguru import logger

# Create router
router = APIRouter(
    prefix="/api/v1/notifications",
    tags=["notifications"],
    dependencies=[Security(get_api_key)],
)

# Create service instance
notification_service = NotificationService()


@router.post(
    "/send", response_model=NotificationResult, status_code=status.HTTP_202_ACCEPTED
)
async def send_notification(
    notification: Notification = Body(...),
) -> NotificationResult:
    """
    Send a notification through the specified channel.

    Args:
        notification: The notification details.

    Returns:
        NotificationResult: The result of the sending attempt.
    """
    logger.info(
        f"Send notification request received: channel={notification.channel}, recipient={notification.recipient}"
    )

    if not settings.NOTIFICATIONS_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Notifications feature is not enabled. Please check API settings.",
        )

    try:
        result = await notification_service.send_notification(notification)
        if result.status == NotificationStatus.FAILED:
            # Optionally return a different status code for immediate failures vs. accepted
            logger.warning(
                f"Notification sending failed immediately for ID {result.notification_id}: {result.error_message}"
            )
            # We still return 202 Accepted as the request was processed, but the body contains the failure
        return result
    except Exception as e:
        logger.error(f"Error sending notification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error sending notification: {str(e)}",
        )


@router.get("/history", response_model=List[NotificationResult])
async def get_notification_history(
    limit: int = Query(
        100,
        ge=1,
        le=1000,
        description="Maximum number of notification results to return",
    ),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
) -> List[NotificationResult]:
    """
    Retrieve the history of recently sent notifications (mock implementation).

    Args:
        limit: Maximum number of results.
        offset: Pagination offset.

    Returns:
        List[NotificationResult]: A list of notification results.
    """
    logger.info(
        f"Get notification history request received: limit={limit}, offset={offset}"
    )

    if not settings.NOTIFICATIONS_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Notifications feature is not enabled.",
        )

    try:
        history = await notification_service.list_sent_notifications(
            limit=limit, offset=offset
        )
        return history
    except Exception as e:
        logger.error(f"Error retrieving notification history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving notification history: {str(e)}",
        )
