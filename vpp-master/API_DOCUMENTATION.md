# VPP Master API Documentation

## Overview

The VPP Master API provides comprehensive documentation through multiple formats:

1. **OpenAPI 3.0 Specification** - Machine-readable API specification
2. **Swagger UI** - Interactive API documentation with try-it-out functionality
3. **ReDoc** - Alternative interactive documentation with clean design
4. **JSON Documentation** - Simple JSON endpoint listing

## Documentation Endpoints

### OpenAPI Specification
- **URL**: `/api/openapi.json`
- **Format**: JSON
- **Description**: Complete OpenAPI 3.0 specification for all endpoints
- **Use Case**: Integration with API clients, code generation, testing tools

### Swagger UI
- **URL**: `/api/docs`
- **Format**: Interactive HTML
- **Description**: Interactive API documentation with try-it-out functionality
- **Features**:
  - Browse all endpoints
  - View request/response schemas
  - Try endpoints directly from the browser
  - View authentication requirements
  - See error codes and responses

### ReDoc
- **URL**: `/api/redoc`
- **Format**: Interactive HTML
- **Description**: Alternative interactive documentation with clean design
- **Features**:
  - Clean, modern interface
  - Search functionality
  - Responsive design
  - Organized by tags

### JSON Documentation
- **URL**: `/docs`
- **Format**: JSON
- **Description**: Simple endpoint listing with links to documentation

## Quick Start

### Base URL
```
Development: http://localhost:8080
Production: https://api.vpp.example.com
```

### API Version
All endpoints use `/api/v1/` prefix for versioning.

## API Modules

### Device Management API
**Base Path**: `/api/v1/devices`

Endpoints for managing distributed energy resources (solar, wind, battery, load).

#### POST /api/v1/devices - Register a new device

Register a new distributed energy resource with the VPP system.

**Request:**
```json
{
  "id": "device-solar-001",
  "device_type": "solar",
  "location": "Building A - Rooftop",
  "capabilities": {
    "max_power": 10000,
    "min_power": 0,
    "ramp_rate": 500,
    "efficiency": 0.95
  },
  "configuration": {
    "power_limit": 8000,
    "mode": "auto",
    "priority_level": 5
  }
}
```

**Response (201 Created):**
```json
{
  "data": {
    "id": "device-solar-001",
    "device_type": "solar",
    "location": "Building A - Rooftop",
    "status": "online",
    "last_heartbeat": "2026-02-16T10:30:00Z",
    "capabilities": {
      "max_power": 10000,
      "min_power": 0,
      "ramp_rate": 500,
      "efficiency": 0.95
    },
    "configuration": {
      "power_limit": 8000,
      "mode": "auto",
      "priority_level": 5
    },
    "created_at": "2026-02-16T10:30:00Z",
    "updated_at": "2026-02-16T10:30:00Z"
  }
}
```

**Error Responses:**
- `400 Bad Request` - Missing required fields or invalid data
- `409 Conflict` - Device with this ID already exists

---

#### GET /api/v1/devices - List all devices

Retrieve all registered devices with pagination support.

**Query Parameters:**
- `page` (integer, default: 1) - Page number
- `page_size` (integer, default: 50) - Items per page (max: 100)

**Example Request:**
```bash
GET /api/v1/devices?page=1&page_size=50
```

**Response (200 OK):**
```json
{
  "data": [
    {
      "id": "device-solar-001",
      "device_type": "solar",
      "location": "Building A - Rooftop",
      "status": "online",
      "last_heartbeat": "2026-02-16T10:30:00Z",
      "capabilities": {
        "max_power": 10000,
        "min_power": 0
      },
      "created_at": "2026-02-16T10:30:00Z",
      "updated_at": "2026-02-16T10:30:00Z"
    },
    {
      "id": "device-wind-001",
      "device_type": "wind",
      "location": "Field B",
      "status": "online",
      "last_heartbeat": "2026-02-16T10:29:55Z",
      "capabilities": {
        "max_power": 50000,
        "min_power": 1000
      },
      "created_at": "2026-02-16T10:25:00Z",
      "updated_at": "2026-02-16T10:29:55Z"
    }
  ],
  "pagination": {
    "total_count": 150,
    "page": 1,
    "page_size": 50
  }
}
```

---

#### GET /api/v1/devices/{device_id} - Get device details

Retrieve detailed information about a specific device.

**Path Parameters:**
- `device_id` (string, required) - Unique device identifier

**Example Request:**
```bash
GET /api/v1/devices/device-solar-001
```

**Response (200 OK):**
```json
{
  "data": {
    "id": "device-solar-001",
    "device_type": "solar",
    "location": "Building A - Rooftop",
    "status": "online",
    "last_heartbeat": "2026-02-16T10:30:00Z",
    "capabilities": {
      "max_power": 10000,
      "min_power": 0,
      "ramp_rate": 500,
      "efficiency": 0.95
    },
    "configuration": {
      "power_limit": 8000,
      "mode": "auto",
      "priority_level": 5
    },
    "created_at": "2026-02-16T10:30:00Z",
    "updated_at": "2026-02-16T10:30:00Z"
  }
}
```

**Error Responses:**
- `404 Not Found` - Device does not exist

---

#### PUT /api/v1/devices/{device_id} - Update device configuration

Update device configuration parameters and operational limits.

**Path Parameters:**
- `device_id` (string, required) - Unique device identifier

**Request:**
```json
{
  "configuration": {
    "power_limit": 7500,
    "mode": "manual",
    "priority_level": 8
  }
}
```

**Response (200 OK):**
```json
{
  "data": {
    "id": "device-solar-001",
    "device_type": "solar",
    "location": "Building A - Rooftop",
    "status": "online",
    "configuration": {
      "power_limit": 7500,
      "mode": "manual",
      "priority_level": 8
    },
    "updated_at": "2026-02-16T10:35:00Z"
  }
}
```

**Error Responses:**
- `400 Bad Request` - Invalid configuration parameters
- `404 Not Found` - Device does not exist

---

#### DELETE /api/v1/devices/{device_id} - Deregister a device

Remove a device from the VPP system.

**Path Parameters:**
- `device_id` (string, required) - Unique device identifier

**Response (200 OK):**
```json
{
  "data": {
    "message": "Device deregistered successfully",
    "device_id": "device-solar-001"
  }
}
```

**Error Responses:**
- `404 Not Found` - Device does not exist

---

#### GET /api/v1/devices/{device_id}/status - Get device status

Retrieve the current status of a specific device.

**Path Parameters:**
- `device_id` (string, required) - Unique device identifier

**Response (200 OK):**
```json
{
  "data": {
    "device_id": "device-solar-001",
    "status": "online",
    "last_heartbeat": "2026-02-16T10:30:00Z",
    "heartbeat_timeout": 30,
    "is_responsive": true
  }
}
```

**Status Values:**
- `online` - Device is connected and responsive
- `offline` - Device has not sent heartbeat within timeout period
- `error` - Device reported an error condition

### Dispatch Control API
**Base Path**: `/api/v1/dispatch`

Endpoints for managing dispatch commands to control devices.

#### POST /api/v1/dispatch - Create and execute a dispatch command

Create and immediately execute a dispatch command to a device.

**Request:**
```json
{
  "device_id": "device-solar-001",
  "command_type": "power_adjustment",
  "target_value": 5000,
  "priority_level": 7
}
```

**Response (201 Created):**
```json
{
  "data": {
    "id": "dispatch-001",
    "device_id": "device-solar-001",
    "command_type": "power_adjustment",
    "target_value": 5000,
    "priority_level": 7,
    "status": "executing",
    "execution_time": "2026-02-16T10:30:05Z",
    "retry_count": 0,
    "created_at": "2026-02-16T10:30:00Z",
    "updated_at": "2026-02-16T10:30:05Z"
  }
}
```

**Error Responses:**
- `400 Bad Request` - Invalid parameters or device is offline
- `409 Conflict` - Device not found

---

#### GET /api/v1/dispatch/{dispatch_id} - Get dispatch details

Retrieve detailed information about a specific dispatch command.

**Path Parameters:**
- `dispatch_id` (string, required) - Unique dispatch identifier

**Response (200 OK):**
```json
{
  "data": {
    "id": "dispatch-001",
    "device_id": "device-solar-001",
    "command_type": "power_adjustment",
    "target_value": 5000,
    "priority_level": 7,
    "status": "completed",
    "execution_time": "2026-02-16T10:30:05Z",
    "retry_count": 0,
    "error_message": null,
    "created_at": "2026-02-16T10:30:00Z",
    "updated_at": "2026-02-16T10:30:10Z"
  }
}
```

---

#### GET /api/v1/dispatch/{dispatch_id}/status - Get dispatch status

Retrieve the current status of a dispatch command.

**Path Parameters:**
- `dispatch_id` (string, required) - Unique dispatch identifier

**Response (200 OK):**
```json
{
  "data": {
    "dispatch_id": "dispatch-001",
    "status": "completed",
    "execution_time": "2026-02-16T10:30:05Z",
    "retry_count": 0,
    "error_message": null
  }
}
```

**Status Values:**
- `pending` - Dispatch created but not yet executed
- `executing` - Dispatch is currently being executed
- `completed` - Dispatch executed successfully
- `failed` - Dispatch execution failed after all retries

---

#### GET /api/v1/dispatch/history - Get dispatch history

Retrieve dispatch history with optional filtering.

**Query Parameters:**
- `device_id` (string, optional) - Filter by device ID
- `status` (string, optional) - Filter by status (pending, executing, completed, failed)
- `start_time` (string, optional) - ISO 8601 timestamp for start of time range
- `end_time` (string, optional) - ISO 8601 timestamp for end of time range
- `page` (integer, default: 1) - Page number
- `page_size` (integer, default: 50) - Items per page (max: 100)

**Example Request:**
```bash
GET /api/v1/dispatch/history?device_id=device-solar-001&status=completed&page=1&page_size=50
```

**Response (200 OK):**
```json
{
  "data": [
    {
      "id": "dispatch-001",
      "device_id": "device-solar-001",
      "command_type": "power_adjustment",
      "target_value": 5000,
      "status": "completed",
      "execution_time": "2026-02-16T10:30:05Z",
      "created_at": "2026-02-16T10:30:00Z"
    },
    {
      "id": "dispatch-002",
      "device_id": "device-solar-001",
      "command_type": "mode_change",
      "target_value": 1,
      "status": "completed",
      "execution_time": "2026-02-16T10:25:05Z",
      "created_at": "2026-02-16T10:25:00Z"
    }
  ],
  "pagination": {
    "total_count": 250,
    "page": 1,
    "page_size": 50
  }
}
```

**Performance:** Query completes within 1 second for databases with 10,000+ records.

---

#### POST /api/v1/dispatch/{dispatch_id}/cancel - Cancel a dispatch

Cancel a scheduled or pending dispatch command.

**Path Parameters:**
- `dispatch_id` (string, required) - Unique dispatch identifier

**Response (200 OK):**
```json
{
  "data": {
    "message": "Dispatch cancelled successfully",
    "dispatch_id": "dispatch-001",
    "previous_status": "pending"
  }
}
```

**Error Responses:**
- `400 Bad Request` - Cannot cancel a dispatch that is already executing or completed
- `404 Not Found` - Dispatch does not exist

---

#### POST /api/v1/dispatch/schedule - Schedule a future dispatch

Schedule a dispatch command for execution at a specified future time.

**Request:**
```json
{
  "device_id": "device-battery-001",
  "command_type": "charge",
  "target_value": 8000,
  "priority_level": 5,
  "scheduled_time": "2026-02-16T15:00:00Z"
}
```

**Response (201 Created):**
```json
{
  "data": {
    "id": "dispatch-scheduled-001",
    "device_id": "device-battery-001",
    "command_type": "charge",
    "target_value": 8000,
    "priority_level": 5,
    "status": "pending",
    "scheduled_time": "2026-02-16T15:00:00Z",
    "created_at": "2026-02-16T10:30:00Z"
  }
}
```

**Error Responses:**
- `400 Bad Request` - Invalid scheduled time (must be in future)
- `409 Conflict` - Device not found

---

#### GET /api/v1/dispatch/scheduled - List scheduled dispatches

Retrieve all scheduled dispatches that have not yet executed.

**Query Parameters:**
- `page` (integer, default: 1) - Page number
- `page_size` (integer, default: 50) - Items per page

**Response (200 OK):**
```json
{
  "data": [
    {
      "id": "dispatch-scheduled-001",
      "device_id": "device-battery-001",
      "command_type": "charge",
      "target_value": 8000,
      "status": "pending",
      "scheduled_time": "2026-02-16T15:00:00Z",
      "created_at": "2026-02-16T10:30:00Z"
    }
  ],
  "pagination": {
    "total_count": 5,
    "page": 1,
    "page_size": 50
  }
}
```

### Protocol Conversion API
**Base Path**: `/api/v1/protocol`

Endpoints for protocol conversion and management.

#### POST /api/v1/protocol/parse - Parse a protocol message

Parse a protocol message and extract data elements.

**Request:**
```json
{
  "protocol": "IEC104",
  "data": "base64-encoded-message-data"
}
```

**Response (200 OK):**
```json
{
  "data": {
    "protocol": "IEC104",
    "parsed_data": {
      "asdu_type": 1,
      "cause_of_transmission": 3,
      "originator_address": 0,
      "information_objects": [
        {
          "ioa": 1,
          "value": 100.5,
          "quality": "good",
          "timestamp": "2026-02-16T10:30:00Z"
        }
      ]
    }
  }
}
```

**Error Responses:**
- `400 Bad Request` - Invalid message structure or unsupported protocol
- `422 Unprocessable Entity` - Message contains unsupported data types

---

#### POST /api/v1/protocol/encode - Encode data to protocol format

Encode internal data model to a specific protocol format.

**Request:**
```json
{
  "protocol": "MQTT",
  "data": {
    "device_id": "device-001",
    "power": 5000,
    "status": "online"
  },
  "qos": 1
}
```

**Response (200 OK):**
```json
{
  "data": {
    "protocol": "MQTT",
    "encoded_data": "base64-encoded-message",
    "topic": "vpp/device-001/status",
    "qos": 1
  }
}
```

**Error Responses:**
- `400 Bad Request` - Invalid data or unsupported protocol
- `422 Unprocessable Entity` - Data cannot be encoded to target protocol

---

#### POST /api/v1/protocol/convert - Convert between protocols

Convert a message from one protocol format to another.

**Request:**
```json
{
  "source_protocol": "IEC104",
  "target_protocol": "MQTT",
  "data": "base64-encoded-source-message"
}
```

**Response (200 OK):**
```json
{
  "data": {
    "source_protocol": "IEC104",
    "target_protocol": "MQTT",
    "converted_data": "base64-encoded-target-message",
    "data_integrity": "verified"
  }
}
```

**Error Responses:**
- `400 Bad Request` - Invalid source message or unsupported protocol pair
- `422 Unprocessable Entity` - Conversion not possible due to data incompatibility

---

#### GET /api/v1/protocol/mappings - Get protocol mappings

Retrieve protocol mapping configurations.

**Query Parameters:**
- `source_protocol` (string, optional) - Filter by source protocol
- `target_protocol` (string, optional) - Filter by target protocol
- `page` (integer, default: 1) - Page number
- `page_size` (integer, default: 50) - Items per page

**Response (200 OK):**
```json
{
  "data": [
    {
      "id": "mapping-001",
      "source_protocol": "IEC104",
      "target_protocol": "MQTT",
      "mapping_rules": {
        "asdu_type_1": "power_measurement",
        "asdu_type_3": "command"
      },
      "is_active": true,
      "created_at": "2026-02-16T10:00:00Z"
    }
  ],
  "pagination": {
    "total_count": 10,
    "page": 1,
    "page_size": 50
  }
}
```

---

#### POST /api/v1/protocol/mappings - Create a protocol mapping

Create a new protocol mapping configuration.

**Request:**
```json
{
  "source_protocol": "IEC104",
  "target_protocol": "MQTT",
  "mapping_rules": {
    "asdu_type_1": "power_measurement",
    "asdu_type_3": "command",
    "asdu_type_5": "setpoint"
  }
}
```

**Response (201 Created):**
```json
{
  "data": {
    "id": "mapping-002",
    "source_protocol": "IEC104",
    "target_protocol": "MQTT",
    "mapping_rules": {
      "asdu_type_1": "power_measurement",
      "asdu_type_3": "command",
      "asdu_type_5": "setpoint"
    },
    "is_active": true,
    "created_at": "2026-02-16T10:30:00Z"
  }
}
```

**Error Responses:**
- `400 Bad Request` - Invalid mapping configuration
- `409 Conflict` - Mapping already exists

---

#### PUT /api/v1/protocol/mappings/{mapping_id} - Update a protocol mapping

Update an existing protocol mapping configuration.

**Path Parameters:**
- `mapping_id` (string, required) - Unique mapping identifier

**Request:**
```json
{
  "mapping_rules": {
    "asdu_type_1": "power_measurement",
    "asdu_type_3": "command",
    "asdu_type_5": "setpoint",
    "asdu_type_7": "quality_descriptor"
  },
  "is_active": true
}
```

**Response (200 OK):**
```json
{
  "data": {
    "id": "mapping-002",
    "source_protocol": "IEC104",
    "target_protocol": "MQTT",
    "mapping_rules": {
      "asdu_type_1": "power_measurement",
      "asdu_type_3": "command",
      "asdu_type_5": "setpoint",
      "asdu_type_7": "quality_descriptor"
    },
    "is_active": true,
    "updated_at": "2026-02-16T10:35:00Z"
  }
}
```

---

#### DELETE /api/v1/protocol/mappings/{mapping_id} - Delete a protocol mapping

Delete a protocol mapping configuration.

**Path Parameters:**
- `mapping_id` (string, required) - Unique mapping identifier

**Response (200 OK):**
```json
{
  "data": {
    "message": "Mapping deleted successfully",
    "mapping_id": "mapping-002"
  }
}
```

**Error Responses:**
- `404 Not Found` - Mapping does not exist

### Analysis API
**Base Path**: `/api/v1/analysis`

Endpoints for power system analysis and reporting.

#### POST /api/v1/analysis/power-flow - Execute power flow analysis

Execute a power flow analysis on the current system state.

**Request:**
```json
{
  "system_state": {
    "buses": [
      {
        "bus_id": 1,
        "voltage_magnitude": 1.0,
        "voltage_angle": 0.0,
        "bus_type": "slack"
      }
    ],
    "generators": [
      {
        "gen_id": 1,
        "bus": 1,
        "p_gen": 100,
        "q_gen": 0
      }
    ],
    "loads": [
      {
        "load_id": 1,
        "bus": 2,
        "p_load": 50,
        "q_load": 10
      }
    ]
  }
}
```

**Response (200 OK):**
```json
{
  "data": {
    "analysis_type": "power_flow",
    "status": "completed",
    "convergence": true,
    "iterations": 3,
    "execution_time_ms": 245,
    "results": {
      "bus_voltages": [
        {
          "bus_id": 1,
          "voltage_magnitude": 1.0,
          "voltage_angle": 0.0
        }
      ],
      "line_flows": [
        {
          "from_bus": 1,
          "to_bus": 2,
          "power_flow": 50.5,
          "loss": 0.5
        }
      ],
      "total_loss": 0.5
    },
    "created_at": "2026-02-16T10:30:00Z"
  }
}
```

**Performance:** Completes within 5 seconds for typical systems.

**Error Responses:**
- `400 Bad Request` - Invalid system state
- `422 Unprocessable Entity` - Analysis failed to converge

---

#### POST /api/v1/analysis/stability - Execute stability analysis

Assess system stability and identify potential risks.

**Request:**
```json
{
  "system_state": {
    "frequency": 50.0,
    "frequency_deviation": 0.05,
    "voltage_stability_margin": 0.15,
    "transient_stability_margin": 0.25
  }
}
```

**Response (200 OK):**
```json
{
  "data": {
    "analysis_type": "stability",
    "status": "completed",
    "execution_time_ms": 1250,
    "risk_level": "low",
    "metrics": {
      "frequency_deviation": 0.05,
      "voltage_stability_margin": 0.15,
      "transient_stability_margin": 0.25,
      "damping_ratio": 0.45
    },
    "recommendations": [
      "System is stable with good margins",
      "Monitor frequency deviation during peak load"
    ],
    "created_at": "2026-02-16T10:30:00Z"
  }
}
```

**Risk Levels:**
- `low` - System is stable with adequate margins
- `medium` - System has reduced margins, monitor closely
- `high` - System is at risk, immediate action recommended

**Performance:** Completes within 10 seconds.

---

#### GET /api/v1/analysis/metrics - Get performance metrics

Retrieve aggregated performance metrics for the system.

**Query Parameters:**
- `time_range` (string, optional) - Time range: "1h", "24h", "7d", "30d" (default: "24h")
- `aggregation` (string, optional) - Aggregation level: "hourly", "daily", "monthly" (default: "hourly")
- `metric_type` (string, optional) - Filter by metric type: "efficiency", "response_time", "dispatch_success"

**Example Request:**
```bash
GET /api/v1/analysis/metrics?time_range=24h&aggregation=hourly&metric_type=efficiency
```

**Response (200 OK):**
```json
{
  "data": {
    "time_range": "24h",
    "aggregation": "hourly",
    "metrics": [
      {
        "timestamp": "2026-02-16T10:00:00Z",
        "efficiency": 0.94,
        "response_time_ms": 125,
        "dispatch_success_rate": 0.98,
        "device_count": 150,
        "online_device_count": 148
      }
    ]
  }
}
```

**Performance:** Completes within 2 seconds.

---

#### POST /api/v1/analysis/report - Generate a report

Generate a comprehensive analysis report.

**Request:**
```json
{
  "report_type": "performance",
  "time_range": "7d",
  "include_recommendations": true,
  "export_format": "json"
}
```

**Response (200 OK):**
```json
{
  "data": {
    "report_id": "report-001",
    "report_type": "performance",
    "time_range": "7d",
    "generated_at": "2026-02-16T10:30:00Z",
    "summary": {
      "total_devices": 150,
      "average_efficiency": 0.93,
      "total_dispatches": 1250,
      "successful_dispatches": 1225,
      "failed_dispatches": 25
    },
    "recommendations": [
      "Optimize device scheduling during peak hours",
      "Investigate 2 devices with low efficiency"
    ],
    "export_url": "/api/v1/analysis/report/report-001/export"
  }
}
```

**Report Types:**
- `performance` - System performance metrics and trends
- `vulnerability` - Security and vulnerability findings
- `analysis` - Detailed power system analysis

**Performance:** Completes within 30 seconds.

---

#### POST /api/v1/analysis/core-dump/upload - Upload Core Dump file

Upload a Core Dump file for analysis.

**Request:**
- Content-Type: `multipart/form-data`
- Field: `file` - Core Dump file (binary)

**Response (201 Created):**
```json
{
  "data": {
    "dump_id": "dump-001",
    "filename": "core.dump",
    "file_size": 1048576,
    "upload_time": "2026-02-16T10:30:00Z",
    "analysis_status": "processing"
  }
}
```

**Error Responses:**
- `400 Bad Request` - Invalid or corrupted Core Dump file
- `413 Payload Too Large` - File exceeds maximum size (100MB)

---

#### GET /api/v1/analysis/core-dump/{dump_id} - Get Core Dump analysis

Retrieve analysis results for an uploaded Core Dump.

**Path Parameters:**
- `dump_id` (string, required) - Unique Core Dump identifier

**Response (200 OK):**
```json
{
  "data": {
    "dump_id": "dump-001",
    "analysis_status": "completed",
    "crash_info": {
      "crash_address": "0x7f1234567890",
      "signal": "SIGSEGV",
      "crash_reason": "Segmentation fault"
    },
    "call_stack": [
      "protocol_handler() at protocol.c:123",
      "message_parser() at parser.c:456",
      "main() at main.c:789"
    ],
    "register_state": {
      "rax": "0x0000000000000000",
      "rbx": "0x00007f1234567890"
    },
    "vulnerability_findings": [
      {
        "type": "buffer_overflow",
        "severity": "high",
        "description": "Buffer overflow in message parsing"
      }
    ],
    "created_at": "2026-02-16T10:30:00Z"
  }
}
```

**Error Responses:**
- `404 Not Found` - Core Dump not found
- `202 Accepted` - Analysis still in progress

---

#### GET /api/v1/analysis/vulnerability-report - Get vulnerability report

Retrieve a comprehensive vulnerability report.

**Query Parameters:**
- `severity` (string, optional) - Filter by severity: "low", "medium", "high", "critical"
- `time_range` (string, optional) - Time range for report (default: "30d")

**Response (200 OK):**
```json
{
  "data": {
    "report_id": "vuln-report-001",
    "generated_at": "2026-02-16T10:30:00Z",
    "time_range": "30d",
    "summary": {
      "total_vulnerabilities": 5,
      "critical": 1,
      "high": 2,
      "medium": 2,
      "low": 0
    },
    "vulnerabilities": [
      {
        "id": "vuln-001",
        "type": "buffer_overflow",
        "severity": "critical",
        "affected_component": "IEC104 Parser",
        "description": "Buffer overflow in ASDU parsing",
        "remediation": "Update to version 2.1.0"
      }
    ]
  }
}
```

## Authentication

The API supports two authentication methods:

### API Key Authentication
- **Header**: `X-API-Key`
- **Usage**: Include the API key in the request header
- **Scope**: Service-to-service communication
- **Example**:
  ```bash
  curl -H "X-API-Key: your-api-key" http://localhost:8080/api/v1/devices
  ```

**API Key Format:**
- 32-character alphanumeric string
- Generated during service registration
- Can be rotated without service restart

### JWT Token Authentication
- **Header**: `Authorization: Bearer <token>`
- **Usage**: Include the JWT token in the Authorization header
- **Scope**: User authentication and authorization
- **Token Expiration**: 24 hours (configurable)
- **Example**:
  ```bash
  curl -H "Authorization: Bearer your-jwt-token" http://localhost:8080/api/v1/devices
  ```

**JWT Token Structure:**
```json
{
  "sub": "user-123",
  "iat": 1645000000,
  "exp": 1645086400,
  "roles": ["admin", "operator"],
  "permissions": ["read:devices", "write:dispatch"]
}
```

### Authorization Roles

| Role | Permissions |
|------|-------------|
| `admin` | Full access to all endpoints |
| `operator` | Read/write access to devices and dispatch |
| `analyst` | Read-only access to analysis endpoints |
| `viewer` | Read-only access to all endpoints |

### Authentication Examples

**Using API Key:**
```bash
curl -X GET http://localhost:8080/api/v1/devices \
  -H "X-API-Key: abc123def456ghi789jkl012mno345pqr"
```

**Using JWT Token:**
```bash
curl -X GET http://localhost:8080/api/v1/devices \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Missing Authentication:**
```bash
curl -X GET http://localhost:8080/api/v1/devices
# Response: 401 Unauthorized
```

**Invalid Credentials:**
```bash
curl -X GET http://localhost:8080/api/v1/devices \
  -H "X-API-Key: invalid-key"
# Response: 401 Unauthorized
```

**Insufficient Permissions:**
```bash
curl -X POST http://localhost:8080/api/v1/dispatch \
  -H "Authorization: Bearer viewer-token"
# Response: 403 Forbidden
```

## Error Handling

All error responses follow a consistent format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      "field": "Additional error details"
    },
    "request_id": "unique-request-id-for-tracking"
  }
}
```

### Error Response Examples

**Validation Error (400):**
```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "Request validation failed",
    "details": {
      "device_id": "Field is required",
      "device_type": "Must be one of: solar, wind, battery, load"
    },
    "request_id": "req-abc123def456"
  }
}
```

**Authentication Error (401):**
```json
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Authentication required",
    "details": {
      "reason": "Missing or invalid API key"
    },
    "request_id": "req-xyz789uvw012"
  }
}
```

**Authorization Error (403):**
```json
{
  "error": {
    "code": "FORBIDDEN",
    "message": "Insufficient permissions",
    "details": {
      "required_role": "admin",
      "user_role": "viewer"
    },
    "request_id": "req-def456ghi789"
  }
}
```

**Not Found Error (404):**
```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "Device not found",
    "details": {
      "device_id": "device-unknown-001"
    },
    "request_id": "req-jkl012mno345"
  }
}
```

**Conflict Error (409):**
```json
{
  "error": {
    "code": "CONFLICT",
    "message": "Device already exists",
    "details": {
      "device_id": "device-solar-001",
      "existing_since": "2026-02-16T10:00:00Z"
    },
    "request_id": "req-pqr678stu901"
  }
}
```

**Unprocessable Entity (422):**
```json
{
  "error": {
    "code": "UNPROCESSABLE_ENTITY",
    "message": "Power flow analysis failed to converge",
    "details": {
      "reason": "Infeasible power flow solution",
      "iterations": 100,
      "max_iterations": 100
    },
    "request_id": "req-vwx234yza567"
  }
}
```

**Rate Limit Error (429):**
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests",
    "details": {
      "limit": 1000,
      "window": "1 hour",
      "reset_at": "2026-02-16T11:30:00Z"
    },
    "request_id": "req-bcd890efg123"
  }
}
```

**Internal Server Error (500):**
```json
{
  "error": {
    "code": "INTERNAL_ERROR",
    "message": "Internal server error",
    "details": {
      "error_id": "err-2026021610300001",
      "timestamp": "2026-02-16T10:30:00Z"
    },
    "request_id": "req-hij456klm789"
  }
}
```

### Common Error Codes

| Code | HTTP Status | Description | Typical Cause |
|------|-------------|-------------|---------------|
| INVALID_REQUEST | 400 | Request validation failed | Missing/invalid fields, wrong data types |
| INVALID_JSON | 400 | Request body is not valid JSON | Malformed JSON in request body |
| UNAUTHORIZED | 401 | Authentication required | Missing or invalid credentials |
| FORBIDDEN | 403 | Authorization failed | Insufficient permissions for operation |
| NOT_FOUND | 404 | Resource not found | Device/dispatch/resource doesn't exist |
| CONFLICT | 409 | Resource conflict | Duplicate ID, resource already exists |
| UNPROCESSABLE_ENTITY | 422 | Request data cannot be processed | Analysis convergence failure, incompatible data |
| RATE_LIMIT_EXCEEDED | 429 | Rate limit exceeded | Too many requests in time window |
| INTERNAL_ERROR | 500 | Internal server error | Unexpected server error |
| SERVICE_UNAVAILABLE | 503 | Service temporarily unavailable | Database connection lost, service maintenance |

### Error Handling Best Practices

1. **Always check the request_id** - Use it for support and debugging
2. **Implement exponential backoff** - For 429 and 503 errors
3. **Log error details** - Include error code, message, and request_id
4. **Handle specific error codes** - Don't just check HTTP status
5. **Retry transient errors** - 429, 503, and some 500 errors
6. **Don't retry client errors** - 400, 401, 403, 404 errors indicate client issues

## Response Format

### Successful Response (Single Item)
```json
{
  "data": {
    "id": "device-123",
    "device_type": "solar",
    "status": "online",
    "created_at": "2026-02-16T10:30:00Z"
  }
}
```

### List Response with Pagination
```json
{
  "data": [
    {
      "id": "device-1",
      "device_type": "solar",
      "status": "online"
    },
    {
      "id": "device-2",
      "device_type": "wind",
      "status": "online"
    }
  ],
  "pagination": {
    "total_count": 100,
    "page": 1,
    "page_size": 50,
    "total_pages": 2
  }
}
```

### Response Headers

All successful responses include standard headers:

```
Content-Type: application/json
X-Request-ID: req-abc123def456
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1645086400
```

### Response Status Codes

| Status | Meaning | Use Case |
|--------|---------|----------|
| 200 | OK | Successful GET, PUT, DELETE |
| 201 | Created | Successful POST (resource created) |
| 202 | Accepted | Request accepted for processing (async) |
| 400 | Bad Request | Invalid request parameters |
| 401 | Unauthorized | Authentication required |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 409 | Conflict | Resource conflict |
| 422 | Unprocessable Entity | Request cannot be processed |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |
| 503 | Service Unavailable | Service temporarily unavailable |

## Rate Limiting

The API implements rate limiting to prevent abuse and ensure fair resource allocation:

### Rate Limit Tiers

| Tier | Per-User Limit | Per-Endpoint Limit | Burst Allowance |
|------|----------------|-------------------|-----------------|
| Standard | 1000 requests/hour | 100 requests/minute | 10 requests/second |
| Premium | 5000 requests/hour | 500 requests/minute | 50 requests/second |
| Enterprise | Unlimited | Unlimited | Unlimited |

### Rate Limit Headers

All responses include rate limit information in headers:

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1645086400
```

**Header Meanings:**
- `X-RateLimit-Limit` - Maximum requests allowed in the current window
- `X-RateLimit-Remaining` - Number of requests remaining in the current window
- `X-RateLimit-Reset` - Unix timestamp when the rate limit window resets

### Rate Limit Exceeded Response

When rate limit is exceeded, the API returns a 429 response:

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many requests",
    "details": {
      "limit": 1000,
      "window": "1 hour",
      "reset_at": "2026-02-16T11:30:00Z",
      "retry_after": 3600
    },
    "request_id": "req-abc123def456"
  }
}
```

### Rate Limiting Strategy

**Recommended approach for clients:**

1. **Check remaining requests** - Monitor `X-RateLimit-Remaining` header
2. **Implement exponential backoff** - When receiving 429 responses
3. **Use Retry-After header** - Wait the specified time before retrying
4. **Batch requests** - Combine multiple operations when possible
5. **Cache responses** - Reduce redundant API calls

**Example retry logic:**
```python
import time
import requests

def make_request_with_retry(url, max_retries=3):
    for attempt in range(max_retries):
        response = requests.get(url)
        
        if response.status_code == 429:
            retry_after = int(response.headers.get('Retry-After', 60))
            print(f"Rate limited. Waiting {retry_after} seconds...")
            time.sleep(retry_after)
            continue
        
        return response
    
    raise Exception("Max retries exceeded")
```

## Monitoring and Observability

### Metrics Endpoint
- **URL**: `/metrics`
- **Format**: Prometheus text format
- **Description**: System metrics for monitoring

### Health Check
- **URL**: `/health`
- **Format**: JSON
- **Description**: System health status

## Example Usage

### Register a Device
```bash
curl -X POST http://localhost:8080/api/v1/devices \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "id": "device-solar-001",
    "device_type": "solar",
    "location": "Building A - Rooftop",
    "capabilities": {
      "max_power": 10000,
      "min_power": 0,
      "efficiency": 0.95
    },
    "configuration": {
      "power_limit": 8000,
      "mode": "auto"
    }
  }'
```

### List All Devices
```bash
curl -X GET "http://localhost:8080/api/v1/devices?page=1&page_size=50" \
  -H "X-API-Key: your-api-key"
```

### Get Device Status
```bash
curl -X GET http://localhost:8080/api/v1/devices/device-solar-001/status \
  -H "X-API-Key: your-api-key"
```

### Update Device Configuration
```bash
curl -X PUT http://localhost:8080/api/v1/devices/device-solar-001 \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "configuration": {
      "power_limit": 7500,
      "mode": "manual",
      "priority_level": 8
    }
  }'
```

### Create a Dispatch Command
```bash
curl -X POST http://localhost:8080/api/v1/dispatch \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "device_id": "device-solar-001",
    "command_type": "power_adjustment",
    "target_value": 5000,
    "priority_level": 5
  }'
```

### Get Dispatch Status
```bash
curl -X GET http://localhost:8080/api/v1/dispatch/dispatch-001/status \
  -H "X-API-Key: your-api-key"
```

### Get Dispatch History
```bash
curl -X GET "http://localhost:8080/api/v1/dispatch/history?device_id=device-solar-001&status=completed&page=1" \
  -H "X-API-Key: your-api-key"
```

### Schedule a Future Dispatch
```bash
curl -X POST http://localhost:8080/api/v1/dispatch/schedule \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "device_id": "device-battery-001",
    "command_type": "charge",
    "target_value": 8000,
    "priority_level": 5,
    "scheduled_time": "2026-02-16T15:00:00Z"
  }'
```

### Parse a Protocol Message
```bash
curl -X POST http://localhost:8080/api/v1/protocol/parse \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "protocol": "IEC104",
    "data": "base64-encoded-message"
  }'
```

### Execute Power Flow Analysis
```bash
curl -X POST http://localhost:8080/api/v1/analysis/power-flow \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "system_state": {
      "buses": [...],
      "generators": [...],
      "loads": [...]
    }
  }'
```

### Get Performance Metrics
```bash
curl -X GET "http://localhost:8080/api/v1/analysis/metrics?time_range=24h&aggregation=hourly" \
  -H "X-API-Key: your-api-key"
```

### Generate a Report
```bash
curl -X POST http://localhost:8080/api/v1/analysis/report \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "report_type": "performance",
    "time_range": "7d",
    "include_recommendations": true,
    "export_format": "json"
  }'
```

### Upload Core Dump File
```bash
curl -X POST http://localhost:8080/api/v1/analysis/core-dump/upload \
  -H "X-API-Key: your-api-key" \
  -F "file=@/path/to/core.dump"
```

### Using JWT Token Authentication
```bash
curl -X GET http://localhost:8080/api/v1/devices \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

## Integration with Tools

### Postman
1. Import the OpenAPI specification from `/api/openapi.json`
2. Create a new collection from the specification
3. Configure authentication with your API key:
   - Go to Collection → Edit → Authorization
   - Select "API Key" type
   - Key: `X-API-Key`
   - Value: Your API key
4. Start testing endpoints

**Import Steps:**
- File → Import → URL
- Enter: `http://localhost:8080/api/openapi.json`
- Click Import

### Insomnia
1. Create a new request collection
2. Import OpenAPI spec: File → Import → From URL
3. Enter: `http://localhost:8080/api/openapi.json`
4. Configure environment variables for authentication
5. Run requests and view responses

### Code Generation

Use OpenAPI Generator to generate client libraries:

**Python Client:**
```bash
openapi-generator-cli generate \
  -i http://localhost:8080/api/openapi.json \
  -g python \
  -o ./generated-client \
  --package-name vpp_client
```

**JavaScript/TypeScript Client:**
```bash
openapi-generator-cli generate \
  -i http://localhost:8080/api/openapi.json \
  -g typescript-axios \
  -o ./generated-client
```

**Go Client:**
```bash
openapi-generator-cli generate \
  -i http://localhost:8080/api/openapi.json \
  -g go \
  -o ./generated-client
```

### API Testing with curl

**Test device registration:**
```bash
curl -X POST http://localhost:8080/api/v1/devices \
  -H "Content-Type: application/json" \
  -H "X-API-Key: test-key" \
  -d '{"id":"test-1","device_type":"solar","location":"Test","capabilities":{}}'
```

**Test with verbose output:**
```bash
curl -v -X GET http://localhost:8080/api/v1/devices \
  -H "X-API-Key: test-key"
```

**Test with response headers:**
```bash
curl -i -X GET http://localhost:8080/api/v1/devices \
  -H "X-API-Key: test-key"
```

### Python Client Example

```python
import requests
import json

BASE_URL = "http://localhost:8080/api/v1"
API_KEY = "your-api-key"

headers = {
    "Content-Type": "application/json",
    "X-API-Key": API_KEY
}

# Register a device
device_data = {
    "id": "device-001",
    "device_type": "solar",
    "location": "Building A",
    "capabilities": {"max_power": 10000}
}

response = requests.post(
    f"{BASE_URL}/devices",
    json=device_data,
    headers=headers
)

if response.status_code == 201:
    device = response.json()["data"]
    print(f"Device registered: {device['id']}")
else:
    error = response.json()["error"]
    print(f"Error: {error['message']}")

# List devices
response = requests.get(
    f"{BASE_URL}/devices",
    headers=headers
)

devices = response.json()["data"]
print(f"Total devices: {len(devices)}")
```

### JavaScript/TypeScript Client Example

```typescript
const BASE_URL = "http://localhost:8080/api/v1";
const API_KEY = "your-api-key";

async function registerDevice(deviceData: any) {
  const response = await fetch(`${BASE_URL}/devices`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-API-Key": API_KEY
    },
    body: JSON.stringify(deviceData)
  });

  if (response.status === 201) {
    const result = await response.json();
    console.log(`Device registered: ${result.data.id}`);
    return result.data;
  } else {
    const error = await response.json();
    console.error(`Error: ${error.error.message}`);
    throw error;
  }
}

// Usage
registerDevice({
  id: "device-001",
  device_type: "solar",
  location: "Building A",
  capabilities: { max_power: 10000 }
});
```

## Documentation Maintenance

The OpenAPI specification is maintained in `utils/openapi_spec.py` and includes:

- All endpoint definitions with request/response schemas
- Error codes and responses
- Authentication requirements
- Example requests and responses
- Rate limiting information

### Adding New Endpoints

When adding new endpoints, follow these steps:

1. **Update OpenAPI Spec** (`utils/openapi_spec.py`):
   ```python
   "paths": {
       "/api/v1/new-endpoint": {
           "post": {
               "summary": "Endpoint description",
               "tags": ["Category"],
               "requestBody": {...},
               "responses": {...}
           }
       }
   }
   ```

2. **Implement Route** (in appropriate `routes/*.py` file):
   ```python
   @app.post('/api/v1/new-endpoint')
   def new_endpoint():
       # Implementation
       pass
   ```

3. **Add Tests** (in `tests/` directory):
   - Unit tests for the endpoint
   - Integration tests with other components
   - Error case tests

4. **Update This Documentation**:
   - Add endpoint section with examples
   - Document request/response formats
   - Document error codes
   - Add curl examples

5. **Test Documentation**:
   - Verify Swagger UI displays correctly
   - Test examples in curl
   - Verify error responses

### Documentation Best Practices

1. **Keep examples current** - Update when API changes
2. **Include error cases** - Show what happens when things go wrong
3. **Use realistic data** - Examples should reflect actual usage
4. **Document all fields** - Every request/response field should be explained
5. **Include performance notes** - Document response time expectations
6. **Version your API** - Use `/api/v1/` prefix for versioning
7. **Maintain backward compatibility** - Don't break existing clients

### Generating Documentation

The API documentation is automatically generated from the OpenAPI spec:

```bash
# View Swagger UI
http://localhost:8080/api/docs

# View ReDoc
http://localhost:8080/api/redoc

# Download OpenAPI spec
http://localhost:8080/api/openapi.json
```

### Documentation Validation

Validate the OpenAPI specification:

```bash
# Using swagger-cli
swagger-cli validate http://localhost:8080/api/openapi.json

# Using openapi-generator
openapi-generator-cli validate -i http://localhost:8080/api/openapi.json
```

## Accessing Documentation

### Local Development

Access documentation at these URLs:

- **Swagger UI**: http://localhost:8080/api/docs
- **ReDoc**: http://localhost:8080/api/redoc
- **OpenAPI Spec**: http://localhost:8080/api/openapi.json
- **JSON Docs**: http://localhost:8080/docs
- **Health Check**: http://localhost:8080/health
- **Metrics**: http://localhost:8080/metrics

### Production

Replace `localhost:8080` with your production domain:

- **Swagger UI**: https://api.vpp.example.com/api/docs
- **ReDoc**: https://api.vpp.example.com/api/redoc
- **OpenAPI Spec**: https://api.vpp.example.com/api/openapi.json
- **JSON Docs**: https://api.vpp.example.com/docs
- **Health Check**: https://api.vpp.example.com/health
- **Metrics**: https://api.vpp.example.com/metrics

### Docker Compose

If running with Docker Compose:

```bash
# Start the application
docker-compose up -d

# Access documentation
curl http://localhost:8080/api/docs
```

### Kubernetes

If running on Kubernetes:

```bash
# Port forward to local machine
kubectl port-forward svc/vpp-api 8080:8080

# Access documentation
curl http://localhost:8080/api/docs
```

## Support and Troubleshooting

### Getting Help

For API support and questions:

1. **Check the interactive documentation** at `/api/docs`
2. **Review error messages** - They include specific details about what went wrong
3. **Check the request ID** - Use it to track issues in logs
4. **Review logs** - Check application logs for detailed error information
5. **Check the health endpoint** - `/health` shows system status

### Common Issues and Solutions

#### 401 Unauthorized

**Problem:** Getting 401 responses for all requests

**Solutions:**
1. Verify API key is correct: `curl -H "X-API-Key: your-key" http://localhost:8080/api/v1/devices`
2. Check API key format - should be 32 characters
3. Verify header name is exactly `X-API-Key` (case-sensitive)
4. For JWT tokens, verify token hasn't expired
5. Check token format: `Authorization: Bearer <token>`

**Debug:**
```bash
# Test with verbose output
curl -v -H "X-API-Key: your-key" http://localhost:8080/api/v1/devices

# Check if service is running
curl http://localhost:8080/health
```

#### 400 Bad Request

**Problem:** Getting 400 errors with validation failures

**Solutions:**
1. Verify all required fields are present
2. Check data types match schema (strings, numbers, booleans)
3. Validate JSON syntax - use a JSON validator
4. Check enum values - use only allowed values
5. Verify date formats are ISO 8601

**Debug:**
```bash
# Pretty print error response
curl -X POST http://localhost:8080/api/v1/devices \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key" \
  -d '{"invalid": "data"}' | jq .

# Validate JSON
echo '{"id":"test"}' | jq .
```

#### 404 Not Found

**Problem:** Resource not found errors

**Solutions:**
1. Verify resource ID is correct
2. Check if resource was actually created
3. Verify you're using the correct endpoint path
4. Check for typos in the URL

**Debug:**
```bash
# List all devices to verify ID exists
curl http://localhost:8080/api/v1/devices \
  -H "X-API-Key: your-key" | jq .

# Check specific device
curl http://localhost:8080/api/v1/devices/device-id \
  -H "X-API-Key: your-key"
```

#### 429 Rate Limited

**Problem:** Getting 429 Too Many Requests

**Solutions:**
1. Reduce request frequency
2. Implement exponential backoff
3. Batch requests when possible
4. Cache responses to reduce redundant calls
5. Check rate limit headers: `X-RateLimit-Remaining`

**Debug:**
```bash
# Check rate limit headers
curl -i http://localhost:8080/api/v1/devices \
  -H "X-API-Key: your-key" | grep X-RateLimit

# Wait for reset time
curl http://localhost:8080/api/v1/devices \
  -H "X-API-Key: your-key" | jq '.error.details.reset_at'
```

#### 500 Internal Server Error

**Problem:** Getting 500 errors

**Solutions:**
1. Check application logs for error details
2. Use the error ID to track the issue
3. Verify database is running and accessible
4. Check system resources (disk space, memory)
5. Restart the application if needed

**Debug:**
```bash
# Check health endpoint
curl http://localhost:8080/health | jq .

# Check logs
docker logs vpp-api

# Check database connection
curl http://localhost:8080/health | jq '.database'
```

#### 503 Service Unavailable

**Problem:** Service is temporarily unavailable

**Solutions:**
1. Wait a few seconds and retry
2. Check if database is running
3. Check if service is running: `docker ps`
4. Check system resources
5. Review application logs

**Debug:**
```bash
# Check if service is running
curl http://localhost:8080/health

# Check Docker container
docker ps | grep vpp

# Check logs
docker logs vpp-api --tail 50
```

### Performance Troubleshooting

#### Slow API Responses

**Problem:** API responses are slow

**Solutions:**
1. Check database query performance
2. Verify indexes are created
3. Check system resources (CPU, memory, disk I/O)
4. Review application logs for slow queries
5. Check network latency

**Debug:**
```bash
# Measure response time
time curl http://localhost:8080/api/v1/devices \
  -H "X-API-Key: your-key"

# Check metrics
curl http://localhost:8080/metrics | grep http_request_duration
```

#### High Memory Usage

**Problem:** Application using too much memory

**Solutions:**
1. Check for memory leaks in logs
2. Reduce database connection pool size
3. Implement caching to reduce database queries
4. Monitor long-running operations
5. Restart the application

**Debug:**
```bash
# Check memory usage
docker stats vpp-api

# Check logs for memory issues
docker logs vpp-api | grep -i memory
```

### Debugging Tips

1. **Use request IDs** - Every response includes a unique request ID for tracking
2. **Enable verbose logging** - Set `LOG_LEVEL=DEBUG` environment variable
3. **Use curl with verbose output** - `curl -v` shows all headers and details
4. **Check response headers** - Include rate limit and request ID information
5. **Use jq for JSON parsing** - Makes error responses easier to read
6. **Monitor metrics** - Check `/metrics` endpoint for performance data
7. **Review logs** - Application logs contain detailed error information

### Getting Support

If you encounter issues:

1. **Collect information:**
   - Request ID from error response
   - Full error message and details
   - Steps to reproduce the issue
   - Application logs
   - System information (OS, Docker version, etc.)

2. **Check documentation:**
   - Review this API documentation
   - Check OpenAPI spec at `/api/openapi.json`
   - Review interactive docs at `/api/docs`

3. **Contact support:**
   - Include request ID and error details
   - Provide steps to reproduce
   - Include relevant logs
   - Describe expected vs actual behavior
