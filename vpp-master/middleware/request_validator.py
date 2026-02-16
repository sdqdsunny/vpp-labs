"""
Request Validation Middleware

Provides request validation for JSON, required fields, and data types.
"""

import json
from bottle import request, response
from pydantic import ValidationError as PydanticValidationError
from utils.logger import setup_logger
from utils.errors import ValidationError
from middleware.error_handler import ErrorHandler

logger = setup_logger(__name__)


class RequestValidator:
    """Validates incoming requests"""
    
    @staticmethod
    def validate_json_content_type():
        """
        Validate that request has JSON content type
        
        Raises:
            ValidationError: If content type is not JSON
        """
        if request.method in ['POST', 'PUT', 'PATCH']:
            content_type = request.content_type
            if content_type and 'json' not in content_type:
                raise ValidationError(
                    "Content-Type must be application/json",
                    error_code="INVALID_REQUEST",
                    http_status=400
                )
    
    @staticmethod
    def validate_json_body():
        """
        Validate that request body is valid JSON
        
        Returns:
            Parsed JSON body
        
        Raises:
            ValidationError: If JSON is invalid
        """
        if request.method in ['POST', 'PUT', 'PATCH']:
            try:
                body = request.json
                if body is None and request.content_length > 0:
                    raise ValidationError(
                        "Request body must be valid JSON",
                        error_code="INVALID_REQUEST",
                        http_status=400
                    )
                return body
            except json.JSONDecodeError as e:
                raise ValidationError(
                    f"Invalid JSON: {str(e)}",
                    error_code="INVALID_REQUEST",
                    http_status=400
                )
    
    @staticmethod
    def validate_required_fields(data: dict, required_fields: list):
        """
        Validate that required fields are present
        
        Args:
            data: Request data
            required_fields: List of required field names
        
        Raises:
            ValidationError: If required fields are missing
        """
        missing_fields = []
        for field in required_fields:
            if field not in data or data[field] is None:
                missing_fields.append(field)
        
        if missing_fields:
            raise ValidationError(
                "Missing required fields",
                error_code="INVALID_REQUEST",
                http_status=400,
                details={"missing_fields": missing_fields}
            )
    
    @staticmethod
    def validate_field_types(data: dict, field_types: dict):
        """
        Validate field data types
        
        Args:
            data: Request data
            field_types: Dictionary of field_name: expected_type
        
        Raises:
            ValidationError: If field types are invalid
        """
        invalid_fields = {}
        for field, expected_type in field_types.items():
            if field in data and data[field] is not None:
                if not isinstance(data[field], expected_type):
                    invalid_fields[field] = f"Expected {expected_type.__name__}, got {type(data[field]).__name__}"
        
        if invalid_fields:
            raise ValidationError(
                "Invalid field types",
                error_code="INVALID_REQUEST",
                http_status=400,
                details=invalid_fields
            )
    
    @staticmethod
    def validate_pydantic_model(data: dict, model_class):
        """
        Validate data against Pydantic model
        
        Args:
            data: Request data
            model_class: Pydantic model class
        
        Returns:
            Validated model instance
        
        Raises:
            ValidationError: If validation fails
        """
        try:
            return model_class(**data)
        except PydanticValidationError as e:
            error_details = {}
            for error in e.errors():
                field = '.'.join(str(x) for x in error['loc'])
                error_details[field] = error['msg']
            
            raise ValidationError(
                "Request validation failed",
                error_code="INVALID_REQUEST",
                http_status=400,
                details=error_details
            )


def setup_request_validation(app):
    """
    Setup request validation for Bottle app
    
    Args:
        app: Bottle application instance
    """
    
    @app.hook('before_request')
    def validate_request():
        """Validate incoming request"""
        # Skip validation for GET requests
        if request.method == 'GET':
            return
        
        # Skip validation for public endpoints
        public_endpoints = ['/health', '/metrics', '/docs']
        if any(request.path.startswith(ep) for ep in public_endpoints):
            return
        
        try:
            # Validate JSON content type
            RequestValidator.validate_json_content_type()
            
            # Validate JSON body
            if request.method in ['POST', 'PUT', 'PATCH']:
                RequestValidator.validate_json_body()
        
        except ValidationError as e:
            logger.warning(
                f"Request validation failed: {e.message}",
                extra={
                    "request_id": getattr(request, 'request_id', 'unknown'),
                    "method": request.method,
                    "path": request.path,
                    "error_code": e.error_code
                }
            )
            
            # Format error response
            error_response, status_code = ErrorHandler.handle_vpp_exception(
                e,
                getattr(request, 'request_id', 'unknown')
            )
            
            response.status = status_code
            response.content_type = 'application/json'
            response.body = error_response
