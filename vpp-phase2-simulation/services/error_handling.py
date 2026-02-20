"""
Error Handling and Retry Logic

Provides utilities for error handling, retry logic, and logging for security tests.
"""

import logging
import time
from typing import Callable, Any, Optional, TypeVar, List
from functools import wraps
from enum import Enum

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RetryableError(Exception):
    """Exception that indicates a retryable error"""
    def __init__(self, message: str, severity: ErrorSeverity = ErrorSeverity.MEDIUM):
        super().__init__(message)
        self.severity = severity


class FatalError(Exception):
    """Exception that indicates a fatal, non-retryable error"""
    def __init__(self, message: str, severity: ErrorSeverity = ErrorSeverity.CRITICAL):
        super().__init__(message)
        self.severity = severity


def retry_with_backoff(max_retries: int = 3, 
                       initial_delay: float = 1.0,
                       max_delay: float = 30.0,
                       backoff_factor: float = 2.0,
                       retryable_exceptions: Optional[List[type]] = None) -> Callable:
    """Decorator for retrying functions with exponential backoff
    
    Args:
        max_retries: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        backoff_factor: Multiplier for delay between retries
        retryable_exceptions: List of exception types to retry on
        
    Returns:
        Decorated function with retry logic
    """
    if retryable_exceptions is None:
        retryable_exceptions = [RetryableError, ConnectionError, TimeoutError]
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            delay = initial_delay
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    logger.debug(f"Executing {func.__name__} (attempt {attempt + 1}/{max_retries + 1})")
                    return func(*args, **kwargs)
                except tuple(retryable_exceptions) as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        logger.warning(
                            f"{func.__name__} failed (attempt {attempt + 1}/{max_retries + 1}): {e}. "
                            f"Retrying in {delay:.1f}s..."
                        )
                        time.sleep(delay)
                        delay = min(delay * backoff_factor, max_delay)
                    else:
                        logger.error(
                            f"{func.__name__} failed after {max_retries + 1} attempts: {e}"
                        )
                except Exception as e:
                    # Non-retryable exception
                    logger.error(f"{func.__name__} failed with non-retryable error: {e}")
                    raise
            
            # All retries exhausted
            if last_exception:
                raise last_exception
            
        return wrapper
    return decorator


def handle_errors(default_return: Any = None,
                  log_level: int = logging.ERROR) -> Callable:
    """Decorator for handling errors gracefully
    
    Args:
        default_return: Value to return if an error occurs
        log_level: Logging level for errors
        
    Returns:
        Decorated function with error handling
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.log(log_level, f"Error in {func.__name__}: {e}", exc_info=True)
                return default_return
        
        return wrapper
    return decorator


class ErrorContext:
    """Context manager for error handling and logging"""
    
    def __init__(self, operation_name: str, log_errors: bool = True):
        """Initialize error context
        
        Args:
            operation_name: Name of the operation for logging
            log_errors: Whether to log errors
        """
        self.operation_name = operation_name
        self.log_errors = log_errors
        self.errors: List[str] = []
        self.start_time = None
    
    def __enter__(self):
        """Enter context"""
        self.start_time = time.time()
        logger.debug(f"Starting operation: {self.operation_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context"""
        duration = time.time() - self.start_time
        
        if exc_type is not None:
            error_msg = f"{exc_type.__name__}: {exc_val}"
            self.errors.append(error_msg)
            
            if self.log_errors:
                logger.error(
                    f"Operation '{self.operation_name}' failed after {duration:.2f}s: {error_msg}",
                    exc_info=(exc_type, exc_val, exc_tb)
                )
        else:
            logger.debug(f"Operation '{self.operation_name}' completed in {duration:.2f}s")
        
        return False  # Don't suppress exceptions
    
    def add_error(self, error_msg: str) -> None:
        """Add an error message to the context
        
        Args:
            error_msg: Error message to add
        """
        self.errors.append(error_msg)
        if self.log_errors:
            logger.warning(f"Error in {self.operation_name}: {error_msg}")
    
    def has_errors(self) -> bool:
        """Check if any errors occurred
        
        Returns:
            True if errors occurred, False otherwise
        """
        return len(self.errors) > 0
    
    def get_errors(self) -> List[str]:
        """Get all errors that occurred
        
        Returns:
            List of error messages
        """
        return self.errors.copy()


class DependencyChecker:
    """Utility for checking and logging dependency availability"""
    
    def __init__(self):
        """Initialize dependency checker"""
        self.checked_dependencies: dict = {}
    
    def check_dependency(self, module_name: str, package_name: Optional[str] = None) -> bool:
        """Check if a dependency is available
        
        Args:
            module_name: Name of the module to import
            package_name: Display name of the package (defaults to module_name)
            
        Returns:
            True if dependency is available, False otherwise
        """
        if package_name is None:
            package_name = module_name
        
        if package_name in self.checked_dependencies:
            return self.checked_dependencies[package_name]
        
        try:
            __import__(module_name)
            self.checked_dependencies[package_name] = True
            logger.debug(f"Dependency '{package_name}' is available")
            return True
        except ImportError:
            self.checked_dependencies[package_name] = False
            logger.warning(f"Dependency '{package_name}' is not available")
            return False
    
    def check_multiple_dependencies(self, dependencies: dict) -> dict:
        """Check multiple dependencies at once
        
        Args:
            dependencies: Dictionary mapping module names to display names
            
        Returns:
            Dictionary with availability status for each dependency
        """
        results = {}
        for module_name, display_name in dependencies.items():
            results[display_name] = self.check_dependency(module_name, display_name)
        return results
    
    def get_unavailable_dependencies(self) -> List[str]:
        """Get list of unavailable dependencies
        
        Returns:
            List of unavailable dependency names
        """
        return [name for name, available in self.checked_dependencies.items() if not available]
    
    def log_dependency_status(self) -> None:
        """Log the status of all checked dependencies"""
        available = [name for name, avail in self.checked_dependencies.items() if avail]
        unavailable = [name for name, avail in self.checked_dependencies.items() if not avail]
        
        if available:
            logger.info(f"Available dependencies: {', '.join(available)}")
        
        if unavailable:
            logger.warning(f"Unavailable dependencies: {', '.join(unavailable)}")


# Global dependency checker instance
_dependency_checker: Optional[DependencyChecker] = None


def get_dependency_checker() -> DependencyChecker:
    """Get or create the global dependency checker
    
    Returns:
        DependencyChecker instance
    """
    global _dependency_checker
    if _dependency_checker is None:
        _dependency_checker = DependencyChecker()
    return _dependency_checker
