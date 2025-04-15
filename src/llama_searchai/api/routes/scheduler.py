"""
Scheduler route handlers for LlamaSearch AI API.
"""

from typing import List, Optional

from fastapi import (
    APIRouter,
    Body,
    HTTPException,
    Path,
    Query,
    Security,
    status,
)
from llamasearchai.api.app import get_api_key
from llamasearchai.config.settings import settings
from llamasearchai.models.scheduler import Job, JobCreate, JobStatus, JobUpdate
from llamasearchai.services.scheduler import SchedulerService
from loguru import logger

# Create router
router = APIRouter(
    prefix="/api/v1/scheduler",
    tags=["scheduler"],
    dependencies=[Security(get_api_key)],
)

# Create service instance
scheduler_service = SchedulerService()


@router.post("/jobs", response_model=Job, status_code=status.HTTP_201_CREATED)
async def create_job(job_create: JobCreate = Body(...)) -> Job:
    """
    Schedule a new background job.

    Args:
        job_create: Data for the new job.

    Returns:
        Job: The newly scheduled job details.
    """
    logger.info(f"Create job request received for task: {job_create.task_name}")

    if not settings.SCHEDULER_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Scheduler is not enabled. Please check API settings.",
        )

    try:
        job = await scheduler_service.schedule_job(job_create)
        return job
    except Exception as e:
        logger.error(f"Error creating job: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating job: {str(e)}",
        )


@router.get("/jobs/{job_id}", response_model=Job)
async def get_job(
    job_id: str = Path(..., description="ID of the job to retrieve")
) -> Job:
    """
    Retrieve details of a specific scheduled job.

    Args:
        job_id: The ID of the job.

    Returns:
        Job: The job details.
    """
    logger.info(f"Get job request received for ID: {job_id}")

    if not settings.SCHEDULER_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Scheduler is not enabled. Please check API settings.",
        )

    try:
        job = await scheduler_service.get_job(job_id)
        if job is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job with ID '{job_id}' not found",
            )
        return job
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        logger.error(f"Error retrieving job {job_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving job: {str(e)}",
        )


@router.get("/jobs", response_model=List[Job])
async def list_jobs(
    status_filter: Optional[JobStatus] = Query(
        None, alias="status", description="Filter jobs by status"
    ),
    limit: int = Query(
        100, ge=1, le=1000, description="Maximum number of jobs to return"
    ),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
) -> List[Job]:
    """
    List scheduled jobs, optionally filtered by status.

    Args:
        status_filter: Optional status to filter jobs by.
        limit: Maximum number of jobs.
        offset: Pagination offset.

    Returns:
        List[Job]: A list of jobs.
    """
    logger.info(
        f"List jobs request received: status={status_filter}, limit={limit}, offset={offset}"
    )

    if not settings.SCHEDULER_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Scheduler is not enabled. Please check API settings.",
        )

    try:
        jobs = await scheduler_service.list_jobs(
            status=status_filter, limit=limit, offset=offset
        )
        return jobs
    except Exception as e:
        logger.error(f"Error listing jobs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing jobs: {str(e)}",
        )


@router.put("/jobs/{job_id}", response_model=Job)
async def update_job(
    job_id: str = Path(..., description="ID of the job to update"),
    job_update: JobUpdate = Body(...),
) -> Job:
    """
    Update an existing scheduled job.

    Args:
        job_id: The ID of the job to update.
        job_update: The update data.

    Returns:
        Job: The updated job details.
    """
    logger.info(f"Update job request received for ID: {job_id}")

    if not settings.SCHEDULER_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Scheduler is not enabled. Please check API settings.",
        )

    try:
        updated_job = await scheduler_service.update_job(job_id, job_update)
        if updated_job is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job with ID '{job_id}' not found",
            )
        return updated_job
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        logger.error(f"Error updating job {job_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating job: {str(e)}",
        )


@router.delete("/jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job(
    job_id: str = Path(..., description="ID of the job to delete")
) -> None:
    """
    Delete (cancel) a scheduled job.

    Args:
        job_id: The ID of the job to delete.
    """
    logger.info(f"Delete job request received for ID: {job_id}")

    if not settings.SCHEDULER_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Scheduler is not enabled. Please check API settings.",
        )

    try:
        deleted = await scheduler_service.delete_job(job_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job with ID '{job_id}' not found",
            )
        return None  # Return None for 204 No Content
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        logger.error(f"Error deleting job {job_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting job: {str(e)}",
        )


@router.post("/jobs/{job_id}/trigger", status_code=status.HTTP_202_ACCEPTED)
async def trigger_job(
    job_id: str = Path(..., description="ID of the job to trigger manually")
) -> Dict[str, str]:
    """
    Manually trigger a job to run immediately.

    Args:
        job_id: The ID of the job to trigger.

    Returns:
        Dict: Confirmation message.
    """
    logger.info(f"Trigger job request received for ID: {job_id}")

    if not settings.SCHEDULER_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Scheduler is not enabled. Please check API settings.",
        )

    try:
        triggered = await scheduler_service.trigger_job(job_id)
        if not triggered:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job with ID '{job_id}' not found or could not be triggered",
            )
        return {"message": f"Job {job_id} triggered successfully"}
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        logger.error(f"Error triggering job {job_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error triggering job: {str(e)}",
        )
