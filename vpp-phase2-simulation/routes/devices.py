"""
Device Emulator API Routes

Provides REST endpoints for device simulator control, state queries, and command processing.

Requirements:
- 9.1: Standard interface implementation
- 9.2: Command processing
- 9.3: State retrieval
- 9.4: VPP Master API compatibility
- 9.5: Concurrent operations support
"""

from bottle import Bottle, request, response, HTTPError
from typing import Dict, Any, List, Optional
import json
import logging
from datetime import datetime

from services.device_emulator import DeviceCommand, CommandResult, DeviceState
from services.power_gen_simulator import SolarSimulator, WindSimulator
from services.storage_simulator import BatterySimulator
from services.demand_simulator import LoadSimulator
from utils.errors import ValidationError, SimulatorError
from utils.logger import get_logger

logger = get_logger(__name__)

# Global device registry
device_registry: Dict[str, Any] = {}


def create_device_routes(app: Bottle) -> None:
    """
    Register device emulator API routes.
    
    Args:
        app: Bottle application instance
    """
    
    @app.post('/api/v1/devices')
    def create_device():
        """
        Create a new device emulator.
        
        Request body:
        {
            "device_id": "dev-001",
            "device_type": "solar|wind|battery|load",
            "parameters": {...}
        }
        """
        try:
            data = request.json
            
            # Validate required fields
            if not data.get('device_id'):
                raise ValidationError("device_id is required")
            if not data.get('device_type'):
                raise ValidationError("device_type is required")
            if not data.get('parameters'):
                raise ValidationError("parameters is required")
            
            device_id = data['device_id']
            device_type = data['device_type']
            parameters = data['parameters']
            
            # Check if device already exists
            if device_id in device_registry:
                raise ValidationError(f"Device already exists: {device_id}")
            
            # Create appropriate device simulator
            device = None
            if device_type == 'solar':
                device = SolarSimulator(device_id, parameters)
            elif device_type == 'wind':
                device = WindSimulator(device_id, parameters)
            elif device_type == 'battery':
                device = BatterySimulator(device_id, parameters)
            elif device_type == 'load':
                device = LoadSimulator(device_id, parameters)
            else:
                raise ValidationError(f"Unknown device type: {device_type}")
            
            # Initialize device
            device.initialize()
            
            # Register device
            device_registry[device_id] = device
            
            response.status = 201
            return {
                'device_id': device_id,
                'device_type': device_type,
                'status': 'created',
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except ValidationError as e:
            response.status = 400
            return {'error': str(e)}
        except Exception as e:
            logger.error(f"Failed to create device: {str(e)}")
            response.status = 500
            return {'error': 'Failed to create device'}
    
    @app.get('/api/v1/devices/<device_id>')
    def get_device(device_id: str):
        """
        Get device state.
        
        Returns:
        {
            "device_id": "dev-001",
            "device_type": "solar",
            "state": {...},
            "timestamp": "2026-02-16T10:30:00Z"
        }
        """
        try:
            if device_id not in device_registry:
                raise ValidationError(f"Device not found: {device_id}")
            
            device = device_registry[device_id]
            state = device.get_state()
            
            return {
                'device_id': state.device_id,
                'device_type': state.device_type,
                'state': state.state_data,
                'timestamp': state.timestamp.isoformat()
            }
            
        except ValidationError as e:
            response.status = 404
            return {'error': str(e)}
        except Exception as e:
            logger.error(f"Failed to get device: {str(e)}")
            response.status = 500
            return {'error': 'Failed to get device'}
    
    @app.get('/api/v1/devices')
    def list_devices():
        """
        List all devices.
        
        Returns:
        {
            "devices": [
                {"device_id": "dev-001", "device_type": "solar", ...},
                ...
            ],
            "count": 1
        }
        """
        try:
            devices = []
            for device_id, device in device_registry.items():
                state = device.get_state()
                devices.append({
                    'device_id': state.device_id,
                    'device_type': state.device_type,
                    'state': state.state_data,
                    'timestamp': state.timestamp.isoformat()
                })
            
            return {
                'devices': devices,
                'count': len(devices)
            }
            
        except Exception as e:
            logger.error(f"Failed to list devices: {str(e)}")
            response.status = 500
            return {'error': 'Failed to list devices'}
    
    @app.post('/api/v1/devices/<device_id>/commands')
    def send_command(device_id: str):
        """
        Send command to device.
        
        Request body:
        {
            "command_type": "charge|discharge|set_output",
            "parameters": {...}
        }
        """
        try:
            if device_id not in device_registry:
                raise ValidationError(f"Device not found: {device_id}")
            
            data = request.json
            
            # Validate required fields
            if not data.get('command_type'):
                raise ValidationError("command_type is required")
            
            device = device_registry[device_id]
            
            # Create command
            command = DeviceCommand(
                command_type=data['command_type'],
                parameters=data.get('parameters', {})
            )
            
            # Execute command
            result = device.set_command(command)
            
            response.status = 200 if result.success else 400
            return {
                'device_id': device_id,
                'success': result.success,
                'message': result.message,
                'data': result.data,
                'timestamp': result.timestamp.isoformat()
            }
            
        except ValidationError as e:
            response.status = 404 if "not found" in str(e) else 400
            return {'error': str(e)}
        except Exception as e:
            logger.error(f"Failed to send command: {str(e)}")
            response.status = 500
            return {'error': 'Failed to send command'}
    
    @app.get('/api/v1/devices/<device_id>/capabilities')
    def get_capabilities(device_id: str):
        """
        Get device capabilities.
        
        Returns:
        {
            "device_id": "dev-001",
            "capabilities": {...}
        }
        """
        try:
            if device_id not in device_registry:
                raise ValidationError(f"Device not found: {device_id}")
            
            device = device_registry[device_id]
            capabilities = device.get_capabilities()
            
            return {
                'device_id': device_id,
                'capabilities': capabilities
            }
            
        except ValidationError as e:
            response.status = 404
            return {'error': str(e)}
        except Exception as e:
            logger.error(f"Failed to get capabilities: {str(e)}")
            response.status = 500
            return {'error': 'Failed to get capabilities'}
    
    @app.post('/api/v1/devices/<device_id>/reset')
    def reset_device(device_id: str):
        """
        Reset device to initial state.
        """
        try:
            if device_id not in device_registry:
                raise ValidationError(f"Device not found: {device_id}")
            
            device = device_registry[device_id]
            device.reset()
            
            return {
                'device_id': device_id,
                'status': 'reset',
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except ValidationError as e:
            response.status = 404
            return {'error': str(e)}
        except Exception as e:
            logger.error(f"Failed to reset device: {str(e)}")
            response.status = 500
            return {'error': 'Failed to reset device'}
    
    @app.delete('/api/v1/devices/<device_id>')
    def delete_device(device_id: str):
        """
        Delete device.
        """
        try:
            if device_id not in device_registry:
                raise ValidationError(f"Device not found: {device_id}")
            
            del device_registry[device_id]
            
            return {
                'device_id': device_id,
                'status': 'deleted',
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except ValidationError as e:
            response.status = 404
            return {'error': str(e)}
        except Exception as e:
            logger.error(f"Failed to delete device: {str(e)}")
            response.status = 500
            return {'error': 'Failed to delete device'}
    
    @app.post('/api/v1/devices/<device_id>/update')
    def update_device(device_id: str):
        """
        Update device state for time step.
        
        Request body:
        {
            "time_delta": 1.0
        }
        """
        try:
            if device_id not in device_registry:
                raise ValidationError(f"Device not found: {device_id}")
            
            data = request.json
            time_delta = data.get('time_delta', 1.0)
            
            if time_delta <= 0:
                raise ValidationError("time_delta must be positive")
            
            device = device_registry[device_id]
            device.update(time_delta)
            
            state = device.get_state()
            
            return {
                'device_id': device_id,
                'state': state.state_data,
                'timestamp': state.timestamp.isoformat()
            }
            
        except ValidationError as e:
            response.status = 400 if "not found" not in str(e) else 404
            return {'error': str(e)}
        except Exception as e:
            logger.error(f"Failed to update device: {str(e)}")
            response.status = 500
            return {'error': 'Failed to update device'}
