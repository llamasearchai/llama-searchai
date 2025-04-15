"""
Monitoring route handlers for LlamaSearch AI API.
"""

from datetime import datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Path, Query, Security, status
from llamasearchai.api.app import get_api_key
from llamasearchai.config.settings import settings
from llamasearchai.models.monitoring import (
    LogEntry,
    LogQuery,
    ServiceStatus,
    SystemMetrics,
)
from llamasearchai.services.monitoring import MonitoringService
from loguru import logger

# Create router
router = APIRouter(
    prefix="/api/v1/monitoring",
    tags=["monitoring"],
    dependencies=[Security(get_api_key)],
)

# Create service instance
monitoring_service = MonitoringService()


@router.get("/metrics", response_model=SystemMetrics)
async def get_metrics() -> SystemMetrics:
    """
    Retrieve current system metrics.

    Returns:
        SystemMetrics: A snapshot of the system's performance metrics.
    """
    logger.info("System metrics request received")

    if not settings.MONITORING_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Monitoring is not enabled. Please check API settings.",
        )

    try:
        return await monitoring_service.get_system_metrics()
    except Exception as e:
        logger.error(f"Error retrieving system metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving system metrics: {str(e)}",
        )


@router.get("/status/{service_name}", response_model=Dict[str, ServiceStatus])
@router.get("/status", response_model=Dict[str, ServiceStatus])
async def get_service_status(
    service_name: Optional[str] = Path(
        None, description="Optional specific service name to query"
    )
) -> Dict[str, ServiceStatus]:
    """
    Retrieve the status of various services or a specific service.

    Args:
        service_name: Optional name of a specific service to query.

    Returns:
        Dict[str, ServiceStatus]: A dictionary mapping service names to their status.
    """
    logger.info(f"Service status request received for: {service_name or 'all'}")

    if not settings.MONITORING_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Monitoring is not enabled. Please check API settings.",
        )

    try:
        return await monitoring_service.get_service_status(service_name)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error retrieving service status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving service status: {str(e)}",
        )


@router.get("/logs", response_model=List[LogEntry])
async def get_logs(
    limit: int = Query(
        100, ge=1, le=1000, description="Maximum number of log entries to return"
    ),
    start_time: Optional[datetime] = Query(
        None, description="Start time for log query (ISO 8601 format)"
    ),
    end_time: Optional[datetime] = Query(
        None, description="End time for log query (ISO 8601 format)"
    ),
    level: Optional[str] = Query(
        None, description="Filter logs by level (e.g., INFO, WARNING, ERROR)"
    ),
    service: Optional[str] = Query(None, description="Filter logs by service name"),
    keyword: Optional[str] = Query(
        None, description="Filter logs by keyword in message"
    ),
) -> List[LogEntry]:
    """
    Retrieve application logs based on the provided query parameters.

    Args:
        limit: Maximum number of log entries.
        start_time: Start time for the query.
        end_time: End time for the query.
        level: Log level filter.
        service: Service name filter.
        keyword: Keyword filter.

    Returns:
        List[LogEntry]: A list of log entries matching the query.
    """
    log_query = LogQuery(
        limit=limit,
        start_time=start_time,
        end_time=end_time,
        level=level,
        service=service,
        keyword=keyword,
    )
    logger.info(f"Log query request received: {log_query.dict(exclude_none=True)}")

    if not settings.MONITORING_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Monitoring is not enabled. Please check API settings.",
        )

    try:
        return await monitoring_service.get_logs(log_query)
    except Exception as e:
        logger.error(f"Error retrieving logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving logs: {str(e)}",
        )
