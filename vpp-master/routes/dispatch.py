"""
Dispatch Control API Routes

HTTP endpoints for dispatch command creation, execution, scheduling, and tracking.
"""

from bottle import request, response
from datetime import datetime
from utils.logger import setup_logger
from utils.validators import DispatchRequest, ScheduledDispatchRequest
from utils.errors import ValidationError
from middleware.error_handler import ErrorHandler
from middleware.response_formatter import ResponseFormatter
from services.dispatch_engine import DispatchEngine
from utils.metrics import time_api_request, record_api_request

logger = setup_logger(__name__)


def setup_dispatch_routes(app):
    """
    Setup dispatch control routes
    
    Args:
        app: Bottle application instance
    """
    
    dispatch_engine = DispatchEngine()
    
    @app.post('/api/v1/dispatch')
    @time_api_request('/api/v1/dispatch', 'POST')
    def create_dispatch():
        """
        Create and execute a dispatch command
        
        Request body:
        {
            "device_id": "device-001",
            "command_type": "power_adjust",
            "target_value": 50.0,
            "priority_level": 5
        }
        
        Returns:
            201 Created with dispatch details
        """
        try:
            request_id = getattr(request, 'request_id', 'unknown')
            
            # Validate request body
            data = request.json
            if not data:
                raise ValidationError("Request body is required")
            
            # Validate against Pydantic model
            dispatch_data = DispatchRequest(**data)
            
            # Create dispatch
            dispatch = dispatch_engine.create_dispatch(dispatch_data)
            
            # Format response
            response_data = ResponseFormatter.format_created_response(
                data=dispatch.to_dict(),
                resource_id=dispatch.id,
                request_id=request_id
            )
            
            response.status = 201
            response.content_type = 'application/json'
            record_api_request('/api/v1/dispatch', 'POST', 201)
            
            return response_data
        
        except ValidationError as e:
            error_response, status = ErrorHandler.handle_vpp_exception(
                e,
                getattr(request, 'request_id', 'unknown')
            )
            response.status = status
            record_api_request('/api/v1/dispatch', 'POST', status)
            return error_response
        
        except Exception as e:
            logger.error(f"Failed to create dispatch: {str(e)}")
            error_response, status = ErrorHandler.handle_vpp_exception(
                e,
                getattr(request, 'request_id', 'unknown')
            )
            response.status = status
            record_api_request('/api/v1/dispatch', 'POST', status)
            return error_response
    
    @app.get('/api/v1/dispatch/<dispatch_id>')
    @time_api_request('/api/v1/dispatch/<dispatch_id>', 'GET')
    def get_dispatch(dispatch_id):
        """
        Get dispatch details
        
        Path parameters:
        - dispatch_id: Dispatch ID
        
        Returns:
            200 OK with dispatch details
        """
        try:
            request_id = getattr(request, 'request_id', 'unknown')
            
            # Get dispatch status to retrieve dispatch details
            status_data = dispatch_engine.get_dispatch_status(dispatch_id)
            
            # Format response
            response_data = ResponseFormatter.format_success_response(
                data=status_data,
                message="Dispatch retrieved successfully",
                request_id=request_id
            )
            
            response.status = 200
            response.content_type = 'application/json'
            record_api_request('/api/v1/dispatch/<dispatch_id>', 'GET', 200)
            
            return response_data
        
        except Exception as e:
            logger.error(f"Failed to get dispatch: {str(e)}")
            error_response, status = ErrorHandler.handle_vpp_exception(
                e,
                getattr(request, 'request_id', 'unknown')
            )
            response.status = status
            record_api_request('/api/v1/dispatch/<dispatch_id>', 'GET', status)
            return error_response
    
    @app.get('/api/v1/dispatch/<dispatch_id>/status')
    @time_api_request('/api/v1/dispatch/<dispatch_id>/status', 'GET')
    def get_dispatch_status(dispatch_id):
        """
        Get dispatch status
        
        Path parameters:
        - dispatch_id: Dispatch ID
        
        Returns:
            200 OK with status information
        """
        try:
            request_id = getattr(request, 'request_id', 'unknown')
            
            # Get dispatch status
            status_data = dispatch_engine.get_dispatch_status(dispatch_id)
            
            # Format response
            response_data = ResponseFormatter.format_success_response(
                data=status_data,
                message="Dispatch status retrieved successfully",
                request_id=request_id
            )
            
            response.status = 200
            response.content_type = 'application/json'
            record_api_request('/api/v1/dispatch/<dispatch_id>/status', 'GET', 200)
            
            return response_data
        
        except Exception as e:
            logger.error(f"Failed to get dispatch status: {str(e)}")
            error_response, status = ErrorHandler.handle_vpp_exception(
                e,
                getattr(request, 'request_id', 'unknown')
            )
            response.status = status
            record_api_request('/api/v1/dispatch/<dispatch_id>/status', 'GET', status)
            return error_response
    
    @app.get('/api/v1/dispatch/history')
    @time_api_request('/api/v1/dispatch/history', 'GET')
    def get_dispatch_history():
        """
        Get dispatch history with filters and pagination
        
        Query parameters:
        - device_id: Filter by device ID
        - status: Filter by status (pending, executing, completed, failed)
        - start_time: Filter by start time (ISO 8601 format)
        - end_time: Filter by end time (ISO 8601 format)
        - page: Page number (default: 1)
        - page_size: Items per page (default: 50, max: 100)
        
        Returns:
            200 OK with dispatch records and pagination metadata
        """
        try:
            request_id = getattr(request, 'request_id', 'unknown')
            
            # Get query parameters
            device_id = request.query.get('device_id', None)
            status_filter = request.query.get('status', None)
            start_time_str = request.query.get('start_time', None)
            end_time_str = request.query.get('end_time', None)
            page = int(request.query.get('page', 1))
            page_size = int(request.query.get('page_size', 50))
            
            # Parse datetime parameters
            start_time = None
            end_time = None
            if start_time_str:
                try:
                    start_time = datetime.fromisoformat(start_time_str)
                except ValueError:
                    raise ValidationError(f"Invalid start_time format: {start_time_str}")
            if end_time_str:
                try:
                    end_time = datetime.fromisoformat(end_time_str)
                except ValueError:
                    raise ValidationError(f"Invalid end_time format: {end_time_str}")
            
            # Get dispatch history
            history_data = dispatch_engine.get_dispatch_history(
                device_id=device_id,
                status=status_filter,
                start_time=start_time,
                end_time=end_time,
                page=page,
                page_size=page_size
            )
            
            # Format response
            response_data = ResponseFormatter.format_list_response(
                items=history_data['dispatches'],
                total_count=history_data['pagination']['total_count'],
                page=page,
                page_size=page_size,
                message="Dispatch history retrieved successfully",
                request_id=request_id
            )
            
            response.status = 200
            response.content_type = 'application/json'
            record_api_request('/api/v1/dispatch/history', 'GET', 200)
            
            return response_data
        
        except ValidationError as e:
            error_response, status = ErrorHandler.handle_vpp_exception(
                e,
                getattr(request, 'request_id', 'unknown')
            )
            response.status = status
            record_api_request('/api/v1/dispatch/history', 'GET', status)
            return error_response
        
        except Exception as e:
            logger.error(f"Failed to get dispatch history: {str(e)}")
            error_response, status = ErrorHandler.handle_vpp_exception(
                e,
                getattr(request, 'request_id', 'unknown')
            )
            response.status = status
            record_api_request('/api/v1/dispatch/history', 'GET', status)
            return error_response
    
    @app.post('/api/v1/dispatch/<dispatch_id>/cancel')
    @time_api_request('/api/v1/dispatch/<dispatch_id>/cancel', 'POST')
    def cancel_dispatch(dispatch_id):
        """
        Cancel a scheduled dispatch
        
        Path parameters:
        - dispatch_id: Dispatch ID to cancel
        
        Returns:
            200 OK with cancellation confirmation
        """
        try:
            request_id = getattr(request, 'request_id', 'unknown')
            
            # Cancel dispatch
            dispatch_engine.cancel_scheduled_dispatch(dispatch_id)
            
            # Format response
            response_data = ResponseFormatter.format_success_response(
                data={"dispatch_id": dispatch_id, "status": "cancelled"},
                message="Dispatch cancelled successfully",
                request_id=request_id
            )
            
            response.status = 200
            response.content_type = 'application/json'
            record_api_request('/api/v1/dispatch/<dispatch_id>/cancel', 'POST', 200)
            
            return response_data
        
        except Exception as e:
            logger.error(f"Failed to cancel dispatch: {str(e)}")
            error_response, status = ErrorHandler.handle_vpp_exception(
                e,
                getattr(request, 'request_id', 'unknown')
            )
            response.status = status
            record_api_request('/api/v1/dispatch/<dispatch_id>/cancel', 'POST', status)
            return error_response
    
    @app.post('/api/v1/dispatch/schedule')
    @time_api_request('/api/v1/dispatch/schedule', 'POST')
    def schedule_dispatch():
        """
        Schedule a future dispatch
        
        Request body:
        {
            "device_id": "device-001",
            "command_type": "power_adjust",
            "target_value": 50.0,
            "priority_level": 5,
            "execution_time": "2026-02-16T15:30:00Z"
        }
        
        Returns:
            201 Created with scheduled dispatch details
        """
        try:
            request_id = getattr(request, 'request_id', 'unknown')
            
            # Validate request body
            data = request.json
            if not data:
                raise ValidationError("Request body is required")
            
            # Validate against Pydantic model
            dispatch_data = ScheduledDispatchRequest(**data)
            
            # Schedule dispatch
            dispatch = dispatch_engine.schedule_dispatch(dispatch_data)
            
            # Format response
            response_data = ResponseFormatter.format_created_response(
                data=dispatch.to_dict(),
                resource_id=dispatch.id,
                request_id=request_id
            )
            
            response.status = 201
            response.content_type = 'application/json'
            record_api_request('/api/v1/dispatch/schedule', 'POST', 201)
            
            return response_data
        
        except ValidationError as e:
            error_response, status = ErrorHandler.handle_vpp_exception(
                e,
                getattr(request, 'request_id', 'unknown')
            )
            response.status = status
            record_api_request('/api/v1/dispatch/schedule', 'POST', status)
            return error_response
        
        except Exception as e:
            logger.error(f"Failed to schedule dispatch: {str(e)}")
            error_response, status = ErrorHandler.handle_vpp_exception(
                e,
                getattr(request, 'request_id', 'unknown')
            )
            response.status = status
            record_api_request('/api/v1/dispatch/schedule', 'POST', status)
            return error_response
    
    @app.get('/api/v1/dispatch/scheduled')
    @time_api_request('/api/v1/dispatch/scheduled', 'GET')
    def list_scheduled_dispatches():
        """
        List scheduled dispatches
        
        Query parameters:
        - page: Page number (default: 1)
        - page_size: Items per page (default: 50, max: 100)
        
        Returns:
            200 OK with scheduled dispatch list and pagination metadata
        """
        try:
            request_id = getattr(request, 'request_id', 'unknown')
            
            # Get pagination parameters
            page = int(request.query.get('page', 1))
            page_size = int(request.query.get('page_size', 50))
            
            # Get scheduled dispatches (filter by scheduled_time is not null)
            history_data = dispatch_engine.get_dispatch_history(
                status="pending",
                page=page,
                page_size=page_size
            )
            
            # Filter to only scheduled dispatches (those with scheduled_time set)
            scheduled_dispatches = [
                d for d in history_data['dispatches']
                if d.get('scheduled_time') is not None
            ]
            
            # Format response
            response_data = ResponseFormatter.format_list_response(
                items=scheduled_dispatches,
                total_count=len(scheduled_dispatches),
                page=page,
                page_size=page_size,
                message="Scheduled dispatches retrieved successfully",
                request_id=request_id
            )
            
            response.status = 200
            response.content_type = 'application/json'
            record_api_request('/api/v1/dispatch/scheduled', 'GET', 200)
            
            return response_data
        
        except Exception as e:
            logger.error(f"Failed to list scheduled dispatches: {str(e)}")
            error_response, status = ErrorHandler.handle_vpp_exception(
                e,
                getattr(request, 'request_id', 'unknown')
            )
            response.status = status
            record_api_request('/api/v1/dispatch/scheduled', 'GET', status)
            return error_response
