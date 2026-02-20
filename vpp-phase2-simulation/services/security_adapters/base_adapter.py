"""
Base Test Adapter Interface

This module defines the abstract base class and data models for all security testing tool adapters.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Any, Optional
import uuid
import logging

logger = logging.getLogger(__name__)


@dataclass
class TestRequest:
    """Represents a security test request"""
    test_type: str  # "connection", "scan", "fuzz", etc.
    adapter_name: str  # "dnp3", "opcua", "boofuzz", "modbus", "can"
    target_host: str
    target_port: int
    target_url: Optional[str] = None  # For OPC UA
    parameters: Dict[str, Any] = field(default_factory=dict)
    timeout: int = 30


@dataclass
class TestResult:
    """Represents a security test result"""
    test_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    test_type: str = ""
    adapter_name: str = ""
    status: str = "pending"  # "success", "failed", "error"
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: Optional[datetime] = None
    duration: float = 0.0
    target_host: str = ""
    target_port: int = 0
    target_url: Optional[str] = None
    result_data: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    vulnerabilities_found: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary"""
        data = asdict(self)
        data['start_time'] = self.start_time.isoformat()
        if self.end_time:
            data['end_time'] = self.end_time.isoformat()
        return data

    def mark_success(self) -> None:
        """Mark test as successful"""
        self.status = "success"
        self.end_time = datetime.utcnow()
        self.duration = (self.end_time - self.start_time).total_seconds()

    def mark_failed(self, error_message: str) -> None:
        """Mark test as failed"""
        self.status = "failed"
        self.error_message = error_message
        self.end_time = datetime.utcnow()
        self.duration = (self.end_time - self.start_time).total_seconds()

    def mark_error(self, error_message: str) -> None:
        """Mark test as error"""
        self.status = "error"
        self.error_message = error_message
        self.end_time = datetime.utcnow()
        self.duration = (self.end_time - self.start_time).total_seconds()


class TestAdapter(ABC):
    """Abstract base class for security testing tool adapters"""

    def __init__(self, name: str):
        """Initialize adapter"""
        self.name = name
        self.available = self._check_availability()
        if not self.available:
            logger.warning(f"Security testing tool '{name}' is not available")

    @abstractmethod
    def _check_availability(self) -> bool:
        """Check if the underlying tool is available"""
        pass

    @abstractmethod
    def execute_test(self, test_request: TestRequest) -> TestResult:
        """Execute a test and return results"""
        pass

    @abstractmethod
    def get_supported_tests(self) -> List[str]:
        """Get list of supported test types"""
        pass

    def is_available(self) -> bool:
        """Check if adapter is available"""
        return self.available

    def _create_result(self, test_request: TestRequest) -> TestResult:
        """Create a test result object"""
        result = TestResult(
            test_type=test_request.test_type,
            adapter_name=self.name,
            target_host=test_request.target_host,
            target_port=test_request.target_port,
            target_url=test_request.target_url,
        )
        return result
