"""
Device Management API Routes

HTTP endpoints for device registration, discovery, and management.
"""

from bottle import request, response
from utils.logger import setup_logger
from utils.validators import DeviceRegistration, DeviceConfig
from utils.errors import ValidationError
from middleware.error_handler import ErrorHandler
from middleware.response_formatter import ResponseFormatter
from services.device_manager import DeviceManager
from utils.metrics import time_api_request, record_api_request

logger = setup_logger(__name__)


def setup_device_routes(app):
    """
    Setup device management routes
    
    Args:
        app: Bottle application instance
    """
    
    device_manager = DeviceManager()
    
    @app.post('/api/v1/devices')
    @time_api_request('/api/v1/devices', 'POST')
    def register_device():
        """
        Register a new device
        
        Request body:
        {
            "device_id": "device-001",
            "device_type": "solar",
            "location": "Building A",
            "capabilities": {"power": 100}
        }
        
        Returns:
            201 Created with device details
        """
        try:
            request_id = getattr(request, 'request_id', 'unknown')
            
            # Validate request body
            data = request.json
            if not data:
                raise ValidationError("Request body is required")
            
            # Validate against Pydantic model
            device_data = DeviceRegistration(**data)
            
            # Register device
            device = device_manager.register_device(device_data)
            
            # Format response
            response_data = ResponseFormatter.format_created_response(
                data=device.to_dict(),
                resource_id=device.id,
                request_id=request_id
            )
            
            response.status = 201
            response.content_type = 'application/json'
            record_api_request('/api/v1/devices', 'POST', 201)
            
            return response_data
        
        except ValidationError as e:
            error_response, status = ErrorHandler.handle_vpp_exception(
                e,
                getattr(request, 'request_id', 'unknown')
            )
            response.status = status
            record_api_request('/api/v1/devices', 'POST', status)
            return error_response
        
        except Exception as e:
            logger.error(f"Failed to register device: {str(e)}")
            error_response, status = ErrorHandler.handle_vpp_exception(
                e,
                getattr(request, 'request_id', 'unknown')
            )
            response.status = status
            record_api_request('/api/v1/devices', 'POST', status)
            return error_response
    
    @app.get('/api/v1/devices')
    @time_api_request('/api/v1/devices', 'GET')
    def list_devices():
        """
        List all devices with pagination
        
        Query parameters:
        - page: Page number (default: 1)
        - page_size: Items per page (default: 50, max: 100)
        - status: Filter by status (online, offline, error)
        
        Returns:
            200 OK with list of devices and pagination metadata
        """
        try:
            request_id = getattr(request, 'request_id', 'unknown')
            
            # Get pagination parameters
            page = int(request.query.get('page', 1))
            page_size = int(request.query.get('page_size', 50))
            status_filter = request.query.get('status', None)
            
            # Discover devices
            devices, total_count = device_manager.discover_devices(
                page=page,
                page_size=page_size,
                status_filter=status_filter
            )
            
            # Format response
            response_data = ResponseFormatter.format_list_response(
                items=[device.to_dict() for device in devices],
                total_count=total_count,
                page=page,
                page_size=page_size,
                message="Devices retrieved successfully",
                request_id=request_id
            )
            
            response.status = 200
            response.content_type = 'application/json'
            record_api_request('/api/v1/devices', 'GET', 200)
            
            return response_data
        
        except ValidationError as e:
            error_response, status = ErrorHandler.handle_vpp_exception(
                e,
                getattr(request, 'request_id', 'unknown')
            )
            response.status = status
            record_api_request('/api/v1/devices', 'GET', status)
            return error_response
        
        except Exception as e:
            logger.error(f"Failed to list devices: {str(e)}")
            error_response, status = ErrorHandler.handle_vpp_exception(
                e,
                getattr(request, 'request_id', 'unknown')
            )
            response.status = status
            record_api_request('/api/v1/devices', 'GET', status)
            return error_response
    
    @app.get('/api/v1/devices/<device_id>')
    @time_api_request('/api/v1/devices/<device_id>', 'GET')
    def get_device(device_id):
        """
        Get device details
        
        Path parameters:
        - device_id: Device ID
        
        Returns:
            200 OK with device details
        """
        try:
            request_id = getattr(request, 'request_id', 'unknown')
            
            # Get device
            device = device_manager.get_device(device_id)
            
            # Format response
            response_data = ResponseFormatter.format_success_response(
                data=device.to_dict(),
                message="Device retrieved successfully",
                request_id=request_id
            )
            
            response.status = 200
            response.content_type = 'application/json'
            record_api_request('/api/v1/devices/<device_id>', 'GET', 200)
            
            return response_data
        
        except Exception as e:
            logger.error(f"Failed to get device: {str(e)}")
            error_response, status = ErrorHandler.handle_vpp_exception(
                e,
                getattr(request, 'request_id', 'unknown')
            )
            response.status = status
            record_api_request('/api/v1/devices/<device_id>', 'GET', status)
            return error_response
    
    @app.put('/api/v1/devices/<device_id>')
    @time_api_request('/api/v1/devices/<device_id>', 'PUT')
    def update_device(device_id):
        """
        Update device configuration
        
        Path parameters:
        - device_id: Device ID
        
        Request body:
        {
            "power_limit": 100.0,
            "mode": "auto",
            "priority_level": 5
        }
        
        Returns:
            200 OK with updated device details
        """
        try:
            request_id = getattr(request, 'request_id', 'unknown')
            
            # Validate request body
            data = request.json
            if not data:
                raise ValidationError("Request body is required")
            
            # Validate against Pydantic model
            config = DeviceConfig(**data)
            
            # Update device
            device = device_manager.update_device_config(device_id, config)
            
            # Format response
            response_data = ResponseFormatter.format_updated_response(
                data=device.to_dict(),
                request_id=request_id
            )
            
            response.status = 200
            response.content_type = 'application/json'
            record_api_request('/api/v1/devices/<device_id>', 'PUT', 200)
            
            return response_data
        
        except ValidationError as e:
            error_response, status = ErrorHandler.handle_vpp_exception(
                e,
                getattr(request, 'request_id', 'unknown')
            )
            response.status = status
            record_api_request('/api/v1/devices/<device_id>', 'PUT', status)
            return error_response
        
        except Exception as e:
            logger.error(f"Failed to update device: {str(e)}")
            error_response, status = ErrorHandler.handle_vpp_exception(
                e,
                getattr(request, 'request_id', 'unknown')
            )
            response.status = status
            record_api_request('/api/v1/devices/<device_id>', 'PUT', status)
            return error_response
    
    @app.delete('/api/v1/devices/<device_id>')
    @time_api_request('/api/v1/devices/<device_id>', 'DELETE')
    def delete_device(device_id):
        """
        Delete a device
        
        Path parameters:
        - device_id: Device ID
        
        Returns:
            200 OK with deletion confirmation
        """
        try:
            request_id = getattr(request, 'request_id', 'unknown')
            
            # Delete device
            device_manager.delete_device(device_id)
            
            # Format response
            response_data = ResponseFormatter.format_deleted_response(
                resource_id=device_id,
                request_id=request_id
            )
            
            response.status = 200
            response.content_type = 'application/json'
            record_api_request('/api/v1/devices/<device_id>', 'DELETE', 200)
            
            return response_data
        
        except Exception as e:
            logger.error(f"Failed to delete device: {str(e)}")
            error_response, status = ErrorHandler.handle_vpp_exception(
                e,
                getattr(request, 'request_id', 'unknown')
            )
            response.status = status
            record_api_request('/api/v1/devices/<device_id>', 'DELETE', status)
            return error_response
    
    @app.get('/api/v1/devices/<device_id>/status')
    @time_api_request('/api/v1/devices/<device_id>/status', 'GET')
    def get_device_status(device_id):
        """
        Get device status
        
        Path parameters:
        - device_id: Device ID
        
        Returns:
            200 OK with device status
        """
        try:
            request_id = getattr(request, 'request_id', 'unknown')
            
            # Get device status
            status = device_manager.get_device_status(device_id)
            
            # Format response
            response_data = ResponseFormatter.format_success_response(
                data=status,
                message="Device status retrieved successfully",
                request_id=request_id
            )
            
            response.status = 200
            response.content_type = 'application/json'
            record_api_request('/api/v1/devices/<device_id>/status', 'GET', 200)
            
            return response_data
        
        except Exception as e:
            logger.error(f"Failed to get device status: {str(e)}")
            error_response, status_code = ErrorHandler.handle_vpp_exception(
                e,
                getattr(request, 'request_id', 'unknown')
            )
            response.status = status_code
            record_api_request('/api/v1/devices/<device_id>/status', 'GET', status_code)
            return error_response
