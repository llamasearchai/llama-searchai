"""
Notification service module for LlamaSearch AI.

This module implements the business logic for sending notifications via various channels.
"""

import random
import time
from datetime import datetime
from typing import List
from uuid import uuid4

from llamasearchai.config.settings import settings
from llamasearchai.models.common import Metadata
from llamasearchai.models.notification import (
    Notification,
    NotificationChannel,
    NotificationResult,
    NotificationStatus,
)
from loguru import logger


class NotificationService:
    """
    Service class for handling notification sending operations.

    Supports sending notifications through different channels (e.g., email, webhook).
    """

    def __init__(self):
        """Initialize the notification service."""
        # In a real implementation, this might initialize connections to email servers (SMTP),
        # webhook endpoints, or other messaging platforms.
        logger.info("NotificationService initialized.")
        self._sent_notifications: List[NotificationResult] = (
            []
        )  # Keep track of sent notifications (mock)

    async def send_notification(self, notification: Notification) -> NotificationResult:
        """
        Send a notification through the specified channel.

        Args:
            notification: The notification object containing details.

        Returns:
            NotificationResult: The result of the notification sending attempt.
        """
        start_time = time.time()
        notification_id = str(uuid4())
        now = datetime.utcnow()
        status = NotificationStatus.PENDING
        error_message = None

        logger.info(
            f"Attempting to send notification {notification_id} via {notification.channel} to {notification.recipient}"
        )

        # Check if the specific channel is enabled in settings (example)
        # if notification.channel == NotificationChannel.EMAIL and not settings.EMAIL_ENABLED:
        #     status = NotificationStatus.FAILED
        #     error_message = "Email channel is not configured or enabled."
        # elif notification.channel == NotificationChannel.WEBHOOK and not settings.WEBHOOK_ENABLED:
        #     status = NotificationStatus.FAILED
        #     error_message = "Webhook channel is not configured or enabled."
        # else:
        # TODO: Implement actual sending logic based on the channel
        try:
            if notification.channel == NotificationChannel.EMAIL:
                # Simulate sending email
                logger.debug(
                    f"Simulating email send to {notification.recipient} with subject: {notification.subject}"
                )
                await asyncio.sleep(
                    random.uniform(0.1, 0.5)
                )  # Simulate network latency
                # Placeholder: Assume success if recipient looks like an email
                if "@" in notification.recipient:
                    status = NotificationStatus.SENT
                    logger.info(
                        f"Successfully simulated sending email notification {notification_id}"
                    )
                else:
                    status = NotificationStatus.FAILED
                    error_message = "Invalid recipient format for email."
                    logger.warning(
                        f"Failed sending email notification {notification_id}: {error_message}"
                    )

            elif notification.channel == NotificationChannel.WEBHOOK:
                # Simulate sending webhook
                logger.debug(f"Simulating webhook POST to {notification.recipient}")
                await asyncio.sleep(
                    random.uniform(0.2, 0.8)
                )  # Simulate network latency
                # Placeholder: Assume success if recipient looks like a URL
                if notification.recipient.startswith(
                    "http://"
                ) or notification.recipient.startswith("https://"):
                    status = NotificationStatus.SENT
                    logger.info(
                        f"Successfully simulated sending webhook notification {notification_id}"
                    )
                else:
                    status = NotificationStatus.FAILED
                    error_message = (
                        "Invalid recipient format for webhook (must be URL)."
                    )
                    logger.warning(
                        f"Failed sending webhook notification {notification_id}: {error_message}"
                    )

            elif notification.channel == NotificationChannel.SLACK:
                # Simulate sending to Slack
                logger.debug(
                    f"Simulating sending Slack message to {notification.recipient}"
                )
                await asyncio.sleep(random.uniform(0.3, 1.0))
                # Placeholder: Assume success for demo
                status = NotificationStatus.SENT
                logger.info(
                    f"Successfully simulated sending Slack notification {notification_id}"
                )

            else:
                status = NotificationStatus.FAILED
                error_message = (
                    f"Unsupported notification channel: {notification.channel}"
                )
                logger.error(error_message)

        except Exception as e:
            logger.error(
                f"Unexpected error sending notification {notification_id}: {e}"
            )
            status = NotificationStatus.FAILED
            error_message = f"Internal server error: {str(e)}"

        processing_time = time.time() - start_time

        result = NotificationResult(
            notification_id=notification_id,
            status=status,
            timestamp=now,
            channel=notification.channel,
            recipient=notification.recipient,
            error_message=error_message,
            metadata=Metadata(
                processing_time=processing_time,
                request_id=notification.metadata.get(
                    "request_id",
                    str(uuid4()) if notification.metadata else str(uuid4()),
                ),  # Reuse request ID if provided
                timestamp=now.isoformat(),
                version=settings.VERSION,
                source="llamasearch-notification-service",
            ),
        )

        self._sent_notifications.append(result)  # Add to mock history
        return result

    async def list_sent_notifications(
        self, limit: int = 100, offset: int = 0
    ) -> List[NotificationResult]:
        """
        List recently sent notifications (mock implementation).

        Args:
            limit: Maximum number of notifications to return.
            offset: Number of notifications to skip for pagination.

        Returns:
            List[NotificationResult]: A list of notification results.
        """
        # Return notifications from our mock history, most recent first
        sorted_notifications = sorted(
            self._sent_notifications, key=lambda x: x.timestamp, reverse=True
        )
        return sorted_notifications[offset : offset + limit]
