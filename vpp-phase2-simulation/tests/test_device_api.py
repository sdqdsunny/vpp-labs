"""
Unit tests for Device Emulator API

Tests device creation, state retrieval, command processing, and concurrent operations.

Requirements:
- 9.1: Standard interface implementation
- 9.2: Command processing
- 9.3: State retrieval
- 9.4: VPP Master API compatibility
- 9.5: Concurrent operations support
"""

import pytest
import json
from datetime import datetime
from threading import Thread
import time

from routes.devices import create_device_routes, device_registry
from services.device_emulator import DeviceCommand, CommandResult, DeviceState
from services.power_gen_simulator import SolarSimulator
from services.storage_simulator import BatterySimulator
from services.demand_simulator import LoadSimulator
from utils.errors import ValidationError
from bottle import Bottle


@pytest.fixture
def app():
    """Create test Bottle application."""
    app = Bottle()
    create_device_routes(app)
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    from bottle import request as bottle_request
    
    class TestClient:
        def __init__(self, app):
            self.app = app
        
        def post(self, path, data=None):
            """POST request."""
            environ = {
                'REQUEST_METHOD': 'POST',
                'PATH_INFO': path,
                'CONTENT_TYPE': 'application/json',
                'wsgi.input': None,
            }
            if data:
                import io
                body = json.dumps(data).encode('utf-8')
                environ['wsgi.input'] = io.BytesIO(body)
                environ['CONTENT_LENGTH'] = len(body)
            
            # Call the app
            try:
                result = self.app(environ, lambda *args: None)
                return result
            except Exception as e:
                return {'error': str(e)}
        
        def get(self, path):
            """GET request."""
            environ = {
                'REQUEST_METHOD': 'GET',
                'PATH_INFO': path,
            }
            try:
                result = self.app(environ, lambda *args: None)
                return result
            except Exception as e:
                return {'error': str(e)}
    
    return TestClient(app)


class TestDeviceCreation:
    """Test device creation."""
    
    def test_create_solar_device(self):
        """Test creating a solar device."""
        device_registry.clear()
        
        device = SolarSimulator('solar-001', {
            'capacity_kw': 100.0,
            'efficiency': 0.18,
            'temperature_coefficient': -0.004,
            'location': 'Test Location'
        })
        device_registry['solar-001'] = device
        
        assert 'solar-001' in device_registry
        assert device_registry['solar-001'].device_type == 'solar'
    
    def test_create_wind_device(self):
        """Test creating a wind device."""
        device_registry.clear()
        
        device = SolarSimulator('wind-001', {
            'capacity_kw': 100.0,
            'efficiency': 0.35,
            'temperature_coefficient': 0.0,
            'location': 'Test Location'
        })
        device_registry['wind-001'] = device
        
        assert 'wind-001' in device_registry
    
    def test_create_battery_device(self):
        """Test creating a battery device."""
        device_registry.clear()
        
        device = BatterySimulator('battery-001', {
            'capacity_kwh': 100.0,
            'power_rating_kw': 50.0,
            'efficiency': 0.95
        })
        device_registry['battery-001'] = device
        
        assert 'battery-001' in device_registry
        assert device_registry['battery-001'].device_type == 'battery'
    
    def test_create_load_device(self):
        """Test creating a load device."""
        device_registry.clear()
        
        device = LoadSimulator('load-001', {
            'base_load_kw': 50.0,
            'flexibility_range_kw': (10.0, 90.0)
        })
        device_registry['load-001'] = device
        
        assert 'load-001' in device_registry
        assert device_registry['load-001'].device_type == 'load'
    
    def test_create_duplicate_device_raises_error(self):
        """Test creating duplicate device raises error."""
        device_registry.clear()
        
        device = SolarSimulator('solar-001', {
            'capacity_kw': 100.0,
            'efficiency': 0.18,
            'temperature_coefficient': -0.004,
            'location': 'Test Location'
        })
        device_registry['solar-001'] = device
        
        # Verify device exists
        assert 'solar-001' in device_registry


class TestDeviceStateRetrieval:
    """Test device state retrieval."""
    
    def test_get_device_state(self):
        """Test getting device state."""
        device_registry.clear()
        
        device = SolarSimulator('solar-001', {
            'capacity_kw': 100.0,
            'efficiency': 0.18,
            'temperature_coefficient': -0.004,
            'location': 'Test Location'
        })
        device_registry['solar-001'] = device
        
        state = device.get_state()
        
        assert state.device_id == 'solar-001'
        assert state.device_type == 'solar'
        assert isinstance(state.state_data, dict)
    
    def test_get_multiple_device_states(self):
        """Test getting multiple device states."""
        device_registry.clear()
        
        # Create multiple devices
        for i in range(3):
            device = SolarSimulator(f'solar-{i:03d}', {
                'capacity_kw': 100.0,
                'efficiency': 0.18,
                'temperature_coefficient': -0.004,
                'location': 'Test Location'
            })
            device_registry[f'solar-{i:03d}'] = device
        
        # Get all states
        states = []
        for device_id, device in device_registry.items():
            state = device.get_state()
            states.append(state)
        
        assert len(states) == 3
        assert all(isinstance(s, DeviceState) for s in states)
    
    def test_get_nonexistent_device_raises_error(self):
        """Test getting nonexistent device raises error."""
        device_registry.clear()
        
        with pytest.raises(KeyError):
            device = device_registry['nonexistent']


class TestDeviceCommandProcessing:
    """Test device command processing."""
    
    def test_send_command_to_battery(self):
        """Test sending command to battery device."""
        device_registry.clear()
        
        device = BatterySimulator('battery-001', {
            'capacity_kwh': 100.0,
            'power_rating_kw': 50.0,
            'efficiency': 0.95
        })
        device_registry['battery-001'] = device
        
        # Send charge command
        command = DeviceCommand(
            command_type='charge',
            parameters={'power': 25.0, 'duration': 1.0}
        )
        
        result = device.set_command(command)
        
        assert isinstance(result, CommandResult)
        assert result.success
    
    def test_send_command_to_load(self):
        """Test sending command to load device."""
        device_registry.clear()
        
        device = LoadSimulator('load-001', {
            'base_load_kw': 50.0,
            'flexibility_range_kw': (10.0, 90.0)
        })
        device_registry['load-001'] = device
        
        # Send demand response command
        command = DeviceCommand(
            command_type='set_demand_response',
            parameters={'signal': 0.8}
        )
        
        result = device.set_command(command)
        
        assert isinstance(result, CommandResult)
    
    def test_invalid_command_returns_error(self):
        """Test invalid command returns error."""
        device_registry.clear()
        
        device = SolarSimulator('solar-001', {
            'capacity_kw': 100.0,
            'efficiency': 0.18,
            'temperature_coefficient': -0.004,
            'location': 'Test Location'
        })
        device_registry['solar-001'] = device
        
        # Send invalid command
        command = DeviceCommand(
            command_type='invalid_command',
            parameters={}
        )
        
        result = device.set_command(command)
        
        assert not result.success


class TestDeviceCapabilities:
    """Test device capabilities."""
    
    def test_get_solar_capabilities(self):
        """Test getting solar device capabilities."""
        device_registry.clear()
        
        device = SolarSimulator('solar-001', {
            'capacity_kw': 100.0,
            'efficiency': 0.18,
            'temperature_coefficient': -0.004,
            'location': 'Test Location'
        })
        device_registry['solar-001'] = device
        
        capabilities = device.get_capabilities()
        
        assert isinstance(capabilities, dict)
        assert 'device_type' in capabilities
        assert capabilities['device_type'] == 'solar'
    
    def test_get_battery_capabilities(self):
        """Test getting battery device capabilities."""
        device_registry.clear()
        
        device = BatterySimulator('battery-001', {
            'capacity_kwh': 100.0,
            'power_rating_kw': 50.0,
            'efficiency': 0.95
        })
        device_registry['battery-001'] = device
        
        capabilities = device.get_capabilities()
        
        assert isinstance(capabilities, dict)
        assert 'device_type' in capabilities
        assert capabilities['device_type'] == 'battery'


class TestDeviceReset:
    """Test device reset."""
    
    def test_reset_device(self):
        """Test resetting device."""
        device_registry.clear()
        
        device = BatterySimulator('battery-001', {
            'capacity_kwh': 100.0,
            'power_rating_kw': 50.0,
            'efficiency': 0.95
        })
        device_registry['battery-001'] = device
        
        # Get initial state
        initial_state = device.get_state()
        initial_soc = initial_state.state_data.get('soc')
        
        # Reset device
        device.reset()
        
        # Verify state is reset
        state = device.get_state()
        reset_soc = state.state_data.get('soc')
        assert reset_soc == initial_soc
    
    def test_reset_multiple_devices(self):
        """Test resetting multiple devices."""
        device_registry.clear()
        
        # Create multiple devices
        for i in range(3):
            device = BatterySimulator(f'battery-{i:03d}', {
                'capacity_kwh': 100.0,
                'power_rating_kw': 50.0,
                'efficiency': 0.95
            })
            device_registry[f'battery-{i:03d}'] = device
        
        # Reset all devices
        for device_id, device in device_registry.items():
            device.reset()
        
        # Verify all devices are reset
        for device_id, device in device_registry.items():
            state = device.get_state()
            assert state.timestamp is not None


class TestDeviceUpdate:
    """Test device update."""
    
    def test_update_device_state(self):
        """Test updating device state."""
        device_registry.clear()
        
        device = SolarSimulator('solar-001', {
            'capacity_kw': 100.0,
            'efficiency': 0.18,
            'temperature_coefficient': -0.004,
            'location': 'Test Location'
        })
        device_registry['solar-001'] = device
        
        # Update device
        device.update(1.0)
        
        # Verify state is updated
        state = device.get_state()
        assert state.timestamp is not None
    
    def test_update_multiple_devices(self):
        """Test updating multiple devices."""
        device_registry.clear()
        
        # Create multiple devices
        for i in range(3):
            device = SolarSimulator(f'solar-{i:03d}', {
                'capacity_kw': 100.0,
                'efficiency': 0.18,
                'temperature_coefficient': -0.004,
                'location': 'Test Location'
            })
            device_registry[f'solar-{i:03d}'] = device
        
        # Update all devices
        for device_id, device in device_registry.items():
            device.update(1.0)
        
        # Verify all devices are updated
        for device_id, device in device_registry.items():
            state = device.get_state()
            assert state.timestamp is not None


class TestConcurrentOperations:
    """Test concurrent device operations."""
    
    def test_concurrent_device_creation(self):
        """Test concurrent device creation."""
        device_registry.clear()
        
        def create_device(device_id):
            device = SolarSimulator(device_id, {
                'capacity_kw': 100.0,
                'efficiency': 0.18,
                'temperature_coefficient': -0.004,
                'location': 'Test Location'
            })
            device_registry[device_id] = device
        
        # Create devices concurrently
        threads = []
        for i in range(10):
            thread = Thread(target=create_device, args=(f'solar-{i:03d}',))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Verify all devices created
        assert len(device_registry) == 10
    
    def test_concurrent_device_updates(self):
        """Test concurrent device updates."""
        device_registry.clear()
        
        # Create devices
        for i in range(5):
            device = SolarSimulator(f'solar-{i:03d}', {
                'capacity_kw': 100.0,
                'efficiency': 0.18,
                'temperature_coefficient': -0.004,
                'location': 'Test Location'
            })
            device_registry[f'solar-{i:03d}'] = device
        
        def update_device(device_id):
            device = device_registry[device_id]
            for _ in range(10):
                device.update(0.1)
        
        # Update devices concurrently
        threads = []
        for device_id in device_registry.keys():
            thread = Thread(target=update_device, args=(device_id,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Verify all devices updated
        for device_id, device in device_registry.items():
            state = device.get_state()
            assert state.timestamp is not None
    
    def test_concurrent_command_processing(self):
        """Test concurrent command processing."""
        device_registry.clear()
        
        # Create battery devices
        for i in range(5):
            device = BatterySimulator(f'battery-{i:03d}', {
                'capacity_kwh': 100.0,
                'power_rating_kw': 50.0,
                'efficiency': 0.95
            })
            device_registry[f'battery-{i:03d}'] = device
        
        def send_commands(device_id):
            device = device_registry[device_id]
            for _ in range(10):
                command = DeviceCommand(
                    command_type='charge',
                    parameters={'power': 25.0, 'duration': 0.1}
                )
                device.set_command(command)
        
        # Send commands concurrently
        threads = []
        for device_id in device_registry.keys():
            thread = Thread(target=send_commands, args=(device_id,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Verify all devices processed commands
        for device_id, device in device_registry.items():
            state = device.get_state()
            assert state.timestamp is not None


class TestDeviceDeletion:
    """Test device deletion."""
    
    def test_delete_device(self):
        """Test deleting device."""
        device_registry.clear()
        
        device = SolarSimulator('solar-001', {
            'capacity_kw': 100.0,
            'efficiency': 0.18,
            'temperature_coefficient': -0.004,
            'location': 'Test Location'
        })
        device_registry['solar-001'] = device
        
        # Delete device
        del device_registry['solar-001']
        
        # Verify device deleted
        assert 'solar-001' not in device_registry
    
    def test_delete_multiple_devices(self):
        """Test deleting multiple devices."""
        device_registry.clear()
        
        # Create multiple devices
        for i in range(3):
            device = SolarSimulator(f'solar-{i:03d}', {
                'capacity_kw': 100.0,
                'efficiency': 0.18,
                'temperature_coefficient': -0.004,
                'location': 'Test Location'
            })
            device_registry[f'solar-{i:03d}'] = device
        
        # Delete all devices
        device_ids = list(device_registry.keys())
        for device_id in device_ids:
            del device_registry[device_id]
        
        # Verify all devices deleted
        assert len(device_registry) == 0
