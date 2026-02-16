"""
Response Formatting Middleware

Provides consistent response formatting for all API endpoints.
"""

import json
from typing import Dict, Any, Optional, List
from bottle import request, response
from utils.logger import setup_logger

logger = setup_logger(__name__)


class ResponseFormatter:
    """Formats API responses in consistent JSON structure"""
    
    @staticmethod
    def format_success_response(
        data: Any,
        status_code: int = 200,
        message: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Format successful response
        
        Args:
            data: Response data
            status_code: HTTP status code
            message: Optional success message
            request_id: Request ID for tracking
        
        Returns:
            Formatted response dictionary
        """
        return {
            "status": "success",
            "code": status_code,
            "message": message or "Request successful",
            "data": data,
            "request_id": request_id or getattr(request, 'request_id', 'unknown'),
            "timestamp": __import__('datetime').datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def format_list_response(
        items: List[Any],
        total_count: int,
        page: int = 1,
        page_size: int = 50,
        message: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Format list response with pagination
        
        Args:
            items: List of items
            total_count: Total number of items
            page: Current page number
            page_size: Items per page
            message: Optional message
            request_id: Request ID for tracking
        
        Returns:
            Formatted list response dictionary
        """
        total_pages = (total_count + page_size - 1) // page_size
        
        return {
            "status": "success",
            "code": 200,
            "message": message or "List retrieved successfully",
            "data": items,
            "pagination": {
                "total_count": total_count,
                "page": page,
                "page_size": page_size,
                "total_pages": total_pages,
                "has_next": page < total_pages,
                "has_previous": page > 1
            },
            "request_id": request_id or getattr(request, 'request_id', 'unknown'),
            "timestamp": __import__('datetime').datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def format_created_response(
        data: Any,
        resource_id: str,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Format created resource response
        
        Args:
            data: Created resource data
            resource_id: ID of created resource
            request_id: Request ID for tracking
        
        Returns:
            Formatted created response dictionary
        """
        return {
            "status": "success",
            "code": 201,
            "message": "Resource created successfully",
            "data": data,
            "resource_id": resource_id,
            "request_id": request_id or getattr(request, 'request_id', 'unknown'),
            "timestamp": __import__('datetime').datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def format_updated_response(
        data: Any,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Format updated resource response
        
        Args:
            data: Updated resource data
            request_id: Request ID for tracking
        
        Returns:
            Formatted updated response dictionary
        """
        return {
            "status": "success",
            "code": 200,
            "message": "Resource updated successfully",
            "data": data,
            "request_id": request_id or getattr(request, 'request_id', 'unknown'),
            "timestamp": __import__('datetime').datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def format_deleted_response(
        resource_id: str,
        request_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Format deleted resource response
        
        Args:
            resource_id: ID of deleted resource
            request_id: Request ID for tracking
        
        Returns:
            Formatted deleted response dictionary
        """
        return {
            "status": "success",
            "code": 200,
            "message": "Resource deleted successfully",
            "resource_id": resource_id,
            "request_id": request_id or getattr(request, 'request_id', 'unknown'),
            "timestamp": __import__('datetime').datetime.utcnow().isoformat()
        }


def setup_response_formatting(app):
    """
    Setup response formatting for Bottle app
    
    Args:
        app: Bottle application instance
    """
    
    @app.hook('after_request')
    def format_response():
        """Format response body"""
        # Skip formatting for non-JSON responses
        if response.content_type and 'json' not in response.content_type:
            return
        
        # Skip formatting for error responses (already formatted)
        if response.status_code >= 400:
            return
        
        # Skip formatting for empty responses
        if not response.body:
            return
        
        try:
            # Try to parse existing response
            body = response.body
            if isinstance(body, bytes):
                body = body.decode('utf-8')
            
            # If already formatted, skip
            if isinstance(body, str):
                data = json.loads(body)
                if isinstance(data, dict) and 'status' in data:
                    return
                
                # Format unformatted response
                formatted = ResponseFormatter.format_success_response(
                    data=data,
                    status_code=response.status_code,
                    request_id=getattr(request, 'request_id', 'unknown')
                )
                response.body = json.dumps(formatted)
                response.content_type = 'application/json'
        except Exception as e:
            logger.error(f"Error formatting response: {str(e)}", exc_info=True)
