"""
Protocol Management Service

Manages protocol adapters, mappings, and conversions for VCC integration.
Provides unified interface for protocol operations.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from services.protocol_adapters.registry import ProtocolRegistry
from services.protocol_adapters.mapper import ProtocolMessageMapper
from services.protocol_adapters.protocol_mappings import PROTOCOL_MAPPINGS
from services.protocol_adapters.transformers import TRANSFORMERS
from services.protocol_adapters.validators import VALIDATORS
from services.protocol_adapters.base import ProtocolMessage, ProtocolException

logger = logging.getLogger(__name__)


class ProtocolManagementService:
    """
    Protocol Management Service
    
    Manages protocol adapters, message mappings, and conversions.
    Provides unified interface for VCC integration.
    """
    
    def __init__(self):
        """Initialize protocol management service"""
        self.registry = ProtocolRegistry()
        self.mapper = ProtocolMessageMapper()
        self._register_adapters()
        self._initialize_mappings()
        logger.info("Protocol Management Service initialized")
    
    def _register_adapters(self) -> None:
        """Register all protocol adapters"""
        try:
            from services.protocol_adapters.iec61850_adapter import IEC61850Adapter
            self.registry.register("iec61850", IEC61850Adapter)
        except Exception as e:
            logger.warning(f"Could not register IEC61850 adapter: {e}")
        
        try:
            from services.protocol_adapters.modbus_adapter import ModbusAdapter
            self.registry.register("modbus", ModbusAdapter)
        except Exception as e:
            logger.warning(f"Could not register Modbus adapter: {e}")
        
        try:
            from services.protocol_adapters.dnp3_adapter import DNP3Adapter
            self.registry.register("dnp3", DNP3Adapter)
        except Exception as e:
            logger.warning(f"Could not register DNP3 adapter: {e}")
        
        try:
            from services.protocol_adapters.mqtt_adapter import MQTTAdapter
            self.registry.register("mqtt", MQTTAdapter)
        except Exception as e:
            logger.warning(f"Could not register MQTT adapter: {e}")
        
        logger.info(f"Registered {len(self.registry.list_protocols())} protocol adapters")
    
    def _initialize_mappings(self) -> None:
        """Initialize all mappings, transformers, and validators"""
        # Register all transformers
        for name, transformer in TRANSFORMERS.items():
            self.mapper.register_transformer(name, transformer)
        
        # Register all validators
        for name, validator in VALIDATORS.items():
            self.mapper.register_validator(name, validator)
        
        # Register all mappings
        for mapping_key, rules in PROTOCOL_MAPPINGS.items():
            source, target = mapping_key.split("->")
            self.mapper.register_mapping(source, target, rules)
        
        logger.info(
            f"Initialized {len(TRANSFORMERS)} transformers, "
            f"{len(VALIDATORS)} validators, "
            f"{len(PROTOCOL_MAPPINGS)} mappings"
        )
    
    # ========================================================================
    # Adapter Management
    # ========================================================================
    
    def create_adapter(
        self,
        protocol_name: str,
        adapter_id: str
    ) -> Dict[str, Any]:
        """
        Create protocol adapter instance.
        
        Args:
            protocol_name: Protocol name (iec61850, modbus, dnp3, mqtt)
            adapter_id: Unique adapter identifier
            
        Returns:
            Adapter information dictionary
            
        Raises:
            ProtocolException: If adapter creation fails
        """
        try:
            adapter = self.registry.create_adapter(protocol_name, adapter_id)
            logger.info(f"Adapter created: {adapter_id} ({protocol_name})")
            return {
                "adapter_id": adapter_id,
                "protocol": protocol_name,
                "status": "created",
                "timestamp": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Failed to create adapter: {e}")
            raise ProtocolException(f"Failed to create adapter: {e}")
    
    def get_adapter(self, adapter_id: str) -> Optional[Dict[str, Any]]:
        """
        Get adapter by ID.
        
        Args:
            adapter_id: Adapter identifier
            
        Returns:
            Adapter information or None if not found
        """
        adapter = self.registry.get_adapter(adapter_id)
        if adapter:
            return {
                "adapter_id": adapter_id,
                "protocol": adapter.protocol_type.value,
                "status": adapter.get_status(),
            }
        return None
    
    def list_adapters(self) -> List[Dict[str, Any]]:
        """
        List all active adapters.
        
        Returns:
            List of adapter information dictionaries
        """
        adapters = []
        for adapter_id in self.registry.list_adapters():
            adapter = self.registry.get_adapter(adapter_id)
            if adapter:
                adapters.append({
                    "adapter_id": adapter_id,
                    "protocol": adapter.protocol_type.value,
                    "status": adapter.get_status(),
                })
        return adapters
    
    def remove_adapter(self, adapter_id: str) -> bool:
        """
        Remove adapter instance.
        
        Args:
            adapter_id: Adapter identifier
            
        Returns:
            True if removed, False if not found
        """
        adapter = self.registry.get_adapter(adapter_id)
        if adapter:
            if adapter.is_connected:
                adapter.disconnect()
            self.registry.remove_adapter(adapter_id)
            logger.info(f"Adapter removed: {adapter_id}")
            return True
        return False
    
    def get_registry_status(self) -> Dict[str, Any]:
        """
        Get protocol registry status.
        
        Returns:
            Registry status information
        """
        status = self.registry.get_status()
        status["timestamp"] = datetime.utcnow().isoformat()
        return status
    
    # ========================================================================
    # Message Mapping and Conversion
    # ========================================================================
    
    def map_message(
        self,
        source_protocol: str,
        target_protocol: str,
        message: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Map message from source protocol to target protocol.
        
        Args:
            source_protocol: Source protocol name
            target_protocol: Target protocol name
            message: Message data
            
        Returns:
            Mapped message
            
        Raises:
            ProtocolException: If mapping fails
        """
        try:
            mapped = self.mapper.map_message(
                source_protocol,
                target_protocol,
                message
            )
            logger.info(
                f"Message mapped: {source_protocol} → {target_protocol}"
            )
            return mapped
        except Exception as e:
            logger.error(f"Message mapping failed: {e}")
            raise ProtocolException(f"Message mapping failed: {e}")
    
    def validate_message(
        self,
        validator_name: str,
        message: Dict[str, Any]
    ) -> bool:
        """
        Validate message using specified validator.
        
        Args:
            validator_name: Validator name
            message: Message to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            is_valid = self.mapper.validate_message(validator_name, message)
            if not is_valid:
                logger.warning(f"Message validation failed: {validator_name}")
            return is_valid
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return False
    
    def transform_data(
        self,
        transformer_name: str,
        data: Dict[str, Any]
    ) -> Any:
        """
        Transform data using specified transformer.
        
        Args:
            transformer_name: Transformer name
            data: Data to transform
            
        Returns:
            Transformed data
            
        Raises:
            ProtocolException: If transformation fails
        """
        try:
            result = self.mapper.transform_data(transformer_name, data)
            return result
        except Exception as e:
            logger.error(f"Data transformation failed: {e}")
            raise ProtocolException(f"Data transformation failed: {e}")
    
    def get_mapper_info(self) -> Dict[str, Any]:
        """
        Get mapper information.
        
        Returns:
            Mapper information dictionary
        """
        info = self.mapper.get_mapping_info()
        return {
            "mappings": info["mappings"],
            "transformers": info["transformers"],
            "validators": info["validators"],
            "total_mappings": info["total_mappings"],
            "total_transformers": info["total_transformers"],
            "total_validators": info["total_validators"],
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    # ========================================================================
    # Protocol Information
    # ========================================================================
    
    def list_supported_protocols(self) -> List[str]:
        """
        List all supported protocols.
        
        Returns:
            List of protocol names
        """
        return self.registry.list_protocols()
    
    def is_protocol_supported(self, protocol_name: str) -> bool:
        """
        Check if protocol is supported.
        
        Args:
            protocol_name: Protocol name
            
        Returns:
            True if supported, False otherwise
        """
        return self.registry.is_protocol_supported(protocol_name)
    
    def get_protocol_info(self, protocol_name: str) -> Optional[Dict[str, Any]]:
        """
        Get protocol information.
        
        Args:
            protocol_name: Protocol name
            
        Returns:
            Protocol information or None if not found
        """
        if not self.is_protocol_supported(protocol_name):
            return None
        
        adapter_class = self.registry.get_adapter_class(protocol_name)
        if not adapter_class:
            return None
        
        return {
            "protocol_name": protocol_name,
            "adapter_class": adapter_class.__name__,
            "supported": True,
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    # ========================================================================
    # Bidirectional Conversion
    # ========================================================================
    
    def convert_iec61850_to_modbus(
        self,
        message: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Convert IEC 61850 message to Modbus format"""
        return self.map_message("iec61850", "modbus", message)
    
    def convert_modbus_to_iec61850(
        self,
        message: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Convert Modbus message to IEC 61850 format"""
        return self.map_message("modbus", "iec61850", message)
    
    def convert_iec61850_to_dnp3(
        self,
        message: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Convert IEC 61850 message to DNP3 format"""
        return self.map_message("iec61850", "dnp3", message)
    
    def convert_dnp3_to_iec61850(
        self,
        message: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Convert DNP3 message to IEC 61850 format"""
        return self.map_message("dnp3", "iec61850", message)
    
    def convert_iec61850_to_mqtt(
        self,
        message: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Convert IEC 61850 message to MQTT format"""
        return self.map_message("iec61850", "mqtt", message)
    
    def convert_mqtt_to_iec61850(
        self,
        message: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Convert MQTT message to IEC 61850 format"""
        return self.map_message("mqtt", "iec61850", message)
    
    def convert_modbus_to_dnp3(
        self,
        message: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Convert Modbus message to DNP3 format"""
        return self.map_message("modbus", "dnp3", message)
    
    def convert_dnp3_to_modbus(
        self,
        message: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Convert DNP3 message to Modbus format"""
        return self.map_message("dnp3", "modbus", message)
    
    def convert_modbus_to_mqtt(
        self,
        message: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Convert Modbus message to MQTT format"""
        return self.map_message("modbus", "mqtt", message)
    
    def convert_mqtt_to_modbus(
        self,
        message: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Convert MQTT message to Modbus format"""
        return self.map_message("mqtt", "modbus", message)
    
    def convert_dnp3_to_mqtt(
        self,
        message: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Convert DNP3 message to MQTT format"""
        return self.map_message("dnp3", "mqtt", message)
    
    def convert_mqtt_to_dnp3(
        self,
        message: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Convert MQTT message to DNP3 format"""
        return self.map_message("mqtt", "dnp3", message)


# Global instance
_protocol_management_service: Optional[ProtocolManagementService] = None


def get_protocol_management_service() -> ProtocolManagementService:
    """Get or create protocol management service singleton"""
    global _protocol_management_service
    if _protocol_management_service is None:
        _protocol_management_service = ProtocolManagementService()
    return _protocol_management_service
