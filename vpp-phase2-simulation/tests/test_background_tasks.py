"""
Unit tests for Background Task Service.

Tests:
- Background task service initialization
- Coordination task scheduling
- Data cleanup task scheduling
- Task execution and callbacks
- Task statistics
- Error handling
"""

import pytest
import time
from datetime import datetime

from services.background_tasks import BackgroundTaskService


class TestBackgroundTaskServiceInitialization:
    """Test background task service initialization."""

    def test_service_initialization(self):
        """Test that service initializes correctly."""
        service = BackgroundTaskService()
        
        assert service.is_running is False
        assert service.coordination_count == 0
        assert service.cleanup_count == 0
        assert service.last_coordination_time is None
        assert service.last_cleanup_time is None
        assert service.coordination_task_id is None
        assert service.cleanup_task_id is None

    def test_service_stats_on_init(self):
        """Test that stats are correct on initialization."""
        service = BackgroundTaskService()
        stats = service.get_stats()
        
        assert stats['is_running'] is False
        assert stats['coordination_count'] == 0
        assert stats['cleanup_count'] == 0
        assert stats['active_jobs'] == 0


class TestSchedulerStartStop:
    """Test scheduler start and stop."""

    def test_start_scheduler(self):
        """Test starting the scheduler."""
        service = BackgroundTaskService()
        service.start()
        
        assert service.is_running is True
        
        # Cleanup
        service.stop()

    def test_stop_scheduler(self):
        """Test stopping the scheduler."""
        service = BackgroundTaskService()
        service.start()
        assert service.is_running is True
        
        service.stop()
        assert service.is_running is False

    def test_start_already_running_scheduler(self):
        """Test starting an already running scheduler."""
        service = BackgroundTaskService()
        service.start()
        
        # Should not raise
        service.start()
        
        assert service.is_running is True
        
        # Cleanup
        service.stop()

    def test_stop_not_running_scheduler(self):
        """Test stopping a scheduler that is not running."""
        service = BackgroundTaskService()
        
        # Should not raise
        service.stop()
        
        assert service.is_running is False


class TestCoordinationTask:
    """Test coordination task."""

    def test_start_coordination_task(self):
        """Test starting coordination task."""
        service = BackgroundTaskService()
        service.start()
        
        service.start_coordination_task(interval_seconds=1)
        
        assert service.coordination_task_id is not None
        
        # Cleanup
        service.stop()

    def test_stop_coordination_task(self):
        """Test stopping coordination task."""
        service = BackgroundTaskService()
        service.start()
        service.start_coordination_task(interval_seconds=1)
        
        assert service.coordination_task_id is not None
        
        service.stop_coordination_task()
        
        assert service.coordination_task_id is None
        
        # Cleanup
        service.stop()

    def test_coordination_task_execution(self):
        """Test coordination task execution."""
        service = BackgroundTaskService()
        service.start()
        
        # Set callback
        callback_count = [0]
        def coordination_callback():
            callback_count[0] += 1
        
        service.set_coordination_callback(coordination_callback)
        service.start_coordination_task(interval_seconds=1)
        
        # Wait for task to execute
        time.sleep(2)
        
        assert service.coordination_count > 0
        assert callback_count[0] > 0
        assert service.last_coordination_time is not None
        
        # Cleanup
        service.stop()

    def test_coordination_task_with_custom_interval(self):
        """Test coordination task with custom interval."""
        service = BackgroundTaskService()
        service.start()
        
        service.start_coordination_task(interval_seconds=2)
        
        stats = service.get_stats()
        assert stats['active_jobs'] > 0
        
        # Cleanup
        service.stop()

    def test_pause_resume_coordination_task(self):
        """Test pausing and resuming coordination task."""
        service = BackgroundTaskService()
        service.start()
        
        callback_count = [0]
        def coordination_callback():
            callback_count[0] += 1
        
        service.set_coordination_callback(coordination_callback)
        service.start_coordination_task(interval_seconds=1)
        
        # Wait for initial execution
        time.sleep(1.5)
        initial_count = callback_count[0]
        
        # Pause task
        service.pause_coordination_task()
        
        # Wait and check that callback is not called
        time.sleep(1.5)
        paused_count = callback_count[0]
        
        # Resume task
        service.resume_coordination_task()
        
        # Wait for execution
        time.sleep(1.5)
        resumed_count = callback_count[0]
        
        assert resumed_count > paused_count
        
        # Cleanup
        service.stop()


class TestCleanupTask:
    """Test cleanup task."""

    def test_start_cleanup_task(self):
        """Test starting cleanup task."""
        service = BackgroundTaskService()
        service.start()
        
        service.start_data_cleanup_task(interval_seconds=1)
        
        assert service.cleanup_task_id is not None
        
        # Cleanup
        service.stop()

    def test_stop_cleanup_task(self):
        """Test stopping cleanup task."""
        service = BackgroundTaskService()
        service.start()
        service.start_data_cleanup_task(interval_seconds=1)
        
        assert service.cleanup_task_id is not None
        
        service.stop_data_cleanup_task()
        
        assert service.cleanup_task_id is None
        
        # Cleanup
        service.stop()

    def test_cleanup_task_execution(self):
        """Test cleanup task execution."""
        service = BackgroundTaskService()
        service.start()
        
        # Set callback
        callback_count = [0]
        def cleanup_callback():
            callback_count[0] += 1
        
        service.set_cleanup_callback(cleanup_callback)
        service.start_data_cleanup_task(interval_seconds=1)
        
        # Wait for task to execute
        time.sleep(2)
        
        assert service.cleanup_count > 0
        assert callback_count[0] > 0
        assert service.last_cleanup_time is not None
        
        # Cleanup
        service.stop()

    def test_cleanup_task_with_custom_interval(self):
        """Test cleanup task with custom interval."""
        service = BackgroundTaskService()
        service.start()
        
        service.start_data_cleanup_task(interval_seconds=2)
        
        stats = service.get_stats()
        assert stats['active_jobs'] > 0
        
        # Cleanup
        service.stop()

    def test_pause_resume_cleanup_task(self):
        """Test pausing and resuming cleanup task."""
        service = BackgroundTaskService()
        service.start()
        
        callback_count = [0]
        def cleanup_callback():
            callback_count[0] += 1
        
        service.set_cleanup_callback(cleanup_callback)
        service.start_data_cleanup_task(interval_seconds=1)
        
        # Wait for initial execution
        time.sleep(1.5)
        initial_count = callback_count[0]
        
        # Pause task
        service.pause_cleanup_task()
        
        # Wait and check that callback is not called
        time.sleep(1.5)
        paused_count = callback_count[0]
        
        # Resume task
        service.resume_cleanup_task()
        
        # Wait for execution
        time.sleep(1.5)
        resumed_count = callback_count[0]
        
        assert resumed_count > paused_count
        
        # Cleanup
        service.stop()


class TestMultipleTasks:
    """Test multiple tasks running together."""

    def test_coordination_and_cleanup_tasks(self):
        """Test coordination and cleanup tasks running together."""
        service = BackgroundTaskService()
        service.start()
        
        coord_count = [0]
        cleanup_count = [0]
        
        def coordination_callback():
            coord_count[0] += 1
        
        def cleanup_callback():
            cleanup_count[0] += 1
        
        service.set_coordination_callback(coordination_callback)
        service.set_cleanup_callback(cleanup_callback)
        
        service.start_coordination_task(interval_seconds=1)
        service.start_data_cleanup_task(interval_seconds=2)
        
        # Wait for tasks to execute
        time.sleep(3)
        
        assert service.coordination_count > 0
        assert service.cleanup_count > 0
        assert coord_count[0] > 0
        assert cleanup_count[0] > 0
        
        stats = service.get_stats()
        assert stats['active_jobs'] == 2
        
        # Cleanup
        service.stop()

    def test_restart_tasks(self):
        """Test restarting tasks."""
        service = BackgroundTaskService()
        service.start()
        
        callback_count = [0]
        def coordination_callback():
            callback_count[0] += 1
        
        service.set_coordination_callback(coordination_callback)
        service.start_coordination_task(interval_seconds=1)
        
        # Wait for execution
        time.sleep(1.5)
        first_count = callback_count[0]
        
        # Stop and restart
        service.stop_coordination_task()
        service.start_coordination_task(interval_seconds=1)
        
        # Wait for execution
        time.sleep(1.5)
        second_count = callback_count[0]
        
        assert second_count > first_count
        
        # Cleanup
        service.stop()


class TestTaskStatistics:
    """Test task statistics."""

    def test_stats_with_running_tasks(self):
        """Test statistics with running tasks."""
        service = BackgroundTaskService()
        service.start()
        
        service.start_coordination_task(interval_seconds=1)
        service.start_data_cleanup_task(interval_seconds=2)
        
        # Wait for tasks to execute
        time.sleep(2)
        
        stats = service.get_stats()
        
        assert stats['is_running'] is True
        assert stats['coordination_count'] > 0
        assert stats['active_jobs'] == 2
        assert stats['last_coordination_time'] is not None
        
        # Cleanup
        service.stop()

    def test_get_job_status(self):
        """Test getting job status."""
        service = BackgroundTaskService()
        service.start()
        
        service.start_coordination_task(interval_seconds=1)
        
        job_status = service.get_job_status('coordination_task')
        
        assert job_status is not None
        assert job_status['id'] == 'coordination_task'
        assert job_status['name'] == 'VCC Coordination Task'
        assert job_status['next_run_time'] is not None
        
        # Cleanup
        service.stop()

    def test_get_nonexistent_job_status(self):
        """Test getting status of nonexistent job."""
        service = BackgroundTaskService()
        service.start()
        
        job_status = service.get_job_status('nonexistent_job')
        
        assert job_status is None
        
        # Cleanup
        service.stop()


class TestCallbacks:
    """Test callback functionality."""

    def test_set_coordination_callback(self):
        """Test setting coordination callback."""
        service = BackgroundTaskService()
        
        def callback():
            pass
        
        service.set_coordination_callback(callback)
        
        assert service.coordination_callback is not None

    def test_set_cleanup_callback(self):
        """Test setting cleanup callback."""
        service = BackgroundTaskService()
        
        def callback():
            pass
        
        service.set_cleanup_callback(callback)
        
        assert service.cleanup_callback is not None

    def test_callback_with_exception(self):
        """Test callback that raises exception."""
        service = BackgroundTaskService()
        service.start()
        
        def failing_callback():
            raise Exception("Test exception")
        
        service.set_coordination_callback(failing_callback)
        service.start_coordination_task(interval_seconds=1)
        
        # Wait for task to execute
        time.sleep(2)
        
        # Should not crash, just log error
        assert service.coordination_count > 0
        
        # Cleanup
        service.stop()


class TestErrorHandling:
    """Test error handling."""

    def test_start_coordination_task_without_scheduler(self):
        """Test starting coordination task without starting scheduler first."""
        service = BackgroundTaskService()
        
        # Should start scheduler automatically
        service.start_coordination_task(interval_seconds=1)
        
        assert service.is_running is True
        assert service.coordination_task_id is not None
        
        # Cleanup
        service.stop()

    def test_start_cleanup_task_without_scheduler(self):
        """Test starting cleanup task without starting scheduler first."""
        service = BackgroundTaskService()
        
        # Should start scheduler automatically
        service.start_data_cleanup_task(interval_seconds=1)
        
        assert service.is_running is True
        assert service.cleanup_task_id is not None
        
        # Cleanup
        service.stop()

    def test_pause_nonexistent_task(self):
        """Test pausing nonexistent task."""
        service = BackgroundTaskService()
        service.start()
        
        # Should not raise
        service.pause_coordination_task()
        
        # Cleanup
        service.stop()

    def test_resume_nonexistent_task(self):
        """Test resuming nonexistent task."""
        service = BackgroundTaskService()
        service.start()
        
        # Should not raise
        service.resume_coordination_task()
        
        # Cleanup
        service.stop()


class TestTaskReplacement:
    """Test task replacement."""

    def test_replace_coordination_task(self):
        """Test replacing coordination task."""
        service = BackgroundTaskService()
        service.start()
        
        callback_count = [0]
        def coordination_callback():
            callback_count[0] += 1
        
        service.set_coordination_callback(coordination_callback)
        
        # Start first task
        service.start_coordination_task(interval_seconds=1)
        first_task_id = service.coordination_task_id
        
        # Wait for execution
        time.sleep(1.5)
        first_count = callback_count[0]
        
        # Start second task (should replace first)
        service.start_coordination_task(interval_seconds=2)
        second_task_id = service.coordination_task_id
        
        # Task ID should be the same (replaced)
        assert first_task_id == second_task_id
        
        # Cleanup
        service.stop()

    def test_replace_cleanup_task(self):
        """Test replacing cleanup task."""
        service = BackgroundTaskService()
        service.start()
        
        callback_count = [0]
        def cleanup_callback():
            callback_count[0] += 1
        
        service.set_cleanup_callback(cleanup_callback)
        
        # Start first task
        service.start_data_cleanup_task(interval_seconds=1)
        first_task_id = service.cleanup_task_id
        
        # Start second task (should replace first)
        service.start_data_cleanup_task(interval_seconds=2)
        second_task_id = service.cleanup_task_id
        
        # Task ID should be the same (replaced)
        assert first_task_id == second_task_id
        
        # Cleanup
        service.stop()
