"""
Protocol Converter Service

Handles protocol parsing, encoding, conversion, and validation.
Supports multiple protocol adapters (IEC 104, MQTT, etc.)
"""

import logging
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
from utils.database import get_session
from models.protocol_mapping import ProtocolMapping
from utils.errors import ProtocolConversionError, ValidationError

logger = logging.getLogger(__name__)


class ProtocolAdapter(ABC):
    """
    Abstract base class for protocol adapters.
    Each protocol (IEC 104, MQTT, etc.) implements this interface.
    """
    
    @abstractmethod
    def parse_message(self, raw_data: bytes) -> Dict[str, Any]:
        """
        Parse raw protocol message into internal data model.
        
        Args:
            raw_data: Raw protocol message bytes
            
        Returns:
            Dictionary with parsed data
            
        Raises:
            ProtocolConversionError: If parsing fails
        """
        pass
    
    @abstractmethod
    def encode_message(self, data: Dict[str, Any]) -> bytes:
        """
        Encode internal data model to protocol format.
        
        Args:
            data: Internal data model dictionary
            
        Returns:
            Raw protocol message bytes
            
        Raises:
            ProtocolConversionError: If encoding fails
        """
        pass
    
    @abstractmethod
    def validate_message(self, data: Dict[str, Any]) -> bool:
        """
        Validate data against protocol specification.
        
        Args:
            data: Data to validate
            
        Returns:
            True if valid, raises exception if invalid
            
        Raises:
            ValidationError: If validation fails
        """
        pass


class ProtocolConverter:
    """
    Main protocol converter service.
    Manages protocol adapters and coordinates conversion operations.
    """
    
    def __init__(self):
        """Initialize protocol converter with available adapters"""
        self.adapters: Dict[str, ProtocolAdapter] = {}
        self._register_adapters()
    
    def _register_adapters(self):
        """Register all available protocol adapters"""
        from services.protocol_adapters import IEC104Adapter, MQTTAdapter
        
        self.register_adapter("iec_104", IEC104Adapter())
        self.register_adapter("mqtt", MQTTAdapter())
    
    def register_adapter(self, protocol_name: str, adapter: ProtocolAdapter):
        """
        Register a protocol adapter.
        
        Args:
            protocol_name: Name of the protocol (e.g., 'iec_104', 'mqtt')
            adapter: Instance of ProtocolAdapter
        """
        if not isinstance(adapter, ProtocolAdapter):
            raise ValueError(f"Adapter must be instance of ProtocolAdapter")
        self.adapters[protocol_name.lower()] = adapter
        logger.info(f"Registered protocol adapter: {protocol_name}")
    
    def parse_message(self, protocol: str, raw_data: bytes) -> Dict[str, Any]:
        """
        Parse a protocol message.
        
        Args:
            protocol: Protocol name (e.g., 'iec_104', 'mqtt')
            raw_data: Raw protocol message bytes
            
        Returns:
            Parsed data as dictionary
            
        Raises:
            ProtocolConversionError: If protocol not supported or parsing fails
            ValidationError: If message structure is invalid
        """
        protocol = protocol.lower()
        
        if protocol not in self.adapters:
            raise ProtocolConversionError(
                f"Protocol '{protocol}' not supported",
                details={"supported_protocols": list(self.adapters.keys())}
            )
        
        try:
            adapter = self.adapters[protocol]
            parsed_data = adapter.parse_message(raw_data)
            logger.debug(f"Successfully parsed {protocol} message")
            return parsed_data
        except Exception as e:
            logger.error(f"Failed to parse {protocol} message: {str(e)}")
            raise ProtocolConversionError(
                f"Failed to parse {protocol} message: {str(e)}",
                details={"protocol": protocol, "error": str(e)}
            )
    
    def encode_message(self, protocol: str, data: Dict[str, Any]) -> bytes:
        """
        Encode data to protocol format.
        
        Args:
            protocol: Protocol name (e.g., 'iec_104', 'mqtt')
            data: Data to encode
            
        Returns:
            Encoded message as bytes
            
        Raises:
            ProtocolConversionError: If protocol not supported or encoding fails
            ValidationError: If data is invalid
        """
        protocol = protocol.lower()
        
        if protocol not in self.adapters:
            raise ProtocolConversionError(
                f"Protocol '{protocol}' not supported",
                details={"supported_protocols": list(self.adapters.keys())}
            )
        
        try:
            adapter = self.adapters[protocol]
            # Validate before encoding
            adapter.validate_message(data)
            encoded_data = adapter.encode_message(data)
            logger.debug(f"Successfully encoded {protocol} message")
            return encoded_data
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Failed to encode {protocol} message: {str(e)}")
            raise ProtocolConversionError(
                f"Failed to encode {protocol} message: {str(e)}",
                details={"protocol": protocol, "error": str(e)}
            )
    
    def validate_message(self, protocol: str, data: Dict[str, Any]) -> bool:
        """
        Validate data against protocol specification.
        
        Args:
            protocol: Protocol name (e.g., 'iec_104', 'mqtt')
            data: Data to validate
            
        Returns:
            True if valid
            
        Raises:
            ProtocolConversionError: If protocol not supported
            ValidationError: If validation fails
        """
        protocol = protocol.lower()
        
        if protocol not in self.adapters:
            raise ProtocolConversionError(
                f"Protocol '{protocol}' not supported",
                details={"supported_protocols": list(self.adapters.keys())}
            )
        
        try:
            adapter = self.adapters[protocol]
            return adapter.validate_message(data)
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Failed to validate {protocol} message: {str(e)}")
            raise ValidationError(
                f"Failed to validate {protocol} message: {str(e)}",
                details={"protocol": protocol, "error": str(e)}
            )
    
    def convert_message(
        self,
        source_protocol: str,
        target_protocol: str,
        raw_data: bytes,
        mapping: Optional[Dict[str, Any]] = None
    ) -> bytes:
        """
        Convert message from one protocol to another.
        
        Args:
            source_protocol: Source protocol name
            target_protocol: Target protocol name
            raw_data: Raw message in source protocol
            mapping: Optional mapping rules for conversion
            
        Returns:
            Encoded message in target protocol
            
        Raises:
            ProtocolConversionError: If conversion fails
        """
        try:
            # Parse from source protocol
            parsed_data = self.parse_message(source_protocol, raw_data)
            
            # Apply mapping if provided
            if mapping:
                parsed_data = self._apply_mapping(parsed_data, mapping)
            
            # Encode to target protocol
            encoded_data = self.encode_message(target_protocol, parsed_data)
            
            logger.info(
                f"Successfully converted message from {source_protocol} to {target_protocol}"
            )
            return encoded_data
        except Exception as e:
            logger.error(
                f"Failed to convert from {source_protocol} to {target_protocol}: {str(e)}"
            )
            raise ProtocolConversionError(
                f"Failed to convert from {source_protocol} to {target_protocol}: {str(e)}",
                details={
                    "source_protocol": source_protocol,
                    "target_protocol": target_protocol,
                    "error": str(e)
                }
            )
    
    def _apply_mapping(self, data: Dict[str, Any], mapping: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply protocol mapping rules to data.
        
        Args:
            data: Parsed data
            mapping: Mapping rules
            
        Returns:
            Mapped data
        """
        # Simple mapping implementation - can be extended
        mapped_data = data.copy()
        
        if "field_mappings" in mapping:
            for source_field, target_field in mapping["field_mappings"].items():
                if source_field in mapped_data:
                    mapped_data[target_field] = mapped_data.pop(source_field)
        
        if "transformations" in mapping:
            for field, transform in mapping["transformations"].items():
                if field in mapped_data:
                    # Apply transformation function
                    if callable(transform):
                        mapped_data[field] = transform(mapped_data[field])
        
        return mapped_data
    
    def get_protocol_mappings(
        self,
        source_protocol: Optional[str] = None,
        target_protocol: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get protocol mappings from database.
        
        Args:
            source_protocol: Filter by source protocol (optional)
            target_protocol: Filter by target protocol (optional)
            
        Returns:
            List of protocol mappings
        """
        session = get_session()
        try:
            query = session.query(ProtocolMapping)
            
            if source_protocol:
                query = query.filter(ProtocolMapping.source_protocol == source_protocol)
            
            if target_protocol:
                query = query.filter(ProtocolMapping.target_protocol == target_protocol)
            
            mappings = query.all()
            return [m.to_dict() for m in mappings]
        finally:
            session.close()
    
    def create_protocol_mapping(
        self,
        mapping_id: str,
        source_protocol: str,
        target_protocol: str,
        mapping_rules: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a new protocol mapping.
        
        Args:
            mapping_id: Unique mapping identifier
            source_protocol: Source protocol name
            target_protocol: Target protocol name
            mapping_rules: Mapping rules configuration
            
        Returns:
            Created mapping as dictionary
            
        Raises:
            ValidationError: If mapping data is invalid
        """
        session = get_session()
        try:
            # Check if mapping already exists
            existing = session.query(ProtocolMapping).filter(
                ProtocolMapping.id == mapping_id
            ).first()
            
            if existing:
                raise ValidationError(
                    f"Protocol mapping with ID '{mapping_id}' already exists"
                )
            
            # Create new mapping
            mapping = ProtocolMapping(
                id=mapping_id,
                source_protocol=source_protocol,
                target_protocol=target_protocol,
                mapping_rules=mapping_rules,
                is_active=True
            )
            
            session.add(mapping)
            session.commit()
            
            logger.info(f"Created protocol mapping: {mapping_id}")
            return mapping.to_dict()
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to create protocol mapping: {str(e)}")
            raise
        finally:
            session.close()
    
    def update_protocol_mapping(
        self,
        mapping_id: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Update an existing protocol mapping.
        
        Args:
            mapping_id: Mapping identifier
            **kwargs: Fields to update (mapping_rules, is_active, etc.)
            
        Returns:
            Updated mapping as dictionary
            
        Raises:
            ValidationError: If mapping not found
        """
        session = get_session()
        try:
            mapping = session.query(ProtocolMapping).filter(
                ProtocolMapping.id == mapping_id
            ).first()
            
            if not mapping:
                raise ValidationError(f"Protocol mapping '{mapping_id}' not found")
            
            # Update allowed fields
            allowed_fields = {'mapping_rules', 'is_active'}
            for field, value in kwargs.items():
                if field in allowed_fields:
                    setattr(mapping, field, value)
            
            session.commit()
            logger.info(f"Updated protocol mapping: {mapping_id}")
            return mapping.to_dict()
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to update protocol mapping: {str(e)}")
            raise
        finally:
            session.close()
    
    def delete_protocol_mapping(self, mapping_id: str) -> bool:
        """
        Delete a protocol mapping.
        
        Args:
            mapping_id: Mapping identifier
            
        Returns:
            True if deleted successfully
            
        Raises:
            ValidationError: If mapping not found
        """
        session = get_session()
        try:
            mapping = session.query(ProtocolMapping).filter(
                ProtocolMapping.id == mapping_id
            ).first()
            
            if not mapping:
                raise ValidationError(f"Protocol mapping '{mapping_id}' not found")
            
            session.delete(mapping)
            session.commit()
            
            logger.info(f"Deleted protocol mapping: {mapping_id}")
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to delete protocol mapping: {str(e)}")
            raise
        finally:
            session.close()


# Global protocol converter instance
_protocol_converter = None


def get_protocol_converter() -> ProtocolConverter:
    """Get or create the global protocol converter instance"""
    global _protocol_converter
    if _protocol_converter is None:
        _protocol_converter = ProtocolConverter()
    return _protocol_converter
