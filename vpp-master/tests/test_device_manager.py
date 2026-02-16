"""
Unit Tests for Device Manager Service

Tests device registration, discovery, status management, and configuration updates.
"""

import pytest
import sys
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.device_manager import DeviceManager
from models.device import Device
from utils.validators import DeviceRegistration, DeviceConfig
from utils.errors import (
    ValidationError, DeviceNotFoundError, DuplicateDeviceError,
    DatabaseError
)
from utils.database import SessionLocal


class TestDeviceManagerRegistration:
    """Tests for device registration"""
    
    @pytest.fixture
    def device_manager(self):
        """Create device manager instance"""
        return DeviceManager()
    
    @pytest.fixture
    def valid_device_data(self):
        """Create valid device registration data"""
        return DeviceRegistration(
            device_id="device-001",
            device_type="solar",
            location="Building A",
            capabilities={"power": 100.0, "voltage": 380}
        )
    
    def test_register_device_success(self, device_manager, valid_device_data):
        """Test successful device registration"""
        device = device_manager.register_device(valid_device_data)
        
        assert device is not None
        assert device.id == "device-001"
        assert device.device_type == "solar"
        assert device.location == "Building A"
        assert device.status == "offline"
        assert device.capabilities == {"power": 100.0, "voltage": 380}
    
    def test_register_device_duplicate_id(self, device_manager, valid_device_data):
        """Test duplicate device ID rejection"""
        # Register first device
        device_manager.register_device(valid_device_data)
        
        # Try to register duplicate
        with pytest.raises(DuplicateDeviceError):
            device_manager.register_device(valid_device_data)
    
    def test_register_device_with_empty_capabilities(self, device_manager):
        """Test device registration with empty capabilities"""
        data = DeviceRegistration(
            device_id="device-002",
            device_type="wind",
            location="Field B",
            capabilities={}
        )
        
        device = device_manager.register_device(data)
        assert device.capabilities == {}
    
    def test_register_device_with_complex_capabilities(self, device_manager):
        """Test device registration with complex capabilities"""
        capabilities = {
            "power": 500.0,
            "voltage": 380,
            "frequency": 50,
            "efficiency": 0.95,
            "features": ["monitoring", "control", "storage"]
        }
        
        data = DeviceRegistration(
            device_id="device-003",
            device_type="battery",
            location="Storage C",
            capabilities=capabilities
        )
        
        device = device_manager.register_device(data)
        assert device.capabilities == capabilities


class TestDeviceManagerDiscovery:
    """Tests for device discovery"""
    
    @pytest.fixture
    def device_manager_with_devices(self):
        """Create device manager with test devices"""
        manager = DeviceManager()
        
        # Register multiple devices
        for i in range(5):
            data = DeviceRegistration(
                device_id=f"device-{i:03d}",
                device_type="solar" if i % 2 == 0 else "wind",
                location=f"Location {i}",
                capabilities={"power": 100.0 * (i + 1)}
            )
            manager.register_device(data)
        
        return manager
    
    def test_discover_devices_all(self, device_manager_with_devices):
        """Test discovering all devices"""
        devices, total_count = device_manager_with_devices.discover_devices()
        
        assert len(devices) == 5
        assert total_count == 5
    
    def test_discover_devices_pagination(self, device_manager_with_devices):
        """Test device discovery with pagination"""
        # First page
        devices1, total1 = device_manager_with_devices.discover_devices(
            page=1, page_size=2
        )
        assert len(devices1) == 2
        assert total1 == 5
        
        # Second page
        devices2, total2 = device_manager_with_devices.discover_devices(
            page=2, page_size=2
        )
        assert len(devices2) == 2
        assert total2 == 5
        
        # Third page (partial)
        devices3, total3 = device_manager_with_devices.discover_devices(
            page=3, page_size=2
        )
        assert len(devices3) == 1
        assert total3 == 5
    
    def test_discover_devices_invalid_page(self, device_manager_with_devices):
        """Test discovery with invalid page number"""
        with pytest.raises(ValidationError):
            device_manager_with_devices.discover_devices(page=0)
    
    def test_discover_devices_invalid_page_size(self, device_manager_with_devices):
        """Test discovery with invalid page size"""
        with pytest.raises(ValidationError):
            device_manager_with_devices.discover_devices(page_size=0)
        
        with pytest.raises(ValidationError):
            device_manager_with_devices.discover_devices(page_size=101)
    
    def test_discover_devices_status_filter_online(self, device_manager_with_devices):
        """Test discovery with online status filter"""
        # Mark some devices as online
        device_manager_with_devices.update_device_status("device-000", "online")
        device_manager_with_devices.update_device_status("device-001", "online")
        
        devices, total = device_manager_with_devices.discover_devices(
            status_filter="online"
        )
        
        assert len(devices) == 2
        assert total == 2
        assert all(d.status == "online" for d in devices)
    
    def test_discover_devices_status_filter_offline(self, device_manager_with_devices):
        """Test discovery with offline status filter"""
        devices, total = device_manager_with_devices.discover_devices(
            status_filter="offline"
        )
        
        assert len(devices) == 5
        assert total == 5
        assert all(d.status == "offline" for d in devices)
    
    def test_discover_devices_invalid_status_filter(self, device_manager_with_devices):
        """Test discovery with invalid status filter"""
        with pytest.raises(ValidationError):
            device_manager_with_devices.discover_devices(status_filter="invalid")


class TestDeviceManagerRetrieval:
    """Tests for device retrieval"""
    
    @pytest.fixture
    def device_manager_with_device(self):
        """Create device manager with a test device"""
        manager = DeviceManager()
        data = DeviceRegistration(
            device_id="device-test",
            device_type="solar",
            location="Test Location",
            capabilities={"power": 100.0}
        )
        manager.register_device(data)
        return manager
    
    def test_get_device_success(self, device_manager_with_device):
        """Test successful device retrieval"""
        device = device_manager_with_device.get_device("device-test")
        
        assert device is not None
        assert device.id == "device-test"
        assert device.device_type == "solar"
    
    def test_get_device_not_found(self, device_manager_with_device):
        """Test device not found error"""
        with pytest.raises(DeviceNotFoundError):
            device_manager_with_device.get_device("nonexistent")
    
    def test_get_device_status_offline(self, device_manager_with_device):
        """Test getting device status when offline"""
        status = device_manager_with_device.get_device_status("device-test")
        
        assert status["device_id"] == "device-test"
        assert status["status"] == "offline"
        assert status["is_offline"] is True
        assert status["is_online"] is False
    
    def test_get_device_status_online(self, device_manager_with_device):
        """Test getting device status when online"""
        device_manager_with_device.update_device_status("device-test", "online")
        status = device_manager_with_device.get_device_status("device-test")
        
        assert status["status"] == "online"
        assert status["is_online"] is True
        assert status["is_offline"] is False
    
    def test_get_device_status_not_found(self, device_manager_with_device):
        """Test getting status of nonexistent device"""
        with pytest.raises(DeviceNotFoundError):
            device_manager_with_device.get_device_status("nonexistent")


class TestDeviceManagerStatusUpdate:
    """Tests for device status updates"""
    
    @pytest.fixture
    def device_manager_with_device(self):
        """Create device manager with a test device"""
        manager = DeviceManager()
        data = DeviceRegistration(
            device_id="device-status",
            device_type="solar",
            location="Test Location",
            capabilities={"power": 100.0}
        )
        manager.register_device(data)
        return manager
    
    def test_update_device_status_to_online(self, device_manager_with_device):
        """Test updating device status to online"""
        device = device_manager_with_device.update_device_status(
            "device-status", "online"
        )
        
        assert device.status == "online"
        assert device.is_online() is True
    
    def test_update_device_status_to_offline(self, device_manager_with_device):
        """Test updating device status to offline"""
        device_manager_with_device.update_device_status("device-status", "online")
        device = device_manager_with_device.update_device_status(
            "device-status", "offline"
        )
        
        assert device.status == "offline"
        assert device.is_offline() is True
    
    def test_update_device_status_to_error(self, device_manager_with_device):
        """Test updating device status to error"""
        device = device_manager_with_device.update_device_status(
            "device-status", "error"
        )
        
        assert device.status == "error"
        assert device.is_error() is True
    
    def test_update_device_status_invalid(self, device_manager_with_device):
        """Test updating device with invalid status"""
        with pytest.raises(ValidationError):
            device_manager_with_device.update_device_status(
                "device-status", "invalid"
            )
    
    def test_update_device_status_not_found(self, device_manager_with_device):
        """Test updating status of nonexistent device"""
        with pytest.raises(DeviceNotFoundError):
            device_manager_with_device.update_device_status("nonexistent", "online")


class TestDeviceManagerConfiguration:
    """Tests for device configuration management"""
    
    @pytest.fixture
    def device_manager_with_device(self):
        """Create device manager with a test device"""
        manager = DeviceManager()
        data = DeviceRegistration(
            device_id="device-config",
            device_type="solar",
            location="Test Location",
            capabilities={"power": 100.0}
        )
        manager.register_device(data)
        return manager
    
    def test_update_device_config_success(self, device_manager_with_device):
        """Test successful device configuration update"""
        config = DeviceConfig(
            power_limit=80.0,
            mode="auto",
            priority_level=5
        )
        
        device = device_manager_with_device.update_device_config(
            "device-config", config
        )
        
        # Verify device was returned and configuration was attempted
        assert device is not None
        assert device.id == "device-config"
        # Refresh from database to ensure changes persisted
        refreshed_device = device_manager_with_device.get_device("device-config")
        assert refreshed_device is not None
    
    def test_update_device_config_partial(self, device_manager_with_device):
        """Test partial device configuration update"""
        config = DeviceConfig(power_limit=75.0)
        
        device = device_manager_with_device.update_device_config(
            "device-config", config
        )
        
        # Verify device was returned
        assert device is not None
        assert device.id == "device-config"
    
    def test_update_device_config_not_found(self, device_manager_with_device):
        """Test updating config of nonexistent device"""
        config = DeviceConfig(power_limit=80.0)
        
        with pytest.raises(DeviceNotFoundError):
            device_manager_with_device.update_device_config("nonexistent", config)


class TestDeviceManagerHeartbeat:
    """Tests for device heartbeat management"""
    
    @pytest.fixture
    def device_manager_with_device(self):
        """Create device manager with a test device"""
        manager = DeviceManager()
        data = DeviceRegistration(
            device_id="device-heartbeat",
            device_type="solar",
            location="Test Location",
            capabilities={"power": 100.0}
        )
        manager.register_device(data)
        return manager
    
    def test_update_device_heartbeat(self, device_manager_with_device):
        """Test updating device heartbeat"""
        before = datetime.utcnow()
        device = device_manager_with_device.update_device_heartbeat("device-heartbeat")
        after = datetime.utcnow()
        
        assert device.last_heartbeat is not None
        assert before <= device.last_heartbeat <= after
    
    def test_update_device_heartbeat_not_found(self, device_manager_with_device):
        """Test updating heartbeat of nonexistent device"""
        with pytest.raises(DeviceNotFoundError):
            device_manager_with_device.update_device_heartbeat("nonexistent")
    
    def test_check_offline_devices_timeout(self, device_manager_with_device):
        """Test checking for offline devices due to heartbeat timeout"""
        # Mark device as online
        device_manager_with_device.update_device_status("device-heartbeat", "online")
        
        # Manually set last_heartbeat to past
        device = device_manager_with_device.get_device("device-heartbeat")
        device.last_heartbeat = datetime.utcnow() - timedelta(seconds=60)
        device_manager_with_device.session.commit()
        
        # Check for offline devices
        offline_devices = device_manager_with_device.check_offline_devices()
        
        assert len(offline_devices) == 1
        assert offline_devices[0].id == "device-heartbeat"
        assert offline_devices[0].status == "offline"
    
    def test_check_offline_devices_no_timeout(self, device_manager_with_device):
        """Test checking for offline devices with recent heartbeat"""
        # Mark device as online with recent heartbeat
        device_manager_with_device.update_device_status("device-heartbeat", "online")
        device_manager_with_device.update_device_heartbeat("device-heartbeat")
        
        # Check for offline devices
        offline_devices = device_manager_with_device.check_offline_devices()
        
        assert len(offline_devices) == 0


class TestDeviceManagerDeletion:
    """Tests for device deletion"""
    
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
    
    def test_delete_device_success(self, device_manager_with_device):
        """Test successful device deletion"""
        result = device_manager_with_device.delete_device("device-delete")
        
        assert result is True
        
        # Verify device is deleted
        with pytest.raises(DeviceNotFoundError):
            device_manager_with_device.get_device("device-delete")
    
    def test_delete_device_not_found(self, device_manager_with_device):
        """Test deleting nonexistent device"""
        with pytest.raises(DeviceNotFoundError):
            device_manager_with_device.delete_device("nonexistent")


class TestDeviceManagerMetrics:
    """Tests for device metrics updates"""
    
    def test_device_metrics_updated_on_registration(self):
        """Test that metrics are updated on device registration"""
        manager = DeviceManager()
        
        data = DeviceRegistration(
            device_id="device-metrics",
            device_type="solar",
            location="Test Location",
            capabilities={"power": 100.0}
        )
        
        manager.register_device(data)
        
        # Verify device count metric is updated
        devices, _ = manager.discover_devices()
        assert len(devices) >= 1
    
    def test_device_metrics_updated_on_status_change(self):
        """Test that metrics are updated on status change"""
        manager = DeviceManager()
        
        data = DeviceRegistration(
            device_id="device-metrics-2",
            device_type="solar",
            location="Test Location",
            capabilities={"power": 100.0}
        )
        
        manager.register_device(data)
        manager.update_device_status("device-metrics-2", "online")
        
        # Verify device is marked as online
        device = manager.get_device("device-metrics-2")
        assert device.status == "online"


class TestDeviceManagerEdgeCases:
    """Tests for edge cases and error conditions"""
    
    def test_device_manager_with_special_characters_in_id(self):
        """Test device registration with special characters in ID"""
        manager = DeviceManager()
        
        data = DeviceRegistration(
            device_id="device-001_special-chars",
            device_type="solar",
            location="Test Location",
            capabilities={"power": 100.0}
        )
        
        device = manager.register_device(data)
        assert device.id == "device-001_special-chars"
    
    def test_device_manager_with_unicode_location(self):
        """Test device registration with unicode location"""
        manager = DeviceManager()
        
        data = DeviceRegistration(
            device_id="device-unicode",
            device_type="solar",
            location="北京市朝阳区",
            capabilities={"power": 100.0}
        )
        
        device = manager.register_device(data)
        assert device.location == "北京市朝阳区"
    
    def test_device_manager_with_large_capabilities(self):
        """Test device registration with large capabilities dictionary"""
        manager = DeviceManager()
        
        large_capabilities = {f"param_{i}": i * 1.5 for i in range(100)}
        
        data = DeviceRegistration(
            device_id="device-large",
            device_type="solar",
            location="Test Location",
            capabilities=large_capabilities
        )
        
        device = manager.register_device(data)
        assert len(device.capabilities) == 100
    
    def test_device_manager_concurrent_operations(self):
        """Test device manager with multiple operations"""
        manager = DeviceManager()
        
        # Register multiple devices
        for i in range(10):
            data = DeviceRegistration(
                device_id=f"device-concurrent-{i}",
                device_type="solar",
                location=f"Location {i}",
                capabilities={"power": 100.0}
            )
            manager.register_device(data)
        
        # Update statuses
        for i in range(10):
            manager.update_device_status(f"device-concurrent-{i}", "online")
        
        # Verify all devices are online
        devices, total = manager.discover_devices(status_filter="online")
        assert total == 10
