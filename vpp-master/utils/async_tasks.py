"""
Asynchronous Task Processing

Provides background task queue and scheduled task execution for long-running operations.
Uses threading for task execution and scheduling.
"""

import threading
import queue
import time
from datetime import datetime, timedelta
from typing import Callable, Any, Optional, Dict, List
from enum import Enum
from utils.logger import setup_logger

logger = setup_logger(__name__)


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Task:
    """Represents a background task."""
    
    def __init__(
        self,
        task_id: str,
        func: Callable,
        args: tuple = (),
        kwargs: dict = None,
        scheduled_time: Optional[datetime] = None
    ):
        """
        Initialize a task.
        
        Args:
            task_id: Unique task identifier
            func: Callable to execute
            args: Positional arguments for the callable
            kwargs: Keyword arguments for the callable
            scheduled_time: Optional scheduled execution time
        """
        self.task_id = task_id
        self.func = func
        self.args = args
        self.kwargs = kwargs or {}
        self.scheduled_time = scheduled_time
        self.status = TaskStatus.PENDING
        self.result = None
        self.error = None
        self.created_at = datetime.utcnow()
        self.started_at = None
        self.completed_at = None
    
    def execute(self) -> Any:
        """
        Execute the task.
        
        Returns:
            Task result
            
        Raises:
            Exception: If task execution fails
        """
        try:
            self.status = TaskStatus.RUNNING
            self.started_at = datetime.utcnow()
            logger.debug(f"Executing task {self.task_id}")
            
            self.result = self.func(*self.args, **self.kwargs)
            
            self.status = TaskStatus.COMPLETED
            self.completed_at = datetime.utcnow()
            logger.info(f"Task {self.task_id} completed successfully")
            
            return self.result
        except Exception as e:
            self.status = TaskStatus.FAILED
            self.error = str(e)
            self.completed_at = datetime.utcnow()
            logger.error(f"Task {self.task_id} failed: {str(e)}")
            raise
    
    def cancel(self) -> None:
        """Cancel the task if it hasn't started."""
        if self.status == TaskStatus.PENDING:
            self.status = TaskStatus.CANCELLED
            logger.info(f"Task {self.task_id} cancelled")
    
    def is_ready_to_execute(self) -> bool:
        """Check if task is ready to execute."""
        if self.scheduled_time is None:
            return self.status == TaskStatus.PENDING
        return self.status == TaskStatus.PENDING and datetime.utcnow() >= self.scheduled_time
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary."""
        return {
            "task_id": self.task_id,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "scheduled_time": self.scheduled_time.isoformat() if self.scheduled_time else None
        }


class TaskQueue:
    """Background task queue for executing long-running operations."""
    
    def __init__(self, num_workers: int = 4):
        """
        Initialize task queue.
        
        Args:
            num_workers: Number of worker threads
        """
        self.num_workers = num_workers
        self.task_queue: queue.Queue = queue.Queue()
        self.tasks: Dict[str, Task] = {}
        self.workers: List[threading.Thread] = []
        self.running = False
        self.lock = threading.Lock()
        logger.info(f"Initializing TaskQueue with {num_workers} workers")
    
    def start(self) -> None:
        """Start the task queue and worker threads."""
        if self.running:
            logger.warning("TaskQueue is already running")
            return
        
        self.running = True
        for i in range(self.num_workers):
            worker = threading.Thread(target=self._worker_loop, daemon=True)
            worker.start()
            self.workers.append(worker)
        
        logger.info(f"TaskQueue started with {self.num_workers} workers")
    
    def stop(self) -> None:
        """Stop the task queue and worker threads."""
        if not self.running:
            logger.warning("TaskQueue is not running")
            return
        
        self.running = False
        
        # Wait for workers to finish
        for worker in self.workers:
            worker.join(timeout=5)
        
        self.workers.clear()
        logger.info("TaskQueue stopped")
    
    def submit_task(
        self,
        task_id: str,
        func: Callable,
        args: tuple = (),
        kwargs: dict = None,
        scheduled_time: Optional[datetime] = None
    ) -> Task:
        """
        Submit a task to the queue.
        
        Args:
            task_id: Unique task identifier
            func: Callable to execute
            args: Positional arguments
            kwargs: Keyword arguments
            scheduled_time: Optional scheduled execution time
            
        Returns:
            Task object
        """
        task = Task(task_id, func, args, kwargs, scheduled_time)
        
        with self.lock:
            self.tasks[task_id] = task
        
        self.task_queue.put(task)
        logger.debug(f"Task {task_id} submitted to queue")
        
        return task
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """
        Get task by ID.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Task object or None if not found
        """
        with self.lock:
            return self.tasks.get(task_id)
    
    def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            True if task was cancelled, False otherwise
        """
        with self.lock:
            task = self.tasks.get(task_id)
            if task:
                task.cancel()
                return True
        return False
    
    def get_all_tasks(self) -> List[Task]:
        """
        Get all tasks.
        
        Returns:
            List of all tasks
        """
        with self.lock:
            return list(self.tasks.values())
    
    def get_pending_tasks(self) -> List[Task]:
        """
        Get all pending tasks.
        
        Returns:
            List of pending tasks
        """
        with self.lock:
            return [t for t in self.tasks.values() if t.status == TaskStatus.PENDING]
    
    def get_completed_tasks(self) -> List[Task]:
        """
        Get all completed tasks.
        
        Returns:
            List of completed tasks
        """
        with self.lock:
            return [t for t in self.tasks.values() if t.status == TaskStatus.COMPLETED]
    
    def get_failed_tasks(self) -> List[Task]:
        """
        Get all failed tasks.
        
        Returns:
            List of failed tasks
        """
        with self.lock:
            return [t for t in self.tasks.values() if t.status == TaskStatus.FAILED]
    
    def _worker_loop(self) -> None:
        """Worker thread main loop."""
        while self.running:
            try:
                # Get task from queue with timeout
                task = self.task_queue.get(timeout=1)
                
                # Check if task is ready to execute
                if task.is_ready_to_execute():
                    try:
                        task.execute()
                    except Exception as e:
                        logger.error(f"Task {task.task_id} execution failed: {str(e)}")
                else:
                    # Task is scheduled for later, put it back in queue
                    self.task_queue.put(task)
                    time.sleep(0.1)
                
                self.task_queue.task_done()
            except queue.Empty:
                # No tasks in queue, continue
                continue
            except Exception as e:
                logger.error(f"Worker thread error: {str(e)}")
    
    def clear_completed_tasks(self, older_than_hours: int = 24) -> int:
        """
        Clear completed tasks older than specified hours.
        
        Args:
            older_than_hours: Remove tasks completed more than this many hours ago
            
        Returns:
            Number of tasks cleared
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=older_than_hours)
        cleared = 0
        
        with self.lock:
            task_ids_to_remove = []
            for task_id, task in self.tasks.items():
                if (task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED] and
                    task.completed_at and task.completed_at < cutoff_time):
                    task_ids_to_remove.append(task_id)
            
            for task_id in task_ids_to_remove:
                del self.tasks[task_id]
                cleared += 1
        
        logger.info(f"Cleared {cleared} completed tasks")
        return cleared


class ScheduledTaskExecutor:
    """Executes tasks on a schedule."""
    
    def __init__(self, task_queue: TaskQueue):
        """
        Initialize scheduled task executor.
        
        Args:
            task_queue: TaskQueue instance to use for execution
        """
        self.task_queue = task_queue
        self.scheduled_tasks: Dict[str, Dict[str, Any]] = {}
        self.running = False
        self.scheduler_thread = None
        self.lock = threading.Lock()
        logger.info("Initializing ScheduledTaskExecutor")
    
    def start(self) -> None:
        """Start the scheduler."""
        if self.running:
            logger.warning("ScheduledTaskExecutor is already running")
            return
        
        self.running = True
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        logger.info("ScheduledTaskExecutor started")
    
    def stop(self) -> None:
        """Stop the scheduler."""
        if not self.running:
            logger.warning("ScheduledTaskExecutor is not running")
            return
        
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        
        logger.info("ScheduledTaskExecutor stopped")
    
    def schedule_task(
        self,
        schedule_id: str,
        func: Callable,
        args: tuple = (),
        kwargs: dict = None,
        interval_seconds: int = 60,
        start_time: Optional[datetime] = None
    ) -> None:
        """
        Schedule a task to run repeatedly.
        
        Args:
            schedule_id: Unique schedule identifier
            func: Callable to execute
            args: Positional arguments
            kwargs: Keyword arguments
            interval_seconds: Interval between executions in seconds
            start_time: Optional start time (defaults to now)
        """
        with self.lock:
            self.scheduled_tasks[schedule_id] = {
                'func': func,
                'args': args,
                'kwargs': kwargs or {},
                'interval_seconds': interval_seconds,
                'last_execution': start_time or datetime.utcnow(),
                'active': True
            }
        
        logger.info(f"Scheduled task {schedule_id} with interval {interval_seconds}s")
    
    def cancel_schedule(self, schedule_id: str) -> bool:
        """
        Cancel a scheduled task.
        
        Args:
            schedule_id: Schedule identifier
            
        Returns:
            True if cancelled, False if not found
        """
        with self.lock:
            if schedule_id in self.scheduled_tasks:
                self.scheduled_tasks[schedule_id]['active'] = False
                logger.info(f"Cancelled schedule {schedule_id}")
                return True
        return False
    
    def _scheduler_loop(self) -> None:
        """Scheduler thread main loop."""
        while self.running:
            try:
                now = datetime.utcnow()
                
                with self.lock:
                    for schedule_id, schedule_info in list(self.scheduled_tasks.items()):
                        if not schedule_info['active']:
                            continue
                        
                        last_execution = schedule_info['last_execution']
                        interval = timedelta(seconds=schedule_info['interval_seconds'])
                        
                        if now >= last_execution + interval:
                            # Time to execute
                            task_id = f"{schedule_id}_{int(time.time() * 1000)}"
                            self.task_queue.submit_task(
                                task_id,
                                schedule_info['func'],
                                schedule_info['args'],
                                schedule_info['kwargs']
                            )
                            schedule_info['last_execution'] = now
                            logger.debug(f"Scheduled task {schedule_id} executed as {task_id}")
                
                time.sleep(1)  # Check every second
            except Exception as e:
                logger.error(f"Scheduler error: {str(e)}")


# Global task queue instance
_task_queue = None
_scheduler = None


def get_task_queue() -> TaskQueue:
    """Get or create the global task queue."""
    global _task_queue
    if _task_queue is None:
        _task_queue = TaskQueue(num_workers=4)
        _task_queue.start()
    return _task_queue


def get_scheduler() -> ScheduledTaskExecutor:
    """Get or create the global scheduler."""
    global _scheduler
    if _scheduler is None:
        _scheduler = ScheduledTaskExecutor(get_task_queue())
        _scheduler.start()
    return _scheduler


def shutdown_async_tasks() -> None:
    """Shutdown all async task processing."""
    global _task_queue, _scheduler
    
    if _scheduler:
        _scheduler.stop()
        _scheduler = None
    
    if _task_queue:
        _task_queue.stop()
        _task_queue = None
    
    logger.info("Async task processing shutdown complete")
