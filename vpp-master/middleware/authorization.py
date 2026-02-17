"""
Authorization Middleware

Provides role-based access control (RBAC) and resource-level permission checks.
"""

import uuid
from typing import Optional, List, Dict, Any
from bottle import request, abort
from utils.logger import setup_logger
from utils.errors import AuthorizationError
from models.user import AuditLog

logger = setup_logger(__name__)


class AuthorizationMiddleware:
    """Handles authorization and access control"""
    
    # Define role-based permissions
    ROLE_PERMISSIONS = {
        'admin': [
            'device:create', 'device:read', 'device:update', 'device:delete',
            'dispatch:create', 'dispatch:read', 'dispatch:update', 'dispatch:delete',
            'protocol:create', 'protocol:read', 'protocol:update', 'protocol:delete',
            'analysis:create', 'analysis:read', 'analysis:update', 'analysis:delete',
            'user:create', 'user:read', 'user:update', 'user:delete',
            'audit:read'
        ],
        'operator': [
            'device:create', 'device:read', 'device:update',
            'dispatch:create', 'dispatch:read', 'dispatch:update',
            'protocol:read',
            'analysis:create', 'analysis:read',
            'audit:read'
        ],
        'viewer': [
            'device:read',
            'dispatch:read',
            'protocol:read',
            'analysis:read',
            'audit:read'
        ]
    }
    
    @staticmethod
    def check_permission(user_context: Dict[str, Any], permission: str) -> bool:
        """
        Check if user has a specific permission
        
        Args:
            user_context: User context dictionary
            permission: Permission string (e.g., 'device:read')
        
        Returns:
            True if user has permission, False otherwise
        """
        user_roles = user_context.get('roles', [])
        
        for role in user_roles:
            role_perms = AuthorizationMiddleware.ROLE_PERMISSIONS.get(role, [])
            if permission in role_perms:
                return True
        
        return False
    
    @staticmethod
    def check_resource_permission(
        user_context: Dict[str, Any],
        resource_type: str,
        action: str,
        resource_id: Optional[str] = None
    ) -> bool:
        """
        Check if user has permission for a specific resource
        
        Args:
            user_context: User context dictionary
            resource_type: Type of resource (e.g., 'device', 'dispatch')
            action: Action to perform (e.g., 'read', 'write', 'delete')
            resource_id: Optional resource ID for fine-grained checks
        
        Returns:
            True if user has permission, False otherwise
        """
        permission = f"{resource_type}:{action}"
        return AuthorizationMiddleware.check_permission(user_context, permission)
    
    @staticmethod
    def log_audit(
        user_id: Optional[str],
        action: str,
        resource_type: str,
        resource_id: str,
        status: str,
        details: Optional[Dict[str, Any]] = None,
        request_id: Optional[str] = None
    ) -> None:
        """
        Log an audit event
        
        Args:
            user_id: User ID performing the action
            action: Action performed (e.g., 'create_device')
            resource_type: Type of resource affected
            resource_id: ID of resource affected
            status: Status of the action ('success' or 'failure')
            details: Additional details about the action
            request_id: Request ID for tracing
        """
        from datetime import datetime
        
        audit_log = AuditLog(
            id=str(uuid.uuid4()),
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            status=status,
            details=details or {},
            request_id=request_id,
            timestamp=datetime.utcnow()
        )
        
        logger.info(
            f"Audit: {action} on {resource_type}/{resource_id}",
            extra={
                "audit_id": audit_log.id,
                "user_id": user_id,
                "action": action,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "status": status,
                "request_id": request_id
            }
        )
        
        # In a real implementation, this would be persisted to the database
        # For now, we just log it
        return audit_log


def setup_authorization(app, protected_routes=None):
    """
    Setup authorization for Bottle app
    
    Args:
        app: Bottle application instance
        protected_routes: List of route patterns that require authorization
    """
    
    if protected_routes is None:
        protected_routes = ['/api/']
    
    @app.hook('before_request')
    def before_request_authorization():
        """Check authorization for protected routes"""
        
        # Skip authorization for public routes
        public_routes = ['/health', '/metrics', '/docs', '/swagger']
        
        if any(request.path.startswith(route) for route in public_routes):
            return
        
        # Check if route requires authorization
        requires_auth = any(
            request.path.startswith(route) for route in protected_routes
        )
        
        if requires_auth:
            # User context should be set by authentication middleware
            user_context = getattr(request, 'user_context', None)
            
            if not user_context:
                logger.warning(
                    "Authorization check failed: no user context",
                    extra={
                        "request_id": getattr(request, 'request_id', 'unknown'),
                        "path": request.path
                    }
                )
                abort(403, "Forbidden")
            
            # User context is already set by authentication middleware
            # No need to set it again
            
            logger.debug(
                "Authorization check passed",
                extra={
                    "request_id": getattr(request, 'request_id', 'unknown'),
                    "user_id": user_context.get('user_id'),
                    "roles": user_context.get('roles')
                }
            )


def require_permission(permission: str):
    """
    Decorator to require a specific permission for a route
    
    Args:
        permission: Permission string (e.g., 'device:read')
    
    Returns:
        Decorator function
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            user_context = getattr(request, 'user_context', None)
            
            if not user_context:
                logger.warning(
                    "Permission check failed: no user context",
                    extra={
                        "request_id": getattr(request, 'request_id', 'unknown'),
                        "required_permission": permission
                    }
                )
                abort(403, "Forbidden")
            
            if not AuthorizationMiddleware.check_permission(user_context, permission):
                logger.warning(
                    "Permission check failed",
                    extra={
                        "request_id": getattr(request, 'request_id', 'unknown'),
                        "user_id": user_context.get('user_id'),
                        "required_permission": permission,
                        "user_roles": user_context.get('roles')
                    }
                )
                abort(403, "Forbidden")
            
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator


def require_resource_permission(resource_type: str, action: str):
    """
    Decorator to require permission for a specific resource
    
    Args:
        resource_type: Type of resource (e.g., 'device')
        action: Action to perform (e.g., 'read')
    
    Returns:
        Decorator function
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            user_context = getattr(request, 'user_context', None)
            
            if not user_context:
                logger.warning(
                    "Resource permission check failed: no user context",
                    extra={
                        "request_id": getattr(request, 'request_id', 'unknown'),
                        "resource_type": resource_type,
                        "action": action
                    }
                )
                abort(403, "Forbidden")
            
            if not AuthorizationMiddleware.check_resource_permission(
                user_context, resource_type, action
            ):
                logger.warning(
                    "Resource permission check failed",
                    extra={
                        "request_id": getattr(request, 'request_id', 'unknown'),
                        "user_id": user_context.get('user_id'),
                        "resource_type": resource_type,
                        "action": action,
                        "user_roles": user_context.get('roles')
                    }
                )
                abort(403, "Forbidden")
            
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator
