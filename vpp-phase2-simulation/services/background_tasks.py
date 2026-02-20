"""
Background Task Service for VCC Master.

Implements:
- BackgroundTaskService: Manages background tasks
- Coordination task (every 10 seconds)
- Data cleanup task (periodic)
- Uses APScheduler for task scheduling
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Callable
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)


class BackgroundTaskService:
    """Service for managing background tasks in VCC Master."""

    def __init__(self):
        """Initialize background task service."""
        self.scheduler = BackgroundScheduler()
        self.coordination_task_id = None
        self.cleanup_task_id = None
        self.coordination_callback: Optional[Callable] = None
        self.cleanup_callback: Optional[Callable] = None
        self.is_running = False
        self.coordination_count = 0
        self.cleanup_count = 0
        self.last_coordination_time: Optional[datetime] = None
        self.last_cleanup_time: Optional[datetime] = None

    def set_coordination_callback(self, callback: Callable):
        """
        Set callback function for coordination task.
        
        Args:
            callback: Function to call for coordination
        """
        self.coordination_callback = callback
        logger.info("Coordination callback set")

    def set_cleanup_callback(self, callback: Callable):
        """
        Set callback function for cleanup task.
        
        Args:
            callback: Function to call for cleanup
        """
        self.cleanup_callback = callback
        logger.info("Cleanup callback set")

    def start(self):
        """Start the background task scheduler."""
        if self.is_running:
            logger.warning("Background task scheduler is already running")
            return
        
        try:
            self.scheduler.start()
            self.is_running = True
            logger.info("Background task scheduler started")
        except Exception as e:
            logger.error(f"Error starting background task scheduler: {str(e)}")
            raise

    def stop(self):
        """Stop the background task scheduler."""
        if not self.is_running:
            logger.warning("Background task scheduler is not running")
            return
        
        try:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("Background task scheduler stopped")
        except Exception as e:
            logger.error(f"Error stopping background task scheduler: {str(e)}")
            raise

    def start_coordination_task(self, interval_seconds: int = 10):
        """
        Start coordination task that runs every N seconds.
        
        Args:
            interval_seconds: Interval in seconds (default 10)
        """
        if not self.is_running:
            logger.warning("Scheduler is not running, starting it first")
            self.start()
        
        try:
            # Remove existing task if any
            if self.coordination_task_id:
                try:
                    self.scheduler.remove_job(self.coordination_task_id)
                except:
                    pass
            
            # Add new coordination task
            job = self.scheduler.add_job(
                self._execute_coordination_task,
                trigger=IntervalTrigger(seconds=interval_seconds),
                id='coordination_task',
                name='VCC Coordination Task',
                replace_existing=True
            )
            
            self.coordination_task_id = job.id
            
            logger.info(f"Coordination task started with interval {interval_seconds}s")
            
        except Exception as e:
            logger.error(f"Error starting coordination task: {str(e)}")
            raise

    def stop_coordination_task(self):
        """Stop the coordination task."""
        try:
            if self.coordination_task_id:
                try:
                    self.scheduler.remove_job(self.coordination_task_id)
                except:
                    pass
                self.coordination_task_id = None
                logger.info("Coordination task stopped")
        except Exception as e:
            logger.error(f"Error stopping coordination task: {str(e)}")
            raise

    def start_data_cleanup_task(self, interval_seconds: int = 3600):
        """
        Start data cleanup task that runs every N seconds.
        
        Args:
            interval_seconds: Interval in seconds (default 3600 = 1 hour)
        """
        if not self.is_running:
            logger.warning("Scheduler is not running, starting it first")
            self.start()
        
        try:
            # Remove existing task if any
            if self.cleanup_task_id:
                try:
                    self.scheduler.remove_job(self.cleanup_task_id)
                except:
                    pass
            
            # Add new cleanup task
            job = self.scheduler.add_job(
                self._execute_cleanup_task,
                trigger=IntervalTrigger(seconds=interval_seconds),
                id='cleanup_task',
                name='Data Cleanup Task',
                replace_existing=True
            )
            
            self.cleanup_task_id = job.id
            
            logger.info(f"Data cleanup task started with interval {interval_seconds}s")
            
        except Exception as e:
            logger.error(f"Error starting data cleanup task: {str(e)}")
            raise

    def stop_data_cleanup_task(self):
        """Stop the data cleanup task."""
        try:
            if self.cleanup_task_id:
                try:
                    self.scheduler.remove_job(self.cleanup_task_id)
                except:
                    pass
                self.cleanup_task_id = None
                logger.info("Data cleanup task stopped")
        except Exception as e:
            logger.error(f"Error stopping data cleanup task: {str(e)}")
            raise

    def _execute_coordination_task(self):
        """Execute coordination task."""
        try:
            logger.debug("Executing coordination task")
            
            self.coordination_count += 1
            self.last_coordination_time = datetime.now()
            
            if self.coordination_callback:
                self.coordination_callback()
            
            logger.debug(f"Coordination task executed (count: {self.coordination_count})")
            
        except Exception as e:
            logger.error(f"Error in coordination task: {str(e)}")

    def _execute_cleanup_task(self):
        """Execute cleanup task."""
        try:
            logger.debug("Executing cleanup task")
            
            self.cleanup_count += 1
            self.last_cleanup_time = datetime.now()
            
            if self.cleanup_callback:
                self.cleanup_callback()
            
            logger.debug(f"Cleanup task executed (count: {self.cleanup_count})")
            
        except Exception as e:
            logger.error(f"Error in cleanup task: {str(e)}")

    def get_stats(self) -> dict:
        """
        Get background task statistics.
        
        Returns:
            dict: Statistics including task counts and last execution times
        """
        jobs = self.scheduler.get_jobs() if self.is_running else []
        
        return {
            "is_running": self.is_running,
            "coordination_count": self.coordination_count,
            "cleanup_count": self.cleanup_count,
            "last_coordination_time": self.last_coordination_time.isoformat() if self.last_coordination_time else None,
            "last_cleanup_time": self.last_cleanup_time.isoformat() if self.last_cleanup_time else None,
            "active_jobs": len(jobs),
            "jobs": [{"id": job.id, "name": job.name, "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None} for job in jobs],
        }

    def get_job_status(self, job_id: str) -> Optional[dict]:
        """
        Get status of a specific job.
        
        Args:
            job_id: Job ID to query
            
        Returns:
            dict with job status, or None if job not found
        """
        try:
            job = self.scheduler.get_job(job_id)
            if job:
                return {
                    "id": job.id,
                    "name": job.name,
                    "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                    "trigger": str(job.trigger),
                }
            return None
        except Exception as e:
            logger.error(f"Error getting job status: {str(e)}")
            return None

    def pause_coordination_task(self):
        """Pause the coordination task."""
        try:
            if self.coordination_task_id:
                job = self.scheduler.get_job(self.coordination_task_id)
                if job:
                    job.pause()
                    logger.info("Coordination task paused")
        except Exception as e:
            logger.error(f"Error pausing coordination task: {str(e)}")

    def resume_coordination_task(self):
        """Resume the coordination task."""
        try:
            if self.coordination_task_id:
                job = self.scheduler.get_job(self.coordination_task_id)
                if job:
                    job.resume()
                    logger.info("Coordination task resumed")
        except Exception as e:
            logger.error(f"Error resuming coordination task: {str(e)}")

    def pause_cleanup_task(self):
        """Pause the cleanup task."""
        try:
            if self.cleanup_task_id:
                job = self.scheduler.get_job(self.cleanup_task_id)
                if job:
                    job.pause()
                    logger.info("Cleanup task paused")
        except Exception as e:
            logger.error(f"Error pausing cleanup task: {str(e)}")

    def resume_cleanup_task(self):
        """Resume the cleanup task."""
        try:
            if self.cleanup_task_id:
                job = self.scheduler.get_job(self.cleanup_task_id)
                if job:
                    job.resume()
                    logger.info("Cleanup task resumed")
        except Exception as e:
            logger.error(f"Error resuming cleanup task: {str(e)}")
