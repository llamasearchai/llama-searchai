"""
Backup service module for LlamaSearch AI.

This module implements the business logic for creating, managing, and restoring backups.
"""

import asyncio
import random
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from uuid import uuid4

from llamasearchai.config.settings import settings
from llamasearchai.models.backup import (
    BackupJob,
    BackupJobCreate,
    BackupJobStatus,
    BackupMetadata,
    RestoreJob,
    RestoreJobCreate,
    RestoreJobStatus,
)
from loguru import logger


class BackupService:
    """
    Service class for handling backup and restore operations.

    Manages the creation, listing, and restoration of data backups.
    """

    def __init__(self):
        """Initialize the backup service."""
        # Ensure the base backup directory exists
        self._backup_dir = Path(settings.STORAGE_DIR) / "backups"
        self._backup_dir.mkdir(parents=True, exist_ok=True)

        self._backup_jobs: Dict[str, BackupJob] = {}
        self._restore_jobs: Dict[str, RestoreJob] = {}
        logger.info(f"BackupService initialized. Backup directory: {self._backup_dir}")

    async def create_backup(self, backup_create: BackupJobCreate) -> BackupJob:
        """
        Initiate a new backup job.

        Args:
            backup_create: Data for the new backup job.

        Returns:
            BackupJob: The newly created backup job details.
        """
        start_time = time.time()
        job_id = str(uuid4())
        now = datetime.utcnow()

        backup_file_name = f"backup_{now.strftime('%Y%m%d_%H%M%S')}_{backup_create.backup_type}.tar.gz"  # Example filename
        backup_path = self._backup_dir / backup_file_name

        job = BackupJob(
            id=job_id,
            status=BackupJobStatus.PENDING,
            backup_type=backup_create.backup_type,
            description=backup_create.description,
            created_at=now,
            updated_at=now,
            metadata=BackupMetadata(
                processing_time=0,
                request_id=str(uuid4()),
                timestamp=now.isoformat(),
                version=settings.VERSION,
                source="llamasearch-backup-service",
            ),
        )

        self._backup_jobs[job_id] = job
        logger.info(
            f"Backup job {job_id} created for type: {backup_create.backup_type}"
        )

        # Start the backup process in the background (mock implementation)
        asyncio.create_task(self._run_backup_job(job_id, backup_path))

        # Update metadata processing time after initiating task
        job.metadata.processing_time = time.time() - start_time
        self._backup_jobs[job_id] = job  # Update with processing time

        return job

    async def _run_backup_job(self, job_id: str, backup_path: Path):
        """Simulate running a backup job."""
        job = self._backup_jobs.get(job_id)
        if not job:
            return

        job.status = BackupJobStatus.RUNNING
        job.updated_at = datetime.utcnow()
        job.started_at = datetime.utcnow()
        self._backup_jobs[job_id] = job
        logger.info(f"Backup job {job_id} started.")

        try:
            # TODO: Implement actual backup logic
            # e.g., dump database, archive files, upload to cloud storage
            await asyncio.sleep(random.uniform(5.0, 15.0))  # Simulate work

            # Create a dummy backup file for demonstration
            backup_path.touch()
            with open(backup_path, "w") as f:
                f.write(
                    f"Mock backup data for job {job_id}\nType: {job.backup_type}\nCreated at: {job.created_at}"
                )

            # Simulate file size
            file_size_bytes = random.randint(
                10 * 1024 * 1024, 500 * 1024 * 1024
            )  # 10MB - 500MB

            job.status = BackupJobStatus.COMPLETED
            job.file_path = str(backup_path.relative_to(settings.STORAGE_DIR))
            job.file_size_bytes = file_size_bytes
            logger.info(
                f"Backup job {job_id} completed successfully. Path: {job.file_path}"
            )

        except Exception as e:
            logger.error(f"Backup job {job_id} failed: {e}")
            job.status = BackupJobStatus.FAILED
            job.error_message = str(e)
        finally:
            job.completed_at = datetime.utcnow()
            job.updated_at = datetime.utcnow()
            if job.started_at:
                job.duration_seconds = (
                    job.completed_at - job.started_at
                ).total_seconds()
            self._backup_jobs[job_id] = job

    async def list_backups(
        self,
        status: Optional[BackupJobStatus] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[BackupJob]:
        """
        List backup jobs, optionally filtered by status.

        Args:
            status: Optional job status to filter by.
            limit: Maximum number of jobs to return.
            offset: Number of jobs to skip for pagination.

        Returns:
            List[BackupJob]: A list of backup jobs.
        """
        all_jobs = list(self._backup_jobs.values())

        if status:
            filtered_jobs = [job for job in all_jobs if job.status == status]
        else:
            filtered_jobs = all_jobs

        # Sort by creation time (most recent first)
        filtered_jobs.sort(key=lambda j: j.created_at, reverse=True)

        return filtered_jobs[offset : offset + limit]

    async def get_backup(self, job_id: str) -> Optional[BackupJob]:
        """
        Retrieve details of a specific backup job.

        Args:
            job_id: The unique identifier of the backup job.

        Returns:
            Optional[BackupJob]: The backup job details if found, otherwise None.
        """
        return self._backup_jobs.get(job_id)

    async def delete_backup(self, job_id: str) -> bool:
        """
        Delete a backup job record and its associated file.

        Args:
            job_id: The ID of the backup job to delete.

        Returns:
            bool: True if the job and file were deleted successfully, False otherwise.
        """
        job = self._backup_jobs.get(job_id)
        if not job:
            return False

        # Attempt to delete the backup file if it exists
        if job.file_path:
            try:
                full_path = Path(settings.STORAGE_DIR) / job.file_path
                if full_path.exists():
                    full_path.unlink()
                    logger.info(f"Deleted backup file: {full_path}")
                else:
                    logger.warning(f"Backup file not found for deletion: {full_path}")
            except Exception as e:
                logger.error(
                    f"Error deleting backup file {job.file_path} for job {job_id}: {e}"
                )
                # Proceed to delete the job record anyway?

        # Delete the job record
        del self._backup_jobs[job_id]
        logger.info(f"Deleted backup job record {job_id}")
        return True

    async def restore_from_backup(self, restore_create: RestoreJobCreate) -> RestoreJob:
        """
        Initiate a restore job from a specified backup.

        Args:
            restore_create: Data for the new restore job.

        Returns:
            RestoreJob: The newly created restore job details.
        """
        start_time = time.time()
        job_id = str(uuid4())
        now = datetime.utcnow()

        # Validate the source backup job exists and is completed
        source_backup = self._backup_jobs.get(restore_create.source_backup_id)
        if not source_backup:
            raise ValueError(
                f"Source backup job ID '{restore_create.source_backup_id}' not found."
            )
        if source_backup.status != BackupJobStatus.COMPLETED:
            raise ValueError(
                f"Source backup job '{restore_create.source_backup_id}' is not completed (status: {source_backup.status}). Cannot restore."
            )
        if not source_backup.file_path:
            raise ValueError(
                f"Source backup job '{restore_create.source_backup_id}' has no associated file path."
            )

        job = RestoreJob(
            id=job_id,
            source_backup_id=restore_create.source_backup_id,
            status=RestoreJobStatus.PENDING,
            restore_options=restore_create.restore_options,
            created_at=now,
            updated_at=now,
            metadata=BackupMetadata(  # Reusing BackupMetadata for simplicity
                processing_time=0,
                request_id=str(uuid4()),
                timestamp=now.isoformat(),
                version=settings.VERSION,
                source="llamasearch-restore-service",
            ),
        )

        self._restore_jobs[job_id] = job
        logger.info(
            f"Restore job {job_id} created from backup {restore_create.source_backup_id}"
        )

        # Start the restore process in the background
        backup_file_path = Path(settings.STORAGE_DIR) / source_backup.file_path
        asyncio.create_task(self._run_restore_job(job_id, backup_file_path))

        # Update metadata processing time
        job.metadata.processing_time = time.time() - start_time
        self._restore_jobs[job_id] = job

        return job

    async def _run_restore_job(self, job_id: str, backup_file_path: Path):
        """Simulate running a restore job."""
        job = self._restore_jobs.get(job_id)
        if not job:
            return

        job.status = RestoreJobStatus.RUNNING
        job.updated_at = datetime.utcnow()
        job.started_at = datetime.utcnow()
        self._restore_jobs[job_id] = job
        logger.info(f"Restore job {job_id} started from {backup_file_path}.")

        try:
            # TODO: Implement actual restore logic
            # e.g., Stop services, clear data, extract archive, load database dump, restart services
            if not backup_file_path.exists():
                raise FileNotFoundError(f"Backup file {backup_file_path} not found.")

            await asyncio.sleep(random.uniform(10.0, 30.0))  # Simulate work

            # Simulate successful restore
            job.status = RestoreJobStatus.COMPLETED
            logger.info(f"Restore job {job_id} completed successfully.")

        except Exception as e:
            logger.error(f"Restore job {job_id} failed: {e}")
            job.status = RestoreJobStatus.FAILED
            job.error_message = str(e)
        finally:
            job.completed_at = datetime.utcnow()
            job.updated_at = datetime.utcnow()
            if job.started_at:
                job.duration_seconds = (
                    job.completed_at - job.started_at
                ).total_seconds()
            self._restore_jobs[job_id] = job

    async def get_restore_job(self, job_id: str) -> Optional[RestoreJob]:
        """
        Retrieve details of a specific restore job.

        Args:
            job_id: The unique identifier of the restore job.

        Returns:
            Optional[RestoreJob]: The restore job details if found, otherwise None.
        """
        return self._restore_jobs.get(job_id)

    async def list_restore_jobs(
        self,
        status: Optional[RestoreJobStatus] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[RestoreJob]:
        """
        List restore jobs, optionally filtered by status.

        Args:
            status: Optional job status to filter by.
            limit: Maximum number of jobs to return.
            offset: Number of jobs to skip for pagination.

        Returns:
            List[RestoreJob]: A list of restore jobs.
        """
        all_jobs = list(self._restore_jobs.values())

        if status:
            filtered_jobs = [job for job in all_jobs if job.status == status]
        else:
            filtered_jobs = all_jobs

        # Sort by creation time (most recent first)
        filtered_jobs.sort(key=lambda j: j.created_at, reverse=True)

        return filtered_jobs[offset : offset + limit]
