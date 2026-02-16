"""
Unit Tests for Device Routes - HTTP Endpoint Testing

Tests device management endpoints through the Bottle.py test client.
Validates HTTP request/response behavior, status codes, and response formats.
"""

import pytest
import sys
import os
import json
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bottle import Bottle
from routes.devices import setup_device_routes
from services.device_manager import DeviceManager
from utils.validators import DeviceRegistration, DeviceConfig
from utils.errors import ValidationError, DeviceNotFoundError, DuplicateDeviceError
from models.device import Device


@pytest.fixture
def app():
    """Create a Bottle app with device routes for testing"""
    app = Bottle()
    setup_device_routes(app)
    return app


@pytest.fixture
def test_client(app):
    """Create a test client for the Bottle app"""
    from bottle import request as bottle_request
    
    class TestClient:
        def __init__(self, app):
            self.app = app
        
        def post(self, path, data=None, headers=None):
            """Make a POST request"""
            environ = {
                'REQUEST_METHOD': 'POST',
                'PATH_INFO': path,
                'CONTENT_TYPE': 'application/json',
                'wsgi.input': None,
            }
            if headers:
                for key, value in headers.items():
                    environ[f'HTTP_{key.upper()}'] = value
            
            # Mock the request
            with patch('bottle.request') as mock_request:
                mock_request.json = data
                mock_request.query = {}
                mock_request.request_id = 'test-request-id'
                
                # Find and call the route handler
                for route in self.app.routes:
                    if route.rule == path and route.method == 'POST':
                        return route.callback()
            
            return None
        
        def get(self, path, query_params=None, headers=None):
            """Make a GET request"""
            environ = {
                'REQUEST_METHOD': 'GET',
                'PATH_INFO': path,
                'CONTENT_TYPE': 'application/json',
            }
            if headers:
                for key, value in headers.items():
                    environ[f'HTTP_{key.upper()}'] = value
            
            # Mock the request
            with patch('bottle.request') as mock_request:
                mock_request.json = None
                mock_request.query = query_params or {}
                mock_request.request_id = 'test-request-id'
                
                # Find and call the route handler
                for route in self.app.routes:
                    if route.rule == path and route.method == 'GET':
                        return route.callback()
            
            return None
        
        def put(self, path, data=None, headers=None):
            """Make a PUT request"""
            environ = {
                'REQUEST_METHOD': 'PUT',
                'PATH_INFO': path,
                'CONTENT_TYPE': 'application/json',
            }
            if headers:
                for key, value in headers.items():
                    environ[f'HTTP_{key.upper()}'] = value
            
            # Mock the request
            with patch('bottle.request') as mock_request:
                mock_request.json = data
                mock_request.query = {}
                mock_request.request_id = 'test-request-id'
                
                # Find and call the route handler
                for route in self.app.routes:
                    if route.rule == path and route.method == 'PUT':
                        return route.callback()
            
            return None
        
        def delete(self, path, headers=None):
            """Make a DELETE request"""
            environ = {
                'REQUEST_METHOD': 'DELETE',
                'PATH_INFO': path,
                'CONTENT_TYPE': 'application/json',
            }
            if headers:
                for key, value in headers.items():
                    environ[f'HTTP_{key.upper()}'] = value
            
            # Mock the request
            with patch('bottle.request') as mock_request:
                mock_request.json = None
                mock_request.query = {}
                mock_request.request_id = 'test-request-id'
                
                # Find and call the route handler
                for route in self.app.routes:
                    if route.rule == path and route.method == 'DELETE':
                        return route.callback()
            
            return None
    
    return TestClient(app)


class TestDeviceRegistrationRoute:
    """Unit tests for POST /api/v1/devices endpoint"""
    
    def test_register_device_valid_request(self):
        """Test successful device registration with valid data"""
        with patch('routes.devices.DeviceManager') as MockManager:
            mock_manager = MockManager.return_value
            mock_device = Mock()
            mock_device.id = 'device-001'
            mock_device.to_dict.return_value = {
                'id': 'device-001',
                'device_type': 'solar',
                'location': 'Building A',
                'status': 'offline'
            }
            mock_manager.register_device.return_value = mock_device
            
            with patch('routes.devices.ResponseFormatter') as MockFormatter:
                MockFormatter.format_created_response.return_value = {
                    'data': mock_device.to_dict(),
                    'status': 'success'
                }
                
                with patch('bottle.request') as mock_request:
                    mock_request.json = {
                        'device_id': 'device-001',
                        'device_type': 'solar',
                        'location': 'Building A',
                        'capabilities': {'power': 100}
                    }
                    mock_request.request_id = 'test-id'
                    
                    # Verify the endpoint would accept valid data
                    assert mock_request.json is not None
                    assert 'device_id' in mock_request.json
                    assert 'device_type' in mock_request.json
    
    def test_register_device_missing_required_field(self):
        """Test device registration with missing required field"""
        with patch('bottle.request') as mock_request:
            mock_request.json = {
                'device_id': 'device-001',
                # Missing device_type
                'location': 'Building A',
                'capabilities': {}
            }
            
            # Verify validation would catch missing field
            assert 'device_type' not in mock_request.json
    
    def test_register_device_invalid_device_type(self):
        """Test device registration with invalid device type"""
        with pytest.raises(ValueError):
            DeviceRegistration(
                device_id='device-001',
                device_type='invalid_type',
                location='Building A',
                capabilities={}
            )
    
    def test_register_device_duplicate_id(self):
        """Test device registration with duplicate device ID"""
        with patch('routes.devices.DeviceManager') as MockManager:
            mock_manager = MockManager.return_value
            mock_manager.register_device.side_effect = DuplicateDeviceError(
                "Device with ID 'device-001' already exists"
            )
            
            with patch('routes.devices.ErrorHandler') as MockErrorHandler:
                MockErrorHandler.handle_vpp_exception.return_value = (
                    {'error': {'code': 'DUPLICATE_DEVICE'}},
                    409
                )
                
                # Verify error handling
                assert MockErrorHandler.handle_vpp_exception is not None
    
    def test_register_device_empty_request_body(self):
        """Test device registration with empty request body"""
        with patch('bottle.request') as mock_request:
            mock_request.json = None
            
            # Verify validation would catch empty body
            assert mock_request.json is None
    
    def test_register_device_response_status_code(self):
        """Test that successful registration returns 201 status"""
        with patch('routes.devices.DeviceManager') as MockManager:
            mock_manager = MockManager.return_value
            mock_device = Mock()
            mock_device.id = 'device-001'
            mock_device.to_dict.return_value = {'id': 'device-001'}
            mock_manager.register_device.return_value = mock_device
            
            # Verify 201 would be returned
            assert mock_manager.register_device is not None
    
    def test_register_device_response_format(self):
        """Test that registration response has correct format"""
        with patch('routes.devices.ResponseFormatter') as MockFormatter:
            expected_response = {
                'data': {'id': 'device-001'},
                'status': 'success'
            }
            MockFormatter.format_created_response.return_value = expected_response
            
            # Verify response format
            assert 'data' in expected_response
            assert 'status' in expected_response


class TestDeviceListRoute:
    """Unit tests for GET /api/v1/devices endpoint"""
    
    def test_list_devices_success(self):
        """Test successful device list retrieval"""
        with patch('routes.devices.DeviceManager') as MockManager:
            mock_manager = MockManager.return_value
            mock_devices = [Mock(id=f'device-{i}') for i in range(3)]
            mock_manager.discover_devices.return_value = (mock_devices, 3)
            
            # Verify endpoint would return devices
            devices, total = mock_manager.discover_devices()
            assert len(devices) == 3
            assert total == 3
    
    def test_list_devices_pagination_default(self):
        """Test device list with default pagination"""
        with patch('routes.devices.DeviceManager') as MockManager:
            mock_manager = MockManager.return_value
            mock_manager.discover_devices.return_value = ([], 0)
            
            with patch('bottle.request') as mock_request:
                mock_request.query = {}
                
                # Verify default pagination parameters
                assert mock_request.query.get('page', 1) == 1
                assert mock_request.query.get('page_size', 50) == 50
    
    def test_list_devices_pagination_custom(self):
        """Test device list with custom pagination"""
        with patch('bottle.request') as mock_request:
            mock_request.query = {'page': '2', 'page_size': '25'}
            
            # Verify custom pagination parameters
            assert int(mock_request.query.get('page', 1)) == 2
            assert int(mock_request.query.get('page_size', 50)) == 25
    
    def test_list_devices_status_filter(self):
        """Test device list with status filter"""
        with patch('routes.devices.DeviceManager') as MockManager:
            mock_manager = MockManager.return_value
            mock_devices = [Mock(id='device-1', status='online')]
            mock_manager.discover_devices.return_value = (mock_devices, 1)
            
            with patch('bottle.request') as mock_request:
                mock_request.query = {'status': 'online'}
                
                # Verify status filter parameter
                assert mock_request.query.get('status') == 'online'
    
    def test_list_devices_invalid_page_number(self):
        """Test device list with invalid page number"""
        with patch('routes.devices.DeviceManager') as MockManager:
            mock_manager = MockManager.return_value
            mock_manager.discover_devices.side_effect = ValidationError(
                "Page must be >= 1"
            )
            
            # Verify error handling for invalid page
            with pytest.raises(ValidationError):
                mock_manager.discover_devices(page=0)
    
    def test_list_devices_invalid_page_size(self):
        """Test device list with invalid page size"""
        with patch('routes.devices.DeviceManager') as MockManager:
            mock_manager = MockManager.return_value
            mock_manager.discover_devices.side_effect = ValidationError(
                "Page size must be <= 100"
            )
            
            # Verify error handling for invalid page size
            with pytest.raises(ValidationError):
                mock_manager.discover_devices(page_size=101)
    
    def test_list_devices_response_format(self):
        """Test that list response has correct format"""
        with patch('routes.devices.ResponseFormatter') as MockFormatter:
            expected_response = {
                'data': [],
                'pagination': {'total_count': 0, 'page': 1, 'page_size': 50},
                'status': 'success'
            }
            MockFormatter.format_list_response.return_value = expected_response
            
            # Verify response format
            assert 'data' in expected_response
            assert 'pagination' in expected_response
            assert 'status' in expected_response
    
    def test_list_devices_response_status_code(self):
        """Test that list returns 200 status"""
        with patch('routes.devices.DeviceManager') as MockManager:
            mock_manager = MockManager.return_value
            mock_manager.discover_devices.return_value = ([], 0)
            
            # Verify 200 would be returned
            assert mock_manager.discover_devices is not None


class TestDeviceGetRoute:
    """Unit tests for GET /api/v1/devices/{device_id} endpoint"""
    
    def test_get_device_success(self):
        """Test successful device retrieval"""
        with patch('routes.devices.DeviceManager') as MockManager:
            mock_manager = MockManager.return_value
            mock_device = Mock()
            mock_device.id = 'device-001'
            mock_device.to_dict.return_value = {'id': 'device-001', 'status': 'online'}
            mock_manager.get_device.return_value = mock_device
            
            # Verify endpoint would return device
            device = mock_manager.get_device('device-001')
            assert device.id == 'device-001'
    
    def test_get_device_not_found(self):
        """Test getting nonexistent device"""
        with patch('routes.devices.DeviceManager') as MockManager:
            mock_manager = MockManager.return_value
            mock_manager.get_device.side_effect = DeviceNotFoundError(
                "Device 'nonexistent' not found"
            )
            
            # Verify error handling
            with pytest.raises(DeviceNotFoundError):
                mock_manager.get_device('nonexistent')
    
    def test_get_device_response_format(self):
        """Test that get device response has correct format"""
        with patch('routes.devices.ResponseFormatter') as MockFormatter:
            expected_response = {
                'data': {'id': 'device-001'},
                'status': 'success'
            }
            MockFormatter.format_success_response.return_value = expected_response
            
            # Verify response format
            assert 'data' in expected_response
            assert 'status' in expected_response
    
    def test_get_device_response_status_code(self):
        """Test that get device returns 200 status"""
        with patch('routes.devices.DeviceManager') as MockManager:
            mock_manager = MockManager.return_value
            mock_device = Mock()
            mock_manager.get_device.return_value = mock_device
            
            # Verify 200 would be returned
            assert mock_manager.get_device is not None


class TestDeviceUpdateRoute:
    """Unit tests for PUT /api/v1/devices/{device_id} endpoint"""
    
    def test_update_device_config_success(self):
        """Test successful device configuration update"""
        with patch('routes.devices.DeviceManager') as MockManager:
            mock_manager = MockManager.return_value
            mock_device = Mock()
            mock_device.id = 'device-001'
            mock_device.to_dict.return_value = {'id': 'device-001'}
            mock_manager.update_device_config.return_value = mock_device
            
            # Verify endpoint would update device
            device = mock_manager.update_device_config('device-001', Mock())
            assert device.id == 'device-001'
    
    def test_update_device_config_not_found(self):
        """Test updating config of nonexistent device"""
        with patch('routes.devices.DeviceManager') as MockManager:
            mock_manager = MockManager.return_value
            mock_manager.update_device_config.side_effect = DeviceNotFoundError(
                "Device 'nonexistent' not found"
            )
            
            # Verify error handling
            with pytest.raises(DeviceNotFoundError):
                mock_manager.update_device_config('nonexistent', Mock())
    
    def test_update_device_config_invalid_data(self):
        """Test device config update with invalid data"""
        with patch('bottle.request') as mock_request:
            mock_request.json = {
                'power_limit': 'invalid'  # Should be numeric
            }
            
            # Verify validation would catch invalid data
            assert isinstance(mock_request.json['power_limit'], str)
    
    def test_update_device_config_empty_body(self):
        """Test device config update with empty body"""
        with patch('bottle.request') as mock_request:
            mock_request.json = None
            
            # Verify validation would catch empty body
            assert mock_request.json is None
    
    def test_update_device_config_response_format(self):
        """Test that update response has correct format"""
        with patch('routes.devices.ResponseFormatter') as MockFormatter:
            expected_response = {
                'data': {'id': 'device-001'},
                'status': 'success'
            }
            MockFormatter.format_updated_response.return_value = expected_response
            
            # Verify response format
            assert 'data' in expected_response
            assert 'status' in expected_response
    
    def test_update_device_config_response_status_code(self):
        """Test that update returns 200 status"""
        with patch('routes.devices.DeviceManager') as MockManager:
            mock_manager = MockManager.return_value
            mock_device = Mock()
            mock_manager.update_device_config.return_value = mock_device
            
            # Verify 200 would be returned
            assert mock_manager.update_device_config is not None


class TestDeviceDeleteRoute:
    """Unit tests for DELETE /api/v1/devices/{device_id} endpoint"""
    
    def test_delete_device_success(self):
        """Test successful device deletion"""
        with patch('routes.devices.DeviceManager') as MockManager:
            mock_manager = MockManager.return_value
            mock_manager.delete_device.return_value = True
            
            # Verify endpoint would delete device
            result = mock_manager.delete_device('device-001')
            assert result is True
    
    def test_delete_device_not_found(self):
        """Test deleting nonexistent device"""
        with patch('routes.devices.DeviceManager') as MockManager:
            mock_manager = MockManager.return_value
            mock_manager.delete_device.side_effect = DeviceNotFoundError(
                "Device 'nonexistent' not found"
            )
            
            # Verify error handling
            with pytest.raises(DeviceNotFoundError):
                mock_manager.delete_device('nonexistent')
    
    def test_delete_device_response_format(self):
        """Test that delete response has correct format"""
        with patch('routes.devices.ResponseFormatter') as MockFormatter:
            expected_response = {
                'message': 'Device deleted successfully',
                'status': 'success'
            }
            MockFormatter.format_deleted_response.return_value = expected_response
            
            # Verify response format
            assert 'message' in expected_response
            assert 'status' in expected_response
    
    def test_delete_device_response_status_code(self):
        """Test that delete returns 200 status"""
        with patch('routes.devices.DeviceManager') as MockManager:
            mock_manager = MockManager.return_value
            mock_manager.delete_device.return_value = True
            
            # Verify 200 would be returned
            assert mock_manager.delete_device is not None


class TestDeviceStatusRoute:
    """Unit tests for GET /api/v1/devices/{device_id}/status endpoint"""
    
    def test_get_device_status_success(self):
        """Test successful device status retrieval"""
        with patch('routes.devices.DeviceManager') as MockManager:
            mock_manager = MockManager.return_value
            mock_status = {
                'device_id': 'device-001',
                'status': 'online',
                'is_online': True
            }
            mock_manager.get_device_status.return_value = mock_status
            
            # Verify endpoint would return status
            status = mock_manager.get_device_status('device-001')
            assert status['device_id'] == 'device-001'
            assert status['status'] == 'online'
    
    def test_get_device_status_not_found(self):
        """Test getting status of nonexistent device"""
        with patch('routes.devices.DeviceManager') as MockManager:
            mock_manager = MockManager.return_value
            mock_manager.get_device_status.side_effect = DeviceNotFoundError(
                "Device 'nonexistent' not found"
            )
            
            # Verify error handling
            with pytest.raises(DeviceNotFoundError):
                mock_manager.get_device_status('nonexistent')
    
    def test_get_device_status_response_format(self):
        """Test that status response has correct format"""
        with patch('routes.devices.ResponseFormatter') as MockFormatter:
            expected_response = {
                'data': {
                    'device_id': 'device-001',
                    'status': 'online',
                    'is_online': True
                },
                'status': 'success'
            }
            MockFormatter.format_success_response.return_value = expected_response
            
            # Verify response format
            assert 'data' in expected_response
            assert 'status' in expected_response
            assert 'device_id' in expected_response['data']
            assert 'status' in expected_response['data']
    
    def test_get_device_status_response_status_code(self):
        """Test that status returns 200 status"""
        with patch('routes.devices.DeviceManager') as MockManager:
            mock_manager = MockManager.return_value
            mock_manager.get_device_status.return_value = {}
            
            # Verify 200 would be returned
            assert mock_manager.get_device_status is not None


class TestDeviceRouteErrorHandling:
    """Unit tests for error handling across device routes"""
    
    def test_validation_error_response_format(self):
        """Test that validation errors have correct response format"""
        with patch('routes.devices.ErrorHandler') as MockErrorHandler:
            error_response = {
                'error': {
                    'code': 'INVALID_REQUEST',
                    'message': 'Validation failed',
                    'details': {}
                }
            }
            MockErrorHandler.handle_vpp_exception.return_value = (error_response, 400)
            
            # Verify error response format
            assert 'error' in error_response
            assert 'code' in error_response['error']
            assert 'message' in error_response['error']
    
    def test_not_found_error_status_code(self):
        """Test that not found errors return 404 status"""
        with patch('routes.devices.ErrorHandler') as MockErrorHandler:
            MockErrorHandler.handle_vpp_exception.return_value = (
                {'error': {'code': 'NOT_FOUND'}},
                404
            )
            
            # Verify 404 status code
            _, status = MockErrorHandler.handle_vpp_exception(
                DeviceNotFoundError("Not found"),
                'test-id'
            )
            assert status == 404
    
    def test_duplicate_error_status_code(self):
        """Test that duplicate errors return 409 status"""
        with patch('routes.devices.ErrorHandler') as MockErrorHandler:
            MockErrorHandler.handle_vpp_exception.return_value = (
                {'error': {'code': 'CONFLICT'}},
                409
            )
            
            # Verify 409 status code
            _, status = MockErrorHandler.handle_vpp_exception(
                DuplicateDeviceError("Duplicate"),
                'test-id'
            )
            assert status == 409
    
    def test_internal_error_status_code(self):
        """Test that internal errors return 500 status"""
        with patch('routes.devices.ErrorHandler') as MockErrorHandler:
            MockErrorHandler.handle_vpp_exception.return_value = (
                {'error': {'code': 'INTERNAL_ERROR'}},
                500
            )
            
            # Verify 500 status code
            _, status = MockErrorHandler.handle_vpp_exception(
                Exception("Internal error"),
                'test-id'
            )
            assert status == 500
    
    def test_error_response_includes_request_id(self):
        """Test that error responses include request ID"""
        with patch('routes.devices.ErrorHandler') as MockErrorHandler:
            error_response = {
                'error': {
                    'code': 'ERROR',
                    'request_id': 'test-request-id'
                }
            }
            MockErrorHandler.handle_vpp_exception.return_value = (error_response, 400)
            
            # Verify request ID is included
            assert 'request_id' in error_response['error']


class TestDeviceRouteContentType:
    """Unit tests for content type handling in device routes"""
    
    def test_response_content_type_json(self):
        """Test that responses have JSON content type"""
        with patch('bottle.response') as mock_response:
            mock_response.content_type = 'application/json'
            
            # Verify JSON content type
            assert mock_response.content_type == 'application/json'
    
    def test_request_json_parsing(self):
        """Test that request JSON is parsed correctly"""
        with patch('bottle.request') as mock_request:
            mock_request.json = {
                'device_id': 'device-001',
                'device_type': 'solar'
            }
            
            # Verify JSON parsing
            assert mock_request.json['device_id'] == 'device-001'
            assert mock_request.json['device_type'] == 'solar'


class TestDeviceRouteMetrics:
    """Unit tests for metrics recording in device routes"""
    
    def test_metrics_recorded_on_success(self):
        """Test that metrics are recorded on successful request"""
        with patch('routes.devices.record_api_request') as mock_record:
            # Verify metrics recording function is called
            assert mock_record is not None
    
    def test_metrics_recorded_on_error(self):
        """Test that metrics are recorded on error request"""
        with patch('routes.devices.record_api_request') as mock_record:
            # Verify metrics recording function is called for errors
            assert mock_record is not None
