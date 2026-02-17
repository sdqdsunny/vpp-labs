"""
Protocol Management Routes

REST API endpoints for protocol adapter management, message mapping, and conversion.
"""

import logging
from bottle import Bottle, request, response
from typing import Dict, Any

from services.protocol_management import get_protocol_management_service
from services.protocol_adapters.base import ProtocolException

logger = logging.getLogger(__name__)


def create_protocol_management_routes(app: Bottle) -> None:
    """
    Create protocol management routes.
    
    Args:
        app: Bottle application instance
    """
    
    # ========================================================================
    # Adapter Management Endpoints
    # ========================================================================
    
    @app.post("/api/v1/protocol/adapters")
    def create_adapter():
        """
        Create protocol adapter instance.
        
        Request body:
        {
            "protocol": "iec61850",
            "adapter_id": "adapter-1"
        }
        
        Returns:
            Adapter information
        """
        try:
            data = request.json
            protocol = data.get("protocol")
            adapter_id = data.get("adapter_id")
            
            if not protocol or not adapter_id:
                response.status = 400
                return {"error": "Missing protocol or adapter_id"}
            
            service = get_protocol_management_service()
            result = service.create_adapter(protocol, adapter_id)
            
            response.status = 201
            return result
        except ProtocolException as e:
            response.status = 400
            return {"error": str(e)}
        except Exception as e:
            logger.error(f"Error creating adapter: {e}")
            response.status = 500
            return {"error": "Internal server error"}
    
    @app.get("/api/v1/protocol/adapters")
    def list_adapters():
        """
        List all active adapters.
        
        Returns:
            List of adapter information
        """
        try:
            service = get_protocol_management_service()
            adapters = service.list_adapters()
            return {"adapters": adapters}
        except Exception as e:
            logger.error(f"Error listing adapters: {e}")
            response.status = 500
            return {"error": "Internal server error"}
    
    @app.get("/api/v1/protocol/adapters/<adapter_id>")
    def get_adapter(adapter_id: str):
        """
        Get adapter by ID.
        
        Args:
            adapter_id: Adapter identifier
            
        Returns:
            Adapter information
        """
        try:
            service = get_protocol_management_service()
            adapter = service.get_adapter(adapter_id)
            
            if not adapter:
                response.status = 404
                return {"error": "Adapter not found"}
            
            return adapter
        except Exception as e:
            logger.error(f"Error getting adapter: {e}")
            response.status = 500
            return {"error": "Internal server error"}
    
    @app.delete("/api/v1/protocol/adapters/<adapter_id>")
    def delete_adapter(adapter_id: str):
        """
        Delete adapter instance.
        
        Args:
            adapter_id: Adapter identifier
            
        Returns:
            Deletion status
        """
        try:
            service = get_protocol_management_service()
            removed = service.remove_adapter(adapter_id)
            
            if not removed:
                response.status = 404
                return {"error": "Adapter not found"}
            
            return {"status": "deleted", "adapter_id": adapter_id}
        except Exception as e:
            logger.error(f"Error deleting adapter: {e}")
            response.status = 500
            return {"error": "Internal server error"}
    
    # ========================================================================
    # Registry Status Endpoints
    # ========================================================================
    
    @app.get("/api/v1/protocol/registry/status")
    def get_registry_status():
        """
        Get protocol registry status.
        
        Returns:
            Registry status information
        """
        try:
            service = get_protocol_management_service()
            status = service.get_registry_status()
            return status
        except Exception as e:
            logger.error(f"Error getting registry status: {e}")
            response.status = 500
            return {"error": "Internal server error"}
    
    @app.get("/api/v1/protocol/supported")
    def list_supported_protocols():
        """
        List all supported protocols.
        
        Returns:
            List of protocol names
        """
        try:
            service = get_protocol_management_service()
            protocols = service.list_supported_protocols()
            return {"protocols": protocols}
        except Exception as e:
            logger.error(f"Error listing protocols: {e}")
            response.status = 500
            return {"error": "Internal server error"}
    
    @app.get("/api/v1/protocol/info/<protocol_name>")
    def get_protocol_info(protocol_name: str):
        """
        Get protocol information.
        
        Args:
            protocol_name: Protocol name
            
        Returns:
            Protocol information
        """
        try:
            service = get_protocol_management_service()
            info = service.get_protocol_info(protocol_name)
            
            if not info:
                response.status = 404
                return {"error": "Protocol not found"}
            
            return info
        except Exception as e:
            logger.error(f"Error getting protocol info: {e}")
            response.status = 500
            return {"error": "Internal server error"}
    
    # ========================================================================
    # Message Mapping Endpoints
    # ========================================================================
    
    @app.post("/api/v1/protocol/map")
    def map_message():
        """
        Map message from source protocol to target protocol.
        
        Request body:
        {
            "source_protocol": "iec61850",
            "target_protocol": "modbus",
            "message": {
                "voltage": 230,
                "current": 10,
                ...
            }
        }
        
        Returns:
            Mapped message
        """
        try:
            data = request.json
            source = data.get("source_protocol")
            target = data.get("target_protocol")
            message = data.get("message")
            
            if not source or not target or not message:
                response.status = 400
                return {"error": "Missing source_protocol, target_protocol, or message"}
            
            service = get_protocol_management_service()
            mapped = service.map_message(source, target, message)
            
            return {"mapped_message": mapped}
        except ProtocolException as e:
            response.status = 400
            return {"error": str(e)}
        except Exception as e:
            logger.error(f"Error mapping message: {e}")
            response.status = 500
            return {"error": "Internal server error"}
    
    @app.post("/api/v1/protocol/validate")
    def validate_message():
        """
        Validate message using specified validator.
        
        Request body:
        {
            "validator": "validate_iec61850_message",
            "message": {
                "voltage": 230,
                "current": 10,
                ...
            }
        }
        
        Returns:
            Validation result
        """
        try:
            data = request.json
            validator = data.get("validator")
            message = data.get("message")
            
            if not validator or not message:
                response.status = 400
                return {"error": "Missing validator or message"}
            
            service = get_protocol_management_service()
            is_valid = service.validate_message(validator, message)
            
            return {
                "validator": validator,
                "is_valid": is_valid,
                "message": "Valid" if is_valid else "Invalid"
            }
        except Exception as e:
            logger.error(f"Error validating message: {e}")
            response.status = 500
            return {"error": "Internal server error"}
    
    @app.post("/api/v1/protocol/transform")
    def transform_data():
        """
        Transform data using specified transformer.
        
        Request body:
        {
            "transformer": "scale_voltage_to_mv",
            "data": {
                "voltage": 230
            }
        }
        
        Returns:
            Transformed data
        """
        try:
            data = request.json
            transformer = data.get("transformer")
            input_data = data.get("data")
            
            if not transformer or not input_data:
                response.status = 400
                return {"error": "Missing transformer or data"}
            
            service = get_protocol_management_service()
            result = service.transform_data(transformer, input_data)
            
            return {
                "transformer": transformer,
                "result": result
            }
        except ProtocolException as e:
            response.status = 400
            return {"error": str(e)}
        except Exception as e:
            logger.error(f"Error transforming data: {e}")
            response.status = 500
            return {"error": "Internal server error"}
    
    # ========================================================================
    # Mapper Information Endpoints
    # ========================================================================
    
    @app.get("/api/v1/protocol/mapper/info")
    def get_mapper_info():
        """
        Get mapper information.
        
        Returns:
            Mapper information including mappings, transformers, validators
        """
        try:
            service = get_protocol_management_service()
            info = service.get_mapper_info()
            return info
        except Exception as e:
            logger.error(f"Error getting mapper info: {e}")
            response.status = 500
            return {"error": "Internal server error"}
    
    # ========================================================================
    # Bidirectional Conversion Endpoints
    # ========================================================================
    
    @app.post("/api/v1/protocol/convert/iec61850-to-modbus")
    def convert_iec61850_to_modbus():
        """Convert IEC 61850 message to Modbus format"""
        try:
            message = request.json.get("message")
            if not message:
                response.status = 400
                return {"error": "Missing message"}
            
            service = get_protocol_management_service()
            result = service.convert_iec61850_to_modbus(message)
            return {"result": result}
        except ProtocolException as e:
            response.status = 400
            return {"error": str(e)}
        except Exception as e:
            logger.error(f"Error converting message: {e}")
            response.status = 500
            return {"error": "Internal server error"}
    
    @app.post("/api/v1/protocol/convert/modbus-to-iec61850")
    def convert_modbus_to_iec61850():
        """Convert Modbus message to IEC 61850 format"""
        try:
            message = request.json.get("message")
            if not message:
                response.status = 400
                return {"error": "Missing message"}
            
            service = get_protocol_management_service()
            result = service.convert_modbus_to_iec61850(message)
            return {"result": result}
        except ProtocolException as e:
            response.status = 400
            return {"error": str(e)}
        except Exception as e:
            logger.error(f"Error converting message: {e}")
            response.status = 500
            return {"error": "Internal server error"}
    
    @app.post("/api/v1/protocol/convert/iec61850-to-dnp3")
    def convert_iec61850_to_dnp3():
        """Convert IEC 61850 message to DNP3 format"""
        try:
            message = request.json.get("message")
            if not message:
                response.status = 400
                return {"error": "Missing message"}
            
            service = get_protocol_management_service()
            result = service.convert_iec61850_to_dnp3(message)
            return {"result": result}
        except ProtocolException as e:
            response.status = 400
            return {"error": str(e)}
        except Exception as e:
            logger.error(f"Error converting message: {e}")
            response.status = 500
            return {"error": "Internal server error"}
    
    @app.post("/api/v1/protocol/convert/dnp3-to-iec61850")
    def convert_dnp3_to_iec61850():
        """Convert DNP3 message to IEC 61850 format"""
        try:
            message = request.json.get("message")
            if not message:
                response.status = 400
                return {"error": "Missing message"}
            
            service = get_protocol_management_service()
            result = service.convert_dnp3_to_iec61850(message)
            return {"result": result}
        except ProtocolException as e:
            response.status = 400
            return {"error": str(e)}
        except Exception as e:
            logger.error(f"Error converting message: {e}")
            response.status = 500
            return {"error": "Internal server error"}
    
    @app.post("/api/v1/protocol/convert/iec61850-to-mqtt")
    def convert_iec61850_to_mqtt():
        """Convert IEC 61850 message to MQTT format"""
        try:
            message = request.json.get("message")
            if not message:
                response.status = 400
                return {"error": "Missing message"}
            
            service = get_protocol_management_service()
            result = service.convert_iec61850_to_mqtt(message)
            return {"result": result}
        except ProtocolException as e:
            response.status = 400
            return {"error": str(e)}
        except Exception as e:
            logger.error(f"Error converting message: {e}")
            response.status = 500
            return {"error": "Internal server error"}
    
    @app.post("/api/v1/protocol/convert/mqtt-to-iec61850")
    def convert_mqtt_to_iec61850():
        """Convert MQTT message to IEC 61850 format"""
        try:
            message = request.json.get("message")
            if not message:
                response.status = 400
                return {"error": "Missing message"}
            
            service = get_protocol_management_service()
            result = service.convert_mqtt_to_iec61850(message)
            return {"result": result}
        except ProtocolException as e:
            response.status = 400
            return {"error": str(e)}
        except Exception as e:
            logger.error(f"Error converting message: {e}")
            response.status = 500
            return {"error": "Internal server error"}
    
    @app.post("/api/v1/protocol/convert/modbus-to-dnp3")
    def convert_modbus_to_dnp3():
        """Convert Modbus message to DNP3 format"""
        try:
            message = request.json.get("message")
            if not message:
                response.status = 400
                return {"error": "Missing message"}
            
            service = get_protocol_management_service()
            result = service.convert_modbus_to_dnp3(message)
            return {"result": result}
        except ProtocolException as e:
            response.status = 400
            return {"error": str(e)}
        except Exception as e:
            logger.error(f"Error converting message: {e}")
            response.status = 500
            return {"error": "Internal server error"}
    
    @app.post("/api/v1/protocol/convert/dnp3-to-modbus")
    def convert_dnp3_to_modbus():
        """Convert DNP3 message to Modbus format"""
        try:
            message = request.json.get("message")
            if not message:
                response.status = 400
                return {"error": "Missing message"}
            
            service = get_protocol_management_service()
            result = service.convert_dnp3_to_modbus(message)
            return {"result": result}
        except ProtocolException as e:
            response.status = 400
            return {"error": str(e)}
        except Exception as e:
            logger.error(f"Error converting message: {e}")
            response.status = 500
            return {"error": "Internal server error"}
    
    @app.post("/api/v1/protocol/convert/modbus-to-mqtt")
    def convert_modbus_to_mqtt():
        """Convert Modbus message to MQTT format"""
        try:
            message = request.json.get("message")
            if not message:
                response.status = 400
                return {"error": "Missing message"}
            
            service = get_protocol_management_service()
            result = service.convert_modbus_to_mqtt(message)
            return {"result": result}
        except ProtocolException as e:
            response.status = 400
            return {"error": str(e)}
        except Exception as e:
            logger.error(f"Error converting message: {e}")
            response.status = 500
            return {"error": "Internal server error"}
    
    @app.post("/api/v1/protocol/convert/mqtt-to-modbus")
    def convert_mqtt_to_modbus():
        """Convert MQTT message to Modbus format"""
        try:
            message = request.json.get("message")
            if not message:
                response.status = 400
                return {"error": "Missing message"}
            
            service = get_protocol_management_service()
            result = service.convert_mqtt_to_modbus(message)
            return {"result": result}
        except ProtocolException as e:
            response.status = 400
            return {"error": str(e)}
        except Exception as e:
            logger.error(f"Error converting message: {e}")
            response.status = 500
            return {"error": "Internal server error"}
    
    @app.post("/api/v1/protocol/convert/dnp3-to-mqtt")
    def convert_dnp3_to_mqtt():
        """Convert DNP3 message to MQTT format"""
        try:
            message = request.json.get("message")
            if not message:
                response.status = 400
                return {"error": "Missing message"}
            
            service = get_protocol_management_service()
            result = service.convert_dnp3_to_mqtt(message)
            return {"result": result}
        except ProtocolException as e:
            response.status = 400
            return {"error": str(e)}
        except Exception as e:
            logger.error(f"Error converting message: {e}")
            response.status = 500
            return {"error": "Internal server error"}
    
    @app.post("/api/v1/protocol/convert/mqtt-to-dnp3")
    def convert_mqtt_to_dnp3():
        """Convert MQTT message to DNP3 format"""
        try:
            message = request.json.get("message")
            if not message:
                response.status = 400
                return {"error": "Missing message"}
            
            service = get_protocol_management_service()
            result = service.convert_mqtt_to_dnp3(message)
            return {"result": result}
        except ProtocolException as e:
            response.status = 400
            return {"error": str(e)}
        except Exception as e:
            logger.error(f"Error converting message: {e}")
            response.status = 500
            return {"error": "Internal server error"}
    
    logger.info("Protocol management routes created")
