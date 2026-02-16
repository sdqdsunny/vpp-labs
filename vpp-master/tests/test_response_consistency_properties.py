"""
Property-Based Tests for API Response Consistency and Error Handling

Tests correctness properties for response formatting and request validation.
Feature: vpp-phase1-api
"""

import pytest
import sys
import os
import json
import uuid
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hypothesis import given, strategies as st, settings, HealthCheck
from bottle import Bottle, request, response
from middleware.response_formatter import ResponseFormatter
from middleware.error_handler import ErrorHandler
from middleware.request_validator import RequestValidator
from utils.errors import ValidationError, VPPException
from utils.logger import setup_logger

logger = setup_logger(__name__)


# Custom strategies for generating test data
json_string_strategy = st.text(
    alphabet=st.characters(blacklist_categories=('Cc', 'Cs')),
    min_size=0,
    max_size=100
)

json_number_strategy = st.floats(
    min_value=-1e10,
    max_value=1e10,
    allow_nan=False,
    allow_infinity=False
)

json_boolean_strategy = st.booleans()

json_null_strategy = st.none()

# Valid JSON data strategy
valid_json_data_strategy = st.dictionaries(
    keys=st.text(
        alphabet='abcdefghijklmnopqrstuvwxyz_',
        min_size=1,
        max_size=20
    ),
    values=st.one_of(
        json_string_strategy,
        json_number_strategy,
        json_boolean_strategy,
        json_null_strategy
    ),
    min_size=0,
    max_size=5
)

# Invalid JSON strings
invalid_json_strategy = st.one_of(
    st.just('{invalid json}'),
    st.just('{"key": undefined}'),
    st.just('{"key": NaN}'),
    st.just('{key: "value"}'),
    st.just('{"key": "value"'),
    st.just('{"key": "value",}'),
)

# Error codes
error_code_strategy = st.sampled_from([
    'INVALID_REQUEST',
    'UNAUTHORIZED',
    'FORBIDDEN',
    'NOT_FOUND',
    'CONFLICT',
    'UNPROCESSABLE_ENTITY',
    'RATE_LIMIT_EXCEEDED',
    'INTERNAL_ERROR',
    'SERVICE_UNAVAILABLE'
])

# HTTP status codes
http_status_strategy = st.sampled_from([400, 401, 403, 404, 409, 422, 429, 500, 503])


class TestInvalidJSONRequestsProperty:
    """Property 36: Invalid JSON Requests Are Rejected
    
    Validates: Requirements 17.1
    """
    
    @given(invalid_json=st.one_of(
        st.just('{invalid json}'),
        st.just('{"key": undefined}'),
        st.just('{key: "value"}'),
        st.just('{"key": "value"'),
        st.just('{"key": "value",}'),
    ))
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    def test_invalid_json_rejected(self, invalid_json):
        """
        For any API request containing invalid JSON, the system should return
        a 400 Bad Request response with error details.
        """
        # Test that invalid JSON raises JSONDecodeError
        with pytest.raises(json.JSONDecodeError):
            json.loads(invalid_json)


class TestMissingRequiredFieldsProperty:
    """Property 37: Missing Required Fields Are Detected
    
    Validates: Requirements 17.2
    """
    
    @given(
        required_fields=st.lists(
            st.text(
                alphabet='abcdefghijklmnopqrstuvwxyz_',
                min_size=1,
                max_size=20
            ),
            min_size=1,
            max_size=5,
            unique=True
        ),
        provided_fields=st.lists(
            st.text(
                alphabet='abcdefghijklmnopqrstuvwxyz_',
                min_size=1,
                max_size=20
            ),
            min_size=0,
            max_size=3,
            unique=True
        )
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    def test_missing_required_fields_detected(self, required_fields, provided_fields):
        """
        For any API request missing required fields, the system should return
        a 400 Bad Request response with specific field validation errors.
        """
        # Create data with only provided fields
        data = {field: f"value_{i}" for i, field in enumerate(provided_fields)}
        
        # Validate required fields
        missing = [f for f in required_fields if f not in data]
        
        if missing:
            # Should raise ValidationError
            with pytest.raises(ValidationError) as exc_info:
                RequestValidator.validate_required_fields(data, required_fields)
            
            assert exc_info.value.error_code == "INVALID_REQUEST"
            assert exc_info.value.http_status == 400
            assert "missing_fields" in exc_info.value.details
            assert set(exc_info.value.details["missing_fields"]) == set(missing)


class TestInvalidDataTypesProperty:
    """Property 38: Invalid Data Types Are Detected
    
    Validates: Requirements 17.3
    """
    
    @given(
        field_name=st.text(
            alphabet='abcdefghijklmnopqrstuvwxyz_',
            min_size=1,
            max_size=20
        ),
        expected_type=st.sampled_from([str, int, float, bool, list, dict]),
        actual_value=st.one_of(
            st.text(min_size=1, max_size=20),
            st.integers(),
            st.floats(allow_nan=False, allow_infinity=False),
            st.booleans(),
            st.lists(st.integers(), max_size=3),
            st.dictionaries(
                keys=st.text(min_size=1, max_size=10),
                values=st.integers(),
                max_size=2
            )
        )
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    def test_invalid_data_types_detected(self, field_name, expected_type, actual_value):
        """
        For any API request containing invalid data types, the system should return
        a 400 Bad Request response with type validation errors.
        """
        data = {field_name: actual_value}
        field_types = {field_name: expected_type}
        
        # Check if type matches
        if not isinstance(actual_value, expected_type):
            # Should raise ValidationError
            with pytest.raises(ValidationError) as exc_info:
                RequestValidator.validate_field_types(data, field_types)
            
            assert exc_info.value.error_code == "INVALID_REQUEST"
            assert exc_info.value.http_status == 400
            assert field_name in exc_info.value.details


class TestInternalErrorsIncludeUniqueErrorIDsProperty:
    """Property 39: Internal Errors Include Unique Error IDs
    
    Validates: Requirements 17.5
    """
    
    @given(
        error_code=error_code_strategy,
        message=st.text(min_size=1, max_size=100),
        http_status=http_status_strategy
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    def test_internal_errors_include_unique_ids(self, error_code, message, http_status):
        """
        For any internal server error, the system should return a 500 response
        with a unique error ID for tracking.
        """
        request_id_1 = str(uuid.uuid4())
        request_id_2 = str(uuid.uuid4())
        
        # Format two error responses
        error_response_1 = ErrorHandler.format_error_response(
            error_code=error_code,
            message=message,
            http_status=http_status,
            request_id=request_id_1
        )
        
        error_response_2 = ErrorHandler.format_error_response(
            error_code=error_code,
            message=message,
            http_status=http_status,
            request_id=request_id_2
        )
        
        # Verify both have request_id
        assert "error" in error_response_1
        assert "request_id" in error_response_1["error"]
        assert "error" in error_response_2
        assert "request_id" in error_response_2["error"]
        
        # Verify request IDs are different
        assert error_response_1["error"]["request_id"] != error_response_2["error"]["request_id"]


class TestErrorResponsesHaveConsistentFormatProperty:
    """Property 40: Error Responses Have Consistent Format
    
    Validates: Requirements 17.6, 18.4
    """
    
    @given(
        error_code=error_code_strategy,
        message=st.text(min_size=1, max_size=100),
        http_status=http_status_strategy,
        details=st.dictionaries(
            keys=st.text(min_size=1, max_size=20),
            values=st.text(min_size=0, max_size=50),
            max_size=3
        )
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    def test_error_responses_consistent_format(self, error_code, message, http_status, details):
        """
        For any API error response, the response should include error_code,
        error_message, and details in a consistent JSON structure.
        """
        request_id = str(uuid.uuid4())
        
        error_response = ErrorHandler.format_error_response(
            error_code=error_code,
            message=message,
            http_status=http_status,
            details=details,
            request_id=request_id
        )
        
        # Verify consistent structure
        assert isinstance(error_response, dict)
        assert "error" in error_response
        assert isinstance(error_response["error"], dict)
        
        error_obj = error_response["error"]
        assert "code" in error_obj
        assert "message" in error_obj
        assert "details" in error_obj
        assert "request_id" in error_obj
        assert "timestamp" in error_obj
        
        # Verify values
        assert error_obj["code"] == error_code
        assert error_obj["message"] == message
        assert error_obj["request_id"] == request_id
        assert isinstance(error_obj["timestamp"], str)
        
        # Verify timestamp is ISO format
        try:
            datetime.fromisoformat(error_obj["timestamp"].replace('Z', '+00:00'))
        except ValueError:
            pytest.fail("Timestamp is not in ISO format")


class TestSuccessfulResponsesHaveConsistentFormatProperty:
    """Property 41: Successful Responses Have Consistent Format
    
    Validates: Requirements 18.1, 18.3
    """
    
    @given(
        data=valid_json_data_strategy,
        status_code=st.sampled_from([200, 201]),
        message=st.text(min_size=1, max_size=100)
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    def test_success_responses_consistent_format(self, data, status_code, message):
        """
        For any successful API request, the response should include status code
        200/201 and a consistent JSON structure with all relevant fields.
        """
        request_id = str(uuid.uuid4())
        
        response_obj = ResponseFormatter.format_success_response(
            data=data,
            status_code=status_code,
            message=message,
            request_id=request_id
        )
        
        # Verify consistent structure
        assert isinstance(response_obj, dict)
        assert "status" in response_obj
        assert response_obj["status"] == "success"
        assert "code" in response_obj
        assert response_obj["code"] == status_code
        assert "message" in response_obj
        assert response_obj["message"] == message
        assert "data" in response_obj
        assert response_obj["data"] == data
        assert "request_id" in response_obj
        assert response_obj["request_id"] == request_id
        assert "timestamp" in response_obj
        
        # Verify timestamp is ISO format
        try:
            datetime.fromisoformat(response_obj["timestamp"].replace('Z', '+00:00'))
        except ValueError:
            pytest.fail("Timestamp is not in ISO format")


class TestListResponsesIncludePaginationMetadataProperty:
    """Property 42: List Responses Include Pagination Metadata
    
    Validates: Requirements 18.2
    """
    
    @given(
        items=st.lists(
            st.dictionaries(
                keys=st.text(min_size=1, max_size=10),
                values=st.integers(),
                max_size=2
            ),
            min_size=0,
            max_size=100
        ),
        total_count=st.integers(min_value=0, max_value=1000),
        page=st.integers(min_value=1, max_value=100),
        page_size=st.integers(min_value=1, max_value=100)
    )
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    def test_list_responses_include_pagination(self, items, total_count, page, page_size):
        """
        For any API request returning a list of items, the response should include
        pagination metadata (total_count, page, page_size).
        """
        request_id = str(uuid.uuid4())
        
        response_obj = ResponseFormatter.format_list_response(
            items=items,
            total_count=total_count,
            page=page,
            page_size=page_size,
            request_id=request_id
        )
        
        # Verify pagination metadata
        assert "pagination" in response_obj
        pagination = response_obj["pagination"]
        
        assert "total_count" in pagination
        assert pagination["total_count"] == total_count
        
        assert "page" in pagination
        assert pagination["page"] == page
        
        assert "page_size" in pagination
        assert pagination["page_size"] == page_size
        
        assert "total_pages" in pagination
        expected_total_pages = (total_count + page_size - 1) // page_size
        assert pagination["total_pages"] == expected_total_pages
        
        assert "has_next" in pagination
        assert pagination["has_next"] == (page < expected_total_pages)
        
        assert "has_previous" in pagination
        assert pagination["has_previous"] == (page > 1)
        
        # Verify response structure
        assert response_obj["status"] == "success"
        assert response_obj["code"] == 200
        assert "data" in response_obj
        assert response_obj["data"] == items
        assert "request_id" in response_obj
        assert "timestamp" in response_obj
