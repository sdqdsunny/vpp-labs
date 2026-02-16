"""
Unit Tests for Asynchronous Task Processing

Tests background task queue and scheduled task execution.
"""

import pytest
import time
from datetime import datetime, timedelta
from utils.async_tasks import (
    Task, TaskStatus, TaskQueue, ScheduledTaskExecutor,
    get_task_queue, get_scheduler, shutdown_async_tasks
)


class TestTask:
    """Test Task class."""
    
    def test_task_creation(self):
        """Test task creation."""
        def dummy_func():
            return "result"
        
        task = Task("task-1", dummy_func)
        
        assert task.task_id == "task-1"
        assert task.status == TaskStatus.PENDING
        assert task.result is None
        assert task.error is None
    
    def test_task_execution_success(self):
        """Test successful task execution."""
        def dummy_func(x, y):
            return x + y
        
        task = Task("task-1", dummy_func, args=(2, 3))
        result = task.execute()
        
        assert result == 5
        assert task.status == TaskStatus.COMPLETED
        assert task.result == 5
        assert task.error is None
    
    def test_task_execution_failure(self):
        """Test failed task execution."""
        def failing_func():
            raise ValueError("Test error")
        
        task = Task("task-1", failing_func)
        
        with pytest.raises(ValueError):
            task.execute()
        
        assert task.status == TaskStatus.FAILED
        assert "Test error" in task.error
    
    def test_task_cancellation(self):
        """Test task cancellation."""
        def dummy_func():
            return "result"
        
        task = Task("task-1", dummy_func)
        task.cancel()
        
        assert task.status == TaskStatus.CANCELLED
    
    def test_task_scheduled_time(self):
        """Test task with scheduled time."""
        def dummy_func():
            return "result"
        
        future_time = datetime.utcnow() + timedelta(seconds=1)
        task = Task("task-1", dummy_func, scheduled_time=future_time)
        
        assert not task.is_ready_to_execute()
        
        time.sleep(1.1)
        assert task.is_ready_to_execute()
    
    def test_task_to_dict(self):
        """Test task serialization."""
        def dummy_func():
            return "result"
        
        task = Task("task-1", dummy_func)
        task.execute()
        
        task_dict = task.to_dict()
        
        assert task_dict["task_id"] == "task-1"
        assert task_dict["status"] == "completed"
        assert task_dict["result"] == "result"


class TestTaskQueue:
    """Test TaskQueue class."""
    
    def test_task_queue_creation(self):
        """Test task queue creation."""
        queue = TaskQueue(num_workers=2)
        
        assert queue.num_workers == 2
        assert not queue.running
    
    def test_task_queue_start_stop(self):
        """Test task queue start and stop."""
        queue = TaskQueue(num_workers=2)
        
        queue.start()
        assert queue.running
        assert len(queue.workers) == 2
        
        queue.stop()
        assert not queue.running
        assert len(queue.workers) == 0
    
    def test_submit_and_execute_task(self):
        """Test submitting and executing a task."""
        queue = TaskQueue(num_workers=1)
        queue.start()
        
        def dummy_func(x):
            return x * 2
        
        task = queue.submit_task("task-1", dummy_func, args=(5,))
        
        # Wait for task to complete
        time.sleep(0.5)
        
        assert task.status == TaskStatus.COMPLETED
        assert task.result == 10
        
        queue.stop()
    
    def test_get_task(self):
        """Test retrieving a task."""
        queue = TaskQueue(num_workers=1)
        queue.start()
        
        def dummy_func():
            return "result"
        
        queue.submit_task("task-1", dummy_func)
        task = queue.get_task("task-1")
        
        assert task is not None
        assert task.task_id == "task-1"
        
        queue.stop()
    
    def test_cancel_task(self):
        """Test cancelling a task."""
        queue = TaskQueue(num_workers=1)
        queue.start()
        
        def dummy_func():
            time.sleep(1)
            return "result"
        
        queue.submit_task("task-1", dummy_func)
        
        # Cancel immediately
        cancelled = queue.cancel_task("task-1")
        assert cancelled
        
        queue.stop()
    
    def test_get_all_tasks(self):
        """Test retrieving all tasks."""
        queue = TaskQueue(num_workers=1)
        queue.start()
        
        def dummy_func():
            return "result"
        
        queue.submit_task("task-1", dummy_func)
        queue.submit_task("task-2", dummy_func)
        
        tasks = queue.get_all_tasks()
        assert len(tasks) >= 2
        
        queue.stop()
    
    def test_get_pending_tasks(self):
        """Test retrieving pending tasks."""
        queue = TaskQueue(num_workers=1)
        queue.start()
        
        def dummy_func():
            time.sleep(0.1)
            return "result"
        
        queue.submit_task("task-1", dummy_func)
        queue.submit_task("task-2", dummy_func)
        
        pending = queue.get_pending_tasks()
        assert len(pending) >= 1
        
        queue.stop()
    
    def test_get_completed_tasks(self):
        """Test retrieving completed tasks."""
        queue = TaskQueue(num_workers=1)
        queue.start()
        
        def dummy_func():
            return "result"
        
        queue.submit_task("task-1", dummy_func)
        
        # Wait for task to complete
        time.sleep(0.5)
        
        completed = queue.get_completed_tasks()
        assert len(completed) >= 1
        
        queue.stop()
    
    def test_get_failed_tasks(self):
        """Test retrieving failed tasks."""
        queue = TaskQueue(num_workers=1)
        queue.start()
        
        def failing_func():
            raise ValueError("Test error")
        
        queue.submit_task("task-1", failing_func)
        
        # Wait for task to fail
        time.sleep(0.5)
        
        failed = queue.get_failed_tasks()
        assert len(failed) >= 1
        
        queue.stop()
    
    def test_clear_completed_tasks(self):
        """Test clearing completed tasks."""
        queue = TaskQueue(num_workers=1)
        queue.start()
        
        def dummy_func():
            return "result"
        
        queue.submit_task("task-1", dummy_func)
        
        # Wait for task to complete
        time.sleep(0.5)
        
        # Clear tasks completed more than 0 hours ago
        cleared = queue.clear_completed_tasks(older_than_hours=0)
        assert cleared >= 1
        
        queue.stop()


class TestScheduledTaskExecutor:
    """Test ScheduledTaskExecutor class."""
    
    def test_scheduler_creation(self):
        """Test scheduler creation."""
        queue = TaskQueue(num_workers=1)
        scheduler = ScheduledTaskExecutor(queue)
        
        assert not scheduler.running
    
    def test_scheduler_start_stop(self):
        """Test scheduler start and stop."""
        queue = TaskQueue(num_workers=1)
        queue.start()
        
        scheduler = ScheduledTaskExecutor(queue)
        scheduler.start()
        
        assert scheduler.running
        
        scheduler.stop()
        assert not scheduler.running
        
        queue.stop()
    
    def test_schedule_task(self):
        """Test scheduling a task."""
        queue = TaskQueue(num_workers=1)
        queue.start()
        
        scheduler = ScheduledTaskExecutor(queue)
        scheduler.start()
        
        call_count = [0]
        
        def dummy_func():
            call_count[0] += 1
        
        scheduler.schedule_task("schedule-1", dummy_func, interval_seconds=1)
        
        # Wait for at least one execution
        time.sleep(2)
        
        assert call_count[0] >= 1
        
        scheduler.stop()
        queue.stop()
    
    def test_cancel_schedule(self):
        """Test cancelling a schedule."""
        queue = TaskQueue(num_workers=1)
        queue.start()
        
        scheduler = ScheduledTaskExecutor(queue)
        scheduler.start()
        
        call_count = [0]
        
        def dummy_func():
            call_count[0] += 1
        
        scheduler.schedule_task("schedule-1", dummy_func, interval_seconds=1)
        
        # Wait for first execution
        time.sleep(1.5)
        first_count = call_count[0]
        
        # Cancel schedule
        cancelled = scheduler.cancel_schedule("schedule-1")
        assert cancelled
        
        # Wait to ensure no more executions
        time.sleep(1.5)
        
        assert call_count[0] == first_count
        
        scheduler.stop()
        queue.stop()
    
    def test_multiple_scheduled_tasks(self):
        """Test multiple scheduled tasks."""
        queue = TaskQueue(num_workers=2)
        queue.start()
        
        scheduler = ScheduledTaskExecutor(queue)
        scheduler.start()
        
        call_counts = [0, 0]
        
        def dummy_func_1():
            call_counts[0] += 1
        
        def dummy_func_2():
            call_counts[1] += 1
        
        scheduler.schedule_task("schedule-1", dummy_func_1, interval_seconds=1)
        scheduler.schedule_task("schedule-2", dummy_func_2, interval_seconds=1)
        
        # Wait for executions
        time.sleep(2)
        
        assert call_counts[0] >= 1
        assert call_counts[1] >= 1
        
        scheduler.stop()
        queue.stop()


class TestGlobalInstances:
    """Test global task queue and scheduler instances."""
    
    def test_get_task_queue(self):
        """Test getting global task queue."""
        queue = get_task_queue()
        
        assert queue is not None
        assert queue.running
        
        shutdown_async_tasks()
    
    def test_get_scheduler(self):
        """Test getting global scheduler."""
        scheduler = get_scheduler()
        
        assert scheduler is not None
        assert scheduler.running
        
        shutdown_async_tasks()
    
    def test_submit_task_to_global_queue(self):
        """Test submitting task to global queue."""
        queue = get_task_queue()
        
        def dummy_func(x):
            return x * 2
        
        task = queue.submit_task("task-1", dummy_func, args=(5,))
        
        # Wait for execution
        time.sleep(0.5)
        
        assert task.status == TaskStatus.COMPLETED
        assert task.result == 10
        
        shutdown_async_tasks()
    
    def test_schedule_task_on_global_scheduler(self):
        """Test scheduling task on global scheduler."""
        scheduler = get_scheduler()
        
        call_count = [0]
        
        def dummy_func():
            call_count[0] += 1
        
        scheduler.schedule_task("schedule-1", dummy_func, interval_seconds=1)
        
        # Wait for execution
        time.sleep(2)
        
        assert call_count[0] >= 1
        
        shutdown_async_tasks()
