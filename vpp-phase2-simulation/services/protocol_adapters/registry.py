"""
Protocol Registry

Manages registration and discovery of protocol adapters.
"""

from typing import Dict, Type, List, Optional
from .base import ProtocolAdapter, ProtocolType
import logging

logger = logging.getLogger(__name__)


class ProtocolRegistry:
    """
    Registry for protocol adapters.
    
    Provides centralized management of protocol adapter implementations.
    """

    _adapters: Dict[str, Type[ProtocolAdapter]] = {}
    _instances: Dict[str, ProtocolAdapter] = {}

    @classmethod
    def register(
        cls,
        protocol_name: str,
        adapter_class: Type[ProtocolAdapter],
    ) -> None:
        """
        Register a protocol adapter.
        
        Args:
            protocol_name: Name of the protocol (e.g., "iec61850", "modbus")
            adapter_class: Adapter class to register
            
        Raises:
            ValueError: If protocol already registered
        """
        if protocol_name in cls._adapters:
            raise ValueError(f"Protocol already registered: {protocol_name}")

        cls._adapters[protocol_name] = adapter_class
        logger.info(f"Registered protocol adapter: {protocol_name}")

    @classmethod
    def unregister(cls, protocol_name: str) -> None:
        """
        Unregister a protocol adapter.
        
        Args:
            protocol_name: Name of the protocol to unregister
        """
        if protocol_name in cls._adapters:
            del cls._adapters[protocol_name]
            logger.info(f"Unregistered protocol adapter: {protocol_name}")

    @classmethod
    def get_adapter_class(cls, protocol_name: str) -> Type[ProtocolAdapter]:
        """
        Get adapter class for protocol.
        
        Args:
            protocol_name: Name of the protocol
            
        Returns:
            Adapter class
            
        Raises:
            ValueError: If protocol not registered
        """
        if protocol_name not in cls._adapters:
            raise ValueError(f"Unknown protocol: {protocol_name}")

        return cls._adapters[protocol_name]

    @classmethod
    def create_adapter(
        cls,
        protocol_name: str,
        adapter_id: str,
    ) -> ProtocolAdapter:
        """
        Create adapter instance for protocol.
        
        Args:
            protocol_name: Name of the protocol
            adapter_id: Unique identifier for adapter instance
            
        Returns:
            Adapter instance
            
        Raises:
            ValueError: If protocol not registered
        """
        adapter_class = cls.get_adapter_class(protocol_name)
        adapter = adapter_class(adapter_id)
        cls._instances[adapter_id] = adapter
        logger.info(f"Created adapter instance: {adapter_id} for protocol: {protocol_name}")
        return adapter

    @classmethod
    def get_adapter(cls, adapter_id: str) -> Optional[ProtocolAdapter]:
        """
        Get adapter instance by ID.
        
        Args:
            adapter_id: Adapter instance ID
            
        Returns:
            Adapter instance or None if not found
        """
        return cls._instances.get(adapter_id)

    @classmethod
    def list_protocols(cls) -> List[str]:
        """
        List all registered protocols.
        
        Returns:
            List of protocol names
        """
        return list(cls._adapters.keys())

    @classmethod
    def list_adapters(cls) -> List[str]:
        """
        List all adapter instances.
        
        Returns:
            List of adapter IDs
        """
        return list(cls._instances.keys())

    @classmethod
    def is_protocol_supported(cls, protocol_name: str) -> bool:
        """
        Check if protocol is supported.
        
        Args:
            protocol_name: Name of the protocol
            
        Returns:
            True if protocol is registered, False otherwise
        """
        return protocol_name in cls._adapters

    @classmethod
    def remove_adapter(cls, adapter_id: str) -> None:
        """
        Remove adapter instance.
        
        Args:
            adapter_id: Adapter instance ID
        """
        if adapter_id in cls._instances:
            del cls._instances[adapter_id]
            logger.info(f"Removed adapter instance: {adapter_id}")

    @classmethod
    def clear(cls) -> None:
        """Clear all registered adapters and instances"""
        cls._adapters.clear()
        cls._instances.clear()
        logger.info("Cleared protocol registry")

    @classmethod
    def get_status(cls) -> Dict[str, any]:
        """
        Get registry status.
        
        Returns:
            Status dictionary
        """
        return {
            "registered_protocols": cls.list_protocols(),
            "active_adapters": cls.list_adapters(),
            "total_protocols": len(cls._adapters),
            "total_instances": len(cls._instances),
        }
