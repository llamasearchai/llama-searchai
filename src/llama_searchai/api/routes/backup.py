"""
Backup route handlers for LlamaSearch AI API.
"""

from pathlib import Path
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
from fastapi.responses import FileResponse
from llamasearchai.api.app import get_api_key
from llamasearchai.config.settings import settings
from llamasearchai.models.backup import (
    BackupJob,
    BackupJobCreate,
    BackupJobStatus,
    RestoreJob,
    RestoreJobCreate,
    RestoreJobStatus,
)
from llamasearchai.services.backup import BackupService
from loguru import logger

# Create router
router = APIRouter(
    prefix="/api/v1/backup",
    tags=["backup"],
    dependencies=[Security(get_api_key)],
)

# Create service instance
backup_service = BackupService()


@router.post("/jobs", response_model=BackupJob, status_code=status.HTTP_202_ACCEPTED)
async def create_backup_job(backup_create: BackupJobCreate = Body(...)) -> BackupJob:
    """
    Initiate a new data backup job.

    The job runs in the background.

    Args:
        backup_create: Data for the new backup job.

    Returns:
        BackupJob: Details of the initiated backup job.
    """
    logger.info(f"Create backup job request received: type={backup_create.backup_type}")

    if not settings.BACKUP_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Backup feature is not enabled. Please check API settings.",
        )

    try:
        job = await backup_service.create_backup(backup_create)
        return job
    except Exception as e:
        logger.error(f"Error creating backup job: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating backup job: {str(e)}",
        )


@router.get("/jobs", response_model=List[BackupJob])
async def list_backup_jobs(
    status_filter: Optional[BackupJobStatus] = Query(
        None, alias="status", description="Filter jobs by status"
    ),
    limit: int = Query(
        100, ge=1, le=1000, description="Maximum number of jobs to return"
    ),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
) -> List[BackupJob]:
    """
    List backup jobs, optionally filtered by status.

    Args:
        status_filter: Optional status to filter jobs by.
        limit: Maximum number of jobs.
        offset: Pagination offset.

    Returns:
        List[BackupJob]: A list of backup jobs.
    """
    logger.info(
        f"List backup jobs request received: status={status_filter}, limit={limit}, offset={offset}"
    )

    if not settings.BACKUP_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Backup feature is not enabled. Please check API settings.",
        )

    try:
        jobs = await backup_service.list_backups(
            status=status_filter, limit=limit, offset=offset
        )
        return jobs
    except Exception as e:
        logger.error(f"Error listing backup jobs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing backup jobs: {str(e)}",
        )


@router.get("/jobs/{job_id}", response_model=BackupJob)
async def get_backup_job(
    job_id: str = Path(..., description="ID of the backup job to retrieve")
) -> BackupJob:
    """
    Retrieve details of a specific backup job.

    Args:
        job_id: The ID of the backup job.

    Returns:
        BackupJob: The backup job details.
    """
    logger.info(f"Get backup job request received for ID: {job_id}")

    if not settings.BACKUP_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Backup feature is not enabled. Please check API settings.",
        )

    try:
        job = await backup_service.get_backup(job_id)
        if job is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Backup job with ID '{job_id}' not found",
            )
        return job
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        logger.error(f"Error retrieving backup job {job_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving backup job: {str(e)}",
        )


@router.delete("/jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_backup_job(
    job_id: str = Path(..., description="ID of the backup job to delete")
) -> None:
    """
    Delete a backup job and its associated file.

    Args:
        job_id: The ID of the backup job to delete.
    """
    logger.info(f"Delete backup job request received for ID: {job_id}")

    if not settings.BACKUP_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Backup feature is not enabled. Please check API settings.",
        )

    try:
        deleted = await backup_service.delete_backup(job_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Backup job with ID '{job_id}' not found",
            )
        return None  # Return None for 204 No Content
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        logger.error(f"Error deleting backup job {job_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting backup job: {str(e)}",
        )


@router.get("/jobs/{job_id}/download")
async def download_backup_file(
    job_id: str = Path(..., description="ID of the backup job to download")
) -> FileResponse:
    """
    Download the backup file associated with a completed job.

    Args:
        job_id: The ID of the backup job.

    Returns:
        FileResponse: The backup file as a downloadable response.
    """
    logger.info(f"Download backup file request for job ID: {job_id}")

    if not settings.BACKUP_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Backup feature is not enabled.",
        )

    job = await backup_service.get_backup(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Backup job '{job_id}' not found.",
        )
    if job.status != BackupJobStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Backup job '{job_id}' is not completed (status: {job.status}).",
        )
    if not job.file_path:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No backup file found for job '{job_id}'.",
        )

    try:
        full_path = Path(settings.STORAGE_DIR) / job.file_path
        if not full_path.is_file():
            logger.error(f"Backup file missing on disk: {full_path}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Backup file for job '{job_id}' not found on server.",
            )

        # Extract filename for the download
        filename = full_path.name

        return FileResponse(
            path=str(full_path), media_type="application/gzip", filename=filename
        )
    except HTTPException:  # Re-raise our own HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error preparing backup file {job.file_path} for download: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error serving backup file.",
        )


# --- Restore Endpoints ---


@router.post(
    "/restore", response_model=RestoreJob, status_code=status.HTTP_202_ACCEPTED
)
async def restore_from_backup(
    restore_create: RestoreJobCreate = Body(...),
) -> RestoreJob:
    """
    Initiate a restore job from a specified backup.

    The job runs in the background.

    Args:
        restore_create: Data for the restore job, including the source backup ID.

    Returns:
        RestoreJob: Details of the initiated restore job.
    """
    logger.info(
        f"Restore from backup request received: source_backup_id={restore_create.source_backup_id}"
    )

    if not settings.RESTORE_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Restore feature is not enabled. Please check API settings.",
        )

    try:
        job = await backup_service.restore_from_backup(restore_create)
        return job
    except ValueError as e:  # Catch specific validation errors from service
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error initiating restore job: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error initiating restore job: {str(e)}",
        )


@router.get("/restore/jobs", response_model=List[RestoreJob])
async def list_restore_jobs(
    status_filter: Optional[RestoreJobStatus] = Query(
        None, alias="status", description="Filter jobs by status"
    ),
    limit: int = Query(
        100, ge=1, le=1000, description="Maximum number of jobs to return"
    ),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
) -> List[RestoreJob]:
    """
    List restore jobs, optionally filtered by status.
    """
    logger.info(
        f"List restore jobs request received: status={status_filter}, limit={limit}, offset={offset}"
    )

    if not settings.RESTORE_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Restore feature is not enabled.",
        )

    try:
        jobs = await backup_service.list_restore_jobs(
            status=status_filter, limit=limit, offset=offset
        )
        return jobs
    except Exception as e:
        logger.error(f"Error listing restore jobs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error listing restore jobs.",
        )


@router.get("/restore/jobs/{job_id}", response_model=RestoreJob)
async def get_restore_job(
    job_id: str = Path(..., description="ID of the restore job to retrieve")
) -> RestoreJob:
    """
    Retrieve details of a specific restore job.
    """
    logger.info(f"Get restore job request received for ID: {job_id}")

    if not settings.RESTORE_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Restore feature is not enabled.",
        )

    job = await backup_service.get_restore_job(job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Restore job with ID '{job_id}' not found",
        )
    return job
