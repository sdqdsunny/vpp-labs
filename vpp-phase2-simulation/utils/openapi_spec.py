"""
OpenAPI 3.0 Specification for VPP Phase 2 Simulation Framework.

Provides comprehensive API documentation for all endpoints including:
- Device Management
- Scenario Management
- Metrics
- Power Flow
- Visualization/Dashboard
"""

def get_openapi_spec():
    """
    Generate OpenAPI 3.0 specification for the VPP Phase 2 Simulation Framework.
    
    Returns:
        dict: Complete OpenAPI specification
    """
    return {
        "openapi": "3.0.0",
        "info": {
            "title": "VPP Phase 2 Simulation Framework API",
            "description": "Comprehensive API for distributed energy resource simulation, scenario execution, and power flow analysis",
            "version": "1.0.0",
            "contact": {
                "name": "VPP Development Team",
                "email": "support@vpp.local"
            },
            "license": {
                "name": "MIT"
            }
        },
        "servers": [
            {
                "url": "http://localhost:8080",
                "description": "Development server"
            },
            {
                "url": "https://api.vpp.local",
                "description": "Production server"
            }
        ],
        "paths": get_paths(),
        "components": get_components(),
        "tags": get_tags()
    }


def get_paths():
    """Get all API paths and operations."""
    return {
        # Health and Status
        "/health": {
            "get": {
                "tags": ["System"],
                "summary": "Health check",
                "description": "Check if the API is healthy",
                "operationId": "healthCheck",
                "responses": {
                    "200": {
                        "description": "API is healthy",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/HealthResponse"}
                            }
                        }
                    }
                }
            }
        },
        "/ready": {
            "get": {
                "tags": ["System"],
                "summary": "Readiness check",
                "description": "Check if the API is ready to serve requests",
                "operationId": "readinessCheck",
                "responses": {
                    "200": {
                        "description": "API is ready",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ReadinessResponse"}
                            }
                        }
                    },
                    "503": {
                        "description": "API is not ready",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                            }
                        }
                    }
                }
            }
        },
        "/metrics": {
            "get": {
                "tags": ["Monitoring"],
                "summary": "Prometheus metrics",
                "description": "Get Prometheus metrics in text format",
                "operationId": "getMetrics",
                "responses": {
                    "200": {
                        "description": "Prometheus metrics",
                        "content": {
                            "text/plain": {
                                "schema": {"type": "string"}
                            }
                        }
                    }
                }
            }
        },
        # Device Management
        "/api/v1/devices": {
            "get": {
                "tags": ["Device Management"],
                "summary": "List all devices",
                "description": "Get a list of all device simulators",
                "operationId": "listDevices",
                "responses": {
                    "200": {
                        "description": "List of devices",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/DeviceListResponse"}
                            }
                        }
                    },
                    "500": {
                        "description": "Server error",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                            }
                        }
                    }
                }
            },
            "post": {
                "tags": ["Device Management"],
                "summary": "Create device",
                "description": "Create a new device simulator",
                "operationId": "createDevice",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/CreateDeviceRequest"}
                        }
                    }
                },
                "responses": {
                    "201": {
                        "description": "Device created",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/DeviceResponse"}
                            }
                        }
                    },
                    "400": {
                        "description": "Invalid request",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                            }
                        }
                    },
                    "500": {
                        "description": "Server error",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                            }
                        }
                    }
                }
            }
        },
        "/api/v1/devices/{device_id}": {
            "get": {
                "tags": ["Device Management"],
                "summary": "Get device details",
                "description": "Get details and current state of a specific device",
                "operationId": "getDevice",
                "parameters": [
                    {
                        "name": "device_id",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"},
                        "description": "Device ID"
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Device details",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/DeviceDetailResponse"}
                            }
                        }
                    },
                    "404": {
                        "description": "Device not found",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                            }
                        }
                    },
                    "500": {
                        "description": "Server error",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                            }
                        }
                    }
                }
            },
            "delete": {
                "tags": ["Device Management"],
                "summary": "Delete device",
                "description": "Delete a device simulator",
                "operationId": "deleteDevice",
                "parameters": [
                    {
                        "name": "device_id",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"},
                        "description": "Device ID"
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Device deleted",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/DeleteResponse"}
                            }
                        }
                    },
                    "404": {
                        "description": "Device not found",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                            }
                        }
                    },
                    "500": {
                        "description": "Server error",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                            }
                        }
                    }
                }
            }
        },
        "/api/v1/devices/{device_id}/commands": {
            "post": {
                "tags": ["Device Management"],
                "summary": "Send command to device",
                "description": "Send a command to a device simulator",
                "operationId": "sendDeviceCommand",
                "parameters": [
                    {
                        "name": "device_id",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"},
                        "description": "Device ID"
                    }
                ],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/DeviceCommandRequest"}
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Command executed",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/CommandResultResponse"}
                            }
                        }
                    },
                    "400": {
                        "description": "Invalid command",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                            }
                        }
                    },
                    "404": {
                        "description": "Device not found",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                            }
                        }
                    },
                    "500": {
                        "description": "Server error",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                            }
                        }
                    }
                }
            }
        },
        "/api/v1/devices/{device_id}/capabilities": {
            "get": {
                "tags": ["Device Management"],
                "summary": "Get device capabilities",
                "description": "Get capabilities of a device simulator",
                "operationId": "getDeviceCapabilities",
                "parameters": [
                    {
                        "name": "device_id",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"},
                        "description": "Device ID"
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Device capabilities",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/CapabilitiesResponse"}
                            }
                        }
                    },
                    "404": {
                        "description": "Device not found",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                            }
                        }
                    },
                    "500": {
                        "description": "Server error",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                            }
                        }
                    }
                }
            }
        },
        "/api/v1/devices/{device_id}/reset": {
            "post": {
                "tags": ["Device Management"],
                "summary": "Reset device",
                "description": "Reset a device simulator to initial state",
                "operationId": "resetDevice",
                "parameters": [
                    {
                        "name": "device_id",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"},
                        "description": "Device ID"
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Device reset",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ResetResponse"}
                            }
                        }
                    },
                    "404": {
                        "description": "Device not found",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                            }
                        }
                    },
                    "500": {
                        "description": "Server error",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                            }
                        }
                    }
                }
            }
        },
        "/api/v1/devices/{device_id}/update": {
            "post": {
                "tags": ["Device Management"],
                "summary": "Update device state",
                "description": "Update device state for a time step",
                "operationId": "updateDevice",
                "parameters": [
                    {
                        "name": "device_id",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"},
                        "description": "Device ID"
                    }
                ],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/UpdateDeviceRequest"}
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Device updated",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/DeviceStateResponse"}
                            }
                        }
                    },
                    "400": {
                        "description": "Invalid request",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                            }
                        }
                    },
                    "404": {
                        "description": "Device not found",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                            }
                        }
                    },
                    "500": {
                        "description": "Server error",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                            }
                        }
                    }
                }
            }
        },
        # Scenario Management
        "/api/v1/scenarios": {
            "get": {
                "tags": ["Scenario Management"],
                "summary": "List all scenarios",
                "description": "Get a list of all scenarios",
                "operationId": "listScenarios",
                "responses": {
                    "200": {
                        "description": "List of scenarios",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ScenarioListResponse"}
                            }
                        }
                    },
                    "500": {
                        "description": "Server error",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                            }
                        }
                    }
                }
            },
            "post": {
                "tags": ["Scenario Management"],
                "summary": "Create scenario",
                "description": "Create a new scenario",
                "operationId": "createScenario",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/CreateScenarioRequest"}
                        }
                    }
                },
                "responses": {
                    "201": {
                        "description": "Scenario created",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ScenarioResponse"}
                            }
                        }
                    },
                    "400": {
                        "description": "Invalid request",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                            }
                        }
                    },
                    "500": {
                        "description": "Server error",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                            }
                        }
                    }
                }
            }
        },
        "/api/v1/scenarios/{scenario_id}": {
            "get": {
                "tags": ["Scenario Management"],
                "summary": "Get scenario details",
                "description": "Get details of a specific scenario",
                "operationId": "getScenario",
                "parameters": [
                    {
                        "name": "scenario_id",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"},
                        "description": "Scenario ID"
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Scenario details",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ScenarioDetailResponse"}
                            }
                        }
                    },
                    "404": {
                        "description": "Scenario not found",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                            }
                        }
                    },
                    "500": {
                        "description": "Server error",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                            }
                        }
                    }
                }
            },
            "delete": {
                "tags": ["Scenario Management"],
                "summary": "Delete scenario",
                "description": "Delete a scenario",
                "operationId": "deleteScenario",
                "parameters": [
                    {
                        "name": "scenario_id",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"},
                        "description": "Scenario ID"
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Scenario deleted",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/DeleteResponse"}
                            }
                        }
                    },
                    "404": {
                        "description": "Scenario not found",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                            }
                        }
                    },
                    "500": {
                        "description": "Server error",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                            }
                        }
                    }
                }
            }
        },
        "/api/v1/scenarios/{scenario_id}/execute": {
            "post": {
                "tags": ["Scenario Management"],
                "summary": "Execute scenario",
                "description": "Execute a scenario",
                "operationId": "executeScenario",
                "parameters": [
                    {
                        "name": "scenario_id",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"},
                        "description": "Scenario ID"
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Scenario execution started",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ExecutionResponse"}
                            }
                        }
                    },
                    "404": {
                        "description": "Scenario not found",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                            }
                        }
                    },
                    "500": {
                        "description": "Server error",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                            }
                        }
                    }
                }
            }
        },
        "/api/v1/scenarios/{scenario_id}/results": {
            "get": {
                "tags": ["Scenario Management"],
                "summary": "Get scenario results",
                "description": "Get results of a completed scenario",
                "operationId": "getScenarioResults",
                "parameters": [
                    {
                        "name": "scenario_id",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"},
                        "description": "Scenario ID"
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Scenario results",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ScenarioResultsResponse"}
                            }
                        }
                    },
                    "404": {
                        "description": "Scenario not found",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                            }
                        }
                    },
                    "500": {
                        "description": "Server error",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                            }
                        }
                    }
                }
            }
        },
        "/api/v1/scenarios/{scenario_id}/export": {
            "get": {
                "tags": ["Scenario Management"],
                "summary": "Export scenario data",
                "description": "Export scenario data in JSON or CSV format",
                "operationId": "exportScenario",
                "parameters": [
                    {
                        "name": "scenario_id",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"},
                        "description": "Scenario ID"
                    },
                    {
                        "name": "format",
                        "in": "query",
                        "schema": {"type": "string", "enum": ["json", "csv"]},
                        "description": "Export format (json or csv)"
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Scenario data exported",
                        "content": {
                            "application/json": {
                                "schema": {"type": "object"}
                            },
                            "text/csv": {
                                "schema": {"type": "string"}
                            }
                        }
                    },
                    "404": {
                        "description": "Scenario not found",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                            }
                        }
                    },
                    "500": {
                        "description": "Server error",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                            }
                        }
                    }
                }
            }
        },
        # Metrics
        "/api/v1/metrics": {
            "get": {
                "tags": ["Metrics"],
                "summary": "Get metrics",
                "description": "Get aggregated metrics",
                "operationId": "getMetricsData",
                "parameters": [
                    {
                        "name": "scenario_id",
                        "in": "query",
                        "schema": {"type": "string"},
                        "description": "Filter by scenario ID"
                    },
                    {
                        "name": "start_time",
                        "in": "query",
                        "schema": {"type": "string", "format": "date-time"},
                        "description": "Start time for metrics"
                    },
                    {
                        "name": "end_time",
                        "in": "query",
                        "schema": {"type": "string", "format": "date-time"},
                        "description": "End time for metrics"
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Metrics data",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/MetricsResponse"}
                            }
                        }
                    },
                    "500": {
                        "description": "Server error",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                            }
                        }
                    }
                }
            }
        },
        "/api/v1/metrics/{metric_name}": {
            "get": {
                "tags": ["Metrics"],
                "summary": "Get specific metric",
                "description": "Get a specific metric by name",
                "operationId": "getMetricByName",
                "parameters": [
                    {
                        "name": "metric_name",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"},
                        "description": "Metric name"
                    },
                    {
                        "name": "scenario_id",
                        "in": "query",
                        "schema": {"type": "string"},
                        "description": "Filter by scenario ID"
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Metric data",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/MetricDataResponse"}
                            }
                        }
                    },
                    "404": {
                        "description": "Metric not found",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                            }
                        }
                    },
                    "500": {
                        "description": "Server error",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                            }
                        }
                    }
                }
            }
        },
        "/api/v1/metrics/query": {
            "post": {
                "tags": ["Metrics"],
                "summary": "Query metrics with filters",
                "description": "Query metrics with advanced filters",
                "operationId": "queryMetrics",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/MetricsQueryRequest"}
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Query results",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/MetricsQueryResponse"}
                            }
                        }
                    },
                    "400": {
                        "description": "Invalid query",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                            }
                        }
                    },
                    "500": {
                        "description": "Server error",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                            }
                        }
                    }
                }
            }
        },
        # Power Flow
        "/api/v1/power-flow": {
            "get": {
                "tags": ["Power Flow"],
                "summary": "Get power flow results",
                "description": "Get current power flow calculation results",
                "operationId": "getPowerFlow",
                "parameters": [
                    {
                        "name": "scenario_id",
                        "in": "query",
                        "schema": {"type": "string"},
                        "description": "Filter by scenario ID"
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Power flow results",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/PowerFlowResponse"}
                            }
                        }
                    },
                    "500": {
                        "description": "Server error",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                            }
                        }
                    }
                }
            }
        },
        "/api/v1/power-flow/calculate": {
            "post": {
                "tags": ["Power Flow"],
                "summary": "Calculate power flow",
                "description": "Calculate power flow for current network state",
                "operationId": "calculatePowerFlow",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/PowerFlowCalculationRequest"}
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Power flow calculated",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/PowerFlowResponse"}
                            }
                        }
                    },
                    "400": {
                        "description": "Invalid request",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                            }
                        }
                    },
                    "500": {
                        "description": "Server error",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                            }
                        }
                    }
                }
            }
        },
        "/api/v1/power-flow/violations": {
            "get": {
                "tags": ["Power Flow"],
                "summary": "Get violations",
                "description": "Get voltage and congestion violations",
                "operationId": "getViolations",
                "parameters": [
                    {
                        "name": "scenario_id",
                        "in": "query",
                        "schema": {"type": "string"},
                        "description": "Filter by scenario ID"
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Violations list",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ViolationsResponse"}
                            }
                        }
                    },
                    "500": {
                        "description": "Server error",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                            }
                        }
                    }
                }
            }
        },
        # Dashboard/Visualization
        "/api/v1/dashboard/status": {
            "get": {
                "tags": ["Dashboard"],
                "summary": "Get dashboard status",
                "description": "Get current dashboard status",
                "operationId": "getDashboardStatus",
                "responses": {
                    "200": {
                        "description": "Dashboard status",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/DashboardStatusResponse"}
                            }
                        }
                    },
                    "500": {
                        "description": "Server error",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                            }
                        }
                    }
                }
            }
        },
        "/api/v1/dashboard/metrics": {
            "get": {
                "tags": ["Dashboard"],
                "summary": "Get dashboard metrics",
                "description": "Get metrics for dashboard display",
                "operationId": "getDashboardMetrics",
                "responses": {
                    "200": {
                        "description": "Dashboard metrics",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/DashboardMetricsResponse"}
                            }
                        }
                    },
                    "500": {
                        "description": "Server error",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                            }
                        }
                    }
                }
            }
        },
        "/api/v1/dashboard/devices": {
            "get": {
                "tags": ["Dashboard"],
                "summary": "Get device status",
                "description": "Get device status for dashboard",
                "operationId": "getDashboardDevices",
                "responses": {
                    "200": {
                        "description": "Device status",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/DashboardDevicesResponse"}
                            }
                        }
                    },
                    "500": {
                        "description": "Server error",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                            }
                        }
                    }
                }
            }
        },
        "/api/v1/dashboard/power-flows": {
            "get": {
                "tags": ["Dashboard"],
                "summary": "Get power flow visualization",
                "description": "Get power flow data for visualization",
                "operationId": "getDashboardPowerFlows",
                "responses": {
                    "200": {
                        "description": "Power flow visualization data",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/DashboardPowerFlowsResponse"}
                            }
                        }
                    },
                    "500": {
                        "description": "Server error",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                            }
                        }
                    }
                }
            }
        },
        "/api/v1/dashboard/alerts": {
            "get": {
                "tags": ["Dashboard"],
                "summary": "Get alerts",
                "description": "Get active alerts for dashboard",
                "operationId": "getDashboardAlerts",
                "responses": {
                    "200": {
                        "description": "Alerts list",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/DashboardAlertsResponse"}
                            }
                        }
                    },
                    "500": {
                        "description": "Server error",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                            }
                        }
                    }
                }
            }
        },
        "/api/v1/dashboard/results": {
            "get": {
                "tags": ["Dashboard"],
                "summary": "Get final results",
                "description": "Get final results for dashboard",
                "operationId": "getDashboardResults",
                "parameters": [
                    {
                        "name": "scenario_id",
                        "in": "query",
                        "schema": {"type": "string"},
                        "description": "Scenario ID"
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Final results",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/DashboardResultsResponse"}
                            }
                        }
                    },
                    "500": {
                        "description": "Server error",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                            }
                        }
                    }
                }
            }
        },
    }


def get_components():
    """Get OpenAPI components (schemas, responses, etc.)."""
    return {
        "schemas": {
            # System Responses
            "HealthResponse": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "example": "healthy"},
                    "version": {"type": "string", "example": "0.1.0"},
                    "environment": {"type": "string", "example": "development"}
                }
            },
            "ReadinessResponse": {
                "type": "object",
                "properties": {
                    "status": {"type": "string", "example": "ready"},
                    "database": {"type": "string", "example": "connected"}
                }
            },
            # Error Response
            "ErrorResponse": {
                "type": "object",
                "properties": {
                    "error": {"type": "string"},
                    "details": {"type": "object"},
                    "request_id": {"type": "string"}
                }
            },
            # Device Schemas
            "CreateDeviceRequest": {
                "type": "object",
                "required": ["device_id", "device_type", "parameters"],
                "properties": {
                    "device_id": {"type": "string", "example": "dev-001"},
                    "device_type": {
                        "type": "string",
                        "enum": ["solar", "wind", "battery", "load"],
                        "example": "solar"
                    },
                    "parameters": {
                        "type": "object",
                        "example": {
                            "capacity": 100,
                            "location": "latitude,longitude"
                        }
                    }
                }
            },
            "DeviceResponse": {
                "type": "object",
                "properties": {
                    "device_id": {"type": "string"},
                    "device_type": {"type": "string"},
                    "status": {"type": "string"},
                    "timestamp": {"type": "string", "format": "date-time"}
                }
            },
            "DeviceDetailResponse": {
                "type": "object",
                "properties": {
                    "device_id": {"type": "string"},
                    "device_type": {"type": "string"},
                    "state": {"type": "object"},
                    "timestamp": {"type": "string", "format": "date-time"}
                }
            },
            "DeviceListResponse": {
                "type": "object",
                "properties": {
                    "devices": {
                        "type": "array",
                        "items": {"$ref": "#/components/schemas/DeviceDetailResponse"}
                    },
                    "count": {"type": "integer"}
                }
            },
            "DeviceCommandRequest": {
                "type": "object",
                "required": ["command_type"],
                "properties": {
                    "command_type": {"type": "string", "example": "charge"},
                    "parameters": {"type": "object"}
                }
            },
            "CommandResultResponse": {
                "type": "object",
                "properties": {
                    "device_id": {"type": "string"},
                    "success": {"type": "boolean"},
                    "message": {"type": "string"},
                    "data": {"type": "object"},
                    "timestamp": {"type": "string", "format": "date-time"}
                }
            },
            "CapabilitiesResponse": {
                "type": "object",
                "properties": {
                    "device_id": {"type": "string"},
                    "capabilities": {"type": "object"}
                }
            },
            "UpdateDeviceRequest": {
                "type": "object",
                "required": ["time_delta"],
                "properties": {
                    "time_delta": {"type": "number", "example": 1.0}
                }
            },
            "DeviceStateResponse": {
                "type": "object",
                "properties": {
                    "device_id": {"type": "string"},
                    "state": {"type": "object"},
                    "timestamp": {"type": "string", "format": "date-time"}
                }
            },
            "DeleteResponse": {
                "type": "object",
                "properties": {
                    "device_id": {"type": "string"},
                    "status": {"type": "string"},
                    "timestamp": {"type": "string", "format": "date-time"}
                }
            },
            "ResetResponse": {
                "type": "object",
                "properties": {
                    "device_id": {"type": "string"},
                    "status": {"type": "string"},
                    "timestamp": {"type": "string", "format": "date-time"}
                }
            },
            # Scenario Schemas
            "CreateScenarioRequest": {
                "type": "object",
                "required": ["name", "definition"],
                "properties": {
                    "name": {"type": "string", "example": "Test Scenario 1"},
                    "description": {"type": "string"},
                    "definition": {"type": "object"}
                }
            },
            "ScenarioResponse": {
                "type": "object",
                "properties": {
                    "scenario_id": {"type": "string"},
                    "name": {"type": "string"},
                    "status": {"type": "string"},
                    "created_at": {"type": "string", "format": "date-time"}
                }
            },
            "ScenarioDetailResponse": {
                "type": "object",
                "properties": {
                    "scenario_id": {"type": "string"},
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "status": {"type": "string"},
                    "definition": {"type": "object"},
                    "created_at": {"type": "string", "format": "date-time"}
                }
            },
            "ScenarioListResponse": {
                "type": "object",
                "properties": {
                    "scenarios": {
                        "type": "array",
                        "items": {"$ref": "#/components/schemas/ScenarioResponse"}
                    },
                    "count": {"type": "integer"}
                }
            },
            "ExecutionResponse": {
                "type": "object",
                "properties": {
                    "scenario_id": {"type": "string"},
                    "status": {"type": "string"},
                    "execution_id": {"type": "string"},
                    "timestamp": {"type": "string", "format": "date-time"}
                }
            },
            "ScenarioResultsResponse": {
                "type": "object",
                "properties": {
                    "scenario_id": {"type": "string"},
                    "status": {"type": "string"},
                    "results": {"type": "object"},
                    "metrics": {"type": "object"},
                    "timestamp": {"type": "string", "format": "date-time"}
                }
            },
            # Metrics Schemas
            "MetricsResponse": {
                "type": "object",
                "properties": {
                    "metrics": {
                        "type": "array",
                        "items": {"type": "object"}
                    },
                    "count": {"type": "integer"}
                }
            },
            "MetricDataResponse": {
                "type": "object",
                "properties": {
                    "metric_name": {"type": "string"},
                    "data": {
                        "type": "array",
                        "items": {"type": "object"}
                    }
                }
            },
            "MetricsQueryRequest": {
                "type": "object",
                "properties": {
                    "metric_names": {"type": "array", "items": {"type": "string"}},
                    "scenario_id": {"type": "string"},
                    "start_time": {"type": "string", "format": "date-time"},
                    "end_time": {"type": "string", "format": "date-time"},
                    "filters": {"type": "object"}
                }
            },
            "MetricsQueryResponse": {
                "type": "object",
                "properties": {
                    "results": {
                        "type": "array",
                        "items": {"type": "object"}
                    },
                    "count": {"type": "integer"}
                }
            },
            # Power Flow Schemas
            "PowerFlowResponse": {
                "type": "object",
                "properties": {
                    "network_state": {"type": "object"},
                    "power_flows": {"type": "array", "items": {"type": "object"}},
                    "violations": {"type": "array", "items": {"type": "object"}},
                    "stability": {"type": "object"},
                    "timestamp": {"type": "string", "format": "date-time"}
                }
            },
            "PowerFlowCalculationRequest": {
                "type": "object",
                "properties": {
                    "scenario_id": {"type": "string"},
                    "network_state": {"type": "object"}
                }
            },
            "ViolationsResponse": {
                "type": "object",
                "properties": {
                    "violations": {
                        "type": "array",
                        "items": {"type": "object"}
                    },
                    "count": {"type": "integer"}
                }
            },
            # Dashboard Schemas
            "DashboardStatusResponse": {
                "type": "object",
                "properties": {
                    "status": {"type": "string"},
                    "active_scenarios": {"type": "integer"},
                    "active_devices": {"type": "integer"},
                    "timestamp": {"type": "string", "format": "date-time"}
                }
            },
            "DashboardMetricsResponse": {
                "type": "object",
                "properties": {
                    "metrics": {"type": "object"},
                    "timestamp": {"type": "string", "format": "date-time"}
                }
            },
            "DashboardDevicesResponse": {
                "type": "object",
                "properties": {
                    "devices": {
                        "type": "array",
                        "items": {"type": "object"}
                    },
                    "count": {"type": "integer"}
                }
            },
            "DashboardPowerFlowsResponse": {
                "type": "object",
                "properties": {
                    "power_flows": {
                        "type": "array",
                        "items": {"type": "object"}
                    },
                    "timestamp": {"type": "string", "format": "date-time"}
                }
            },
            "DashboardAlertsResponse": {
                "type": "object",
                "properties": {
                    "alerts": {
                        "type": "array",
                        "items": {"type": "object"}
                    },
                    "count": {"type": "integer"}
                }
            },
            "DashboardResultsResponse": {
                "type": "object",
                "properties": {
                    "scenario_id": {"type": "string"},
                    "results": {"type": "object"},
                    "analysis": {"type": "object"},
                    "timestamp": {"type": "string", "format": "date-time"}
                }
            }
        }
    }


def get_tags():
    """Get OpenAPI tags for grouping operations."""
    return [
        {
            "name": "System",
            "description": "System health and status endpoints"
        },
        {
            "name": "Monitoring",
            "description": "Monitoring and metrics endpoints"
        },
        {
            "name": "Device Management",
            "description": "Device simulator control and management"
        },
        {
            "name": "Scenario Management",
            "description": "Scenario creation, execution, and management"
        },
        {
            "name": "Metrics",
            "description": "Metrics collection and querying"
        },
        {
            "name": "Power Flow",
            "description": "Power flow calculation and analysis"
        },
        {
            "name": "Dashboard",
            "description": "Dashboard and visualization endpoints"
        }
    ]
