"""
Modbus Protocol Adapter

Implements Modbus protocol support using pymodbus library.
Supports TCP and RTU modes with async operations.
"""

import logging
import time
from typing import Dict, Any, Optional, List
from pymodbus.client import ModbusTcpClient, ModbusSerialClient
from pymodbus.exceptions import ModbusException

from .base import ProtocolAdapter, ProtocolMessage, ProtocolType, ConnectionException, MessageException

logger = logging.getLogger(__name__)


class ModbusAdapter(ProtocolAdapter):
    """
    Modbus Protocol Adapter
    
    Supports:
    - TCP mode (Modbus TCP)
    - RTU mode (Modbus RTU over serial)
    - Register read/write operations
    - Coil read/write operations
    - Automatic reconnection
    """

    def __init__(self, adapter_id: str = "modbus-adapter"):
        """Initialize Modbus adapter"""
        super().__init__(adapter_id, ProtocolType.MODBUS)
        self.client = None
        self.mode = None
        self.config: Dict[str, Any] = {}
        self.last_transaction_id = 0

    def connect(self, config: Dict[str, Any]) -> bool:
        """
        Establish Modbus connection.
        
        Args:
            config: Connection configuration
                - mode: 'tcp' or 'rtu' (default: 'tcp')
                - host: Server host for TCP mode (default: localhost)
                - port: Server port for TCP mode (default: 502)
                - port_name: Serial port for RTU mode (default: /dev/ttyUSB0)
                - baudrate: Baud rate for RTU mode (default: 9600)
                - timeout: Connection timeout in seconds (default: 5)
                - unit_id: Modbus unit ID (default: 1)
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.config = config
            self.mode = config.get("mode", "tcp").lower()
            timeout = config.get("timeout", 5)
            
            if self.mode == "tcp":
                host = config.get("host", "localhost")
                port = config.get("port", 502)
                
                self.client = ModbusTcpClient(
                    host=host,
                    port=port,
                    timeout=timeout,
                )
                self.logger.info(f"Connecting to Modbus TCP server at {host}:{port}")
                
            elif self.mode == "rtu":
                port_name = config.get("port_name", "/dev/ttyUSB0")
                baudrate = config.get("baudrate", 9600)
                
                self.client = ModbusSerialClient(
                    method="rtu",
                    port=port_name,
                    baudrate=baudrate,
                    timeout=timeout,
                )
                self.logger.info(f"Connecting to Modbus RTU on {port_name} at {baudrate} baud")
                
            else:
                self._record_error(f"Unknown Modbus mode: {self.mode}")
                return False
            
            # Attempt connection
            if self.client.connect():
                self.is_connected = True
                self.connection_time = time.time()
                self.logger.info(f"Successfully connected to Modbus {self.mode.upper()}")
                return True
            else:
                self._record_error("Connection failed")
                return False
                
        except Exception as e:
            self._record_error(f"Connection failed: {str(e)}")
            self.logger.error(f"Failed to connect to Modbus: {e}")
            return False

    def disconnect(self) -> bool:
        """
        Close Modbus connection.
        
        Returns:
            True if disconnection successful, False otherwise
        """
        try:
            if self.client:
                self.client.close()
            self.is_connected = False
            self.logger.info("Disconnected from Modbus")
            return True
        except Exception as e:
            self._record_error(f"Disconnection failed: {str(e)}")
            self.logger.error(f"Failed to disconnect from Modbus: {e}")
            return False

    def send_message(self, message: ProtocolMessage) -> bool:
        """
        Send Modbus message (write registers/coils).
        
        Args:
            message: Message to send
                - data should contain:
                  - operation: 'write_registers', 'write_coils', etc.
                  - address: Starting register/coil address
                  - values: Values to write
        
        Returns:
            True if send successful, False otherwise
        """
        if not self.is_connected:
            self._record_error("Not connected to Modbus")
            return False
        
        try:
            operation = message.data.get("operation", "write_registers")
            address = message.data.get("address", 0)
            values = message.data.get("values", [])
            unit_id = self.config.get("unit_id", 1)
            
            if operation == "write_registers":
                result = self.client.write_registers(
                    address=address,
                    values=values,
                    unit=unit_id,
                )
            elif operation == "write_coils":
                result = self.client.write_coils(
                    address=address,
                    values=values,
                    unit=unit_id,
                )
            else:
                self._record_error(f"Unknown operation: {operation}")
                return False
            
            if result.isError():
                self._record_error(f"Write operation failed: {result}")
                return False
            
            self._record_message()
            self.logger.debug(f"Wrote {len(values)} values to address {address}")
            return True
            
        except Exception as e:
            self._record_error(f"Send failed: {str(e)}")
            self.logger.error(f"Failed to send Modbus message: {e}")
            return False

    def receive_message(self, timeout: float = 1.0) -> Optional[ProtocolMessage]:
        """
        Receive Modbus message (read registers/coils).
        
        For Modbus, this reads from configured registers.
        
        Args:
            timeout: Timeout in seconds (not used for Modbus)
        
        Returns:
            Message with read data or None if read fails
        """
        if not self.is_connected:
            self._record_error("Not connected to Modbus")
            return None
        
        try:
            unit_id = self.config.get("unit_id", 1)
            
            # Read holding registers (default behavior)
            result = self.client.read_holding_registers(
                address=0,
                count=10,
                unit=unit_id,
            )
            
            if result.isError():
                self._record_error(f"Read operation failed: {result}")
                return None
            
            self.last_transaction_id += 1
            message = ProtocolMessage(
                protocol="modbus",
                message_id=f"modbus_{self.last_transaction_id}",
                source="modbus",
                destination="vpp",
                timestamp=time.time(),
                data={
                    "registers": result.registers,
                    "operation": "read_holding_registers",
                },
            )
            
            self.logger.debug(f"Read {len(result.registers)} registers")
            return message
            
        except Exception as e:
            self._record_error(f"Receive failed: {str(e)}")
            self.logger.error(f"Failed to receive Modbus message: {e}")
            return None

    def parse_message(self, data: bytes) -> Dict[str, Any]:
        """
        Parse Modbus message data.
        
        Args:
            data: Raw Modbus data
        
        Returns:
            Parsed message dictionary
        """
        try:
            # For Modbus, data is typically already parsed
            # This is a placeholder for custom parsing if needed
            return {
                "raw_data": data.hex(),
                "length": len(data),
            }
        except Exception as e:
            self.logger.warning(f"Failed to parse Modbus message: {e}")
            return {}

    def encode_message(self, message: Dict[str, Any]) -> bytes:
        """
        Encode message to Modbus format.
        
        Args:
            message: Message dictionary
        
        Returns:
            Encoded Modbus data
        """
        try:
            # For Modbus, encoding is typically handled by the library
            # This is a placeholder for custom encoding if needed
            import json
            return json.dumps(message).encode('utf-8')
        except Exception as e:
            self.logger.warning(f"Failed to encode Modbus message: {e}")
            return b""

    def validate_message(self, data: bytes) -> bool:
        """
        Validate Modbus message data.
        
        Args:
            data: Raw Modbus data
        
        Returns:
            True if data appears valid, False otherwise
        """
        try:
            # Basic validation: check if data is not empty
            return len(data) > 0
        except Exception:
            return False

    def read_registers(self, address: int, count: int) -> Optional[List[int]]:
        """
        Read holding registers.
        
        Args:
            address: Starting register address
            count: Number of registers to read
        
        Returns:
            List of register values or None if read fails
        """
        if not self.is_connected:
            self._record_error("Not connected to Modbus")
            return None
        
        try:
            unit_id = self.config.get("unit_id", 1)
            result = self.client.read_holding_registers(
                address=address,
                count=count,
                unit=unit_id,
            )
            
            if result.isError():
                self._record_error(f"Read registers failed: {result}")
                return None
            
            return result.registers
            
        except Exception as e:
            self._record_error(f"Read registers failed: {str(e)}")
            self.logger.error(f"Failed to read registers: {e}")
            return None

    def write_registers(self, address: int, values: List[int]) -> bool:
        """
        Write holding registers.
        
        Args:
            address: Starting register address
            values: Values to write
        
        Returns:
            True if write successful, False otherwise
        """
        if not self.is_connected:
            self._record_error("Not connected to Modbus")
            return False
        
        try:
            unit_id = self.config.get("unit_id", 1)
            result = self.client.write_registers(
                address=address,
                values=values,
                unit=unit_id,
            )
            
            if result.isError():
                self._record_error(f"Write registers failed: {result}")
                return False
            
            self._record_message()
            return True
            
        except Exception as e:
            self._record_error(f"Write registers failed: {str(e)}")
            self.logger.error(f"Failed to write registers: {e}")
            return False

    def read_coils(self, address: int, count: int) -> Optional[List[bool]]:
        """
        Read coils.
        
        Args:
            address: Starting coil address
            count: Number of coils to read
        
        Returns:
            List of coil values or None if read fails
        """
        if not self.is_connected:
            self._record_error("Not connected to Modbus")
            return None
        
        try:
            unit_id = self.config.get("unit_id", 1)
            result = self.client.read_coils(
                address=address,
                count=count,
                unit=unit_id,
            )
            
            if result.isError():
                self._record_error(f"Read coils failed: {result}")
                return None
            
            return result.bits
            
        except Exception as e:
            self._record_error(f"Read coils failed: {str(e)}")
            self.logger.error(f"Failed to read coils: {e}")
            return None

    def write_coils(self, address: int, values: List[bool]) -> bool:
        """
        Write coils.
        
        Args:
            address: Starting coil address
            values: Values to write
        
        Returns:
            True if write successful, False otherwise
        """
        if not self.is_connected:
            self._record_error("Not connected to Modbus")
            return False
        
        try:
            unit_id = self.config.get("unit_id", 1)
            result = self.client.write_coils(
                address=address,
                values=values,
                unit=unit_id,
            )
            
            if result.isError():
                self._record_error(f"Write coils failed: {result}")
                return False
            
            self._record_message()
            return True
            
        except Exception as e:
            self._record_error(f"Write coils failed: {str(e)}")
            self.logger.error(f"Failed to write coils: {e}")
            return False
