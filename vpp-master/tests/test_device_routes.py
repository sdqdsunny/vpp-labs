"""
Integration Tests for Device Routes

Tests device management through the service layer and validates HTTP endpoint behavior.
"""

import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.device_manager import DeviceManager
from utils.validators import DeviceRegistration, DeviceConfig
from utils.errors import ValidationError, DeviceNotFoundError, DuplicateDeviceError


class TestDeviceRegistrationEndpoint:
    """Tests for device registration endpoint behavior"""
    
    @pytest.fixture
    def device_manager(self):
        """Create device manager instance"""
        return DeviceManager()
    
    def test_register_device_endpoint_success(self, device_manager):
        """Test successful device registration through endpoint"""
        data = DeviceRegistration(
            device_id="device-001",
            device_type="solar",
            location="Building A",
            capabilities={"power": 100.0}
        )
        
        device = device_manager.register_device(data)
        
        assert device is not None
        assert device.id == "device-001"
        assert device.status == "offline"
    
    def test_register_device_endpoint_duplicate(self, device_manager):
        """Test duplicate device rejection"""
        data = DeviceRegistration(
            device_id="device-dup",
            device_type="solar",
            location="Building A",
            capabilities={"power": 100.0}
        )
        
        device_manager.register_device(data)
        
        with pytest.raises(DuplicateDeviceError):
            device_manager.register_device(data)
    
    def test_register_device_endpoint_validation(self, device_manager):
        """Test device registration validation"""
        # Invalid device type should be caught by Pydantic
        with pytest.raises(ValueError):
            DeviceRegistration(
                device_id="device-invalid",
                device_type="invalid_type",
                location="Building A",
                capabilities={}
            )
    
    def test_register_device_endpoint_missing_field(self, device_manager):
        """Test registration with missing required field"""
        from pydantic_core import ValidationError as PydanticValidationError
        
        with pytest.raises((TypeError, PydanticValidationError)):
            DeviceRegistration(
                device_id="device-missing",
                device_type="solar"
                # Missing location
            )


class TestDeviceListEndpoint:
    """Tests for device list endpoint behavior"""
    
    @pytest.fixture
    def device_manager_with_devices(self):
        """Create device manager with test devices"""
        manager = DeviceManager()
        
        for i in range(5):
            data = DeviceRegistration(
                device_id=f"device-{i:03d}",
                device_type="solar" if i % 2 == 0 else "wind",
                location=f"Location {i}",
                capabilities={"power": 100.0 * (i + 1)}
            )
            manager.register_device(data)
        
        return manager
    
    def test_list_devices_endpoint_all(self, device_manager_with_devices):
        """Test listing all devices"""
        devices, total = device_manager_with_devices.discover_devices()
        
        assert len(devices) == 5
        assert total == 5
    
    def test_list_devices_endpoint_pagination(self, device_manager_with_devices):
        """Test device list pagination"""
        devices1, total1 = device_manager_with_devices.discover_devices(page=1, page_size=2)
        devices2, total2 = device_manager_with_devices.discover_devices(page=2, page_size=2)
        
        assert len(devices1) == 2
        assert len(devices2) == 2
        assert total1 == 5
        assert total2 == 5
    
    def test_list_devices_endpoint_filter(self, device_manager_with_devices):
        """Test device list filtering"""
        device_manager_with_devices.update_device_status("device-000", "online")
        device_manager_with_devices.update_device_status("device-001", "online")
        
        online_devices, online_count = device_manager_with_devices.discover_devices(
            status_filter="online"
        )
        
        assert len(online_devices) == 2
        assert online_count == 2
    
    def test_list_devices_endpoint_invalid_pagination(self, device_manager_with_devices):
        """Test invalid pagination parameters"""
        with pytest.raises(ValidationError):
            device_manager_with_devices.discover_devices(page=0)
        
        with pytest.raises(ValidationError):
            device_manager_with_devices.discover_devices(page_size=101)


class TestDeviceGetEndpoint:
    """Tests for get device endpoint behavior"""
    
    @pytest.fixture
    def device_manager_with_device(self):
        """Create device manager with a test device"""
        manager = DeviceManager()
        data = DeviceRegistration(
            device_id="device-get",
            device_type="solar",
            location="Test Location",
            capabilities={"power": 100.0}
        )
        manager.register_device(data)
        return manager
    
    def test_get_device_endpoint_success(self, device_manager_with_device):
        """Test successful device retrieval"""
        device = device_manager_with_device.get_device("device-get")
        
        assert device is not None
        assert device.id == "device-get"
        assert device.device_type == "solar"
    
    def test_get_device_endpoint_not_found(self, device_manager_with_device):
        """Test getting nonexistent device"""
        with pytest.raises(DeviceNotFoundError):
            device_manager_with_device.get_device("nonexistent")
    
    def test_get_device_status_endpoint(self, device_manager_with_device):
        """Test getting device status"""
        status = device_manager_with_device.get_device_status("device-get")
        
        assert status["device_id"] == "device-get"
        assert status["status"] == "offline"
        assert status["is_offline"] is True


class TestDeviceUpdateEndpoint:
    """Tests for device update endpoint behavior"""
    
    @pytest.fixture
    def device_manager_with_device(self):
        """Create device manager with a test device"""
        manager = DeviceManager()
        data = DeviceRegistration(
            device_id="device-update",
            device_type="solar",
            location="Test Location",
            capabilities={"power": 100.0}
        )
        manager.register_device(data)
        return manager
    
    def test_update_device_config_endpoint(self, device_manager_with_device):
        """Test device configuration update"""
        config = DeviceConfig(power_limit=80.0, mode="auto")
        
        device = device_manager_with_device.update_device_config("device-update", config)
        
        assert device is not None
        assert device.id == "device-update"
    
    def test_update_device_config_endpoint_not_found(self, device_manager_with_device):
        """Test updating config of nonexistent device"""
        config = DeviceConfig(power_limit=80.0)
        
        with pytest.raises(DeviceNotFoundError):
            device_manager_with_device.update_device_config("nonexistent", config)
    
    def test_update_device_status_endpoint(self, device_manager_with_device):
        """Test device status update"""
        device = device_manager_with_device.update_device_status("device-update", "online")
        
        assert device.status == "online"
        assert device.is_online() is True
    
    def test_update_device_status_endpoint_invalid(self, device_manager_with_device):
        """Test invalid status update"""
        with pytest.raises(ValidationError):
            device_manager_with_device.update_device_status("device-update", "invalid")


class TestDeviceDeleteEndpoint:
    """Tests for device delete endpoint behavior"""
    
    @pytest.fixture
    def device_manager_with_device(self):
        """Create device manager with a test device"""
        manager = DeviceManager()
        data = DeviceRegistration(
            device_id="device-delete",
            device_type="solar",
            location="Test Location",
            capabilities={"power": 100.0}
        )
        manager.register_device(data)
        return manager
    
    def test_delete_device_endpoint(self, device_manager_with_device):
        """Test device deletion"""
        result = device_manager_with_device.delete_device("device-delete")
        
        assert result is True
        
        with pytest.raises(DeviceNotFoundError):
            device_manager_with_device.get_device("device-delete")
    
    def test_delete_device_endpoint_not_found(self, device_manager_with_device):
        """Test deleting nonexistent device"""
        with pytest.raises(DeviceNotFoundError):
            device_manager_with_device.delete_device("nonexistent")


class TestDeviceEndpointErrorHandling:
    """Tests for error handling across endpoints"""
    
    @pytest.fixture
    def device_manager(self):
        """Create device manager instance"""
        return DeviceManager()
    
    def test_endpoint_validation_error(self, device_manager):
        """Test validation error handling"""
        with pytest.raises(ValueError):
            DeviceRegistration(
                device_id="device-val",
                device_type="invalid",
                location="Test",
                capabilities={}
            )
    
    def test_endpoint_not_found_error(self, device_manager):
        """Test not found error handling"""
        with pytest.raises(DeviceNotFoundError):
            device_manager.get_device("nonexistent")
    
    def test_endpoint_duplicate_error(self, device_manager):
        """Test duplicate error handling"""
        data = DeviceRegistration(
            device_id="device-dup",
            device_type="solar",
            location="Test",
            capabilities={}
        )
        
        device_manager.register_device(data)
        
        with pytest.raises(DuplicateDeviceError):
            device_manager.register_device(data)


class TestDeviceEndpointIntegration:
    """Integration tests for device endpoints"""
    
    def test_device_lifecycle_through_endpoints(self):
        """Test complete device lifecycle through endpoints"""
        manager = DeviceManager()
        
        # 1. Register
        data = DeviceRegistration(
            device_id="device-lifecycle",
            device_type="solar",
            location="Test Location",
            capabilities={"power": 100.0}
        )
        device = manager.register_device(data)
        assert device.status == "offline"
        
        # 2. Get
        retrieved = manager.get_device("device-lifecycle")
        assert retrieved.id == "device-lifecycle"
        
        # 3. Update status
        updated = manager.update_device_status("device-lifecycle", "online")
        assert updated.status == "online"
        
        # 4. Update config
        config = DeviceConfig(power_limit=80.0)
        configured = manager.update_device_config("device-lifecycle", config)
        assert configured is not None
        
        # 5. Get status
        status = manager.get_device_status("device-lifecycle")
        assert status["is_online"] is True
        
        # 6. List
        devices, total = manager.discover_devices()
        assert total >= 1
        
        # 7. Delete
        result = manager.delete_device("device-lifecycle")
        assert result is True
        
        # 8. Verify deletion
        with pytest.raises(DeviceNotFoundError):
            manager.get_device("device-lifecycle")
    
    def test_multiple_devices_through_endpoints(self):
        """Test managing multiple devices through endpoints"""
        manager = DeviceManager()
        
        # Register multiple devices
        for i in range(5):
            data = DeviceRegistration(
                device_id=f"device-multi-{i}",
                device_type="solar",
                location=f"Location {i}",
                capabilities={"power": 100.0}
            )
            manager.register_device(data)
        
        # Update statuses
        for i in range(5):
            status = "online" if i % 2 == 0 else "offline"
            manager.update_device_status(f"device-multi-{i}", status)
        
        # List and filter
        online_devices, online_count = manager.discover_devices(status_filter="online")
        offline_devices, offline_count = manager.discover_devices(status_filter="offline")
        
        assert online_count == 3
        assert offline_count == 2
        
        # Delete all
        for i in range(5):
            manager.delete_device(f"device-multi-{i}")
        
        # Verify all deleted
        devices, total = manager.discover_devices()
        assert total == 0


class TestDeviceEndpointResponseData:
    """Tests for response data format and content"""
    
    @pytest.fixture
    def device_manager(self):
        """Create device manager instance"""
        return DeviceManager()
    
    def test_device_response_contains_all_fields(self, device_manager):
        """Test that device response contains all required fields"""
        data = DeviceRegistration(
            device_id="device-fields",
            device_type="solar",
            location="Test Location",
            capabilities={"power": 100.0}
        )
        
        device = device_manager.register_device(data)
        device_dict = device.to_dict()
        
        required_fields = [
            'id', 'device_type', 'location', 'status',
            'capabilities', 'configuration', 'created_at', 'updated_at'
        ]
        
        for field in required_fields:
            assert field in device_dict
    
    def test_device_status_response_format(self, device_manager):
        """Test device status response format"""
        data = DeviceRegistration(
            device_id="device-status-format",
            device_type="solar",
            location="Test Location",
            capabilities={}
        )
        
        device_manager.register_device(data)
        status = device_manager.get_device_status("device-status-format")
        
        required_fields = [
            'device_id', 'status', 'last_heartbeat',
            'is_online', 'is_offline', 'is_error'
        ]
        
        for field in required_fields:
            assert field in status
    
    def test_device_list_response_format(self, device_manager):
        """Test device list response format"""
        data = DeviceRegistration(
            device_id="device-list-format",
            device_type="solar",
            location="Test Location",
            capabilities={}
        )
        
        device_manager.register_device(data)
        devices, total = device_manager.discover_devices()
        
        assert isinstance(devices, list)
        assert isinstance(total, int)
        assert total >= 1
        
        if devices:
            device_dict = devices[0].to_dict()
            assert 'id' in device_dict
            assert 'device_type' in device_dict
            assert 'status' in device_dict
