"""
OpenAPI 3.0 Specification for VPP Master API
"""

OPENAPI_SPEC = {
    "openapi": "3.0.0",
    "info": {
        "title": "VPP Master API",
        "description": "Virtual Power Plant Master Station API for managing distributed energy resources, dispatch operations, protocol conversion, and power system analysis",
        "version": "1.0.0",
        "contact": {
            "name": "VPP Development Team"
        }
    },
    "servers": [
        {
            "url": "http://localhost:8080",
            "description": "Development server"
        },
        {
            "url": "https://api.vpp.example.com",
            "description": "Production server"
        }
    ],
    "components": {
        "securitySchemes": {
            "ApiKeyAuth": {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-Key",
                "description": "API Key for authentication"
            },
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "JWT token for authentication"
            }
        },
        "schemas": {
            "Device": {
                "type": "object",
                "required": ["id", "device_type", "location", "capabilities"],
                "properties": {
                    "id": {
                        "type": "string",
                        "description": "Unique device identifier"
                    },
                    "device_type": {
                        "type": "string",
                        "enum": ["solar", "wind", "battery", "load"],
                        "description": "Type of distributed energy resource"
                    },
                    "location": {
                        "type": "string",
                        "description": "Physical location of the device"
                    },
                    "status": {
                        "type": "string",
                        "enum": ["online", "offline", "error"],
                        "description": "Current device status"
                    },
                    "last_heartbeat": {
                        "type": "string",
                        "format": "date-time",
                        "description": "Timestamp of last heartbeat"
                    },
                    "capabilities": {
                        "type": "object",
                        "description": "Device capabilities and specifications"
                    },
                    "configuration": {
                        "type": "object",
                        "description": "Device configuration parameters"
                    },
                    "created_at": {
                        "type": "string",
                        "format": "date-time"
                    },
                    "updated_at": {
                        "type": "string",
                        "format": "date-time"
                    }
                }
            },
            "Dispatch": {
                "type": "object",
                "required": ["device_id", "command_type", "target_value"],
                "properties": {
                    "id": {
                        "type": "string",
                        "description": "Unique dispatch identifier"
                    },
                    "device_id": {
                        "type": "string",
                        "description": "Target device ID"
                    },
                    "command_type": {
                        "type": "string",
                        "description": "Type of command to execute"
                    },
                    "target_value": {
                        "type": "number",
                        "description": "Target value for the command"
                    },
                    "priority_level": {
                        "type": "integer",
                        "description": "Priority level (0-10)"
                    },
                    "status": {
                        "type": "string",
                        "enum": ["pending", "executing", "completed", "failed"],
                        "description": "Current dispatch status"
                    },
                    "execution_time": {
                        "type": "string",
                        "format": "date-time",
                        "description": "When the dispatch was executed"
                    },
                    "scheduled_time": {
                        "type": "string",
                        "format": "date-time",
                        "description": "Scheduled execution time"
                    },
                    "retry_count": {
                        "type": "integer",
                        "description": "Number of retry attempts"
                    },
                    "error_message": {
                        "type": "string",
                        "description": "Error message if dispatch failed"
                    },
                    "created_at": {
                        "type": "string",
                        "format": "date-time"
                    },
                    "updated_at": {
                        "type": "string",
                        "format": "date-time"
                    }
                }
            },
            "ErrorResponse": {
                "type": "object",
                "properties": {
                    "error": {
                        "type": "object",
                        "properties": {
                            "code": {
                                "type": "string",
                                "description": "Error code"
                            },
                            "message": {
                                "type": "string",
                                "description": "Error message"
                            },
                            "details": {
                                "type": "object",
                                "description": "Additional error details"
                            },
                            "request_id": {
                                "type": "string",
                                "description": "Unique request ID for tracking"
                            }
                        }
                    }
                }
            },
            "PaginatedResponse": {
                "type": "object",
                "properties": {
                    "data": {
                        "type": "array",
                        "description": "List of items"
                    },
                    "pagination": {
                        "type": "object",
                        "properties": {
                            "total_count": {
                                "type": "integer"
                            },
                            "page": {
                                "type": "integer"
                            },
                            "page_size": {
                                "type": "integer"
                            }
                        }
                    }
                }
            }
        }
    },
    "security": [
        {"ApiKeyAuth": []},
        {"BearerAuth": []}
    ],
    "paths": {
        "/api/v1/devices": {
            "post": {
                "summary": "Register a new device",
                "tags": ["Devices"],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/Device"}
                        }
                    }
                },
                "responses": {
                    "201": {
                        "description": "Device registered successfully",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Device"}
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
                    "409": {
                        "description": "Device already exists",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                            }
                        }
                    }
                }
            },
            "get": {
                "summary": "List all devices",
                "tags": ["Devices"],
                "parameters": [
                    {
                        "name": "page",
                        "in": "query",
                        "schema": {"type": "integer", "default": 1}
                    },
                    {
                        "name": "page_size",
                        "in": "query",
                        "schema": {"type": "integer", "default": 50}
                    }
                ],
                "responses": {
                    "200": {
                        "description": "List of devices",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/PaginatedResponse"}
                            }
                        }
                    }
                }
            }
        },
        "/api/v1/devices/{device_id}": {
            "get": {
                "summary": "Get device details",
                "tags": ["Devices"],
                "parameters": [
                    {
                        "name": "device_id",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"}
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Device details",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Device"}
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
                    }
                }
            },
            "put": {
                "summary": "Update device configuration",
                "tags": ["Devices"],
                "parameters": [
                    {
                        "name": "device_id",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"}
                    }
                ],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/Device"}
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Device updated",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Device"}
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
                    }
                }
            },
            "delete": {
                "summary": "Deregister a device",
                "tags": ["Devices"],
                "parameters": [
                    {
                        "name": "device_id",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"}
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Device deregistered"
                    },
                    "404": {
                        "description": "Device not found"
                    }
                }
            }
        },
        "/api/v1/devices/{device_id}/status": {
            "get": {
                "summary": "Get device status",
                "tags": ["Devices"],
                "parameters": [
                    {
                        "name": "device_id",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"}
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Device status",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "device_id": {"type": "string"},
                                        "status": {"type": "string"},
                                        "last_heartbeat": {"type": "string", "format": "date-time"}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "/api/v1/dispatch": {
            "post": {
                "summary": "Create and execute a dispatch command",
                "tags": ["Dispatch"],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/Dispatch"}
                        }
                    }
                },
                "responses": {
                    "201": {
                        "description": "Dispatch created",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Dispatch"}
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
                    }
                }
            }
        },
        "/api/v1/dispatch/{dispatch_id}": {
            "get": {
                "summary": "Get dispatch details",
                "tags": ["Dispatch"],
                "parameters": [
                    {
                        "name": "dispatch_id",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"}
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Dispatch details",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/Dispatch"}
                            }
                        }
                    }
                }
            }
        },
        "/api/v1/dispatch/{dispatch_id}/status": {
            "get": {
                "summary": "Get dispatch status",
                "tags": ["Dispatch"],
                "parameters": [
                    {
                        "name": "dispatch_id",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"}
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Dispatch status"
                    }
                }
            }
        },
        "/api/v1/dispatch/history": {
            "get": {
                "summary": "Get dispatch history",
                "tags": ["Dispatch"],
                "parameters": [
                    {
                        "name": "device_id",
                        "in": "query",
                        "schema": {"type": "string"}
                    },
                    {
                        "name": "status",
                        "in": "query",
                        "schema": {"type": "string"}
                    },
                    {
                        "name": "page",
                        "in": "query",
                        "schema": {"type": "integer", "default": 1}
                    },
                    {
                        "name": "page_size",
                        "in": "query",
                        "schema": {"type": "integer", "default": 50}
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Dispatch history",
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/PaginatedResponse"}
                            }
                        }
                    }
                }
            }
        },
        "/api/v1/dispatch/{dispatch_id}/cancel": {
            "post": {
                "summary": "Cancel a dispatch",
                "tags": ["Dispatch"],
                "parameters": [
                    {
                        "name": "dispatch_id",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"}
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Dispatch cancelled"
                    }
                }
            }
        },
        "/api/v1/dispatch/schedule": {
            "post": {
                "summary": "Schedule a future dispatch",
                "tags": ["Dispatch"],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/Dispatch"}
                        }
                    }
                },
                "responses": {
                    "201": {
                        "description": "Dispatch scheduled"
                    }
                }
            }
        },
        "/api/v1/dispatch/scheduled": {
            "get": {
                "summary": "List scheduled dispatches",
                "tags": ["Dispatch"],
                "responses": {
                    "200": {
                        "description": "List of scheduled dispatches"
                    }
                }
            }
        },
        "/api/v1/protocol/parse": {
            "post": {
                "summary": "Parse a protocol message",
                "tags": ["Protocol"],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "protocol": {"type": "string"},
                                    "data": {"type": "string"}
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Parsed message"
                    }
                }
            }
        },
        "/api/v1/protocol/encode": {
            "post": {
                "summary": "Encode data to protocol format",
                "tags": ["Protocol"],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "protocol": {"type": "string"},
                                    "data": {"type": "object"}
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Encoded message"
                    }
                }
            }
        },
        "/api/v1/protocol/convert": {
            "post": {
                "summary": "Convert between protocols",
                "tags": ["Protocol"],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "source_protocol": {"type": "string"},
                                    "target_protocol": {"type": "string"},
                                    "data": {"type": "object"}
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Converted message"
                    }
                }
            }
        },
        "/api/v1/protocol/mappings": {
            "get": {
                "summary": "Get protocol mappings",
                "tags": ["Protocol"],
                "responses": {
                    "200": {
                        "description": "List of protocol mappings"
                    }
                }
            },
            "post": {
                "summary": "Create a protocol mapping",
                "tags": ["Protocol"],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "source_protocol": {"type": "string"},
                                    "target_protocol": {"type": "string"},
                                    "mapping_rules": {"type": "object"}
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "201": {
                        "description": "Mapping created"
                    }
                }
            }
        },
        "/api/v1/analysis/power-flow": {
            "post": {
                "summary": "Execute power flow analysis",
                "tags": ["Analysis"],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "system_state": {"type": "object"}
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Analysis results"
                    }
                }
            }
        },
        "/api/v1/analysis/stability": {
            "post": {
                "summary": "Execute stability analysis",
                "tags": ["Analysis"],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "system_state": {"type": "object"}
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Analysis results"
                    }
                }
            }
        },
        "/api/v1/analysis/metrics": {
            "get": {
                "summary": "Get performance metrics",
                "tags": ["Analysis"],
                "parameters": [
                    {
                        "name": "time_range",
                        "in": "query",
                        "schema": {"type": "string"}
                    }
                ],
                "responses": {
                    "200": {
                        "description": "Performance metrics"
                    }
                }
            }
        },
        "/api/v1/analysis/report": {
            "post": {
                "summary": "Generate a report",
                "tags": ["Analysis"],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "report_type": {"type": "string"}
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "200": {
                        "description": "Generated report"
                    }
                }
            }
        }
    }
}
