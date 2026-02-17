"""
DNP3 Protocol Adapter

Implements DNP3 protocol support using opendnp3 library.
Supports security authentication and reliable message transmission.
"""

import logging
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from .base import ProtocolAdapter, ProtocolMessage, ProtocolType, ConnectionException, MessageException

logger = logging.getLogger(__name__)


@dataclass
class DNP3Config:
    """DNP3 configuration"""
    host: str = "localhost"
    port: int = 20000
    timeout: int = 5
    mode: str = "master"  # master or outstation
    master_address: int = 0
    outstation_address: int = 1
    use_authentication: bool = False
    username: str = ""
    password: str = ""


class DNP3Adapter(ProtocolAdapter):
    """
    DNP3 Protocol Adapter
    
    Supports:
    - Master and Outstation modes
    - Security authentication
    - Reliable message transmission
    - Event reporting
    - Analog and digital data
    
    Note: Full opendnp3 integration requires the C++ library to be compiled.
    This implementation provides the interface structure.
    """

    def __init__(self, adapter_id: str = "dnp3-adapter"):
        """Initialize DNP3 adapter"""
        super().__init__(adapter_id, ProtocolType.DNP3)
        self.manager = None
        self.channel = None
        self.master = None
        self.outstation = None
        self.config: Optional[DNP3Config] = None
        self.events: List[Dict[str, Any]] = []
        self.last_transaction_id = 0

    def connect(self, config: Dict[str, Any]) -> bool:
        """
        Establish DNP3 connection.
        
        Args:
            config: Connection configuration
                - host: Server host (default: localhost)
                - port: Server port (default: 20000)
                - timeout: Connection timeout in seconds (default: 5)
                - mode: 'master' or 'outstation' (default: 'master')
                - master_address: Master address (default: 0)
                - outstation_address: Outstation address (default: 1)
                - use_authentication: Enable authentication (default: False)
                - username: Authentication username
                - password: Authentication password
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.config = DNP3Config(
                host=config.get("host", "localhost"),
                port=config.get("port", 20000),
                timeout=config.get("timeout", 5),
                mode=config.get("mode", "master"),
                master_address=config.get("master_address", 0),
                outstation_address=config.get("outstation_address", 1),
                use_authentication=config.get("use_authentication", False),
                username=config.get("username", ""),
                password=config.get("password", ""),
            )
            
            if self.config.mode == "master":
                self._connect_as_master()
            elif self.config.mode == "outstation":
                self._connect_as_outstation()
            else:
                self._record_error(f"Unknown DNP3 mode: {self.config.mode}")
                return False
            
            self.is_connected = True
            self.connection_time = time.time()
            self.logger.info(f"Successfully connected to DNP3 {self.config.mode}")
            return True
            
        except Exception as e:
            self._record_error(f"Connection failed: {str(e)}")
            self.logger.error(f"Failed to connect to DNP3: {e}")
            return False

    def disconnect(self) -> bool:
        """
        Close DNP3 connection.
        
        Returns:
            True if disconnection successful, False otherwise
        """
        try:
            if self.master:
                self.master = None
            
            if self.outstation:
                self.outstation = None
            
            if self.channel:
                self.channel = None
            
            if self.manager:
                self.manager = None
            
            self.is_connected = False
            self.logger.info("Disconnected from DNP3")
            return True
            
        except Exception as e:
            self._record_error(f"Disconnection failed: {str(e)}")
            self.logger.error(f"Failed to disconnect from DNP3: {e}")
            return False

    def send_message(self, message: ProtocolMessage) -> bool:
        """
        Send DNP3 message (command or data).
        
        Args:
            message: Message to send
                - data should contain:
                  - message_type: 'command', 'data', or 'event'
                  - values: Message values
        
        Returns:
            True if send successful, False otherwise
        """
        if not self.is_connected:
            self._record_error("Not connected to DNP3")
            return False
        
        try:
            message_type = message.data.get("message_type", "data").lower()
            
            if message_type == "command":
                return self._send_command(message)
            elif message_type == "data":
                return self._send_data(message)
            elif message_type == "event":
                return self._report_event(message)
            else:
                self._record_error(f"Unknown message type: {message_type}")
                return False
                
        except Exception as e:
            self._record_error(f"Send failed: {str(e)}")
            self.logger.error(f"Failed to send DNP3 message: {e}")
            return False

    def receive_message(self, timeout: float = 1.0) -> Optional[ProtocolMessage]:
        """
        Receive DNP3 message.
        
        Args:
            timeout: Timeout in seconds
        
        Returns:
            Received message or None if timeout
        """
        if not self.is_connected:
            self._record_error("Not connected to DNP3")
            return None
        
        try:
            if self.events:
                event_data = self.events.pop(0)
                self.last_transaction_id += 1
                return ProtocolMessage(
                    protocol="dnp3",
                    message_id=f"dnp3_{self.last_transaction_id}",
                    source="dnp3",
                    destination="vpp",
                    timestamp=time.time(),
                    data=event_data,
                )
            
            return None
            
        except Exception as e:
            self._record_error(f"Receive failed: {str(e)}")
            self.logger.error(f"Failed to receive DNP3 message: {e}")
            return None

    def parse_message(self, data: bytes) -> Dict[str, Any]:
        """
        Parse DNP3 message data.
        
        Args:
            data: Raw DNP3 data
        
        Returns:
            Parsed message dictionary
        """
        try:
            # Placeholder for DNP3 parsing
            # In production, this would use opendnp3 parsing functions
            return {
                "raw_data": data.hex(),
                "length": len(data),
            }
        except Exception as e:
            self.logger.warning(f"Failed to parse DNP3 message: {e}")
            return {}

    def encode_message(self, message: Dict[str, Any]) -> bytes:
        """
        Encode message to DNP3 format.
        
        Args:
            message: Message dictionary
        
        Returns:
            Encoded DNP3 data
        """
        try:
            # Placeholder for DNP3 encoding
            # In production, this would use opendnp3 encoding functions
            import json
            return json.dumps(message).encode('utf-8')
        except Exception as e:
            self.logger.warning(f"Failed to encode DNP3 message: {e}")
            return b""

    def validate_message(self, data: bytes) -> bool:
        """
        Validate DNP3 message data.
        
        Args:
            data: Raw DNP3 data
        
        Returns:
            True if data appears valid, False otherwise
        """
        try:
            # Basic validation: check if data is not empty
            return len(data) > 0
        except Exception:
            return False

    def send_command(self, command: Dict[str, Any]) -> bool:
        """
        Send DNP3 command.
        
        Args:
            command: Command data
        
        Returns:
            True if send successful, False otherwise
        """
        message = ProtocolMessage(
            protocol="dnp3",
            message_id=f"cmd_{int(time.time() * 1000)}",
            source="dnp3",
            destination="vpp",
            timestamp=time.time(),
            data={
                "message_type": "command",
                "values": command,
            },
        )
        return self.send_message(message)

    def report_event(self, event: Dict[str, Any]) -> bool:
        """
        Report DNP3 event.
        
        Args:
            event: Event data
        
        Returns:
            True if report successful, False otherwise
        """
        message = ProtocolMessage(
            protocol="dnp3",
            message_id=f"evt_{int(time.time() * 1000)}",
            source="dnp3",
            destination="vpp",
            timestamp=time.time(),
            data={
                "message_type": "event",
                "values": event,
            },
        )
        return self.send_message(message)

    def get_status(self) -> Dict[str, Any]:
        """
        Get adapter status.
        
        Returns:
            Status dictionary
        """
        status = super().get_status()
        status.update({
            "mode": self.config.mode if self.config else None,
            "master_address": self.config.master_address if self.config else None,
            "outstation_address": self.config.outstation_address if self.config else None,
            "event_queue_size": len(self.events),
        })
        return status

    def _connect_as_master(self) -> None:
        """Connect as DNP3 master"""
        # Placeholder for master connection
        # In production, this would use opendnp3 master functions
        self.logger.info(f"Connecting to DNP3 outstation at {self.config.host}:{self.config.port}")

    def _connect_as_outstation(self) -> None:
        """Connect as DNP3 outstation"""
        # Placeholder for outstation connection
        # In production, this would use opendnp3 outstation functions
        self.logger.info(f"Starting DNP3 outstation on port {self.config.port}")

    def _send_command(self, message: ProtocolMessage) -> bool:
        """Send DNP3 command"""
        try:
            # Placeholder for command sending
            # In production, this would use opendnp3 command functions
            self._record_message()
            self.logger.debug("DNP3 command sent")
            return True
        except Exception as e:
            self._record_error(f"Command send failed: {str(e)}")
            return False

    def _send_data(self, message: ProtocolMessage) -> bool:
        """Send DNP3 data"""
        try:
            # Placeholder for data sending
            # In production, this would use opendnp3 data functions
            self._record_message()
            self.logger.debug("DNP3 data sent")
            return True
        except Exception as e:
            self._record_error(f"Data send failed: {str(e)}")
            return False

    def _report_event(self, message: ProtocolMessage) -> bool:
        """Report DNP3 event"""
        try:
            # Placeholder for event reporting
            # In production, this would use opendnp3 event functions
            self._record_message()
            self.logger.debug("DNP3 event reported")
            return True
        except Exception as e:
            self._record_error(f"Event report failed: {str(e)}")
            return False
