"""
Protocol Conversion API Routes

Handles HTTP endpoints for protocol parsing, encoding, conversion, and mapping management.
"""

import logging
from bottle import request, response
from services.protocol_converter import get_protocol_converter
from utils.errors import ProtocolConversionError, ValidationError
from utils.database import get_session
from models.protocol_mapping import ProtocolMapping
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)


def setup_protocol_routes(app):
    """
    Register protocol conversion routes with the Bottle app.
    
    Args:
        app: Bottle application instance
    """
    
    # ========================================================================
    # Protocol Message Operations
    # ========================================================================
    
    @app.post('/api/v1/protocol/parse')
    def parse_protocol_message():
        """
        Parse a protocol message.
        
        Request body:
        {
            "protocol": "iec_104" or "mqtt",
            "data": "<base64-encoded message>" or raw bytes
        }
        
        Response:
        {
            "status": "success",
            "data": {
                "protocol": "iec_104",
                "parsed_data": {...}
            }
        }
        """
        try:
            body = request.json
            
            if not body:
                raise ValidationError("Request body is required")
            
            protocol = body.get("protocol", "").lower()
            if not protocol:
                raise ValidationError("protocol field is required")
            
            # Get raw data - can be base64 encoded or hex string
            data_input = body.get("data")
            if not data_input:
                raise ValidationError("data field is required")
            
            # Convert data to bytes
            if isinstance(data_input, str):
                try:
                    # Try hex first
                    raw_data = bytes.fromhex(data_input)
                except ValueError:
                    # Try base64
                    import base64
                    try:
                        raw_data = base64.b64decode(data_input)
                    except Exception:
                        raise ValidationError("data must be valid hex or base64 string")
            else:
                raw_data = bytes(data_input)
            
            # Parse message
            converter = get_protocol_converter()
            parsed_data = converter.parse_message(protocol, raw_data)
            
            response.status = 200
            return {
                "status": "success",
                "data": {
                    "protocol": protocol,
                    "parsed_data": parsed_data
                }
            }
        
        except ValidationError as e:
            response.status = 400
            return {
                "status": "error",
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": str(e),
                    "details": e.details if hasattr(e, 'details') else {}
                }
            }
        except ProtocolConversionError as e:
            response.status = 400
            return {
                "status": "error",
                "error": {
                    "code": "PROTOCOL_ERROR",
                    "message": str(e),
                    "details": e.details if hasattr(e, 'details') else {}
                }
            }
        except Exception as e:
            logger.error(f"Error parsing protocol message: {str(e)}", exc_info=True)
            response.status = 500
            return {
                "status": "error",
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Failed to parse protocol message"
                }
            }
    
    @app.post('/api/v1/protocol/encode')
    def encode_protocol_message():
        """
        Encode data to protocol format.
        
        Request body:
        {
            "protocol": "iec_104" or "mqtt",
            "data": {
                "protocol": "iec_104",
                "send_sequence": 0,
                "receive_sequence": 0,
                "asdu": {...}
            }
        }
        
        Response:
        {
            "status": "success",
            "data": {
                "protocol": "iec_104",
                "encoded_data": "<hex-encoded message>"
            }
        }
        """
        try:
            body = request.json
            
            if not body:
                raise ValidationError("Request body is required")
            
            protocol = body.get("protocol", "").lower()
            if not protocol:
                raise ValidationError("protocol field is required")
            
            data = body.get("data")
            if not data:
                raise ValidationError("data field is required")
            
            # Encode message
            converter = get_protocol_converter()
            encoded_data = converter.encode_message(protocol, data)
            
            response.status = 200
            return {
                "status": "success",
                "data": {
                    "protocol": protocol,
                    "encoded_data": encoded_data.hex()
                }
            }
        
        except ValidationError as e:
            response.status = 400
            return {
                "status": "error",
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": str(e),
                    "details": e.details if hasattr(e, 'details') else {}
                }
            }
        except ProtocolConversionError as e:
            response.status = 400
            return {
                "status": "error",
                "error": {
                    "code": "PROTOCOL_ERROR",
                    "message": str(e),
                    "details": e.details if hasattr(e, 'details') else {}
                }
            }
        except Exception as e:
            logger.error(f"Error encoding protocol message: {str(e)}", exc_info=True)
            response.status = 500
            return {
                "status": "error",
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Failed to encode protocol message"
                }
            }
    
    @app.post('/api/v1/protocol/convert')
    def convert_protocol_message():
        """
        Convert message between protocols.
        
        Request body:
        {
            "source_protocol": "iec_104",
            "target_protocol": "mqtt",
            "data": "<hex-encoded message>",
            "mapping_id": "optional-mapping-id"
        }
        
        Response:
        {
            "status": "success",
            "data": {
                "source_protocol": "iec_104",
                "target_protocol": "mqtt",
                "converted_data": "<hex-encoded message>"
            }
        }
        """
        try:
            body = request.json
            
            if not body:
                raise ValidationError("Request body is required")
            
            source_protocol = body.get("source_protocol", "").lower()
            if not source_protocol:
                raise ValidationError("source_protocol field is required")
            
            target_protocol = body.get("target_protocol", "").lower()
            if not target_protocol:
                raise ValidationError("target_protocol field is required")
            
            data_input = body.get("data")
            if not data_input:
                raise ValidationError("data field is required")
            
            # Convert data to bytes
            if isinstance(data_input, str):
                try:
                    raw_data = bytes.fromhex(data_input)
                except ValueError:
                    import base64
                    try:
                        raw_data = base64.b64decode(data_input)
                    except Exception:
                        raise ValidationError("data must be valid hex or base64 string")
            else:
                raw_data = bytes(data_input)
            
            # Get mapping if provided
            mapping = None
            mapping_id = body.get("mapping_id")
            if mapping_id:
                session = get_session()
                try:
                    mapping_obj = session.query(ProtocolMapping).filter(
                        ProtocolMapping.id == mapping_id
                    ).first()
                    if mapping_obj:
                        mapping = mapping_obj.mapping_rules
                finally:
                    session.close()
            
            # Convert message
            converter = get_protocol_converter()
            converted_data = converter.convert_message(
                source_protocol,
                target_protocol,
                raw_data,
                mapping
            )
            
            response.status = 200
            return {
                "status": "success",
                "data": {
                    "source_protocol": source_protocol,
                    "target_protocol": target_protocol,
                    "converted_data": converted_data.hex()
                }
            }
        
        except ValidationError as e:
            response.status = 400
            return {
                "status": "error",
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": str(e),
                    "details": e.details if hasattr(e, 'details') else {}
                }
            }
        except ProtocolConversionError as e:
            response.status = 400
            return {
                "status": "error",
                "error": {
                    "code": "PROTOCOL_ERROR",
                    "message": str(e),
                    "details": e.details if hasattr(e, 'details') else {}
                }
            }
        except Exception as e:
            logger.error(f"Error converting protocol message: {str(e)}", exc_info=True)
            response.status = 500
            return {
                "status": "error",
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Failed to convert protocol message"
                }
            }
    
    # ========================================================================
    # Protocol Mapping Management
    # ========================================================================
    
    @app.get('/api/v1/protocol/mappings')
    def get_protocol_mappings():
        """
        Get protocol mappings.
        
        Query parameters:
        - source_protocol: Filter by source protocol (optional)
        - target_protocol: Filter by target protocol (optional)
        
        Response:
        {
            "status": "success",
            "data": [
                {
                    "id": "mapping-1",
                    "source_protocol": "iec_104",
                    "target_protocol": "mqtt",
                    "mapping_rules": {...},
                    "is_active": true,
                    "created_at": "2026-02-16T10:30:00Z",
                    "updated_at": "2026-02-16T10:30:00Z"
                }
            ]
        }
        """
        try:
            source_protocol = request.query.get("source_protocol")
            target_protocol = request.query.get("target_protocol")
            
            converter = get_protocol_converter()
            mappings = converter.get_protocol_mappings(source_protocol, target_protocol)
            
            response.status = 200
            return {
                "status": "success",
                "data": mappings
            }
        
        except Exception as e:
            logger.error(f"Error getting protocol mappings: {str(e)}", exc_info=True)
            response.status = 500
            return {
                "status": "error",
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Failed to get protocol mappings"
                }
            }
    
    @app.post('/api/v1/protocol/mappings')
    def create_protocol_mapping():
        """
        Create a new protocol mapping.
        
        Request body:
        {
            "source_protocol": "iec_104",
            "target_protocol": "mqtt",
            "mapping_rules": {
                "field_mappings": {...},
                "transformations": {...}
            }
        }
        
        Response:
        {
            "status": "success",
            "data": {
                "id": "mapping-1",
                "source_protocol": "iec_104",
                "target_protocol": "mqtt",
                "mapping_rules": {...},
                "is_active": true,
                "created_at": "2026-02-16T10:30:00Z",
                "updated_at": "2026-02-16T10:30:00Z"
            }
        }
        """
        try:
            body = request.json
            
            if not body:
                raise ValidationError("Request body is required")
            
            source_protocol = body.get("source_protocol", "").lower()
            if not source_protocol:
                raise ValidationError("source_protocol field is required")
            
            target_protocol = body.get("target_protocol", "").lower()
            if not target_protocol:
                raise ValidationError("target_protocol field is required")
            
            mapping_rules = body.get("mapping_rules", {})
            
            # Generate mapping ID
            mapping_id = f"mapping-{uuid.uuid4().hex[:8]}"
            
            # Create mapping
            converter = get_protocol_converter()
            mapping = converter.create_protocol_mapping(
                mapping_id,
                source_protocol,
                target_protocol,
                mapping_rules
            )
            
            response.status = 201
            return {
                "status": "success",
                "data": mapping
            }
        
        except ValidationError as e:
            response.status = 400
            return {
                "status": "error",
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": str(e),
                    "details": e.details if hasattr(e, 'details') else {}
                }
            }
        except Exception as e:
            logger.error(f"Error creating protocol mapping: {str(e)}", exc_info=True)
            response.status = 500
            return {
                "status": "error",
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Failed to create protocol mapping"
                }
            }
    
    @app.put('/api/v1/protocol/mappings/<mapping_id>')
    def update_protocol_mapping(mapping_id):
        """
        Update a protocol mapping.
        
        Request body:
        {
            "mapping_rules": {...},
            "is_active": true
        }
        
        Response:
        {
            "status": "success",
            "data": {
                "id": "mapping-1",
                "source_protocol": "iec_104",
                "target_protocol": "mqtt",
                "mapping_rules": {...},
                "is_active": true,
                "created_at": "2026-02-16T10:30:00Z",
                "updated_at": "2026-02-16T10:30:00Z"
            }
        }
        """
        try:
            body = request.json
            
            if not body:
                raise ValidationError("Request body is required")
            
            # Update mapping
            converter = get_protocol_converter()
            mapping = converter.update_protocol_mapping(mapping_id, **body)
            
            response.status = 200
            return {
                "status": "success",
                "data": mapping
            }
        
        except ValidationError as e:
            response.status = 400
            return {
                "status": "error",
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": str(e),
                    "details": e.details if hasattr(e, 'details') else {}
                }
            }
        except Exception as e:
            logger.error(f"Error updating protocol mapping: {str(e)}", exc_info=True)
            response.status = 500
            return {
                "status": "error",
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Failed to update protocol mapping"
                }
            }
    
    @app.delete('/api/v1/protocol/mappings/<mapping_id>')
    def delete_protocol_mapping(mapping_id):
        """
        Delete a protocol mapping.
        
        Response:
        {
            "status": "success",
            "data": {
                "id": "mapping-1",
                "deleted": true
            }
        }
        """
        try:
            # Delete mapping
            converter = get_protocol_converter()
            converter.delete_protocol_mapping(mapping_id)
            
            response.status = 200
            return {
                "status": "success",
                "data": {
                    "id": mapping_id,
                    "deleted": True
                }
            }
        
        except ValidationError as e:
            response.status = 404
            return {
                "status": "error",
                "error": {
                    "code": "NOT_FOUND",
                    "message": str(e),
                    "details": e.details if hasattr(e, 'details') else {}
                }
            }
        except Exception as e:
            logger.error(f"Error deleting protocol mapping: {str(e)}", exc_info=True)
            response.status = 500
            return {
                "status": "error",
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Failed to delete protocol mapping"
                }
            }
