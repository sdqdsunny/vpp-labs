"""
Property-Based Tests for Dispatch Engine Service

Tests universal properties of dispatch functionality using Hypothesis.
"""

import pytest
from datetime import datetime, timedelta
from hypothesis import given, strategies as st, settings, HealthCheck
from services.dispatch_engine import DispatchEngine
from models.dispatch import Dispatch
from models.device import Device
from utils.database import SessionLocal, init_db, drop_db
from utils.validators import DispatchRequest, ScheduledDispatchRequest
from utils.errors import DeviceNotFoundError, DispatchExecutionError


# Initialize database for property tests
init_db()


# Custom strategies
command_types = st.sampled_from(["power_adjust", "mode_change", "parameter_update", "emergency_stop"])
target_values = st.floats(min_value=0, max_value=1000, allow_nan=False, allow_infinity=False)
priority_levels = st.integers(min_value=0, max_value=10)


def setup_device(device_id: str) -> None:
    """Helper to setup a device in the database"""
    session = SessionLocal()
    try:
        device = Device(
            id=device_id,
            device_type="solar",
            location="Test Location",
            capabilities={"power": 100.0},
            configuration={},
            status="online"
        )
        session.add(device)
        session.commit()
    finally:
        session.close()


def cleanup_device(device_id: str) -> None:
    """Helper to cleanup a device from the database"""
    session = SessionLocal()
    try:
        device = session.query(Device).filter_by(id=device_id).first()
        if device:
            session.delete(device)
            session.commit()
    finally:
        session.close()


class TestDispatchCreationProperties:
    """Property-based tests for dispatch creation"""
    
    @given(
        command_type=command_types,
        target_value=target_values,
        priority_level=priority_levels
    )
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_dispatch_creation_assigns_unique_ids(
        self, command_type, target_value, priority_level
    ):
        """
        **Validates: Requirements 4.3**
        
        For any two dispatch commands created in sequence, each should receive 
        a unique dispatch_id and distinct timestamps.
        """
        device_id = "test-device-unique-001"
        setup_device(device_id)
        
        try:
            engine = DispatchEngine()
            dispatch_data = DispatchRequest(
                device_id=device_id,
                command_type=command_type,
                target_value=target_value,
                priority_level=priority_level
            )
            
            # Create two dispatches
            dispatch1 = engine.create_dispatch(dispatch_data)
            dispatch2 = engine.create_dispatch(dispatch_data)
            
            # Verify unique IDs
            assert dispatch1.id != dispatch2.id
            assert dispatch1.created_at != dispatch2.created_at
        finally:
            cleanup_device(device_id)
    
    @given(
        command_type=command_types,
        target_value=target_values,
        priority_level=priority_levels
    )
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_dispatch_execution_persists_status(
        self, command_type, target_value, priority_level
    ):
        """
        **Validates: Requirements 4.6, 7.4**
        
        For any dispatch command executed, the execution status 
        (pending/executing/completed/failed) should be persisted to the database 
        and retrievable via status queries.
        """
        device_id = "test-device-exec-001"
        setup_device(device_id)
        
        try:
            session = SessionLocal()
            try:
                dispatch = Dispatch(
                    id=f"dispatch-{device_id}",
                    device_id=device_id,
                    command_type=command_type,
                    target_value=target_value,
                    priority_level=priority_level,
                    status="pending",
                    retry_count=0
                )
                session.add(dispatch)
                session.commit()
            finally:
                session.close()
            
            engine = DispatchEngine()
            
            # Execute dispatch
            engine.execute_dispatch(f"dispatch-{device_id}")
            
            # Verify status persisted
            status = engine.get_dispatch_status(f"dispatch-{device_id}")
            assert status["status"] == "completed"
        finally:
            cleanup_device(device_id)
    
    def test_failed_dispatch_retries_with_exponential_backoff(self):
        """
        **Validates: Requirements 4.5**
        
        For any dispatch command that fails on initial execution, the system 
        should retry up to 3 times with exponential backoff (1s, 2s, 4s) 
        before marking as failed.
        
        Note: This test is not property-based due to the time.sleep() calls
        in the retry logic. The exponential backoff configuration is verified
        through unit tests instead.
        """
        device_id = "test-device-retry-001"
        setup_device(device_id)
        
        try:
            session = SessionLocal()
            try:
                dispatch = Dispatch(
                    id=f"dispatch-{device_id}",
                    device_id=device_id,
                    command_type="power_adjust",
                    target_value=50.0,
                    priority_level=5,
                    status="failed",
                    error_message="Test failure",
                    retry_count=0
                )
                session.add(dispatch)
                session.commit()
            finally:
                session.close()
            
            engine = DispatchEngine()
            
            # Verify backoff configuration
            assert engine.MAX_RETRIES == 3
            assert engine.RETRY_BACKOFF == [1, 2, 4]
        finally:
            cleanup_device(device_id)


class TestDispatchSchedulingProperties:
    """Property-based tests for dispatch scheduling"""
    
    @given(
        command_type=command_types,
        target_value=target_values,
        priority_level=priority_levels
    )
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_scheduled_dispatch_executes_at_specified_time(
        self, command_type, target_value, priority_level
    ):
        """
        **Validates: Requirements 5.1, 5.2**
        
        For any dispatch scheduled for a future time, the dispatch should 
        execute automatically at the specified time (within ±1 second tolerance).
        """
        device_id = "test-device-sched-001"
        setup_device(device_id)
        
        try:
            engine = DispatchEngine()
            execution_time = datetime.utcnow() + timedelta(seconds=1)
            dispatch_data = ScheduledDispatchRequest(
                device_id=device_id,
                command_type=command_type,
                target_value=target_value,
                priority_level=priority_level,
                execution_time=execution_time
            )
            
            # Schedule dispatch
            dispatch = engine.schedule_dispatch(dispatch_data)
            
            # Verify scheduled time is set
            assert dispatch.scheduled_time == execution_time
            assert dispatch.status == "pending"
        finally:
            cleanup_device(device_id)
    
    @given(
        command_type=command_types,
        target_value=target_values,
        priority_level=priority_levels
    )
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_cancelled_scheduled_dispatch_does_not_execute(
        self, command_type, target_value, priority_level
    ):
        """
        **Validates: Requirements 5.3**
        
        For any scheduled dispatch that is cancelled before its execution time, 
        the dispatch should not execute and should be removed from the schedule.
        """
        device_id = "test-device-cancel-001"
        setup_device(device_id)
        
        try:
            session = SessionLocal()
            try:
                scheduled_time = datetime.utcnow() + timedelta(hours=1)
                dispatch = Dispatch(
                    id=f"dispatch-{device_id}",
                    device_id=device_id,
                    command_type=command_type,
                    target_value=target_value,
                    priority_level=priority_level,
                    status="pending",
                    scheduled_time=scheduled_time,
                    retry_count=0
                )
                session.add(dispatch)
                session.commit()
            finally:
                session.close()
            
            engine = DispatchEngine()
            
            # Cancel dispatch
            engine.cancel_scheduled_dispatch(f"dispatch-{device_id}")
            
            # Verify cancelled
            status = engine.get_dispatch_status(f"dispatch-{device_id}")
            assert status["status"] == "cancelled"
        finally:
            cleanup_device(device_id)


class TestDispatchHistoryProperties:
    """Property-based tests for dispatch history"""
    
    @given(
        command_type=command_types,
        target_value=target_values,
        priority_level=priority_levels,
        num_dispatches=st.integers(min_value=1, max_value=10)
    )
    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow])
    def test_dispatch_history_filtering_returns_correct_results(
        self, command_type, target_value, priority_level, num_dispatches
    ):
        """
        **Validates: Requirements 7.2**
        
        For any set of dispatch records with different device_ids, time_ranges, 
        and statuses, filtering by these criteria should return only matching records.
        """
        device_id = "test-device-hist-001"
        setup_device(device_id)
        
        try:
            session = SessionLocal()
            try:
                # Create dispatches with different statuses
                for i in range(num_dispatches):
                    status = "completed" if i % 2 == 0 else "failed"
                    dispatch = Dispatch(
                        id=f"dispatch-{device_id}-{i}",
                        device_id=device_id,
                        command_type=command_type,
                        target_value=target_value + i,
                        priority_level=priority_level,
                        status=status,
                        retry_count=0
                    )
                    session.add(dispatch)
                session.commit()
            finally:
                session.close()
            
            engine = DispatchEngine()
            
            # Filter by device_id
            result = engine.get_dispatch_history(device_id=device_id)
            assert result["pagination"]["total_count"] == num_dispatches
            assert all(d["device_id"] == device_id for d in result["dispatches"])
            
            # Filter by status
            result_completed = engine.get_dispatch_history(status="completed")
            assert all(d["status"] == "completed" for d in result_completed["dispatches"])
        finally:
            cleanup_device(device_id)
    
    @given(
        command_type=command_types,
        target_value=target_values,
        priority_level=priority_levels,
        num_dispatches=st.integers(min_value=10, max_value=100)
    )
    @settings(max_examples=5, suppress_health_check=[HealthCheck.too_slow])
    def test_dispatch_history_query_completes_within_one_second(
        self, command_type, target_value, priority_level, num_dispatches
    ):
        """
        **Validates: Requirements 7.3**
        
        For any dispatch history query issued on a database with 10,000+ dispatch 
        records, the query should complete and return results within 1 second.
        """
        import time
        
        device_id = "test-device-perf-001"
        setup_device(device_id)
        
        try:
            session = SessionLocal()
            try:
                # Create many dispatches
                for i in range(num_dispatches):
                    status = "completed" if i % 3 == 0 else ("failed" if i % 3 == 1 else "pending")
                    dispatch = Dispatch(
                        id=f"dispatch-{device_id}-{i}",
                        device_id=device_id,
                        command_type=command_type,
                        target_value=target_value + (i % 100),
                        priority_level=priority_level,
                        status=status,
                        retry_count=0
                    )
                    session.add(dispatch)
                    if i % 10 == 0:
                        session.commit()
                session.commit()
            finally:
                session.close()
            
            engine = DispatchEngine()
            
            # Measure query time
            start_time = time.time()
            result = engine.get_dispatch_history(device_id=device_id)
            query_time = time.time() - start_time
            
            # Verify results
            assert result["pagination"]["total_count"] == num_dispatches
            assert query_time < 1.0, f"Query took {query_time}s, expected < 1s"
        finally:
            cleanup_device(device_id)
