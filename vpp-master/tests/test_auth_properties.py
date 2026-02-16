"""
Property-Based Tests for Authentication and Authorization

Tests correctness properties for authentication and authorization.
Feature: vpp-phase1-api
"""

import pytest
import sys
import os
import json
import uuid
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hypothesis import given, strategies as st, settings, HealthCheck
from bottle import Bottle, request, response
from middleware.auth import AuthenticationMiddleware
from middleware.authorization import AuthorizationMiddleware
from utils.errors import AuthenticationError, AuthorizationError
from utils.logger import setup_logger

logger = setup_logger(__name__)


# Custom strategies for generating test data
api_key_strategy = st.sampled_from([
    'vpp-master-key-dev',
    'vpp-vcc-key-dev',
    'vpp-monitor-key-dev',
    'invalid-key-12345',
    'another-invalid-key'
])

invalid_api_key_strategy = st.text(
    alphabet='abcdefghijklmnopqrstuvwxyz0123456789-',
    min_size=10,
    max_size=50
).filter(lambda x: x not in [
    'vpp-master-key-dev',
    'vpp-vcc-key-dev',
    'vpp-monitor-key-dev'
])

user_id_strategy = st.text(
    alphabet='abcdefghijklmnopqrstuvwxyz0123456789-',
    min_size=5,
    max_size=20
)

username_strategy = st.text(
    alphabet='abcdefghijklmnopqrstuvwxyz0123456789_',
    min_size=3,
    max_size=20
)

role_strategy = st.sampled_from(['admin', 'operator', 'viewer'])

roles_strategy = st.lists(
    role_strategy,
    min_size=1,
    max_size=3,
    unique=True
)

permission_strategy = st.sampled_from([
    'device:read', 'device:create', 'device:update', 'device:delete',
    'dispatch:read', 'dispatch:create', 'dispatch:update', 'dispatch:delete',
    'protocol:read', 'protocol:create', 'protocol:update', 'protocol:delete',
    'analysis:read', 'analysis:create', 'analysis:update', 'analysis:delete',
    'user:read', 'user:create', 'user:update', 'user:delete',
    'audit:read'
])


class TestUnauthenticatedRequestsProperty:
    """Property 43: Unauthenticated Requests Are Rejected
    
    Validates: Requirements 19.1
    """
    
    @given(st.just(None))
    @settings(max_examples=100)
    def test_unauthenticated_requests_rejected(self, auth_header):
        """
        For any API request issued without authentication credentials,
        the system should return a 401 Unauthorized response.
        """
        # Create a mock request without authentication
        app = Bottle()
        
        @app.route('/api/test')
        def test_endpoint():
            return {'status': 'ok'}
        
        # Test that missing credentials raises AuthenticationError
        with pytest.raises(AuthenticationError):
            # Simulate request without credentials
            AuthenticationMiddleware.extract_user_context()


class TestInvalidCredentialsProperty:
    """Property 44: Invalid Credentials Are Rejected
    
    Validates: Requirements 19.2
    """
    
    @given(invalid_api_key=invalid_api_key_strategy)
    @settings(max_examples=100)
    def test_invalid_credentials_rejected(self, invalid_api_key):
        """
        For any API request issued with invalid credentials,
        the system should return a 401 Unauthorized response.
        """
        # Test that invalid API key is rejected
        is_valid = AuthenticationMiddleware.validate_api_key(invalid_api_key)
        assert is_valid is False, f"Invalid API key {invalid_api_key} should be rejected"
    
    @given(invalid_token=st.text(
        alphabet='abcdefghijklmnopqrstuvwxyz0123456789.',
        min_size=20,
        max_size=100
    ))
    @settings(max_examples=100)
    def test_invalid_token_rejected(self, invalid_token):
        """
        For any JWT token that is invalid or expired,
        the system should raise AuthenticationError.
        """
        # Test that invalid token raises error
        with pytest.raises(AuthenticationError):
            AuthenticationMiddleware.validate_token(invalid_token)


class TestUnauthorizedOperationsProperty:
    """Property 45: Unauthorized Operations Are Rejected
    
    Validates: Requirements 19.3
    """
    
    @given(
        user_roles=st.lists(
            st.sampled_from(['viewer']),
            min_size=1,
            max_size=1
        ),
        required_permission=st.sampled_from([
            'device:create', 'device:delete',
            'dispatch:create', 'dispatch:delete',
            'user:create', 'user:delete'
        ])
    )
    @settings(max_examples=100)
    def test_unauthorized_operations_rejected(self, user_roles, required_permission):
        """
        For any authenticated user attempting an operation they are not authorized for,
        the system should return a 403 Forbidden response.
        """
        # Create user context with viewer role
        user_context = {
            'user_id': 'test-user',
            'username': 'testuser',
            'roles': user_roles,
            'auth_type': 'token'
        }
        
        # Check that viewer cannot perform admin operations
        has_permission = AuthorizationMiddleware.check_permission(
            user_context,
            required_permission
        )
        
        # Viewer should not have create/delete permissions
        assert has_permission is False, \
            f"Viewer should not have permission {required_permission}"
    
    @given(
        user_roles=st.lists(
            st.sampled_from(['operator']),
            min_size=1,
            max_size=1
        ),
        required_permission=st.sampled_from([
            'user:create', 'user:delete', 'user:update'
        ])
    )
    @settings(max_examples=100)
    def test_operator_cannot_manage_users(self, user_roles, required_permission):
        """
        For any operator attempting to manage users,
        the system should deny the operation.
        """
        # Create user context with operator role
        user_context = {
            'user_id': 'test-operator',
            'username': 'operator',
            'roles': user_roles,
            'auth_type': 'token'
        }
        
        # Check that operator cannot manage users
        has_permission = AuthorizationMiddleware.check_permission(
            user_context,
            required_permission
        )
        
        # Operator should not have user management permissions
        assert has_permission is False, \
            f"Operator should not have permission {required_permission}"


class TestTokenGenerationAndValidation:
    """Test token generation and validation"""
    
    @given(
        user_id=user_id_strategy,
        username=username_strategy,
        roles=roles_strategy
    )
    @settings(max_examples=50)
    def test_token_generation_and_validation(self, user_id, username, roles):
        """
        For any valid user credentials, generating and validating a token
        should succeed and return the correct user context.
        """
        # Generate token
        token = AuthenticationMiddleware.generate_token(user_id, username, roles)
        
        # Token should be a non-empty string
        assert isinstance(token, str)
        assert len(token) > 0
        
        # Validate token
        payload = AuthenticationMiddleware.validate_token(token)
        
        # Payload should contain correct user information
        assert payload['user_id'] == user_id
        assert payload['username'] == username
        assert payload['roles'] == roles


class TestRoleBasedAccessControl:
    """Test role-based access control"""
    
    @given(
        role=role_strategy,
        permission=permission_strategy
    )
    @settings(max_examples=100)
    def test_role_permissions_consistency(self, role, permission):
        """
        For any role and permission combination, the permission check
        should be consistent with the defined role permissions.
        """
        user_context = {
            'user_id': 'test-user',
            'username': 'testuser',
            'roles': [role],
            'auth_type': 'token'
        }
        
        # Check permission
        has_permission = AuthorizationMiddleware.check_permission(
            user_context,
            permission
        )
        
        # Verify against role permissions
        expected_permissions = AuthorizationMiddleware.ROLE_PERMISSIONS.get(role, [])
        expected_result = permission in expected_permissions
        
        assert has_permission == expected_result, \
            f"Permission check for {role}:{permission} should be {expected_result}"
    
    @given(
        roles=st.lists(
            role_strategy,
            min_size=1,
            max_size=3,
            unique=True
        ),
        permission=permission_strategy
    )
    @settings(max_examples=100)
    def test_multiple_roles_permissions(self, roles, permission):
        """
        For any user with multiple roles, the permission check
        should return True if any role has the permission.
        """
        user_context = {
            'user_id': 'test-user',
            'username': 'testuser',
            'roles': roles,
            'auth_type': 'token'
        }
        
        # Check permission
        has_permission = AuthorizationMiddleware.check_permission(
            user_context,
            permission
        )
        
        # Verify against all role permissions
        expected_result = False
        for role in roles:
            role_perms = AuthorizationMiddleware.ROLE_PERMISSIONS.get(role, [])
            if permission in role_perms:
                expected_result = True
                break
        
        assert has_permission == expected_result, \
            f"Permission check for roles {roles}:{permission} should be {expected_result}"


class TestResourcePermissionChecks:
    """Test resource-level permission checks"""
    
    @given(
        user_roles=st.lists(
            st.sampled_from(['admin']),
            min_size=1,
            max_size=1
        ),
        resource_type=st.sampled_from(['device', 'dispatch', 'protocol', 'analysis']),
        action=st.sampled_from(['read', 'create', 'update', 'delete'])
    )
    @settings(max_examples=100)
    def test_admin_has_all_permissions(self, user_roles, resource_type, action):
        """
        For any admin user, checking resource permissions
        should always return True.
        """
        user_context = {
            'user_id': 'admin-user',
            'username': 'admin',
            'roles': user_roles,
            'auth_type': 'token'
        }
        
        # Check resource permission
        has_permission = AuthorizationMiddleware.check_resource_permission(
            user_context,
            resource_type,
            action
        )
        
        # Admin should have all permissions
        assert has_permission is True, \
            f"Admin should have {resource_type}:{action} permission"
    
    @given(
        user_roles=st.lists(
            st.sampled_from(['viewer']),
            min_size=1,
            max_size=1
        ),
        resource_type=st.sampled_from(['device', 'dispatch', 'protocol', 'analysis']),
        action=st.sampled_from(['create', 'update', 'delete'])
    )
    @settings(max_examples=100)
    def test_viewer_cannot_modify_resources(self, user_roles, resource_type, action):
        """
        For any viewer user, checking modify permissions (create, update, delete)
        should return False.
        """
        user_context = {
            'user_id': 'viewer-user',
            'username': 'viewer',
            'roles': user_roles,
            'auth_type': 'token'
        }
        
        # Check resource permission
        has_permission = AuthorizationMiddleware.check_resource_permission(
            user_context,
            resource_type,
            action
        )
        
        # Viewer should not have modify permissions
        assert has_permission is False, \
            f"Viewer should not have {resource_type}:{action} permission"


class TestAuditLogging:
    """Test audit logging functionality"""
    
    @given(
        user_id=user_id_strategy,
        action=st.text(
            alphabet='abcdefghijklmnopqrstuvwxyz_',
            min_size=5,
            max_size=30
        ),
        resource_type=st.sampled_from(['device', 'dispatch', 'protocol', 'analysis']),
        resource_id=st.text(
            alphabet='abcdefghijklmnopqrstuvwxyz0123456789-',
            min_size=5,
            max_size=20
        ),
        status=st.sampled_from(['success', 'failure'])
    )
    @settings(max_examples=50)
    def test_audit_logging(self, user_id, action, resource_type, resource_id, status):
        """
        For any audit event, logging should create an audit log entry
        with all required fields.
        """
        request_id = str(uuid.uuid4())
        
        # Log audit event
        audit_log = AuthorizationMiddleware.log_audit(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            status=status,
            request_id=request_id
        )
        
        # Verify audit log has all required fields
        assert audit_log.user_id == user_id
        assert audit_log.action == action
        assert audit_log.resource_type == resource_type
        assert audit_log.resource_id == resource_id
        assert audit_log.status == status
        assert audit_log.request_id == request_id
        assert audit_log.id is not None
        # Timestamp should be set (it's set by the model default)
        assert isinstance(audit_log.timestamp, datetime)
