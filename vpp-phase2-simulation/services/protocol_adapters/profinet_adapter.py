"""
Profinet Protocol Adapter

Implements Profinet communication for Siemens PLC and industrial automation.
Supports reading/writing PLC variables and device communication.
"""

from typing import Dict, Any, Optional, List
from .base import ProtocolAdapter, ProtocolMessage, ProtocolType
import logging
from pycomm3 import CIPDriver

logger = logging.getLogger(__name__)


class ProfinetConfig:
    """Profinet Configuration"""
    
    def __init__(self, ip_address: str, port: int = 2000, slot: int = 1):
        self.ip_address = ip_address
        self.port = port
        self.slot = slot
        self.timeout = 10


class ProfinetAdapter(ProtocolAdapter):
    """
    Profinet Protocol Adapter
    
    Provides Profinet communication for Siemens industrial automation systems.
    Supports reading/writing variables from PLCs via Profinet protocol.
    """
    
    def __init__(self, adapter_id: str = "profinet-adapter"):
        super().__init__(adapter_id, ProtocolType.PROFINET)
        self.driver: Optional[CIPDriver] = None
        self.config: Optional[ProfinetConfig] = None
        self.variables_cache: Dict[str, Any] = {}
        
    def connect(self, config: Dict[str, Any]) -> bool:
        """
        Connect to Profinet device (PLC)
        
        Args:
            config: Configuration with 'ip_address', 'port', 'slot'
            
        Returns:
            True if connection successful
        """
        try:
            self.config = ProfinetConfig(
                ip_address=config.get('ip_address', '192.168.1.100'),
                port=config.get('port', 2000),
                slot=config.get('slot', 1)
            )
            
            # Create CIP driver for Profinet communication
            self.driver = CIPDriver(
                ip=self.config.ip_address,
                port=self.config.port,
                slot=self.config.slot
            )
            
            # Test connection
            if self.driver.open():
                self.is_connected = True
                logger.info(f"Connected to Profinet device: {self.config.ip_address}:{self.config.port}")
                return True
            else:
                logger.error("Failed to open Profinet connection")
                return False
                
        except Exception as e:
            logger.error(f"Failed to connect to Profinet device: {e}")
            self.is_connected = False
            return False
    
    def disconnect(self) -> bool:
        """Disconnect from Profinet device"""
        try:
            if self.driver:
                self.driver.close()
            self.is_connected = False
            logger.info("Disconnected from Profinet device")
            return True
        except Exception as e:
            logger.error(f"Disconnect error: {e}")
            return False
    
    def read_variable(self, tag_name: str) -> Optional[Any]:
        """
        Read a variable from PLC
        
        Args:
            tag_name: PLC variable name (e.g., "DB1.DBD0")
            
        Returns:
            Variable value or None if read failed
        """
        try:
            if not self.is_connected or not self.driver:
                return None
            
            result = self.driver.read(tag_name)
            
            if result is not None:
                self.variables_cache[tag_name] = result
                logger.debug(f"Read variable {tag_name}: {result}")
                return result
            else:
                logger.warning(f"Failed to read variable {tag_name}")
                return None
                
        except Exception as e:
            logger.error(f"Read error for {tag_name}: {e}")
            return None
    
    def write_variable(self, tag_name: str, value: Any) -> bool:
        """
        Write a variable to PLC
        
        Args:
            tag_name: PLC variable name
            value: Value to write
            
        Returns:
            True if write successful
        """
        try:
            if not self.is_connected or not self.driver:
                return False
            
            result = self.driver.write(tag_name, value)
            
            if result:
                self.variables_cache[tag_name] = value
                logger.debug(f"Wrote variable {tag_name}: {value}")
                return True
            else:
                logger.warning(f"Failed to write variable {tag_name}")
                return False
                
        except Exception as e:
            logger.error(f"Write error for {tag_name}: {e}")
            return False
    
    def read_multiple(self, tag_names: List[str]) -> Dict[str, Any]:
        """
        Read multiple variables from PLC
        
        Args:
            tag_names: List of PLC variable names
            
        Returns:
            Dictionary of variable names and values
        """
        try:
            if not self.is_connected or not self.driver:
                return {}
            
            results = {}
            for tag_name in tag_names:
                value = self.read_variable(tag_name)
                if value is not None:
                    results[tag_name] = value
            
            return results
            
        except Exception as e:
            logger.error(f"Read multiple error: {e}")
            return {}
    
    def write_multiple(self, variables: Dict[str, Any]) -> bool:
        """
        Write multiple variables to PLC
        
        Args:
            variables: Dictionary of variable names and values
            
        Returns:
            True if all writes successful
        """
        try:
            if not self.is_connected or not self.driver:
                return False
            
            all_success = True
            for tag_name, value in variables.items():
                if not self.write_variable(tag_name, value):
                    all_success = False
            
            return all_success
            
        except Exception as e:
            logger.error(f"Write multiple error: {e}")
            return False
    
    def send_message(self, message: ProtocolMessage) -> bool:
        """
        Send Profinet message (write operation)
        
        Args:
            message: Protocol message with tag_name and value
            
        Returns:
            True if send successful
        """
        try:
            tag_name = message.data.get('tag_name')
            value = message.data.get('value')
            
            if not tag_name or value is None:
                logger.error("Invalid message: missing tag_name or value")
                return False
            
            return self.write_variable(tag_name, value)
            
        except Exception as e:
            logger.error(f"Send message error: {e}")
            return False
    
    def receive_message(self, timeout: float = 1.0) -> Optional[ProtocolMessage]:
        """
        Receive Profinet message (read operation)
        
        Note: Profinet is request-response based.
        This method is provided for interface compatibility.
        
        Args:
            timeout: Timeout in seconds
            
        Returns:
            None (Profinet doesn't support unsolicited messages)
        """
        return None
    
    def parse_message(self, data: bytes) -> Dict[str, Any]:
        """Parse Profinet message data"""
        return {}
    
    def encode_message(self, message: Dict[str, Any]) -> bytes:
        """Encode Profinet message"""
        return b''
    
    def validate_message(self, data: bytes) -> bool:
        """Validate Profinet message"""
        return True
    
    def get_device_info(self) -> Optional[Dict[str, Any]]:
        """Get Profinet device information"""
        try:
            if not self.is_connected or not self.driver:
                return None
            
            return {
                'ip_address': self.config.ip_address,
                'port': self.config.port,
                'slot': self.config.slot,
                'connected': self.is_connected
            }
            
        except Exception as e:
            logger.error(f"Failed to get device info: {e}")
            return None
