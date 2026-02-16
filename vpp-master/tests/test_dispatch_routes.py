"""
Integration Tests for Dispatch Routes

Tests dispatch control through the service layer and validates HTTP endpoint behavior.
"""

import pytest
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.dispatch_engine import DispatchEngine
from services.device_manager import DeviceManager
from utils.validators import DispatchRequest, ScheduledDispatchRequest, DeviceRegistration
from utils.errors import ValidationError, DeviceNotFoundError, DispatchExecutionError


class TestDispatchCreationEndpoint:
    """Tests for dispatch creation endpoint behavior"""
    
    @pytest.fixture
    def setup_device_and_engine(self):
        """Setup device and dispatch engine"""
        device_manager = DeviceManager()
        dispatch_engine = DispatchEngine()
        
        # Register and activate a device
        device_data = DeviceRegistration(
            device_id="device-dispatch-001",
            device_type="solar",
            location="Building A",
            capabilities={"power": 100.0}
        )
        device_manager.register_device(device_data)
        device_manager.update_device_status("device-dispatch-001", "online")
        
        return dispatch_engine, device_manager
    
    def test_create_dispatch_endpoint_success(self, setup_device_and_engine):
        """Test successful dispatch creation"""
        dispatch_engine, _ = setup_device_and_engine
        
        data = DispatchRequest(
            device_id="device-dispatch-001",
            command_type="power_adjust",
            target_value=50.0,
            priority_level=5
        )
        
        dispatch = dispatch_engine.create_dispatch(data)
        
        assert dispatch is not None
        assert dispatch.device_id == "device-dispatch-001"
        assert dispatch.command_type == "power_adjust"
        assert dispatch.target_value == 50.0
        assert dispatch.status == "pending"
    
    def test_create_dispatch_endpoint_device_not_found(self, setup_device_and_engine):
        """Test dispatch creation with nonexistent device"""
        dispatch_engine, _ = setup_device_and_engine
        
        data = DispatchRequest(
            device_id="nonexistent-device",
            command_type="power_adjust",
            target_value=50.0,
            priority_level=5
        )
        
        with pytest.raises(DeviceNotFoundError):
            dispatch_engine.create_dispatch(data)
    
    def test_create_dispatch_endpoint_device_offline(self, setup_device_and_engine):
        """Test dispatch creation with offline device"""
        dispatch_engine, device_manager = setup_device_and_engine
        
        # Create offline device
        device_data = DeviceRegistration(
            device_id="device-offline",
            device_type="solar",
            location="Building B",
            capabilities={"power": 100.0}
        )
        device_manager.register_device(device_data)
        # Device is offline by default
        
        data = DispatchRequest(
            device_id="device-offline",
            command_type="power_adjust",
            target_value=50.0,
            priority_level=5
        )
        
        with pytest.raises(DispatchExecutionError):
            dispatch_engine.create_dispatch(data)
    
    def test_create_dispatch_endpoint_validation(self, setup_device_and_engine):
        """Test dispatch creation validation"""
        dispatch_engine, _ = setup_device_and_engine
        
        # Invalid priority level
        with pytest.raises(ValueError):
            DispatchRequest(
                device_id="device-dispatch-001",
                command_type="power_adjust",
                target_value=50.0,
                priority_level=15  # Invalid: > 10
            )


class TestDispatchGetEndpoint:
    """Tests for get dispatch endpoint behavior"""
    
    @pytest.fixture
    def setup_dispatch(self):
        """Setup dispatch for testing"""
        device_manager = DeviceManager()
        dispatch_engine = DispatchEngine()
        
        # Register and activate device
        device_data = DeviceRegistration(
            device_id="device-get-dispatch",
            device_type="solar",
            location="Building A",
            capabilities={"power": 100.0}
        )
        device_manager.register_device(device_data)
        device_manager.update_device_status("device-get-dispatch", "online")
        
        # Create dispatch
        dispatch_data = DispatchRequest(
            device_id="device-get-dispatch",
            command_type="power_adjust",
            target_value=50.0,
            priority_level=5
        )
        dispatch = dispatch_engine.create_dispatch(dispatch_data)
        
        return dispatch_engine, dispatch
    
    def test_get_dispatch_endpoint_success(self, setup_dispatch):
        """Test successful dispatch retrieval"""
        dispatch_engine, dispatch = setup_dispatch
        
        status = dispatch_engine.get_dispatch_status(dispatch.id)
        
        assert status is not None
        assert status["dispatch_id"] == dispatch.id
        assert status["status"] == "pending"
    
    def test_get_dispatch_endpoint_not_found(self, setup_dispatch):
        """Test getting nonexistent dispatch"""
        dispatch_engine, _ = setup_dispatch
        
        with pytest.raises(DeviceNotFoundError):
            dispatch_engine.get_dispatch_status("nonexistent-dispatch")


class TestDispatchStatusEndpoint:
    """Tests for dispatch status endpoint behavior"""
    
    @pytest.fixture
    def setup_dispatch(self):
        """Setup dispatch for testing"""
        device_manager = DeviceManager()
        dispatch_engine = DispatchEngine()
        
        # Register and activate device
        device_data = DeviceRegistration(
            device_id="device-status-dispatch",
            device_type="solar",
            location="Building A",
            capabilities={"power": 100.0}
        )
        device_manager.register_device(device_data)
        device_manager.update_device_status("device-status-dispatch", "online")
        
        # Create dispatch
        dispatch_data = DispatchRequest(
            device_id="device-status-dispatch",
            command_type="power_adjust",
            target_value=50.0,
            priority_level=5
        )
        dispatch = dispatch_engine.create_dispatch(dispatch_data)
        
        return dispatch_engine, dispatch
    
    def test_get_dispatch_status_endpoint(self, setup_dispatch):
        """Test getting dispatch status"""
        dispatch_engine, dispatch = setup_dispatch
        
        status = dispatch_engine.get_dispatch_status(dispatch.id)
        
        assert status["dispatch_id"] == dispatch.id
        assert status["status"] == "pending"
        assert status["retry_count"] == 0
        assert status["error_message"] is None


class TestDispatchHistoryEndpoint:
    """Tests for dispatch history endpoint behavior"""
    
    @pytest.fixture
    def setup_dispatch_history(self):
        """Setup multiple dispatches for history testing"""
        device_manager = DeviceManager()
        dispatch_engine = DispatchEngine()
        
        # Register and activate devices
        for i in range(2):
            device_data = DeviceRegistration(
                device_id=f"device-history-{i:03d}",
                device_type="solar",
                location=f"Building {i}",
                capabilities={"power": 100.0}
            )
            device_manager.register_device(device_data)
            device_manager.update_device_status(f"device-history-{i:03d}", "online")
        
        # Create multiple dispatches
        dispatches = []
        for i in range(5):
            dispatch_data = DispatchRequest(
                device_id=f"device-history-{i % 2:03d}",
                command_type="power_adjust",
                target_value=50.0 + i * 10,
                priority_level=i % 5
            )
            dispatch = dispatch_engine.create_dispatch(dispatch_data)
            dispatches.append(dispatch)
        
        return dispatch_engine, dispatches
    
    def test_get_dispatch_history_endpoint_all(self, setup_dispatch_history):
        """Test getting all dispatch history"""
        dispatch_engine, dispatches = setup_dispatch_history
        
        history = dispatch_engine.get_dispatch_history()
        
        assert len(history['dispatches']) >= 5
        assert history['pagination']['total_count'] >= 5
    
    def test_get_dispatch_history_endpoint_pagination(self, setup_dispatch_history):
        """Test dispatch history pagination"""
        dispatch_engine, _ = setup_dispatch_history
        
        page1 = dispatch_engine.get_dispatch_history(page=1, page_size=2)
        page2 = dispatch_engine.get_dispatch_history(page=2, page_size=2)
        
        assert len(page1['dispatches']) == 2
        assert len(page2['dispatches']) == 2
        assert page1['pagination']['total_count'] >= 5
    
    def test_get_dispatch_history_endpoint_filter_device(self, setup_dispatch_history):
        """Test dispatch history filtering by device"""
        dispatch_engine, _ = setup_dispatch_history
        
        history = dispatch_engine.get_dispatch_history(device_id="device-history-000")
        
        assert all(d['device_id'] == "device-history-000" for d in history['dispatches'])
    
    def test_get_dispatch_history_endpoint_filter_status(self, setup_dispatch_history):
        """Test dispatch history filtering by status"""
        dispatch_engine, _ = setup_dispatch_history
        
        history = dispatch_engine.get_dispatch_history(status="pending")
        
        assert all(d['status'] == "pending" for d in history['dispatches'])
    
    def test_get_dispatch_history_endpoint_filter_time(self, setup_dispatch_history):
        """Test dispatch history filtering by time range"""
        dispatch_engine, _ = setup_dispatch_history
        
        now = datetime.utcnow()
        start_time = now - timedelta(hours=1)
        end_time = now + timedelta(hours=1)
        
        history = dispatch_engine.get_dispatch_history(
            start_time=start_time,
            end_time=end_time
        )
        
        assert len(history['dispatches']) >= 5


class TestDispatchCancelEndpoint:
    """Tests for dispatch cancellation endpoint behavior"""
    
    @pytest.fixture
    def setup_scheduled_dispatch(self):
        """Setup scheduled dispatch for cancellation testing"""
        device_manager = DeviceManager()
        dispatch_engine = DispatchEngine()
        
        # Register and activate device
        device_data = DeviceRegistration(
            device_id="device-cancel",
            device_type="solar",
            location="Building A",
            capabilities={"power": 100.0}
        )
        device_manager.register_device(device_data)
        device_manager.update_device_status("device-cancel", "online")
        
        # Create scheduled dispatch
        future_time = datetime.utcnow() + timedelta(hours=1)
        dispatch_data = ScheduledDispatchRequest(
            device_id="device-cancel",
            command_type="power_adjust",
            target_value=50.0,
            priority_level=5,
            execution_time=future_time
        )
        dispatch = dispatch_engine.schedule_dispatch(dispatch_data)
        
        return dispatch_engine, dispatch
    
    def test_cancel_dispatch_endpoint_success(self, setup_scheduled_dispatch):
        """Test successful dispatch cancellation"""
        dispatch_engine, dispatch = setup_scheduled_dispatch
        
        dispatch_engine.cancel_scheduled_dispatch(dispatch.id)
        
        status = dispatch_engine.get_dispatch_status(dispatch.id)
        assert status["status"] == "cancelled"
    
    def test_cancel_dispatch_endpoint_not_found(self, setup_scheduled_dispatch):
        """Test cancelling nonexistent dispatch"""
        dispatch_engine, _ = setup_scheduled_dispatch
        
        with pytest.raises(DeviceNotFoundError):
            dispatch_engine.cancel_scheduled_dispatch("nonexistent-dispatch")
    
    def test_cancel_dispatch_endpoint_not_scheduled(self, setup_scheduled_dispatch):
        """Test cancelling non-scheduled dispatch"""
        dispatch_engine, _ = setup_scheduled_dispatch
        
        device_manager = DeviceManager()
        device_data = DeviceRegistration(
            device_id="device-cancel-2",
            device_type="solar",
            location="Building B",
            capabilities={"power": 100.0}
        )
        device_manager.register_device(device_data)
        device_manager.update_device_status("device-cancel-2", "online")
        
        # Create non-scheduled dispatch
        dispatch_data = DispatchRequest(
            device_id="device-cancel-2",
            command_type="power_adjust",
            target_value=50.0,
            priority_level=5
        )
        dispatch = dispatch_engine.create_dispatch(dispatch_data)
        
        with pytest.raises(DispatchExecutionError):
            dispatch_engine.cancel_scheduled_dispatch(dispatch.id)


class TestDispatchScheduleEndpoint:
    """Tests for dispatch scheduling endpoint behavior"""
    
    @pytest.fixture
    def setup_device_and_engine(self):
        """Setup device and dispatch engine"""
        device_manager = DeviceManager()
        dispatch_engine = DispatchEngine()
        
        # Register and activate device
        device_data = DeviceRegistration(
            device_id="device-schedule",
            device_type="solar",
            location="Building A",
            capabilities={"power": 100.0}
        )
        device_manager.register_device(device_data)
        device_manager.update_device_status("device-schedule", "online")
        
        return dispatch_engine, device_manager
    
    def test_schedule_dispatch_endpoint_success(self, setup_device_and_engine):
        """Test successful dispatch scheduling"""
        dispatch_engine, _ = setup_device_and_engine
        
        future_time = datetime.utcnow() + timedelta(hours=1)
        data = ScheduledDispatchRequest(
            device_id="device-schedule",
            command_type="power_adjust",
            target_value=50.0,
            priority_level=5,
            execution_time=future_time
        )
        
        dispatch = dispatch_engine.schedule_dispatch(data)
        
        assert dispatch is not None
        assert dispatch.device_id == "device-schedule"
        assert dispatch.scheduled_time == future_time
        assert dispatch.status == "pending"
    
    def test_schedule_dispatch_endpoint_device_not_found(self, setup_device_and_engine):
        """Test scheduling dispatch for nonexistent device"""
        dispatch_engine, _ = setup_device_and_engine
        
        future_time = datetime.utcnow() + timedelta(hours=1)
        data = ScheduledDispatchRequest(
            device_id="nonexistent-device",
            command_type="power_adjust",
            target_value=50.0,
            priority_level=5,
            execution_time=future_time
        )
        
        with pytest.raises(DeviceNotFoundError):
            dispatch_engine.schedule_dispatch(data)


class TestDispatchListScheduledEndpoint:
    """Tests for list scheduled dispatches endpoint behavior"""
    
    @pytest.fixture
    def setup_scheduled_dispatches(self):
        """Setup multiple scheduled dispatches"""
        device_manager = DeviceManager()
        dispatch_engine = DispatchEngine()
        
        # Register and activate device
        device_data = DeviceRegistration(
            device_id="device-list-scheduled",
            device_type="solar",
            location="Building A",
            capabilities={"power": 100.0}
        )
        device_manager.register_device(device_data)
        device_manager.update_device_status("device-list-scheduled", "online")
        
        # Create multiple scheduled dispatches
        for i in range(3):
            future_time = datetime.utcnow() + timedelta(hours=i+1)
            dispatch_data = ScheduledDispatchRequest(
                device_id="device-list-scheduled",
                command_type="power_adjust",
                target_value=50.0 + i * 10,
                priority_level=i,
                execution_time=future_time
            )
            dispatch_engine.schedule_dispatch(dispatch_data)
        
        return dispatch_engine
    
    def test_list_scheduled_dispatches_endpoint(self, setup_scheduled_dispatches):
        """Test listing scheduled dispatches"""
        dispatch_engine = setup_scheduled_dispatches
        
        history = dispatch_engine.get_dispatch_history(status="pending")
        scheduled = [d for d in history['dispatches'] if d.get('scheduled_time') is not None]
        
        assert len(scheduled) >= 3


class TestDispatchExecutionEndpoint:
    """Tests for dispatch execution endpoint behavior"""
    
    @pytest.fixture
    def setup_dispatch(self):
        """Setup dispatch for execution testing"""
        device_manager = DeviceManager()
        dispatch_engine = DispatchEngine()
        
        # Register and activate device
        device_data = DeviceRegistration(
            device_id="device-execute",
            device_type="solar",
            location="Building A",
            capabilities={"power": 100.0}
        )
        device_manager.register_device(device_data)
        device_manager.update_device_status("device-execute", "online")
        
        # Create dispatch
        dispatch_data = DispatchRequest(
            device_id="device-execute",
            command_type="power_adjust",
            target_value=50.0,
            priority_level=5
        )
        dispatch = dispatch_engine.create_dispatch(dispatch_data)
        
        return dispatch_engine, dispatch
    
    def test_execute_dispatch_endpoint_success(self, setup_dispatch):
        """Test successful dispatch execution"""
        dispatch_engine, dispatch = setup_dispatch
        
        result = dispatch_engine.execute_dispatch(dispatch.id)
        
        assert result is not None
        assert result["status"] == "success"
        assert "executed_at" in result
    
    def test_execute_dispatch_endpoint_not_found(self, setup_dispatch):
        """Test executing nonexistent dispatch"""
        dispatch_engine, _ = setup_dispatch
        
        with pytest.raises(DeviceNotFoundError):
            dispatch_engine.execute_dispatch("nonexistent-dispatch")


class TestDispatchResponseFormat:
    """Tests for dispatch response format consistency"""
    
    @pytest.fixture
    def setup_dispatch(self):
        """Setup dispatch for response format testing"""
        device_manager = DeviceManager()
        dispatch_engine = DispatchEngine()
        
        # Register and activate device
        device_data = DeviceRegistration(
            device_id="device-format",
            device_type="solar",
            location="Building A",
            capabilities={"power": 100.0}
        )
        device_manager.register_device(device_data)
        device_manager.update_device_status("device-format", "online")
        
        # Create dispatch
        dispatch_data = DispatchRequest(
            device_id="device-format",
            command_type="power_adjust",
            target_value=50.0,
            priority_level=5
        )
        dispatch = dispatch_engine.create_dispatch(dispatch_data)
        
        return dispatch_engine, dispatch
    
    def test_dispatch_response_format(self, setup_dispatch):
        """Test dispatch response format consistency"""
        dispatch_engine, dispatch = setup_dispatch
        
        dispatch_dict = dispatch.to_dict()
        
        # Verify all required fields are present
        required_fields = [
            'id', 'device_id', 'command_type', 'target_value',
            'priority_level', 'status', 'retry_count', 'created_at', 'updated_at'
        ]
        
        for field in required_fields:
            assert field in dispatch_dict
    
    def test_dispatch_status_response_format(self, setup_dispatch):
        """Test dispatch status response format"""
        dispatch_engine, dispatch = setup_dispatch
        
        status = dispatch_engine.get_dispatch_status(dispatch.id)
        
        # Verify all required fields are present
        required_fields = [
            'dispatch_id', 'status', 'execution_time',
            'retry_count', 'error_message', 'updated_at'
        ]
        
        for field in required_fields:
            assert field in status
