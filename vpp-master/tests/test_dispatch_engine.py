"""
Unit Tests for Dispatch Engine Service

Tests dispatch creation, execution, scheduling, and tracking functionality.
"""

import pytest
from datetime import datetime, timedelta
from services.dispatch_engine import DispatchEngine
from models.dispatch import Dispatch
from models.device import Device
from utils.validators import DispatchRequest, ScheduledDispatchRequest
from utils.errors import (
    DeviceNotFoundError, DispatchExecutionError, DatabaseError
)


class TestDispatchCreation:
    """Tests for dispatch creation"""
    
    def test_create_dispatch_success(self, db_session):
        """Test successful dispatch creation"""
        # Setup
        device = Device(
            id="test-device-001",
            device_type="solar",
            location="Test Location",
            capabilities={"power": 100.0},
            configuration={},
            status="online"
        )
        db_session.add(device)
        db_session.commit()
        
        engine = DispatchEngine()
        dispatch_data = DispatchRequest(
            device_id="test-device-001",
            command_type="power_adjust",
            target_value=50.0,
            priority_level=5
        )
        
        # Execute
        dispatch = engine.create_dispatch(dispatch_data)
        
        # Verify
        assert dispatch.id is not None
        assert dispatch.device_id == "test-device-001"
        assert dispatch.command_type == "power_adjust"
        assert dispatch.target_value == 50.0
        assert dispatch.priority_level == 5
        assert dispatch.status == "pending"
        assert dispatch.retry_count == 0
    
    def test_create_dispatch_device_not_found(self, db_session):
        """Test dispatch creation with non-existent device"""
        engine = DispatchEngine()
        dispatch_data = DispatchRequest(
            device_id="non-existent-device",
            command_type="power_adjust",
            target_value=50.0,
            priority_level=5
        )
        
        with pytest.raises(DeviceNotFoundError):
            engine.create_dispatch(dispatch_data)
    
    def test_create_dispatch_device_offline(self, db_session):
        """Test dispatch creation with offline device"""
        # Setup
        device = Device(
            id="test-device-001",
            device_type="solar",
            location="Test Location",
            capabilities={"power": 100.0},
            configuration={},
            status="offline"
        )
        db_session.add(device)
        db_session.commit()
        
        engine = DispatchEngine()
        dispatch_data = DispatchRequest(
            device_id="test-device-001",
            command_type="power_adjust",
            target_value=50.0,
            priority_level=5
        )
        
        with pytest.raises(DispatchExecutionError):
            engine.create_dispatch(dispatch_data)
    
    def test_create_dispatch_persists_to_database(self, db_session):
        """Test that created dispatch is persisted to database"""
        # Setup
        device = Device(
            id="test-device-001",
            device_type="solar",
            location="Test Location",
            capabilities={"power": 100.0},
            configuration={},
            status="online"
        )
        db_session.add(device)
        db_session.commit()
        
        engine = DispatchEngine()
        dispatch_data = DispatchRequest(
            device_id="test-device-001",
            command_type="power_adjust",
            target_value=50.0,
            priority_level=5
        )
        
        # Execute
        dispatch = engine.create_dispatch(dispatch_data)
        dispatch_id = dispatch.id
        
        # Verify persistence
        retrieved = db_session.query(Dispatch).filter_by(id=dispatch_id).first()
        assert retrieved is not None
        assert retrieved.device_id == "test-device-001"
        assert retrieved.command_type == "power_adjust"


class TestDispatchExecution:
    """Tests for dispatch execution"""
    
    def test_execute_dispatch_success(self, db_session):
        """Test successful dispatch execution"""
        # Setup
        device = Device(
            id="test-device-001",
            device_type="solar",
            location="Test Location",
            capabilities={"power": 100.0},
            configuration={},
            status="online"
        )
        db_session.add(device)
        
        dispatch = Dispatch(
            id="test-dispatch-001",
            device_id="test-device-001",
            command_type="power_adjust",
            target_value=50.0,
            priority_level=5,
            status="pending",
            retry_count=0
        )
        db_session.add(dispatch)
        db_session.commit()
        
        engine = DispatchEngine()
        
        # Execute
        result = engine.execute_dispatch("test-dispatch-001")
        
        # Verify
        assert result["status"] == "success"
        assert result["target_value"] == 50.0
        
        # Verify dispatch status updated
        updated = db_session.query(Dispatch).filter_by(id="test-dispatch-001").first()
        assert updated.status == "completed"
        assert updated.execution_time is not None
    
    def test_execute_dispatch_not_found(self, db_session):
        """Test execution of non-existent dispatch"""
        engine = DispatchEngine()
        
        with pytest.raises(DeviceNotFoundError):
            engine.execute_dispatch("non-existent-dispatch")
    
    def test_execute_dispatch_updates_status(self, db_session):
        """Test that execution updates dispatch status"""
        # Setup
        device = Device(
            id="test-device-001",
            device_type="solar",
            location="Test Location",
            capabilities={"power": 100.0},
            configuration={},
            status="online"
        )
        db_session.add(device)
        
        dispatch = Dispatch(
            id="test-dispatch-001",
            device_id="test-device-001",
            command_type="power_adjust",
            target_value=50.0,
            priority_level=5,
            status="pending",
            retry_count=0
        )
        db_session.add(dispatch)
        db_session.commit()
        
        engine = DispatchEngine()
        
        # Execute
        engine.execute_dispatch("test-dispatch-001")
        
        # Verify status progression
        updated = db_session.query(Dispatch).filter_by(id="test-dispatch-001").first()
        assert updated.status == "completed"


class TestDispatchScheduling:
    """Tests for dispatch scheduling"""
    
    def test_schedule_dispatch_success(self, db_session):
        """Test successful dispatch scheduling"""
        # Setup
        device = Device(
            id="test-device-001",
            device_type="solar",
            location="Test Location",
            capabilities={"power": 100.0},
            configuration={},
            status="online"
        )
        db_session.add(device)
        db_session.commit()
        
        engine = DispatchEngine()
        execution_time = datetime.utcnow() + timedelta(hours=1)
        dispatch_data = ScheduledDispatchRequest(
            device_id="test-device-001",
            command_type="power_adjust",
            target_value=50.0,
            priority_level=5,
            execution_time=execution_time
        )
        
        # Execute
        dispatch = engine.schedule_dispatch(dispatch_data)
        
        # Verify
        assert dispatch.id is not None
        assert dispatch.device_id == "test-device-001"
        assert dispatch.status == "pending"
        assert dispatch.scheduled_time == execution_time
    
    def test_schedule_dispatch_device_not_found(self, db_session):
        """Test scheduling with non-existent device"""
        engine = DispatchEngine()
        execution_time = datetime.utcnow() + timedelta(hours=1)
        dispatch_data = ScheduledDispatchRequest(
            device_id="non-existent-device",
            command_type="power_adjust",
            target_value=50.0,
            priority_level=5,
            execution_time=execution_time
        )
        
        with pytest.raises(DeviceNotFoundError):
            engine.schedule_dispatch(dispatch_data)
    
    def test_schedule_dispatch_persists_scheduled_time(self, db_session):
        """Test that scheduled time is persisted"""
        # Setup
        device = Device(
            id="test-device-001",
            device_type="solar",
            location="Test Location",
            capabilities={"power": 100.0},
            configuration={},
            status="online"
        )
        db_session.add(device)
        db_session.commit()
        
        engine = DispatchEngine()
        execution_time = datetime.utcnow() + timedelta(hours=1)
        dispatch_data = ScheduledDispatchRequest(
            device_id="test-device-001",
            command_type="power_adjust",
            target_value=50.0,
            priority_level=5,
            execution_time=execution_time
        )
        
        # Execute
        dispatch = engine.schedule_dispatch(dispatch_data)
        dispatch_id = dispatch.id
        
        # Verify persistence
        retrieved = db_session.query(Dispatch).filter_by(id=dispatch_id).first()
        assert retrieved.scheduled_time == execution_time


class TestDispatchStatus:
    """Tests for dispatch status tracking"""
    
    def test_get_dispatch_status_success(self, db_session):
        """Test successful status retrieval"""
        # Setup
        device = Device(
            id="test-device-001",
            device_type="solar",
            location="Test Location",
            capabilities={"power": 100.0},
            configuration={},
            status="online"
        )
        db_session.add(device)
        
        dispatch = Dispatch(
            id="test-dispatch-001",
            device_id="test-device-001",
            command_type="power_adjust",
            target_value=50.0,
            priority_level=5,
            status="pending",
            retry_count=0
        )
        db_session.add(dispatch)
        db_session.commit()
        
        engine = DispatchEngine()
        
        # Execute
        status = engine.get_dispatch_status("test-dispatch-001")
        
        # Verify
        assert status["dispatch_id"] == "test-dispatch-001"
        assert status["status"] == "pending"
        assert status["retry_count"] == 0
    
    def test_get_dispatch_status_not_found(self, db_session):
        """Test status retrieval for non-existent dispatch"""
        engine = DispatchEngine()
        
        with pytest.raises(DeviceNotFoundError):
            engine.get_dispatch_status("non-existent-dispatch")


class TestDispatchHistory:
    """Tests for dispatch history queries"""
    
    def test_get_dispatch_history_all(self, db_session):
        """Test retrieving all dispatch history"""
        # Setup
        device = Device(
            id="test-device-001",
            device_type="solar",
            location="Test Location",
            capabilities={"power": 100.0},
            configuration={},
            status="online"
        )
        db_session.add(device)
        
        for i in range(5):
            dispatch = Dispatch(
                id=f"test-dispatch-{i:03d}",
                device_id="test-device-001",
                command_type="power_adjust",
                target_value=50.0 + i,
                priority_level=5,
                status="completed",
                retry_count=0
            )
            db_session.add(dispatch)
        db_session.commit()
        
        engine = DispatchEngine()
        
        # Execute
        result = engine.get_dispatch_history()
        
        # Verify
        assert result["pagination"]["total_count"] == 5
        assert len(result["dispatches"]) == 5
    
    def test_get_dispatch_history_filter_by_device(self, db_session):
        """Test filtering history by device ID"""
        # Setup
        device1 = Device(
            id="test-device-001",
            device_type="solar",
            location="Test Location 1",
            capabilities={"power": 100.0},
            configuration={},
            status="online"
        )
        device2 = Device(
            id="test-device-002",
            device_type="wind",
            location="Test Location 2",
            capabilities={"power": 200.0},
            configuration={},
            status="online"
        )
        db_session.add(device1)
        db_session.add(device2)
        
        for i in range(3):
            dispatch = Dispatch(
                id=f"test-dispatch-dev1-{i:03d}",
                device_id="test-device-001",
                command_type="power_adjust",
                target_value=50.0,
                priority_level=5,
                status="completed",
                retry_count=0
            )
            db_session.add(dispatch)
        
        for i in range(2):
            dispatch = Dispatch(
                id=f"test-dispatch-dev2-{i:03d}",
                device_id="test-device-002",
                command_type="power_adjust",
                target_value=100.0,
                priority_level=5,
                status="completed",
                retry_count=0
            )
            db_session.add(dispatch)
        db_session.commit()
        
        engine = DispatchEngine()
        
        # Execute
        result = engine.get_dispatch_history(device_id="test-device-001")
        
        # Verify
        assert result["pagination"]["total_count"] == 3
        assert len(result["dispatches"]) == 3
        assert all(d["device_id"] == "test-device-001" for d in result["dispatches"])
    
    def test_get_dispatch_history_filter_by_status(self, db_session):
        """Test filtering history by status"""
        # Setup
        device = Device(
            id="test-device-001",
            device_type="solar",
            location="Test Location",
            capabilities={"power": 100.0},
            configuration={},
            status="online"
        )
        db_session.add(device)
        
        for i in range(3):
            dispatch = Dispatch(
                id=f"test-dispatch-completed-{i:03d}",
                device_id="test-device-001",
                command_type="power_adjust",
                target_value=50.0,
                priority_level=5,
                status="completed",
                retry_count=0
            )
            db_session.add(dispatch)
        
        for i in range(2):
            dispatch = Dispatch(
                id=f"test-dispatch-failed-{i:03d}",
                device_id="test-device-001",
                command_type="power_adjust",
                target_value=50.0,
                priority_level=5,
                status="failed",
                retry_count=3
            )
            db_session.add(dispatch)
        db_session.commit()
        
        engine = DispatchEngine()
        
        # Execute
        result = engine.get_dispatch_history(status="completed")
        
        # Verify
        assert result["pagination"]["total_count"] == 3
        assert len(result["dispatches"]) == 3
        assert all(d["status"] == "completed" for d in result["dispatches"])
    
    def test_get_dispatch_history_pagination(self, db_session):
        """Test pagination of dispatch history"""
        # Setup
        device = Device(
            id="test-device-001",
            device_type="solar",
            location="Test Location",
            capabilities={"power": 100.0},
            configuration={},
            status="online"
        )
        db_session.add(device)
        
        for i in range(100):
            dispatch = Dispatch(
                id=f"test-dispatch-{i:03d}",
                device_id="test-device-001",
                command_type="power_adjust",
                target_value=50.0,
                priority_level=5,
                status="completed",
                retry_count=0
            )
            db_session.add(dispatch)
        db_session.commit()
        
        engine = DispatchEngine()
        
        # Execute
        result1 = engine.get_dispatch_history(page=1, page_size=50)
        result2 = engine.get_dispatch_history(page=2, page_size=50)
        
        # Verify
        assert result1["pagination"]["total_count"] == 100
        assert len(result1["dispatches"]) == 50
        assert len(result2["dispatches"]) == 50
        assert result1["pagination"]["total_pages"] == 2


class TestDispatchCancellation:
    """Tests for dispatch cancellation"""
    
    def test_cancel_scheduled_dispatch_success(self, db_session):
        """Test successful dispatch cancellation"""
        # Setup
        device = Device(
            id="test-device-001",
            device_type="solar",
            location="Test Location",
            capabilities={"power": 100.0},
            configuration={},
            status="online"
        )
        db_session.add(device)
        
        scheduled_time = datetime.utcnow() + timedelta(hours=1)
        dispatch = Dispatch(
            id="test-dispatch-001",
            device_id="test-device-001",
            command_type="power_adjust",
            target_value=50.0,
            priority_level=5,
            status="pending",
            scheduled_time=scheduled_time,
            retry_count=0
        )
        db_session.add(dispatch)
        db_session.commit()
        
        engine = DispatchEngine()
        
        # Execute
        engine.cancel_scheduled_dispatch("test-dispatch-001")
        
        # Verify
        updated = db_session.query(Dispatch).filter_by(id="test-dispatch-001").first()
        assert updated.status == "cancelled"
    
    def test_cancel_dispatch_not_found(self, db_session):
        """Test cancellation of non-existent dispatch"""
        engine = DispatchEngine()
        
        with pytest.raises(DeviceNotFoundError):
            engine.cancel_scheduled_dispatch("non-existent-dispatch")
    
    def test_cancel_dispatch_not_scheduled(self, db_session):
        """Test cancellation of non-scheduled dispatch"""
        # Setup
        device = Device(
            id="test-device-001",
            device_type="solar",
            location="Test Location",
            capabilities={"power": 100.0},
            configuration={},
            status="online"
        )
        db_session.add(device)
        
        dispatch = Dispatch(
            id="test-dispatch-001",
            device_id="test-device-001",
            command_type="power_adjust",
            target_value=50.0,
            priority_level=5,
            status="pending",
            scheduled_time=None,
            retry_count=0
        )
        db_session.add(dispatch)
        db_session.commit()
        
        engine = DispatchEngine()
        
        with pytest.raises(DispatchExecutionError):
            engine.cancel_scheduled_dispatch("test-dispatch-001")
    
    def test_cancel_dispatch_already_executed(self, db_session):
        """Test cancellation of already executed dispatch"""
        # Setup
        device = Device(
            id="test-device-001",
            device_type="solar",
            location="Test Location",
            capabilities={"power": 100.0},
            configuration={},
            status="online"
        )
        db_session.add(device)
        
        scheduled_time = datetime.utcnow() - timedelta(hours=1)
        dispatch = Dispatch(
            id="test-dispatch-001",
            device_id="test-device-001",
            command_type="power_adjust",
            target_value=50.0,
            priority_level=5,
            status="completed",
            scheduled_time=scheduled_time,
            retry_count=0
        )
        db_session.add(dispatch)
        db_session.commit()
        
        engine = DispatchEngine()
        
        with pytest.raises(DispatchExecutionError):
            engine.cancel_scheduled_dispatch("test-dispatch-001")


class TestDispatchRetry:
    """Tests for dispatch retry logic"""
    
    def test_retry_failed_dispatch_success(self, db_session):
        """Test successful dispatch retry"""
        # Setup
        device = Device(
            id="test-device-001",
            device_type="solar",
            location="Test Location",
            capabilities={"power": 100.0},
            configuration={},
            status="online"
        )
        db_session.add(device)
        
        dispatch = Dispatch(
            id="test-dispatch-001",
            device_id="test-device-001",
            command_type="power_adjust",
            target_value=50.0,
            priority_level=5,
            status="failed",
            error_message="Initial failure",
            retry_count=0
        )
        db_session.add(dispatch)
        db_session.commit()
        
        engine = DispatchEngine()
        
        # Execute
        result = engine.retry_failed_dispatch("test-dispatch-001")
        
        # Verify
        assert result["status"] == "success"
        assert result["retry_count"] == 1
        
        updated = db_session.query(Dispatch).filter_by(id="test-dispatch-001").first()
        assert updated.status == "completed"
        assert updated.retry_count == 1
    
    def test_retry_dispatch_not_found(self, db_session):
        """Test retry of non-existent dispatch"""
        engine = DispatchEngine()
        
        with pytest.raises(DeviceNotFoundError):
            engine.retry_failed_dispatch("non-existent-dispatch")
    
    def test_retry_dispatch_not_failed(self, db_session):
        """Test retry of non-failed dispatch"""
        # Setup
        device = Device(
            id="test-device-001",
            device_type="solar",
            location="Test Location",
            capabilities={"power": 100.0},
            configuration={},
            status="online"
        )
        db_session.add(device)
        
        dispatch = Dispatch(
            id="test-dispatch-001",
            device_id="test-device-001",
            command_type="power_adjust",
            target_value=50.0,
            priority_level=5,
            status="pending",
            retry_count=0
        )
        db_session.add(dispatch)
        db_session.commit()
        
        engine = DispatchEngine()
        
        with pytest.raises(DispatchExecutionError):
            engine.retry_failed_dispatch("test-dispatch-001")
    
    def test_retry_dispatch_max_retries_exceeded(self, db_session):
        """Test retry when max retries exceeded"""
        # Setup
        device = Device(
            id="test-device-001",
            device_type="solar",
            location="Test Location",
            capabilities={"power": 100.0},
            configuration={},
            status="online"
        )
        db_session.add(device)
        
        dispatch = Dispatch(
            id="test-dispatch-001",
            device_id="test-device-001",
            command_type="power_adjust",
            target_value=50.0,
            priority_level=5,
            status="failed",
            error_message="Multiple failures",
            retry_count=3
        )
        db_session.add(dispatch)
        db_session.commit()
        
        engine = DispatchEngine()
        
        with pytest.raises(DispatchExecutionError):
            engine.retry_failed_dispatch("test-dispatch-001")
    
    def test_retry_dispatch_exponential_backoff(self, db_session):
        """Test exponential backoff during retries"""
        # Setup
        device = Device(
            id="test-device-001",
            device_type="solar",
            location="Test Location",
            capabilities={"power": 100.0},
            configuration={},
            status="online"
        )
        db_session.add(device)
        
        dispatch = Dispatch(
            id="test-dispatch-001",
            device_id="test-device-001",
            command_type="power_adjust",
            target_value=50.0,
            priority_level=5,
            status="failed",
            error_message="Initial failure",
            retry_count=0
        )
        db_session.add(dispatch)
        db_session.commit()
        
        engine = DispatchEngine()
        
        # Verify backoff times
        assert engine.RETRY_BACKOFF == [1, 2, 4]
        assert engine.MAX_RETRIES == 3
