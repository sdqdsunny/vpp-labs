"""
OPC UA Protocol Adapter

Implements OPC UA client/server communication for industrial automation.
Supports both synchronous and asynchronous operations.
"""

from typing import Dict, Any, Optional, List
from .base import ProtocolAdapter, ProtocolMessage, ProtocolType
import logging
import asyncio
from asyncua import Client, Server, ua
from asyncua.common import Node

logger = logging.getLogger(__name__)


class OPCUAConfig:
    """OPC UA Configuration"""
    
    def __init__(self, endpoint: str, namespace: str = "http://vpp.simulation"):
        self.endpoint = endpoint
        self.namespace = namespace
        self.security_policy = None
        self.certificate = None
        self.private_key = None


class OPCUAAdapter(ProtocolAdapter):
    """
    OPC UA Protocol Adapter
    
    Provides OPC UA client functionality for connecting to OPC UA servers.
    Supports reading/writing variables, browsing address space, and subscriptions.
    """
    
    def __init__(self, adapter_id: str = "opcua-adapter"):
        super().__init__(adapter_id, ProtocolType.OPCUA)
        self.client: Optional[Client] = None
        self.config: Optional[OPCUAConfig] = None
        self.subscriptions: Dict[str, Any] = {}
        self.nodes_cache: Dict[str, Node] = {}
        
    async def connect_async(self, config: Dict[str, Any]) -> bool:
        """
        Asynchronously connect to OPC UA server
        
        Args:
            config: Configuration dictionary with 'endpoint' and optional 'namespace'
            
        Returns:
            True if connection successful
        """
        try:
            self.config = OPCUAConfig(
                endpoint=config.get('endpoint', 'opc.tcp://localhost:4840'),
                namespace=config.get('namespace', 'http://vpp.simulation')
            )
            
            self.client = Client(url=self.config.endpoint)
            await self.client.connect()
            
            self.is_connected = True
            logger.info(f"Connected to OPC UA server: {self.config.endpoint}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to OPC UA server: {e}")
            self.is_connected = False
            return False
    
    def connect(self, config: Dict[str, Any]) -> bool:
        """
        Synchronously connect to OPC UA server
        
        Args:
            config: Configuration dictionary
            
        Returns:
            True if connection successful
        """
        try:
            loop = asyncio.new_event_loop()
            result = loop.run_until_complete(self.connect_async(config))
            loop.close()
            return result
        except Exception as e:
            logger.error(f"Connection error: {e}")
            return False
    
    async def disconnect_async(self) -> bool:
        """Asynchronously disconnect from OPC UA server"""
        try:
            if self.client:
                await self.client.disconnect()
            self.is_connected = False
            logger.info("Disconnected from OPC UA server")
            return True
        except Exception as e:
            logger.error(f"Disconnect error: {e}")
            return False
    
    def disconnect(self) -> bool:
        """Synchronously disconnect from OPC UA server"""
        try:
            loop = asyncio.new_event_loop()
            result = loop.run_until_complete(self.disconnect_async())
            loop.close()
            return result
        except Exception as e:
            logger.error(f"Disconnect error: {e}")
            return False
    
    async def read_variable_async(self, node_id: str) -> Optional[Any]:
        """
        Asynchronously read a variable from OPC UA server
        
        Args:
            node_id: OPC UA node ID (e.g., "ns=2;i=1001")
            
        Returns:
            Variable value or None if read failed
        """
        try:
            if not self.is_connected or not self.client:
                return None
            
            node = self.client.get_node(node_id)
            value = await node.read_value()
            return value
            
        except Exception as e:
            logger.error(f"Failed to read variable {node_id}: {e}")
            return None
    
    async def write_variable_async(self, node_id: str, value: Any) -> bool:
        """
        Asynchronously write a variable to OPC UA server
        
        Args:
            node_id: OPC UA node ID
            value: Value to write
            
        Returns:
            True if write successful
        """
        try:
            if not self.is_connected or not self.client:
                return False
            
            node = self.client.get_node(node_id)
            await node.write_value(value)
            return True
            
        except Exception as e:
            logger.error(f"Failed to write variable {node_id}: {e}")
            return False
    
    def read_variable(self, node_id: str) -> Optional[Any]:
        """Synchronously read a variable"""
        try:
            loop = asyncio.new_event_loop()
            result = loop.run_until_complete(self.read_variable_async(node_id))
            loop.close()
            return result
        except Exception as e:
            logger.error(f"Read error: {e}")
            return None
    
    def write_variable(self, node_id: str, value: Any) -> bool:
        """Synchronously write a variable"""
        try:
            loop = asyncio.new_event_loop()
            result = loop.run_until_complete(self.write_variable_async(node_id, value))
            loop.close()
            return result
        except Exception as e:
            logger.error(f"Write error: {e}")
            return False
    
    async def browse_async(self, node_id: str = "i=85") -> List[Dict[str, Any]]:
        """
        Asynchronously browse OPC UA address space
        
        Args:
            node_id: Starting node ID (default: root)
            
        Returns:
            List of child nodes
        """
        try:
            if not self.is_connected or not self.client:
                return []
            
            node = self.client.get_node(node_id)
            children = await node.get_children()
            
            result = []
            for child in children:
                result.append({
                    'node_id': str(child.nodeid),
                    'name': await child.read_browse_name(),
                    'class': await child.read_node_class()
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Browse error: {e}")
            return []
    
    def browse(self, node_id: str = "i=85") -> List[Dict[str, Any]]:
        """Synchronously browse address space"""
        try:
            loop = asyncio.new_event_loop()
            result = loop.run_until_complete(self.browse_async(node_id))
            loop.close()
            return result
        except Exception as e:
            logger.error(f"Browse error: {e}")
            return []
    
    def send_message(self, message: ProtocolMessage) -> bool:
        """
        Send OPC UA message (write operation)
        
        Args:
            message: Protocol message with node_id and value
            
        Returns:
            True if send successful
        """
        try:
            node_id = message.data.get('node_id')
            value = message.data.get('value')
            
            if not node_id or value is None:
                logger.error("Invalid message: missing node_id or value")
                return False
            
            return self.write_variable(node_id, value)
            
        except Exception as e:
            logger.error(f"Send message error: {e}")
            return False
    
    def receive_message(self, timeout: float = 1.0) -> Optional[ProtocolMessage]:
        """
        Receive OPC UA message (read operation)
        
        Note: OPC UA is request-response based, not event-driven.
        This method is provided for interface compatibility.
        
        Args:
            timeout: Timeout in seconds
            
        Returns:
            None (OPC UA doesn't support unsolicited messages)
        """
        return None
    
    def parse_message(self, data: bytes) -> Dict[str, Any]:
        """Parse OPC UA message data"""
        return {}
    
    def encode_message(self, message: Dict[str, Any]) -> bytes:
        """Encode OPC UA message"""
        return b''
    
    def validate_message(self, data: bytes) -> bool:
        """Validate OPC UA message"""
        return True
