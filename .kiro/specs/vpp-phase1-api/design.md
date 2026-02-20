# Phase 1 API Development - Design Document

## Overview

The Phase 1 API Development establishes the core API infrastructure for the VPP Master Station using Bottle.py, a lightweight zero-dependency web framework. The design focuses on four main API modules that provide device management, dispatch control, protocol conversion, and analysis functionality.

The architecture follows a modular, layered approach with clear separation of concerns:
- **Route Layer**: HTTP endpoint handlers using Bottle.py
- **Service Layer**: Business logic implementation
- **Data Layer**: Database models and persistence using SQLAlchemy
- **Integration Layer**: External system communication (VCC, monitoring systems)

Key design principles:
- **Simplicity**: Bottle.py's minimal overhead enables fast development and deployment
- **Modularity**: Each API module is independently deployable and testable
- **Reliability**: Comprehensive error handling and data validation
- **Observability**: Prometheus metrics and structured logging throughout
- **Scalability**: Stateless design enables horizontal scaling

## Architecture

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    VPP Master Station                        │
│                   (Bottle.py Application)                    │
├─────────────────────────────────────────────────────────────┤
│                      Route Layer                             │
│  ┌──────────────┬──────────────┬──────────────┬────────────┐ │
│  │   Devices    │   Dispatch   │   Protocol   │  Analysis  │ │
│  │   Routes     │   Routes     │   Routes     │  Routes    │ │
│  └──────────────┴──────────────┴──────────────┴────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                     Service Layer                            │
│  ┌──────────────┬──────────────┬──────────────┬────────────┐ │
│  │   Device     │   Dispatch   │   Protocol   │  Analysis  │ │
│  │   Manager    │   Engine     │   Converter  │  Service   │ │
│  └──────────────┴──────────────┴──────────────┴────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                      Data Layer                              │
│  ┌──────────────┬──────────────┬──────────────┬────────────┐ │
│  │   Device     │   Dispatch   │   Protocol   │  Analysis  │ │
│  │   Models     │   Models     │   Models     │  Models    │ │
│  └──────────────┴──────────────┴──────────────┴────────────┘ │
│                    (SQLAlchemy ORM)                          │
├─────────────────────────────────────────────────────────────┤
│                   Integration Layer                          │
│  ┌──────────────┬──────────────┬──────────────┬────────────┐ │
│  │   Database   │   VCC        │  Prometheus  │  Logging   │ │
│  │   (SQLite/   │  (REST API)  │  (Metrics)   │  (JSON)    │ │
│  │   PostgreSQL)│              │              │            │ │
│  └──────────────┴──────────────┴──────────────┴────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Module Organization

```
vpp-master/
├── app.py                          # Main application entry point
├── config.py                       # Configuration management
├── routes/
│   ├── __init__.py
│   ├── devices.py                 # Device management endpoints
│   ├── dispatch.py                # Dispatch control endpoints
│   ├── protocol.py                # Protocol conversion endpoints
│   └── analysis.py                # Analysis functionality endpoints
├── services/
│   ├── __init__.py
│   ├── device_manager.py          # Device management logic
│   ├── dispatch_engine.py         # Dispatch execution logic
│   ├── protocol_converter.py      # Protocol translation logic
│   ├── analyzer.py                # Analysis logic
│   └── event_emitter.py           # Event publishing
├── models/
│   ├── __init__.py
│   ├── device.py                  # Device data model
│   ├── dispatch.py                # Dispatch data model
│   ├── protocol_mapping.py        # Protocol mapping model
│   └── analysis_result.py         # Analysis result model
├── utils/
│   ├── __init__.py
│   ├── logger.py                  # Logging configuration
│   ├── validators.py              # Data validation
│   ├── errors.py                  # Custom exceptions
│   └── metrics.py                 # Prometheus metrics
├── middleware/
│   ├── __init__.py
│   ├── auth.py                    # Authentication middleware
│   ├── error_handler.py           # Error handling middleware
│   └── request_logger.py          # Request logging middleware
└── tests/
    ├── __init__.py
    ├── test_devices.py
    ├── test_dispatch.py
    ├── test_protocol.py
    └── test_analysis.py
```

## Components and Interfaces

### 1. Device Management API

#### Device Manager Service

**Responsibilities**:
- Register new devices with validation
- Discover and list all devices
- Monitor device status and heartbeats
- Manage device configuration
- Emit device lifecycle events

**Key Methods**:
```python
class DeviceManager:
    def register_device(device_data: DeviceRegistration) -> Device
    def discover_devices() -> List[Device]
    def get_device(device_id: str) -> Device
    def update_device_config(device_id: str, config: DeviceConfig) -> Device
    def get_device_status(device_id: str) -> DeviceStatus
    def mark_device_offline(device_id: str) -> None
    def update_device_status(device_id: str, status: str) -> None
```

#### Device Routes

**Endpoints**:
- `POST /api/v1/devices` - Register a new device
- `GET /api/v1/devices` - List all devices with pagination
- `GET /api/v1/devices/{device_id}` - Get device details
- `PUT /api/v1/devices/{device_id}` - Update device configuration
- `DELETE /api/v1/devices/{device_id}` - Deregister a device
- `GET /api/v1/devices/{device_id}/status` - Get device status
- `POST /api/v1/devices/discover` - Trigger device discovery

### 2. Dispatch Control API

#### Dispatch Engine Service

**Responsibilities**:
- Create and validate dispatch commands
- Execute dispatch commands with retry logic
- Schedule future dispatch operations
- Track dispatch status in real-time
- Maintain dispatch history
- Emit dispatch lifecycle events

**Key Methods**:
```python
class DispatchEngine:
    def create_dispatch(dispatch_data: DispatchRequest) -> Dispatch
    def execute_dispatch(dispatch_id: str) -> DispatchResult
    def schedule_dispatch(dispatch_data: DispatchRequest, execution_time: datetime) -> ScheduledDispatch
    def get_dispatch_status(dispatch_id: str) -> DispatchStatus
    def get_dispatch_history(filters: DispatchFilter) -> List[Dispatch]
    def cancel_scheduled_dispatch(dispatch_id: str) -> None
    def retry_failed_dispatch(dispatch_id: str) -> DispatchResult
```

#### Dispatch Routes

**Endpoints**:
- `POST /api/v1/dispatch` - Create and execute a dispatch command
- `GET /api/v1/dispatch/{dispatch_id}` - Get dispatch details
- `GET /api/v1/dispatch/{dispatch_id}/status` - Get dispatch status
- `GET /api/v1/dispatch/history` - Get dispatch history with filters
- `POST /api/v1/dispatch/{dispatch_id}/cancel` - Cancel a dispatch
- `POST /api/v1/dispatch/schedule` - Schedule a future dispatch
- `GET /api/v1/dispatch/scheduled` - List scheduled dispatches

### 3. Protocol Conversion API

#### Protocol Converter Service

**Responsibilities**:
- Parse and validate protocol messages
- Convert between different protocol formats
- Maintain protocol mapping configurations
- Handle protocol-specific errors
- Support extensible protocol adapters

**Key Methods**:
```python
class ProtocolConverter:
    def parse_message(protocol: str, raw_data: bytes) -> Dict
    def encode_message(protocol: str, data: Dict) -> bytes
    def convert_message(source_protocol: str, target_protocol: str, data: Dict) -> Dict
    def validate_message(protocol: str, data: Dict) -> ValidationResult
    def get_protocol_mappings(source: str, target: str) -> List[ProtocolMapping]
    def create_protocol_mapping(mapping_config: MappingConfig) -> ProtocolMapping
```

#### Protocol Routes

**Endpoints**:
- `POST /api/v1/protocol/parse` - Parse a protocol message
- `POST /api/v1/protocol/encode` - Encode data to protocol format
- `POST /api/v1/protocol/convert` - Convert between protocols
- `GET /api/v1/protocol/mappings` - Get protocol mappings
- `POST /api/v1/protocol/mappings` - Create a protocol mapping
- `PUT /api/v1/protocol/mappings/{mapping_id}` - Update a mapping
- `DELETE /api/v1/protocol/mappings/{mapping_id}` - Delete a mapping

### 4. Analysis Functionality API

#### Analyzer Service

**Responsibilities**:
- Execute power flow analysis
- Assess system stability
- Calculate performance metrics
- Generate comprehensive reports
- Analyze Core Dump files
- Generate vulnerability reports

**Key Methods**:
```python
class Analyzer:
    def analyze_power_flow(system_state: SystemState) -> PowerFlowResult
    def analyze_stability(system_state: SystemState) -> StabilityResult
    def calculate_metrics(time_range: TimeRange, aggregation: str) -> MetricsResult
    def generate_report(report_type: str, filters: Dict) -> Report
    def analyze_core_dump(core_dump_file: bytes) -> CoreDumpAnalysis
    def generate_vulnerability_report(filters: Dict) -> VulnerabilityReport
```

#### Analysis Routes

**Endpoints**:
- `POST /api/v1/analysis/power-flow` - Execute power flow analysis
- `POST /api/v1/analysis/stability` - Execute stability analysis
- `GET /api/v1/analysis/metrics` - Get performance metrics
- `POST /api/v1/analysis/report` - Generate a report
- `POST /api/v1/analysis/core-dump/upload` - Upload Core Dump file
- `GET /api/v1/analysis/core-dump/{dump_id}` - Get Core Dump analysis
- `GET /api/v1/analysis/vulnerability-report` - Get vulnerability report

## Data Models

### Device Model

```python
class Device(Base):
    __tablename__ = "devices"
    
    id: str = Column(String, primary_key=True)
    device_type: str = Column(String, nullable=False)  # solar, wind, battery, load
    location: str = Column(String, nullable=False)
    status: str = Column(String, default="offline")  # online, offline, error
    last_heartbeat: datetime = Column(DateTime, nullable=True)
    capabilities: JSON = Column(JSON, nullable=False)
    configuration: JSON = Column(JSON, nullable=False)
    created_at: datetime = Column(DateTime, default=datetime.utcnow)
    updated_at: datetime = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    dispatches = relationship("Dispatch", back_populates="device")
```

### Dispatch Model

```python
class Dispatch(Base):
    __tablename__ = "dispatches"
    
    id: str = Column(String, primary_key=True)
    device_id: str = Column(String, ForeignKey("devices.id"), nullable=False)
    command_type: str = Column(String, nullable=False)
    target_value: float = Column(Float, nullable=False)
    priority_level: int = Column(Integer, default=0)
    status: str = Column(String, default="pending")  # pending, executing, completed, failed
    execution_time: datetime = Column(DateTime, nullable=True)
    scheduled_time: datetime = Column(DateTime, nullable=True)
    retry_count: int = Column(Integer, default=0)
    error_message: str = Column(String, nullable=True)
    created_at: datetime = Column(DateTime, default=datetime.utcnow)
    updated_at: datetime = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    device = relationship("Device", back_populates="dispatches")
```

### Protocol Mapping Model

```python
class ProtocolMapping(Base):
    __tablename__ = "protocol_mappings"
    
    id: str = Column(String, primary_key=True)
    source_protocol: str = Column(String, nullable=False)
    target_protocol: str = Column(String, nullable=False)
    mapping_rules: JSON = Column(JSON, nullable=False)
    is_active: bool = Column(Boolean, default=True)
    created_at: datetime = Column(DateTime, default=datetime.utcnow)
    updated_at: datetime = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

### Analysis Result Model

```python
class AnalysisResult(Base):
    __tablename__ = "analysis_results"
    
    id: str = Column(String, primary_key=True)
    analysis_type: str = Column(String, nullable=False)  # power_flow, stability, metrics
    system_state: JSON = Column(JSON, nullable=False)
    result_data: JSON = Column(JSON, nullable=False)
    status: str = Column(String, default="completed")
    error_message: str = Column(String, nullable=True)
    execution_time_ms: int = Column(Integer, nullable=False)
    created_at: datetime = Column(DateTime, default=datetime.utcnow)
```

## Error Handling

### Error Response Format

All error responses follow a consistent format:

```json
{
  "error": {
    "code": "DEVICE_NOT_FOUND",
    "message": "Device with ID 'device-123' not found",
    "details": {
      "device_id": "device-123",
      "timestamp": "2026-02-16T10:30:00Z"
    },
    "request_id": "req-abc123def456"
  }
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| INVALID_REQUEST | 400 | Request validation failed |
| UNAUTHORIZED | 401 | Authentication required |
| FORBIDDEN | 403 | Authorization failed |
| NOT_FOUND | 404 | Resource not found |
| CONFLICT | 409 | Resource conflict (e.g., duplicate ID) |
| UNPROCESSABLE_ENTITY | 422 | Request data cannot be processed |
| RATE_LIMIT_EXCEEDED | 429 | Rate limit exceeded |
| INTERNAL_ERROR | 500 | Internal server error |
| SERVICE_UNAVAILABLE | 503 | Service temporarily unavailable |

### Exception Hierarchy

```python
class VPPException(Exception):
    """Base exception for all VPP errors"""
    pass

class ValidationError(VPPException):
    """Data validation failed"""
    pass

class DeviceNotFoundError(VPPException):
    """Device not found"""
    pass

class DispatchExecutionError(VPPException):
    """Dispatch execution failed"""
    pass

class ProtocolConversionError(VPPException):
    """Protocol conversion failed"""
    pass

class AnalysisError(VPPException):
    """Analysis execution failed"""
    pass
```

## Testing Strategy

### Unit Testing

Unit tests validate individual components in isolation:

**Device Manager Tests**:
- Device registration with valid/invalid data
- Device discovery and listing
- Device status updates
- Device configuration management
- Duplicate device ID handling

**Dispatch Engine Tests**:
- Dispatch creation and validation
- Dispatch execution with retry logic
- Dispatch scheduling
- Dispatch status tracking
- Dispatch history queries

**Protocol Converter Tests**:
- IEC 104 message parsing
- MQTT message parsing
- Protocol validation
- Error handling for malformed messages
- Protocol mapping application

**Analyzer Tests**:
- Power flow analysis execution
- Stability analysis execution
- Metrics calculation
- Report generation
- Core Dump analysis

### Property-Based Testing

Property-based tests validate universal properties across generated inputs using Hypothesis (Python):

**Configuration**:
- Minimum 100 iterations per property test
- Each test tagged with feature name and property number
- Tag format: `Feature: vpp-phase1-api, Property {number}: {property_text}`

**Test Framework**: Hypothesis for Python

### Integration Testing

Integration tests validate component interactions:

- Device registration → Dispatch creation → Execution flow
- Protocol conversion → Dispatch execution flow
- Analysis → Report generation flow
- Error handling across components

### Test Coverage Goals

- Unit tests: 80% code coverage minimum
- Critical paths: 100% coverage
- Error handling: 100% coverage
- Integration tests: All major workflows

## Monitoring and Observability

### Prometheus Metrics

**Application Metrics**:
- `vpp_api_requests_total` - Total API requests by endpoint and method
- `vpp_api_request_duration_seconds` - API request duration histogram
- `vpp_api_errors_total` - Total API errors by error code
- `vpp_device_count` - Current number of registered devices
- `vpp_device_online_count` - Number of online devices
- `vpp_dispatch_total` - Total dispatch commands by status
- `vpp_dispatch_duration_seconds` - Dispatch execution duration
- `vpp_analysis_duration_seconds` - Analysis execution duration
- `vpp_database_connection_pool_size` - Database connection pool size
- `vpp_database_query_duration_seconds` - Database query duration

**System Metrics**:
- CPU usage
- Memory usage
- Disk I/O
- Network I/O

### Structured Logging

All logs use JSON format with structured fields:

```json
{
  "timestamp": "2026-02-16T10:30:00Z",
  "level": "INFO",
  "logger": "vpp.services.device_manager",
  "message": "Device registered successfully",
  "request_id": "req-abc123def456",
  "device_id": "device-123",
  "device_type": "solar",
  "duration_ms": 45
}
```

### Alerting Rules

- API error rate > 5% for 5 minutes
- API response time p95 > 1000ms for 5 minutes
- Device offline count > 10% of total devices
- Dispatch failure rate > 10% for 5 minutes
- Database connection pool exhaustion
- Analysis execution time > 30 seconds

## Security Considerations

### Authentication

- API key authentication for service-to-service communication
- JWT tokens for user authentication (future phase)
- Token expiration and refresh mechanisms

### Authorization

- Role-based access control (RBAC)
- Resource-level permissions
- Audit logging for all operations

### Data Protection

- Encryption at rest for sensitive data
- Encryption in transit (HTTPS/TLS)
- Secure credential management
- Input validation and sanitization

### Rate Limiting

- Per-user rate limits: 1000 requests/hour
- Per-endpoint rate limits: 100 requests/minute
- Burst allowance: 10 requests/second

## Deployment Architecture

### Development Environment

```
Docker Compose:
- VPP Master (Bottle.py)
- PostgreSQL (database)
- Redis (caching)
- Prometheus (metrics)
- Grafana (visualization)
```

### Production Environment

```
Kubernetes:
- VPP Master replicas (3+)
- PostgreSQL StatefulSet
- Redis cluster
- Prometheus + AlertManager
- Grafana
- Ingress controller
```

### Scaling Considerations

- Stateless API design enables horizontal scaling
- Database connection pooling for efficient resource usage
- Redis caching for frequently accessed data
- Asynchronous task processing for long-running operations
- Load balancing across API instances



## Correctness Properties

A property is a characteristic or behavior that should hold true across all valid executions of a system—essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.

### Property-Based Testing Overview

Property-based testing (PBT) validates software correctness by testing universal properties across many generated inputs. Each property is a formal specification that should hold for all valid inputs.

### Core Principles

1. **Universal Quantification**: Every property must contain an explicit "for all" statement
2. **Requirements Traceability**: Each property must reference the requirements it validates
3. **Executable Specifications**: Properties must be implementable as automated tests
4. **Comprehensive Coverage**: Properties should cover all testable acceptance criteria

### Correctness Properties

#### Device Management Properties

**Property 1: Device Registration Creates Retrievable Record**

*For any* valid device metadata (device_id, device_type, location, capabilities), registering a device should result in that device being retrievable via the discovery endpoint with identical metadata.

**Validates: Requirements 1.1, 1.5**

**Property 2: Duplicate Device IDs Are Rejected**

*For any* device already registered with a given device_id, attempting to register another device with the same device_id should be rejected with a 409 Conflict response.

**Validates: Requirements 1.3**

**Property 3: Invalid Device Registration Is Rejected**

*For any* device registration request missing required fields (device_id, device_type, location), the registration should be rejected with a 400 Bad Request response containing specific field validation errors.

**Validates: Requirements 1.2**

**Property 4: Discovery Returns All Registered Devices**

*For any* set of registered devices, the discovery endpoint should return a list containing all registered devices with their current status.

**Validates: Requirements 1.4**

**Property 5: Device Status Reflects Heartbeat Timeout**

*For any* device that fails to send a heartbeat within the configured timeout period (30 seconds), the device status should transition to offline and remain offline until a heartbeat is received.

**Validates: Requirements 2.2**

**Property 6: Offline Devices Cannot Receive Dispatches**

*For any* device marked as offline, attempting to create a dispatch command for that device should be rejected with a 400 Bad Request response.

**Validates: Requirements 2.4**

**Property 7: Device Configuration Updates Persist**

*For any* valid device configuration update, the updated configuration should be persisted to the database and retrievable via subsequent queries.

**Validates: Requirements 3.1, 3.3**

**Property 8: Invalid Device Configuration Is Rejected**

*For any* device configuration update with invalid parameters (e.g., power_limit exceeding device capability), the update should be rejected with a 400 Bad Request response.

**Validates: Requirements 3.2**

#### Dispatch Control Properties

**Property 9: Dispatch Creation Assigns Unique IDs**

*For any* two dispatch commands created in sequence, each should receive a unique dispatch_id and distinct timestamps.

**Validates: Requirements 4.3**

**Property 10: Dispatch Execution Persists Status**

*For any* dispatch command executed, the execution status (pending/executing/completed/failed) should be persisted to the database and retrievable via status queries.

**Validates: Requirements 4.6, 7.4**

**Property 11: Failed Dispatch Retries With Exponential Backoff**

*For any* dispatch command that fails on initial execution, the system should retry up to 3 times with exponential backoff (1s, 2s, 4s) before marking as failed.

**Validates: Requirements 4.5**

**Property 12: Scheduled Dispatch Executes at Specified Time**

*For any* dispatch scheduled for a future time, the dispatch should execute automatically at the specified time (within ±1 second tolerance).

**Validates: Requirements 5.1, 5.2**

**Property 13: Cancelled Scheduled Dispatch Does Not Execute**

*For any* scheduled dispatch that is cancelled before its execution time, the dispatch should not execute and should be removed from the schedule.

**Validates: Requirements 5.3**

**Property 14: Dispatch History Filtering Returns Correct Results**

*For any* set of dispatch records with different device_ids, time_ranges, and statuses, filtering by these criteria should return only matching records.

**Validates: Requirements 7.2**

**Property 15: Dispatch History Query Completes Within 1 Second**

*For any* dispatch history query issued on a database with 10,000+ dispatch records, the query should complete and return results within 1 second.

**Validates: Requirements 7.3**

#### Protocol Conversion Properties

**Property 16: IEC 104 Message Parsing Extracts All Data Elements**

*For any* valid IEC 104 message conforming to IEC 60870-5-104 standard, parsing should extract all data elements and convert them to the internal data model without loss of information.

**Validates: Requirements 8.1, 8.3**

**Property 17: Invalid IEC 104 Messages Are Rejected**

*For any* IEC 104 message with invalid structure (incorrect ASDU format, invalid length field), parsing should be rejected with a 400 Bad Request response containing specific parsing errors.

**Validates: Requirements 8.2**

**Property 18: IEC 104 Encoding Produces Valid Messages**

*For any* internal command converted to IEC 104 format, the resulting message should conform to the IEC 60870-5-104 standard and be parseable by a standard IEC 104 parser.

**Validates: Requirements 8.4**

**Property 19: Protocol Conversion Maintains Data Integrity**

*For any* message converted from IEC 104 to MQTT and back to IEC 104, the final message should contain equivalent data to the original message (round-trip property).

**Validates: Requirements 8.5, 9.5**

**Property 20: MQTT Message Parsing Extracts Payload**

*For any* valid MQTT message conforming to MQTT 3.1.1 specification, parsing should extract the payload and convert it to the internal data model.

**Validates: Requirements 9.1, 9.3**

**Property 21: Invalid MQTT Messages Are Rejected**

*For any* MQTT message with invalid structure (malformed topic, invalid QoS), parsing should be rejected with a 400 Bad Request response.

**Validates: Requirements 9.2**

**Property 22: MQTT Encoding Produces Valid Messages**

*For any* internal command converted to MQTT format, the resulting message should conform to MQTT 3.1.1 specification with appropriate QoS level.

**Validates: Requirements 9.4**

**Property 23: Protocol Validation Detects All Structural Errors**

*For any* protocol message with structural errors, validation should detect the error and return a 400 Bad Request response with specific error details.

**Validates: Requirements 10.1, 10.2**

**Property 24: Malformed Messages Do Not Crash System**

*For any* malformed protocol message, the system should not crash or enter an undefined state, but instead return an error response.

**Validates: Requirements 10.5**

#### Analysis Properties

**Property 25: Power Flow Analysis Completes Within 5 Seconds**

*For any* power flow analysis request with valid device parameters, the analysis should complete and return results within 5 seconds.

**Validates: Requirements 11.4**

**Property 26: Power Flow Analysis Results Persist**

*For any* power flow analysis executed, the results should be persisted to the database and retrievable via historical queries.

**Validates: Requirements 11.5**

**Property 27: Non-Convergent Analysis Returns Error**

*For any* power flow analysis that fails to converge, the system should return a 422 Unprocessable Entity response with convergence failure details.

**Validates: Requirements 11.3**

**Property 28: Stability Analysis Completes Within 10 Seconds**

*For any* stability analysis request, the analysis should complete and return results with risk level (low/medium/high) within 10 seconds.

**Validates: Requirements 12.1, 12.2, 12.4**

**Property 29: Metrics Calculation Completes Within 2 Seconds**

*For any* metrics query with time range filters, the system should return aggregated metrics within 2 seconds.

**Validates: Requirements 13.4**

**Property 30: Metrics Results Persist**

*For any* metrics calculation executed, the results should be persisted to the database and retrievable via historical queries.

**Validates: Requirements 13.3**

**Property 31: Report Generation Completes Within 30 Seconds**

*For any* report generation request with valid report type, the system should complete the report and return it in JSON format within 30 seconds.

**Validates: Requirements 14.1, 14.3, 14.4**

**Property 32: Report Results Persist**

*For any* report generated, the report should be persisted to the database and retrievable via historical queries.

**Validates: Requirements 14.5**

**Property 33: Core Dump Analysis Extracts Crash Information**

*For any* valid Core Dump file, analysis should extract crash information (crash address, call stack, register state) and generate a vulnerability report.

**Validates: Requirements 15.1, 15.2**

**Property 34: Invalid Core Dump Files Are Rejected**

*For any* invalid or corrupted Core Dump file, the system should return a 400 Bad Request response with specific error details.

**Validates: Requirements 15.4**

**Property 35: Core Dump Analysis Results Persist**

*For any* Core Dump analyzed, the analysis results should be persisted to the database and retrievable via historical queries.

**Validates: Requirements 15.5**

#### API Response and Error Handling Properties

**Property 36: Invalid JSON Requests Are Rejected**

*For any* API request containing invalid JSON, the system should return a 400 Bad Request response with error details.

**Validates: Requirements 17.1**

**Property 37: Missing Required Fields Are Detected**

*For any* API request missing required fields, the system should return a 400 Bad Request response with specific field validation errors.

**Validates: Requirements 17.2**

**Property 38: Invalid Data Types Are Detected**

*For any* API request containing invalid data types, the system should return a 400 Bad Request response with type validation errors.

**Validates: Requirements 17.3**

**Property 39: Internal Errors Include Unique Error IDs**

*For any* internal server error, the system should return a 500 response with a unique error ID for tracking.

**Validates: Requirements 17.5**

**Property 40: Error Responses Have Consistent Format**

*For any* API error response, the response should include error_code, error_message, and details in a consistent JSON structure.

**Validates: Requirements 17.6, 18.4**

**Property 41: Successful Responses Have Consistent Format**

*For any* successful API request, the response should include status code 200/201 and a consistent JSON structure with all relevant fields.

**Validates: Requirements 18.1, 18.3**

**Property 42: List Responses Include Pagination Metadata**

*For any* API request returning a list of items, the response should include pagination metadata (total_count, page, page_size).

**Validates: Requirements 18.2**

#### Authentication and Authorization Properties

**Property 43: Unauthenticated Requests Are Rejected**

*For any* API request issued without authentication credentials, the system should return a 401 Unauthorized response.

**Validates: Requirements 19.1**

**Property 44: Invalid Credentials Are Rejected**

*For any* API request issued with invalid credentials, the system should return a 401 Unauthorized response.

**Validates: Requirements 19.2**

**Property 45: Unauthorized Operations Are Rejected**

*For any* authenticated user attempting an operation they are not authorized for, the system should return a 403 Forbidden response.

**Validates: Requirements 19.3**

#### Monitoring and Observability Properties

**Property 46: API Metrics Are Recorded**

*For any* API request processed, Prometheus metrics should be recorded including request count, response time, and status code.

**Validates: Requirements 20.1**

**Property 47: Prometheus Metrics Are Properly Formatted**

*For any* Prometheus metrics query, the endpoint should return metrics in valid Prometheus text format.

**Validates: Requirements 20.2**

**Property 48: Request Logging Includes Required Fields**

*For any* API request processed, the log should include method, path, status code, and response time.

**Validates: Requirements 21.1**

**Property 49: Error Logging Includes Stack Traces**

*For any* API error, the log should include full context including stack trace and request details.

**Validates: Requirements 21.2**

**Property 50: Unique Request IDs Are Generated**

*For any* API request processed, a unique request ID should be generated and included in logs for tracing.

**Validates: Requirements 21.3**

#### Rate Limiting Properties

**Property 51: Rate Limit Exceeded Returns 429**

*For any* API client that exceeds the configured rate limit, the system should return a 429 Too Many Requests response.

**Validates: Requirements 22.1**

**Property 52: Rate Limit Headers Are Included**

*For any* API response, rate limit information should be included in response headers (X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset).

**Validates: Requirements 22.2**

#### Data Persistence Properties

**Property 53: Written Data Persists Durably**

*For any* data written to the database, the data should be persisted immediately and durably, retrievable via subsequent queries.

**Validates: Requirements 24.1**

**Property 54: Transaction Rollback Maintains Consistency**

*For any* database transaction that fails, all changes should be rolled back and data consistency should be maintained.

**Validates: Requirements 24.2**

**Property 55: Queries Return Most Recent Data**

*For any* data query, the system should return the most recent committed data, not stale or intermediate states.

**Validates: Requirements 24.3**

#### Performance and Scalability Properties

**Property 56: Device Queries Scale to 1000 Devices**

*For any* device query issued on a system with 1000 registered devices, the query should complete and return results within 500ms.

**Validates: Requirements 25.1**

**Property 57: High-Frequency Dispatch Commands Process Without Loss**

*For any* sequence of 100 dispatch commands issued per second, all commands should be processed and persisted without data loss.

**Validates: Requirements 25.2**

**Property 58: Status Query Completes Within 500ms**

*For any* status query for all devices issued on a system with 1000+ devices, the query should complete within 500ms.

**Validates: Requirements 2.5**

