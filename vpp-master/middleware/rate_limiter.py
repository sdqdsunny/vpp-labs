"""
Rate Limiting Middleware

Implements per-user and per-endpoint rate limiting with configurable limits.
"""

import time
from collections import defaultdict
from bottle import request, response
from utils.logger import setup_logger
from datetime import datetime, timedelta

logger = setup_logger(__name__)

# Rate limit configuration
PER_USER_LIMIT = 1000  # requests per hour
PER_ENDPOINT_LIMIT = 100  # requests per minute
HOUR_SECONDS = 3600
MINUTE_SECONDS = 60


class RateLimiter:
    """Rate limiter for API requests"""
    
    def __init__(self):
        """Initialize rate limiter"""
        self.user_requests = defaultdict(list)  # user_id -> [(timestamp, endpoint), ...]
        self.endpoint_requests = defaultdict(list)  # endpoint -> [(timestamp, user_id), ...]
    
    def get_user_id(self):
        """Extract user ID from request"""
        # Try to get from auth context
        if hasattr(request, 'user_id'):
            return request.user_id
        # Fallback to API key or IP address
        api_key = request.headers.get('X-API-Key', '')
        if api_key:
            return api_key
        return request.remote_addr
    
    def cleanup_old_requests(self, requests_list, window_seconds):
        """Remove requests older than the time window"""
        current_time = time.time()
        cutoff_time = current_time - window_seconds
        return [req_time for req_time in requests_list if req_time > cutoff_time]
    
    def check_user_rate_limit(self, user_id):
        """
        Check if user has exceeded hourly rate limit
        
        Returns:
            (is_allowed, remaining, reset_time)
        """
        current_time = time.time()
        
        # Clean up old requests
        self.user_requests[user_id] = self.cleanup_old_requests(
            self.user_requests[user_id],
            HOUR_SECONDS
        )
        
        request_count = len(self.user_requests[user_id])
        
        if request_count >= PER_USER_LIMIT:
            # Calculate reset time (when oldest request expires)
            oldest_request = min(self.user_requests[user_id])
            reset_time = int(oldest_request + HOUR_SECONDS)
            return False, 0, reset_time
        
        remaining = PER_USER_LIMIT - request_count - 1
        reset_time = int(current_time + HOUR_SECONDS)
        
        return True, remaining, reset_time
    
    def check_endpoint_rate_limit(self, endpoint, user_id):
        """
        Check if endpoint has exceeded per-minute rate limit
        
        Returns:
            (is_allowed, remaining, reset_time)
        """
        current_time = time.time()
        
        # Clean up old requests
        self.endpoint_requests[endpoint] = self.cleanup_old_requests(
            self.endpoint_requests[endpoint],
            MINUTE_SECONDS
        )
        
        request_count = len(self.endpoint_requests[endpoint])
        
        if request_count >= PER_ENDPOINT_LIMIT:
            # Calculate reset time (when oldest request expires)
            oldest_request = min(self.endpoint_requests[endpoint])
            reset_time = int(oldest_request + MINUTE_SECONDS)
            return False, 0, reset_time
        
        remaining = PER_ENDPOINT_LIMIT - request_count - 1
        reset_time = int(current_time + MINUTE_SECONDS)
        
        return True, remaining, reset_time
    
    def record_request(self, user_id, endpoint):
        """Record a request for rate limiting"""
        current_time = time.time()
        self.user_requests[user_id].append(current_time)
        self.endpoint_requests[endpoint].append(current_time)


# Global rate limiter instance
rate_limiter = RateLimiter()


def setup_rate_limiting(app):
    """
    Setup rate limiting for Bottle app
    
    Args:
        app: Bottle application instance
    """
    
    @app.hook('before_request')
    def check_rate_limits():
        """Check rate limits before processing request"""
        # Skip rate limiting for health check and metrics endpoints
        if request.path in ['/health', '/metrics', '/docs', '/']:
            return
        
        user_id = rate_limiter.get_user_id()
        endpoint = request.path
        
        # Check user rate limit (per hour)
        user_allowed, user_remaining, user_reset = rate_limiter.check_user_rate_limit(user_id)
        
        # Check endpoint rate limit (per minute)
        endpoint_allowed, endpoint_remaining, endpoint_reset = rate_limiter.check_endpoint_rate_limit(
            endpoint,
            user_id
        )
        
        # Store rate limit info in request for response headers
        request.rate_limit_user_remaining = user_remaining
        request.rate_limit_user_reset = user_reset
        request.rate_limit_endpoint_remaining = endpoint_remaining
        request.rate_limit_endpoint_reset = endpoint_reset
        
        # If either limit is exceeded, return 429
        if not user_allowed:
            logger.warning(
                f"User rate limit exceeded for {user_id}",
                extra={
                    "request_id": getattr(request, 'request_id', 'unknown'),
                    "user_id": user_id,
                    "limit_type": "user_hourly"
                }
            )
            response.status = 429
            response.content_type = 'application/json'
            import json
            return json.dumps({
                "error": {
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": "User rate limit exceeded (1000 requests/hour)",
                    "request_id": getattr(request, 'request_id', 'unknown')
                }
            })
        
        if not endpoint_allowed:
            logger.warning(
                f"Endpoint rate limit exceeded for {endpoint}",
                extra={
                    "request_id": getattr(request, 'request_id', 'unknown'),
                    "endpoint": endpoint,
                    "limit_type": "endpoint_per_minute"
                }
            )
            response.status = 429
            response.content_type = 'application/json'
            import json
            return json.dumps({
                "error": {
                    "code": "RATE_LIMIT_EXCEEDED",
                    "message": "Endpoint rate limit exceeded (100 requests/minute)",
                    "request_id": getattr(request, 'request_id', 'unknown')
                }
            })
        
        # Record this request
        rate_limiter.record_request(user_id, endpoint)
    
    @app.hook('after_request')
    def add_rate_limit_headers():
        """Add rate limit headers to response"""
        # Skip for health check and metrics endpoints
        if request.path in ['/health', '/metrics', '/docs', '/']:
            return
        
        # Add rate limit headers
        if hasattr(request, 'rate_limit_user_remaining'):
            response.headers['X-RateLimit-Limit'] = str(PER_USER_LIMIT)
            response.headers['X-RateLimit-Remaining'] = str(request.rate_limit_user_remaining)
            response.headers['X-RateLimit-Reset'] = str(request.rate_limit_user_reset)
            
            # Also add endpoint-specific headers
            response.headers['X-RateLimit-Endpoint-Limit'] = str(PER_ENDPOINT_LIMIT)
            response.headers['X-RateLimit-Endpoint-Remaining'] = str(request.rate_limit_endpoint_remaining)
            response.headers['X-RateLimit-Endpoint-Reset'] = str(request.rate_limit_endpoint_reset)
