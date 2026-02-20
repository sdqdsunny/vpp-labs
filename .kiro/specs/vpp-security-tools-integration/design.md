# Design Document: VPP Security Tools Integration

## Overview

This design document specifies the architecture and implementation approach for integrating three open-source security testing tools (OpenDNP3, python-opcua, and Boofuzz) into the VPP Phase 2 security testing framework.

The integration follows an adapter pattern where each tool is wrapped in a standardized adapter that implements a common interface. This allows the SecurityTestManager to manage all tools uniformly while maintaining tool-specific functionality.

### Key Design Principles

1. **Adapter Pattern**: Each security testing tool is wrapped in an adapter that implements a standard interface
2. **Graceful Degradation**: Missing dependencies don't break the system; tools are marked as unavailable
3. **Standardized Results**: All test results follow a consistent format for easy integration with other components
4. **Docker-First**: All tools must work correctly in containerized environments
5. **Extensibility**: New tools can be added by implementing the adapter interface

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Web Interface (Flask/Bottle)             │
│              /security_tester endpoint                      │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│              SecurityTestManager                            │
│  - Manages all test adapters                               │
│  - Routes test requests to appropriate adapters            │
│  - Stores test results                                     │
└────────────────────────┬────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
┌───────▼────────┐ ┌────▼──────────┐ ┌──▼──────────────┐
│ ModbusAdapter  │ │ DNP3Adapter   │ │ OPCUAAdapter   │
│ (PyModbus)     │ │ (OpenDNP3)    │ │ (python-opcua) │
└────────────────┘ └───────────────┘ └────────────────┘
        │                │                │
        └────────────────┼────────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
┌───────▼────────┐ ┌────▼──────────┐ ┌──▼──────────────┐
│ CANAdapter     │ │ BoofuzzAdapter│ │ ResultStorage  │
│ (SocketCAN)    │ │ (Boofuzz)     │ │ (Database)     │
└────────────────┘ └───────────────┘ └────────────────┘
```

### Component Interactions

1. **Web Interface** → Receives test requests from users
2. **SecurityTestManager** → Routes requests to appropriate adapters
3. **Test Adapters** → Execute tests using underlying tools
4. **Result Storage** → Persists test results for historical analysis
5. **Protocol Analyzer** → Integrates with test results for correlation

## Components and Interfaces

### 1. SecurityTestManager (Enhanced)

The existing SecurityTestManager is enhanced to support the new adapters.

```python
class SecurityTestManager:
    def __init__(self):
        self.adapters: Dict[str, TestAdapter] = {}
        self.results: Dict[str, TestResult] = {}
        self.lock = threading.RLock()
    
    def register_adapter(self, name: str, adapter: TestAdapter) -> None:
        """Register a test adapter"""
        
    def run_test(self, test_request: TestRequest) -> TestResult:
        """Execute a test and return results"""
        
    def get_available_tools(self) -> Dict[str, bool]:
        """Get availability status of all tools"""
        
    def get_test_results(self, test_id: str) -> Optional[TestResult]:
        """Retrieve a test result"""
```

### 2. TestAdapter Interface

All test adapters implement this interface:

```python
class TestAdapter(ABC):
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the underlying tool is available"""
        
    @abstractmethod
    def execute_test(self, test_request: TestRequest) -> TestResult:
        """Execute a test and return results"""
        
    @abstractmethod
    def get_supported_tests(self) -> List[str]:
        """Get list of supported test types"""
```

### 3. DNP3Adapter

Wraps OpenDNP3 functionality:

```python
class DNP3Adapter(TestAdapter):
    def __init__(self):
        self.available = self._check_availability()
    
    def execute_test(self, test_request: TestRequest) -> TestResult:
        if test_request.test_type == "connection":
            return self._test_connection(test_request)
        elif test_request.test_type == "scan":
            return self._test_scan(test_request)
        # ... other test types
    
    def _test_connection(self, request: TestRequest) -> TestResult:
        """Test DNP3 connection"""
        
    def _test_scan(self, request: TestRequest) -> TestResult:
        """Scan DNP3 points"""
```

### 4. OPCUAAdapter

Wraps python-opcua functionality:

```python
class OPCUAAdapter(TestAdapter):
    def __init__(self):
        self.available = self._check_availability()
    
    def execute_test(self, test_request: TestRequest) -> TestResult:
        if test_request.test_type == "connection":
            return self._test_connection(test_request)
        elif test_request.test_type == "browse":
            return self._test_browse(test_request)
        # ... other test types
    
    def _test_connection(self, request: TestRequest) -> TestResult:
        """Test OPC UA connection"""
        
    def _test_browse(self, request: TestRequest) -> TestResult:
        """Browse OPC UA namespace"""
```

### 5. BoofuzzAdapter

Wraps Boofuzz functionality:

```python
class BoofuzzAdapter(TestAdapter):
    def __init__(self):
        self.available = self._check_availability()
    
    def execute_test(self, test_request: TestRequest) -> TestResult:
        if test_request.test_type == "modbus_fuzz":
            return self._fuzz_modbus(test_request)
        elif test_request.test_type == "dnp3_fuzz":
            return self._fuzz_dnp3(test_request)
        # ... other test types
    
    def _fuzz_modbus(self, request: TestRequest) -> TestResult:
        """Fuzz Modbus protocol"""
        
    def _fuzz_dnp3(self, request: TestRequest) -> TestResult:
        """Fuzz DNP3 protocol"""
```

### 6. TestResult Data Model

```python
@dataclass
class TestResult:
    test_id: str
    test_type: str
    adapter_name: str
    status: str  # "success", "failed", "error"
    start_time: datetime
    end_time: datetime
    duration: float
    target_host: str
    target_port: int
    target_url: Optional[str]  # For OPC UA
    result_data: Dict[str, Any]
    error_message: Optional[str]
    vulnerabilities_found: List[str]
    metadata: Dict[str, Any]
```

## Data Models

### Test Request

```python
@dataclass
class TestRequest:
    test_type: str  # "connection", "scan", "fuzz", etc.
    adapter_name: str  # "dnp3", "opcua", "boofuzz"
    target_host: str
    target_port: int
    target_url: Optional[str]  # For OPC UA
    parameters: Dict[str, Any]  # Tool-specific parameters
    timeout: int = 30
```

### Test Result Storage Schema

```sql
CREATE TABLE test_results (
    id UUID PRIMARY KEY,
    test_type VARCHAR(50),
    adapter_name VARCHAR(50),
    status VARCHAR(20),
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    duration FLOAT,
    target_host VARCHAR(255),
    target_port INTEGER,
    target_url VARCHAR(255),
    result_data JSONB,
    error_message TEXT,
    vulnerabilities JSONB,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_adapter_name ON test_results(adapter_name);
CREATE INDEX idx_target_host ON test_results(target_host);
CREATE INDEX idx_created_at ON test_results(created_at);
```

## Correctness Properties

A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.

### Property 1: Adapter Registration and Discovery

*For any* security testing tool adapter, when the SecurityTestManager initializes, that adapter should be registered and appear in the available tools list.

**Validates: Requirements 1.1, 2.1, 3.4, 5.2**

### Property 2: Graceful Dependency Handling

*For any* missing security testing tool dependency, the system should continue operation with that tool marked as unavailable, and a warning should be logged.

**Validates: Requirements 1.5, 2.5, 3.4, 4.2**

### Property 3: Test Result Standardization

*For any* security test executed by any adapter, the result should contain all required fields (test_id, test_type, status, start_time, end_time, target_host, target_port) in a consistent format.

**Validates: Requirements 1.4, 2.4, 3.3, 5.3**

### Property 4: Error Handling and Recovery

*For any* test adapter that encounters an error, the adapter should catch the exception and return a TestResult with status="error" and a descriptive error_message.

**Validates: Requirements 5.4, 10.1**

### Property 5: Test Result Persistence

*For any* completed security test, the test result should be stored in persistent storage and retrievable by test_id.

**Validates: Requirements 9.1**

### Property 6: Historical Result Retrieval

*For any* test result created within the past 30 days, the result should be retrievable through the historical results API.

**Validates: Requirements 9.2**

### Property 7: Result Filtering

*For any* set of test results, filtering by protocol, target_host, or test_type should return only results matching the filter criteria.

**Validates: Requirements 9.3**

### Property 8: Protocol Analyzer Integration

*For any* completed security test, the test metadata should be in a format compatible with the protocol analyzer, and the analyzer should be able to parse and display the test findings.

**Validates: Requirements 7.1, 7.2**

### Property 9: Vulnerability Tagging

*For any* discovered vulnerability in a security test, the related network flows should be tagged with the vulnerability information.

**Validates: Requirements 7.3**

### Property 10: Docker Container Network Access

*For any* security test running in a Docker container, the test should have network access to other containers on the 10.0.8.0/24 network.

**Validates: Requirements 8.3**

### Property 11: Dependency Installation

*For any* required security testing tool dependency declared in requirements.txt, the dependency should be installed during project deployment.

**Validates: Requirements 4.1**

### Property 12: Startup Verification

*For any* system startup, the system should verify that all declared dependencies are available and report their status in the available tools list.

**Validates: Requirements 4.4, 8.2**

### Property 13: Retry Logic

*For any* network error encountered during a security test, the system should retry the test up to 3 times before reporting failure.

**Validates: Requirements 10.3**

### Property 14: Export Completeness

*For any* exported test result, the export should include all metadata, findings, and vulnerability information in a structured format.

**Validates: Requirements 9.4, 7.4**

## Error Handling

### Dependency Missing

When a security testing tool dependency is not installed:
1. Log a warning message
2. Mark the adapter as unavailable
3. Return error response when user attempts to use the tool
4. Continue operation with other tools

### Network Error

When a test encounters a network error:
1. Retry up to 3 times with exponential backoff
2. Log each retry attempt
3. If all retries fail, return error result with descriptive message
4. Record the error in test history

### Invalid Parameters

When a test request has invalid parameters:
1. Validate parameters before executing test
2. Return error response with validation details
3. Log the invalid request
4. Do not execute the test

### Adapter Initialization Error

When an adapter fails to initialize:
1. Log the error with full context
2. Mark the adapter as unavailable
3. Continue system operation
4. Report the error in available tools list

## Testing Strategy

### Unit Testing

Unit tests verify individual adapter functionality with mocked dependencies:

- **DNP3Adapter Tests**: Mock OpenDNP3 library, test connection and scanning logic
- **OPCUAAdapter Tests**: Mock python-opcua library, test connection and browsing logic
- **BoofuzzAdapter Tests**: Mock Boofuzz library, test fuzzing logic
- **SecurityTestManager Tests**: Test adapter registration, routing, and result storage
- **Error Handling Tests**: Test graceful degradation when dependencies are missing

### Property-Based Testing

Property-based tests verify universal properties across many generated inputs:

- **Adapter Registration Property**: Generate random adapters, verify they register correctly
- **Result Standardization Property**: Generate random test requests, verify results have consistent format
- **Error Handling Property**: Generate random error conditions, verify graceful handling
- **Persistence Property**: Generate random test results, verify they persist and retrieve correctly
- **Filtering Property**: Generate random test results with various metadata, verify filtering works correctly

### Integration Testing

Integration tests verify the full workflow:

- **End-to-End Test Execution**: Execute a test from request to result storage
- **Protocol Analyzer Integration**: Verify test results integrate with protocol analyzer
- **Docker Container Testing**: Verify all tools work in Docker containers
- **Network Access Testing**: Verify containers can reach each other on the VPP network

### Test Configuration

- Minimum 100 iterations per property-based test
- Unit tests for each adapter (minimum 10 tests per adapter)
- Integration tests for full workflows (minimum 5 tests)
- All tests must pass before deployment

## Deployment Considerations

### Docker Image

The Docker image must include:
- Python 3.11 base image
- All dependencies from requirements.txt
- System packages for DNP3, OPC UA, and Boofuzz support
- Network tools for testing (curl, ping, netstat)

### Environment Variables

- `SECURITY_TOOLS_ENABLED`: Enable/disable security testing (default: true)
- `TEST_TIMEOUT`: Default timeout for tests in seconds (default: 30)
- `RESULT_RETENTION_DAYS`: Days to retain test results (default: 30)

### Network Configuration

- All containers must be on the 10.0.8.0/24 network
- Security testing tools must have access to test targets
- Firewall rules must allow test traffic

### Monitoring and Logging

- All test executions logged with timestamps
- Failed tests logged with error details
- Missing dependencies logged as warnings
- Test results exported to monitoring system

