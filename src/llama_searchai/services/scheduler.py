"""
Scheduler service module for LlamaSearch AI.

This module implements the business logic for scheduling and managing background tasks.
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from uuid import uuid4

from llamasearchai.models.scheduler import (
    Job,
    JobCreate,
    JobStatus,
    JobUpdate,
    Schedule,
    SchedulerMetadata,
)
from loguru import logger


class SchedulerService:
    """
    Service class for handling task scheduling operations.

    Manages the creation, retrieval, update, and deletion of scheduled jobs.
    """

    def __init__(self):
        """Initialize the scheduler service."""
        # In a real implementation, this would likely use a library like APScheduler,
        # Celery Beat, or integrate with a dedicated task queue system.
        self._jobs: Dict[str, Job] = {}
        self._scheduler_running = False
        logger.info("SchedulerService initialized.")
        # Optionally start a background task runner if needed
        # asyncio.create_task(self._run_scheduler())

    async def schedule_job(self, job_create: JobCreate) -> Job:
        """
        Schedule a new background job.

        Args:
            job_create: Data for the new job to be scheduled.

        Returns:
            Job: The newly created and scheduled job.
        """
        # Record start time
        start_time = time.time()

        job_id = str(uuid4())
        now = datetime.utcnow()

        # Calculate next run time based on schedule
        next_run = self._calculate_next_run(job_create.schedule)

        job = Job(
            id=job_id,
            task_name=job_create.task_name,
            schedule=job_create.schedule,
            args=job_create.args,
            kwargs=job_create.kwargs,
            status=JobStatus.PENDING,
            created_at=now,
            updated_at=now,
            next_run_time=next_run,
            timeout_seconds=job_create.timeout_seconds,
            max_retries=job_create.max_retries,
            retry_delay_seconds=job_create.retry_delay_seconds,
        )

        # TODO: Implement actual scheduling logic (e.g., add to APScheduler)
        self._jobs[job_id] = job
        logger.info(f"Scheduled new job {job_id}: {job.task_name}")

        # Calculate processing time
        processing_time = time.time() - start_time

        # Create metadata (example)
        metadata = SchedulerMetadata(
            processing_time=processing_time,
            request_id=str(uuid4()),
            timestamp=datetime.utcnow().isoformat(),
            version="0.1.0",
            source="llamasearch-scheduler-service",
            total_jobs=len(self._jobs),
            pending_jobs=sum(
                1 for j in self._jobs.values() if j.status == JobStatus.PENDING
            ),
        )

        # Add metadata to the job response (optional, depending on API design)
        # job.metadata = metadata # Pydantic model doesn't have this field by default

        return job

    async def get_job(self, job_id: str) -> Optional[Job]:
        """
        Retrieve details of a specific scheduled job.

        Args:
            job_id: The unique identifier of the job.

        Returns:
            Optional[Job]: The job details if found, otherwise None.
        """
        # TODO: Retrieve job from the actual scheduler store
        return self._jobs.get(job_id)

    async def list_jobs(
        self, status: Optional[JobStatus] = None, limit: int = 100, offset: int = 0
    ) -> List[Job]:
        """
        List scheduled jobs, optionally filtered by status.

        Args:
            status: Optional job status to filter by.
            limit: Maximum number of jobs to return.
            offset: Number of jobs to skip for pagination.

        Returns:
            List[Job]: A list of scheduled jobs.
        """
        # TODO: Retrieve jobs from the actual scheduler store
        all_jobs = list(self._jobs.values())

        if status:
            filtered_jobs = [job for job in all_jobs if job.status == status]
        else:
            filtered_jobs = all_jobs

        # Sort by creation time (most recent first)
        filtered_jobs.sort(key=lambda j: j.created_at, reverse=True)

        return filtered_jobs[offset : offset + limit]

    async def update_job(self, job_id: str, job_update: JobUpdate) -> Optional[Job]:
        """
        Update an existing scheduled job.

        Args:
            job_id: The ID of the job to update.
            job_update: The fields to update.

        Returns:
            Optional[Job]: The updated job details if found, otherwise None.
        """
        job = self._jobs.get(job_id)
        if not job:
            return None

        # TODO: Implement actual job update logic in the scheduler
        update_data = job_update.dict(exclude_unset=True)

        for key, value in update_data.items():
            setattr(job, key, value)

        # Recalculate next run time if schedule changed
        if "schedule" in update_data:
            job.next_run_time = self._calculate_next_run(job.schedule)

        job.updated_at = datetime.utcnow()
        self._jobs[job_id] = job  # Update mock store
        logger.info(f"Updated job {job_id}")

        return job

    async def delete_job(self, job_id: str) -> bool:
        """
        Delete (cancel) a scheduled job.

        Args:
            job_id: The ID of the job to delete.

        Returns:
            bool: True if the job was deleted successfully, False otherwise.
        """
        # TODO: Implement actual job deletion logic in the scheduler
        if job_id in self._jobs:
            del self._jobs[job_id]
            logger.info(f"Deleted job {job_id}")
            return True
        return False

    async def trigger_job(self, job_id: str) -> bool:
        """
        Manually trigger a scheduled job to run immediately.

        Args:
            job_id: The ID of the job to trigger.

        Returns:
            bool: True if the job was found and triggered, False otherwise.
        """
        job = self._jobs.get(job_id)
        if not job:
            return False

        # TODO: Implement actual job triggering logic (e.g., run the task function)
        logger.info(f"Manually triggering job {job_id}: {job.task_name}")
        # Simulate running the job
        job.status = JobStatus.RUNNING
        job.last_run_time = datetime.utcnow()
        # Simulate completion after a short delay
        await asyncio.sleep(random.uniform(0.5, 2.0))
        job.status = JobStatus.COMPLETED
        job.updated_at = datetime.utcnow()
        self._jobs[job_id] = job  # Update mock store

        return True

    def _calculate_next_run(self, schedule: Schedule) -> Optional[datetime]:
        """
        Calculate the next run time based on the schedule. (Placeholder)

        Args:
            schedule: The schedule details.

        Returns:
            Optional[datetime]: The next scheduled run time, or None if it's a one-off run
                                  that should have already happened or is invalid.
        """
        now = datetime.utcnow()

        if schedule.run_once_at:
            return schedule.run_once_at if schedule.run_once_at > now else None

        if schedule.interval_seconds:
            # Simple interval calculation for demonstration
            return now + timedelta(seconds=schedule.interval_seconds)

        if schedule.cron_expression:
            # TODO: Implement proper cron parsing and next run calculation
            # Using a library like 'croniter' would be appropriate here.
            # For now, just schedule it for 5 minutes from now as a placeholder.
            return now + timedelta(minutes=5)

        return None  # Should not happen if schedule is valid

    async def _run_scheduler(self):
        """
        Background task to check and run pending jobs. (Placeholder)
        This would be handled by the underlying scheduler library in a real implementation.
        """
        self._scheduler_running = True
        logger.info("Mock scheduler loop started.")
        while self._scheduler_running:
            now = datetime.utcnow()
            for job_id, job in list(self._jobs.items()):
                if (
                    job.status == JobStatus.PENDING
                    and job.next_run_time
                    and job.next_run_time <= now
                ):
                    logger.info(f"Running job {job_id}: {job.task_name}")
                    job.status = JobStatus.RUNNING
                    job.last_run_time = now
                    # Simulate job execution
                    await asyncio.sleep(random.uniform(0.1, 1.0))
                    # Simulate outcome
                    if random.random() < 0.9:  # 90% success rate
                        job.status = JobStatus.COMPLETED
                    else:
                        job.status = JobStatus.FAILED
                        job.retries_left = (
                            job.retries_left - 1 if job.retries_left > 0 else 0
                        )
                    job.updated_at = datetime.utcnow()

                    # Reschedule if it's a recurring job
                    if job.status == JobStatus.COMPLETED and (
                        job.schedule.interval_seconds or job.schedule.cron_expression
                    ):
                        job.next_run_time = self._calculate_next_run(job.schedule)
                        job.status = JobStatus.PENDING  # Reset status for next run
                    elif job.status == JobStatus.FAILED and job.retries_left > 0:
                        # Simple retry logic: schedule after delay
                        job.next_run_time = now + timedelta(
                            seconds=job.retry_delay_seconds
                        )
                        job.status = JobStatus.PENDING
                    else:
                        # Job is finished (completed one-off, failed with no retries)
                        job.next_run_time = None

                    self._jobs[job_id] = job  # Update mock store

            await asyncio.sleep(10)  # Check every 10 seconds
        logger.info("Mock scheduler loop stopped.")

    async def stop_scheduler(self):
        """Stop the mock scheduler loop."""
        self._scheduler_running = False
