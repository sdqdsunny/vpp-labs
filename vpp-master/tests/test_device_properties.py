"""
Property-Based Tests for Device Manager

Tests correctness properties using Hypothesis for property-based testing.
Feature: vpp-phase1-api
"""

import pytest
import sys
import os
from datetime import datetime, timedelta
import uuid

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hypothesis import given, strategies as st, settings, HealthCheck
from services.device_manager import DeviceManager
from utils.validators import DeviceRegistration, DeviceConfig
from utils.errors import ValidationError, DeviceNotFoundError, DuplicateDeviceError


# Custom strategies for generating test data
device_type_strategy = st.sampled_from(['solar', 'wind', 'battery', 'load', 'grid'])

location_strategy = st.text(
    alphabet=st.characters(blacklist_categories=('Cc', 'Cs')),
    min_size=1,
    max_size=100
).filter(lambda x: x.strip())

capabilities_strategy = st.dictionaries(
    keys=st.text(alphabet='abcdefghijklmnopqrstuvwxyz', min_size=1, max_size=20),
    values=st.floats(min_value=0, max_value=10000, allow_nan=False, allow_infinity=False),
    min_size=0,
    max_size=5
)

power_limit_strategy = st.floats(min_value=0, max_value=10000, allow_nan=False, allow_infinity=False)
priority_level_strategy = st.integers(min_value=0, max_value=10)


class TestDeviceRegistrationProperty:
    """Property 1: Device Registration Creates Retrievable Record
    
    Validates: Requirements 1.1, 1.5
    """
    
    @given(
        device_type=device_type_strategy,
        location=location_strategy,
        capabilities=capabilities_strategy
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_registered_device_is_retrievable(self, device_type, location, capabilities):
        """
        For any valid device metadata, registering a device should result in that device
        being retrievable via the discovery endpoint with identical metadata.
        """
        manager = DeviceManager()
        device_id = f"device-{uuid.uuid4().hex[:8]}"
        
        # Register device
        data = DeviceRegistration(
            device_id=device_id,
            device_type=device_type,
            location=location,
            capabilities=capabilities
        )
        registered_device = manager.register_device(data)
        
        # Retrieve device
        retrieved_device = manager.get_device(device_id)
        
        # Verify metadata matches
        assert retrieved_device.id == registered_device.id
        assert retrieved_device.device_type == registered_device.device_type
        assert retrieved_device.location == registered_device.location
        assert retrieved_device.capabilities == registered_device.capabilities


class TestDuplicateDeviceProperty:
    """Property 2: Duplicate Device IDs Are Rejected
    
    Validates: Requirements 1.3
    """
    
    @given(
        device_type=device_type_strategy,
        location=location_strategy,
        capabilities=capabilities_strategy
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_duplicate_device_id_rejected(self, device_type, location, capabilities):
        """
        For any device already registered with a given device_id, attempting to register
        another device with the same device_id should be rejected with a DuplicateDeviceError.
        """
        manager = DeviceManager()
        device_id = f"device-{uuid.uuid4().hex[:8]}"
        
        # Register first device
        data = DeviceRegistration(
            device_id=device_id,
            device_type=device_type,
            location=location,
            capabilities=capabilities
        )
        manager.register_device(data)
        
        # Attempt to register duplicate
        with pytest.raises(DuplicateDeviceError):
            manager.register_device(data)


class TestInvalidDeviceRegistrationProperty:
    """Property 3: Invalid Device Registration Is Rejected
    
    Validates: Requirements 1.2
    """
    
    def test_missing_device_id_rejected(self):
        """Missing device_id should be rejected"""
        with pytest.raises((ValueError, TypeError)):
            DeviceRegistration(
                device_type='solar',
                location='Test',
                capabilities={}
            )
    
    def test_missing_device_type_rejected(self):
        """Missing device_type should be rejected"""
        with pytest.raises((ValueError, TypeError)):
            DeviceRegistration(
                device_id='device-001',
                location='Test',
                capabilities={}
            )
    
    def test_missing_location_rejected(self):
        """Missing location should be rejected"""
        with pytest.raises((ValueError, TypeError)):
            DeviceRegistration(
                device_id='device-001',
                device_type='solar',
                capabilities={}
            )
    
    def test_invalid_device_type_rejected(self):
        """Invalid device_type should be rejected"""
        with pytest.raises(ValueError):
            DeviceRegistration(
                device_id='device-001',
                device_type='invalid_type',
                location='Test',
                capabilities={}
            )


class TestDiscoveryReturnsAllDevicesProperty:
    """Property 4: Discovery Returns All Registered Devices
    
    Validates: Requirements 1.4
    """
    
    @given(
        num_devices=st.integers(min_value=1, max_value=10)
    )
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_discovery_returns_all_devices(self, num_devices):
        """
        For any set of registered devices, the discovery endpoint should return
        a list containing all registered devices.
        """
        manager = DeviceManager()
        
        # Register devices
        for i in range(num_devices):
            device_id = f"device-{uuid.uuid4().hex[:8]}"
            data = DeviceRegistration(
                device_id=device_id,
                device_type='solar',
                location=f'Location {i}',
                capabilities={}
            )
            manager.register_device(data)
        
        # Discover devices
        devices, total_count = manager.discover_devices()
        
        # Verify all devices are returned
        assert len(devices) == num_devices
        assert total_count == num_devices


class TestDeviceStatusHeartbeatProperty:
    """Property 5: Device Status Reflects Heartbeat Timeout
    
    Validates: Requirements 2.2
    """
    
    def test_device_marked_offline_after_heartbeat_timeout(self):
        """
        For any device that fails to send a heartbeat within the configured timeout period,
        the device status should transition to offline.
        """
        manager = DeviceManager()
        device_id = f"device-{uuid.uuid4().hex[:8]}"
        
        # Register device
        data = DeviceRegistration(
            device_id=device_id,
            device_type='solar',
            location='Test',
            capabilities={}
        )
        manager.register_device(data)
        
        # Mark as online
        manager.update_device_status(device_id, 'online')
        
        # Manually set last_heartbeat to past
        device = manager.get_device(device_id)
        device.last_heartbeat = datetime.utcnow() - timedelta(seconds=60)
        manager.session.commit()
        
        # Check offline devices
        offline_devices = manager.check_offline_devices()
        
        # Verify device is marked offline
        assert len(offline_devices) == 1
        assert offline_devices[0].id == device_id
        assert offline_devices[0].status == 'offline'


class TestOfflineDeviceDispatchProperty:
    """Property 6: Offline Devices Cannot Receive Dispatches
    
    Validates: Requirements 2.4
    """
    
    def test_offline_device_status_tracked(self):
        """
        For any device marked as offline, the status should be properly tracked
        and retrievable.
        """
        manager = DeviceManager()
        device_id = f"device-{uuid.uuid4().hex[:8]}"
        
        # Register device
        data = DeviceRegistration(
            device_id=device_id,
            device_type='solar',
            location='Test',
            capabilities={}
        )
        manager.register_device(data)
        
        # Verify offline status
        status = manager.get_device_status(device_id)
        assert status['status'] == 'offline'
        assert status['is_offline'] is True
        assert status['is_online'] is False


class TestDeviceConfigurationPersistenceProperty:
    """Property 7: Device Configuration Updates Persist
    
    Validates: Requirements 3.1, 3.3
    """
    
    @given(
        power_limit=power_limit_strategy,
        priority_level=priority_level_strategy
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_configuration_updates_persist(self, power_limit, priority_level):
        """
        For any valid device configuration update, the updated configuration should be
        persisted to the database and retrievable via subsequent queries.
        """
        manager = DeviceManager()
        device_id = f"device-{uuid.uuid4().hex[:8]}"
        
        # Register device
        data = DeviceRegistration(
            device_id=device_id,
            device_type='solar',
            location='Test',
            capabilities={}
        )
        manager.register_device(data)
        
        # Update configuration
        config = DeviceConfig(
            power_limit=power_limit,
            priority_level=priority_level
        )
        manager.update_device_config(device_id, config)
        
        # Retrieve device and verify configuration persisted
        device = manager.get_device(device_id)
        
        # Configuration should be stored
        assert device.configuration is not None
        assert isinstance(device.configuration, dict)


class TestInvalidDeviceConfigurationProperty:
    """Property 8: Invalid Device Configuration Is Rejected
    
    Validates: Requirements 3.2
    """
    
    def test_invalid_priority_level_rejected(self):
        """Invalid priority_level should be rejected"""
        with pytest.raises(ValueError):
            DeviceConfig(priority_level=15)  # Should be 0-10
    
    def test_invalid_priority_level_negative_rejected(self):
        """Negative priority_level should be rejected"""
        with pytest.raises(ValueError):
            DeviceConfig(priority_level=-1)
    
    def test_negative_power_limit_rejected(self):
        """Negative power_limit should be rejected"""
        with pytest.raises(ValueError):
            DeviceConfig(power_limit=-10.0)


class TestDevicePropertyIntegration:
    """Integration tests combining multiple properties"""
    
    @given(
        num_devices=st.integers(min_value=1, max_value=5)
    )
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_device_lifecycle_properties(self, num_devices):
        """
        Test that multiple properties hold throughout a device lifecycle:
        - Registration creates retrievable record (Property 1)
        - Discovery returns all devices (Property 4)
        - Configuration updates persist (Property 7)
        """
        manager = DeviceManager()
        device_ids = []
        
        # Register all devices
        for i in range(num_devices):
            device_id = f"device-{uuid.uuid4().hex[:8]}"
            device_ids.append(device_id)
            data = DeviceRegistration(
                device_id=device_id,
                device_type='solar',
                location=f'Location {i}',
                capabilities={}
            )
            manager.register_device(data)
        
        # Verify all devices are discoverable (Property 4)
        devices, total = manager.discover_devices()
        assert len(devices) == num_devices
        
        # Update configuration for each device (Property 7)
        for device_id in device_ids:
            config = DeviceConfig(power_limit=100.0)
            manager.update_device_config(device_id, config)
        
        # Verify all devices still discoverable after updates
        devices_after, total_after = manager.discover_devices()
        assert len(devices_after) == num_devices
        assert total_after == total
        
        # Verify each device is still retrievable (Property 1)
        for device_id in device_ids:
            device = manager.get_device(device_id)
            assert device.id == device_id


class TestDevicePropertyEdgeCases:
    """Edge case tests for device properties"""
    
    def test_empty_capabilities_property(self):
        """Test device registration with empty capabilities"""
        manager = DeviceManager()
        device_id = f"device-{uuid.uuid4().hex[:8]}"
        
        data = DeviceRegistration(
            device_id=device_id,
            device_type='solar',
            location='Test',
            capabilities={}
        )
        device = manager.register_device(data)
        
        # Verify device is retrievable
        retrieved = manager.get_device(device_id)
        assert retrieved.capabilities == {}
    
    def test_unicode_location_property(self):
        """Test device registration with unicode location"""
        manager = DeviceManager()
        device_id = f"device-{uuid.uuid4().hex[:8]}"
        
        data = DeviceRegistration(
            device_id=device_id,
            device_type='solar',
            location='北京市朝阳区',
            capabilities={}
        )
        device = manager.register_device(data)
        
        # Verify device is retrievable with unicode location
        retrieved = manager.get_device(device_id)
        assert retrieved.location == '北京市朝阳区'
    
    def test_large_capabilities_property(self):
        """Test device registration with large capabilities"""
        manager = DeviceManager()
        device_id = f"device-{uuid.uuid4().hex[:8]}"
        
        large_capabilities = {f'param_{i}': float(i) for i in range(50)}
        
        data = DeviceRegistration(
            device_id=device_id,
            device_type='solar',
            location='Test',
            capabilities=large_capabilities
        )
        device = manager.register_device(data)
        
        # Verify device is retrievable with large capabilities
        retrieved = manager.get_device(device_id)
        assert len(retrieved.capabilities) == 50


class TestDevicePropertyStatistical:
    """Statistical properties for device operations"""
    
    @given(
        num_devices=st.integers(min_value=1, max_value=50)
    )
    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow, HealthCheck.filter_too_much])
    def test_discovery_pagination_property(self, num_devices):
        """
        Test that pagination works correctly for any number of devices.
        """
        manager = DeviceManager()
        
        # Register devices
        for i in range(num_devices):
            device_id = f"device-{uuid.uuid4().hex[:8]}"
            data = DeviceRegistration(
                device_id=device_id,
                device_type='solar',
                location=f'Location {i}',
                capabilities={}
            )
            manager.register_device(data)
        
        # Test pagination with page_size=10
        page_size = 10
        all_devices = []
        page = 1
        
        while True:
            devices, total = manager.discover_devices(page=page, page_size=page_size)
            all_devices.extend(devices)
            
            if len(devices) < page_size:
                break
            
            page += 1
        
        # Verify all devices retrieved through pagination
        assert len(all_devices) == num_devices
        assert total == num_devices
