"""
Authentication Middleware

Provides API key and token-based authentication for VPP Master API.
"""

import os
import jwt
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from bottle import request, abort
from utils.logger import setup_logger
from utils.errors import AuthenticationError

logger = setup_logger(__name__)


class AuthenticationMiddleware:
    """Handles API authentication"""
    
    # Valid API keys (in production, these should be stored in a database)
    VALID_API_KEYS = {
        os.getenv('API_KEY_MASTER', 'vpp-master-key-dev'),
        os.getenv('API_KEY_VCC', 'vpp-vcc-key-dev'),
        os.getenv('API_KEY_MONITOR', 'vpp-monitor-key-dev'),
    }
    
    # JWT configuration
    JWT_SECRET = os.getenv('JWT_SECRET', 'vpp-jwt-secret-dev')
    JWT_ALGORITHM = 'HS256'
    JWT_EXPIRATION_HOURS = int(os.getenv('JWT_EXPIRATION_HOURS', '24'))
    
    @staticmethod
    def get_api_key_from_request() -> str:
        """
        Extract API key from request headers
        
        Returns:
            API key string
        
        Raises:
            AuthenticationError: If API key is missing
        """
        # Check Authorization header
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            return auth_header[7:]
        
        # Check X-API-Key header
        api_key = request.headers.get('X-API-Key', '')
        if api_key:
            return api_key
        
        raise AuthenticationError("Missing API key")
    
    @staticmethod
    def validate_api_key(api_key: str) -> bool:
        """
        Validate API key
        
        Args:
            api_key: API key to validate
        
        Returns:
            True if valid, False otherwise
        """
        return api_key in AuthenticationMiddleware.VALID_API_KEYS
    
    @staticmethod
    def generate_token(user_id: str, username: str, roles: list = None) -> str:
        """
        Generate JWT token for authenticated user
        
        Args:
            user_id: User ID
            username: Username
            roles: List of user roles
        
        Returns:
            JWT token string
        """
        payload = {
            'user_id': user_id,
            'username': username,
            'roles': roles or [],
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(hours=AuthenticationMiddleware.JWT_EXPIRATION_HOURS),
            'jti': str(uuid.uuid4())
        }
        
        token = jwt.encode(
            payload,
            AuthenticationMiddleware.JWT_SECRET,
            algorithm=AuthenticationMiddleware.JWT_ALGORITHM
        )
        
        return token
    
    @staticmethod
    def validate_token(token: str) -> Dict[str, Any]:
        """
        Validate JWT token and extract user context
        
        Args:
            token: JWT token string
        
        Returns:
            Decoded token payload
        
        Raises:
            AuthenticationError: If token is invalid or expired
        """
        try:
            payload = jwt.decode(
                token,
                AuthenticationMiddleware.JWT_SECRET,
                algorithms=[AuthenticationMiddleware.JWT_ALGORITHM]
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise AuthenticationError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise AuthenticationError(f"Invalid token: {str(e)}")
    
    @staticmethod
    def extract_user_context() -> Dict[str, Any]:
        """
        Extract user context from request
        
        Returns:
            User context dictionary with user_id, username, roles
        
        Raises:
            AuthenticationError: If authentication fails
        """
        auth_header = request.headers.get('Authorization', '')
        
        # Check for Bearer token (JWT)
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
            payload = AuthenticationMiddleware.validate_token(token)
            return {
                'user_id': payload.get('user_id'),
                'username': payload.get('username'),
                'roles': payload.get('roles', []),
                'auth_type': 'token'
            }
        
        # Check for API key
        api_key = request.headers.get('X-API-Key', '')
        if api_key:
            if not AuthenticationMiddleware.validate_api_key(api_key):
                raise AuthenticationError("Invalid API key")
            
            # Map API key to user context
            user_context = AuthenticationMiddleware._get_user_context_from_api_key(api_key)
            return user_context
        
        raise AuthenticationError("Missing authentication credentials")
    
    @staticmethod
    def _get_user_context_from_api_key(api_key: str) -> Dict[str, Any]:
        """
        Map API key to user context
        
        Args:
            api_key: API key string
        
        Returns:
            User context dictionary
        """
        # Map API keys to user contexts
        api_key_mapping = {
            os.getenv('API_KEY_MASTER', 'vpp-master-key-dev'): {
                'user_id': 'master-service',
                'username': 'master-service',
                'roles': ['admin', 'operator'],
                'auth_type': 'api_key'
            },
            os.getenv('API_KEY_VCC', 'vpp-vcc-key-dev'): {
                'user_id': 'vcc-service',
                'username': 'vcc-service',
                'roles': ['operator'],
                'auth_type': 'api_key'
            },
            os.getenv('API_KEY_MONITOR', 'vpp-monitor-key-dev'): {
                'user_id': 'monitor-service',
                'username': 'monitor-service',
                'roles': ['viewer'],
                'auth_type': 'api_key'
            }
        }
        
        return api_key_mapping.get(api_key, {
            'user_id': 'unknown',
            'username': 'unknown',
            'roles': [],
            'auth_type': 'api_key'
        })
    
    @staticmethod
    def authenticate_request() -> Dict[str, Any]:
        """
        Authenticate incoming request
        
        Returns:
            User context dictionary
        
        Raises:
            AuthenticationError: If authentication fails
        """
        try:
            user_context = AuthenticationMiddleware.extract_user_context()
            
            logger.debug(
                "Authentication successful",
                extra={
                    "request_id": getattr(request, 'request_id', 'unknown'),
                    "user_id": user_context.get('user_id'),
                    "auth_type": user_context.get('auth_type')
                }
            )
            
            return user_context
        
        except AuthenticationError as e:
            logger.warning(
                f"Authentication failed: {e.message}",
                extra={
                    "request_id": getattr(request, 'request_id', 'unknown'),
                    "remote_addr": request.remote_addr
                }
            )
            raise


def setup_authentication(app, protected_routes=None):
    """
    Setup authentication for Bottle app
    
    Args:
        app: Bottle application instance
        protected_routes: List of route patterns that require authentication
                         If None, all routes except /health require authentication
    """
    
    if protected_routes is None:
        protected_routes = ['/api/']
    
    @app.hook('before_request')
    def before_request_auth():
        """Check authentication for protected routes"""
        
        # Skip authentication for public routes
        public_routes = ['/health', '/metrics', '/docs', '/swagger']
        
        if any(request.path.startswith(route) for route in public_routes):
            return
        
        # Check if route requires authentication
        requires_auth = any(
            request.path.startswith(route) for route in protected_routes
        )
        
        if requires_auth:
            try:
                user_context = AuthenticationMiddleware.authenticate_request()
                request.user_context = user_context
                
                logger.debug(
                    "Authentication successful",
                    extra={
                        "request_id": getattr(request, 'request_id', 'unknown'),
                        "user_id": user_context.get('user_id')
                    }
                )
            
            except Exception as e:
                logger.warning(
                    f"Authentication error: {str(e)}",
                    extra={
                        "request_id": getattr(request, 'request_id', 'unknown')
                    }
                )
                abort(401, "Unauthorized")
