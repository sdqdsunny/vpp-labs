"""
Error Handling Tests

Tests for error handling, retry logic, and dependency checking utilities.
"""

import pytest
import time
from unittest.mock import Mock, patch

from services.error_handling import (
    ErrorSeverity,
    RetryableError,
    FatalError,
    retry_with_backoff,
    handle_errors,
    ErrorContext,
    DependencyChecker,
    get_dependency_checker
)


class TestErrorSeverity:
    """Test ErrorSeverity enum"""
    
    def test_severity_values(self):
        """Test severity enum values"""
        assert ErrorSeverity.LOW.value == "low"
        assert ErrorSeverity.MEDIUM.value == "medium"
        assert ErrorSeverity.HIGH.value == "high"
        assert ErrorSeverity.CRITICAL.value == "critical"


class TestRetryableError:
    """Test RetryableError exception"""
    
    def test_retryable_error_creation(self):
        """Test creating a retryable error"""
        error = RetryableError("Test error", ErrorSeverity.HIGH)
        
        assert str(error) == "Test error"
        assert error.severity == ErrorSeverity.HIGH
    
    def test_retryable_error_default_severity(self):
        """Test retryable error with default severity"""
        error = RetryableError("Test error")
        
        assert error.severity == ErrorSeverity.MEDIUM


class TestFatalError:
    """Test FatalError exception"""
    
    def test_fatal_error_creation(self):
        """Test creating a fatal error"""
        error = FatalError("Test error", ErrorSeverity.CRITICAL)
        
        assert str(error) == "Test error"
        assert error.severity == ErrorSeverity.CRITICAL
    
    def test_fatal_error_default_severity(self):
        """Test fatal error with default severity"""
        error = FatalError("Test error")
        
        assert error.severity == ErrorSeverity.CRITICAL


class TestRetryWithBackoff:
    """Test retry_with_backoff decorator"""
    
    def test_successful_execution(self):
        """Test successful execution without retries"""
        mock_func = Mock(return_value="success")
        
        @retry_with_backoff(max_retries=3)
        def test_func():
            return mock_func()
        
        result = test_func()
        
        assert result == "success"
        assert mock_func.call_count == 1
    
    def test_retry_on_retryable_error(self):
        """Test retrying on retryable error"""
        mock_func = Mock(side_effect=[
            RetryableError("Error 1"),
            RetryableError("Error 2"),
            "success"
        ])
        
        @retry_with_backoff(max_retries=3, initial_delay=0.01, max_delay=0.1)
        def test_func():
            return mock_func()
        
        result = test_func()
        
        assert result == "success"
        assert mock_func.call_count == 3
    
    def test_max_retries_exceeded(self):
        """Test that exception is raised after max retries"""
        mock_func = Mock(side_effect=RetryableError("Persistent error"))
        
        @retry_with_backoff(max_retries=2, initial_delay=0.01, max_delay=0.1)
        def test_func():
            return mock_func()
        
        with pytest.raises(RetryableError):
            test_func()
        
        assert mock_func.call_count == 3  # Initial + 2 retries
    
    def test_non_retryable_error_not_retried(self):
        """Test that non-retryable errors are not retried"""
        mock_func = Mock(side_effect=ValueError("Non-retryable error"))
        
        @retry_with_backoff(max_retries=3, initial_delay=0.01)
        def test_func():
            return mock_func()
        
        with pytest.raises(ValueError):
            test_func()
        
        assert mock_func.call_count == 1
    
    def test_custom_retryable_exceptions(self):
        """Test with custom retryable exceptions"""
        class CustomError(Exception):
            pass
        
        mock_func = Mock(side_effect=[
            CustomError("Error 1"),
            "success"
        ])
        
        @retry_with_backoff(max_retries=2, initial_delay=0.01, retryable_exceptions=[CustomError])
        def test_func():
            return mock_func()
        
        result = test_func()
        
        assert result == "success"
        assert mock_func.call_count == 2
    
    def test_exponential_backoff(self):
        """Test exponential backoff timing"""
        mock_func = Mock(side_effect=[
            RetryableError("Error 1"),
            RetryableError("Error 2"),
            "success"
        ])
        
        @retry_with_backoff(max_retries=3, initial_delay=0.05, backoff_factor=2.0, max_delay=1.0)
        def test_func():
            return mock_func()
        
        start_time = time.time()
        result = test_func()
        elapsed = time.time() - start_time
        
        # Should have delays of ~0.05s and ~0.1s
        assert result == "success"
        assert elapsed >= 0.15  # At least 0.05 + 0.1


class TestHandleErrors:
    """Test handle_errors decorator"""
    
    def test_successful_execution(self):
        """Test successful execution without errors"""
        @handle_errors(default_return="default")
        def test_func():
            return "success"
        
        result = test_func()
        
        assert result == "success"
    
    def test_error_handling_with_default_return(self):
        """Test error handling with default return value"""
        @handle_errors(default_return="default")
        def test_func():
            raise ValueError("Test error")
        
        result = test_func()
        
        assert result == "default"
    
    def test_error_handling_with_none_default(self):
        """Test error handling with None as default"""
        @handle_errors(default_return=None)
        def test_func():
            raise ValueError("Test error")
        
        result = test_func()
        
        assert result is None
    
    def test_error_handling_with_dict_default(self):
        """Test error handling with dict as default"""
        default_dict = {"error": True}
        
        @handle_errors(default_return=default_dict)
        def test_func():
            raise ValueError("Test error")
        
        result = test_func()
        
        assert result == default_dict


class TestErrorContext:
    """Test ErrorContext context manager"""
    
    def test_successful_operation(self):
        """Test successful operation in context"""
        with ErrorContext("test_operation") as ctx:
            pass
        
        assert not ctx.has_errors()
        assert len(ctx.get_errors()) == 0
    
    def test_error_in_context(self):
        """Test error handling in context"""
        with pytest.raises(ValueError):
            with ErrorContext("test_operation") as ctx:
                raise ValueError("Test error")
    
    def test_add_error_to_context(self):
        """Test adding errors to context"""
        with ErrorContext("test_operation") as ctx:
            ctx.add_error("Error 1")
            ctx.add_error("Error 2")
        
        assert ctx.has_errors()
        assert len(ctx.get_errors()) == 2
        assert "Error 1" in ctx.get_errors()
        assert "Error 2" in ctx.get_errors()
    
    def test_error_context_timing(self):
        """Test that error context tracks timing"""
        with ErrorContext("test_operation") as ctx:
            time.sleep(0.05)
        
        # Just verify it doesn't crash and tracks timing
        assert ctx.start_time is not None


class TestDependencyChecker:
    """Test DependencyChecker utility"""
    
    def test_check_available_dependency(self):
        """Test checking an available dependency"""
        checker = DependencyChecker()
        
        # json is always available
        result = checker.check_dependency("json", "json")
        
        assert result is True
    
    def test_check_unavailable_dependency(self):
        """Test checking an unavailable dependency"""
        checker = DependencyChecker()
        
        result = checker.check_dependency("nonexistent_module_xyz", "nonexistent")
        
        assert result is False
    
    def test_dependency_caching(self):
        """Test that dependency checks are cached"""
        checker = DependencyChecker()
        
        # First check
        result1 = checker.check_dependency("json", "json")
        # Second check (should use cache)
        result2 = checker.check_dependency("json", "json")
        
        assert result1 is True
        assert result2 is True
    
    def test_check_multiple_dependencies(self):
        """Test checking multiple dependencies"""
        checker = DependencyChecker()
        
        dependencies = {
            "json": "json",
            "nonexistent_xyz": "nonexistent"
        }
        
        results = checker.check_multiple_dependencies(dependencies)
        
        assert results["json"] is True
        assert results["nonexistent"] is False
    
    def test_get_unavailable_dependencies(self):
        """Test getting list of unavailable dependencies"""
        checker = DependencyChecker()
        
        checker.check_dependency("json", "json")
        checker.check_dependency("nonexistent_xyz", "nonexistent")
        
        unavailable = checker.get_unavailable_dependencies()
        
        assert "nonexistent" in unavailable
        assert "json" not in unavailable
    
    def test_log_dependency_status(self):
        """Test logging dependency status"""
        checker = DependencyChecker()
        
        checker.check_dependency("json", "json")
        checker.check_dependency("nonexistent_xyz", "nonexistent")
        
        # Should not raise any exceptions
        checker.log_dependency_status()


class TestGlobalDependencyChecker:
    """Test global dependency checker functions"""
    
    def test_get_dependency_checker_singleton(self):
        """Test that global dependency checker is a singleton"""
        checker1 = get_dependency_checker()
        checker2 = get_dependency_checker()
        
        assert checker1 is checker2
    
    def test_dependency_checker_instance(self):
        """Test that global dependency checker is correct type"""
        checker = get_dependency_checker()
        
        assert isinstance(checker, DependencyChecker)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
