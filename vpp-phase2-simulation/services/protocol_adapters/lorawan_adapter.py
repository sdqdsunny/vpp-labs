"""
LoRaWAN Protocol Adapter

Implements LoRaWAN communication for long-range IoT applications.
Supports device communication, uplink/downlink messages, and network management.
"""

from typing import Dict, Any, Optional, List
from .base import ProtocolAdapter, ProtocolMessage, ProtocolType
import logging
import json
import time
from datetime import datetime

logger = logging.getLogger(__name__)


class LoRaWANConfig:
    """LoRaWAN Configuration"""
    
    def __init__(self, gateway_url: str, app_id: str, app_key: str):
        self.gateway_url = gateway_url
        self.app_id = app_id
        self.app_key = app_key
        self.region = "EU868"  # Default region
        self.class_type = "A"  # LoRaWAN class (A, B, or C)


class LoRaWANDevice:
    """LoRaWAN Device Information"""
    
    def __init__(self, dev_eui: str, app_eui: str, app_key: str):
        self.dev_eui = dev_eui
        self.app_eui = app_eui
        self.app_key = app_key
        self.dev_addr = None
        self.nwk_skey = None
        self.app_skey = None
        self.fcnt_up = 0
        self.fcnt_down = 0
        self.last_seen = None


class LoRaWANAdapter(ProtocolAdapter):
    """
    LoRaWAN Protocol Adapter
    
    Provides LoRaWAN communication for long-range IoT applications.
    Supports device management, uplink/downlink messages, and network operations.
    """
    
    def __init__(self, adapter_id: str = "lorawan-adapter"):
        super().__init__(adapter_id, ProtocolType.LORAWAN)
        self.config: Optional[LoRaWANConfig] = None
        self.devices: Dict[str, LoRaWANDevice] = {}
        self.message_queue: List[Dict[str, Any]] = []
        self.uplink_callbacks: List[callable] = []
        self.downlink_callbacks: List[callable] = []
        
    def connect(self, config: Dict[str, Any]) -> bool:
        """
        Connect to LoRaWAN network server
        
        Args:
            config: Configuration with 'gateway_url', 'app_id', 'app_key'
            
        Returns:
            True if connection successful
        """
        try:
            self.config = LoRaWANConfig(
                gateway_url=config.get('gateway_url', 'http://localhost:8080'),
                app_id=config.get('app_id', 'vpp-app'),
                app_key=config.get('app_key', 'default-key')
            )
            
            self.config.region = config.get('region', 'EU868')
            self.config.class_type = config.get('class_type', 'A')
            
            # Simulate connection to LoRaWAN network server
            self.is_connected = True
            self.connection_time = time.time()
            
            logger.info(
                f"Connected to LoRaWAN network: {self.config.gateway_url} "
                f"(App: {self.config.app_id}, Region: {self.config.region})"
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to LoRaWAN network: {e}")
            self.is_connected = False
            return False
    
    def disconnect(self) -> bool:
        """Disconnect from LoRaWAN network"""
        try:
            self.is_connected = False
            self.devices.clear()
            self.message_queue.clear()
            logger.info("Disconnected from LoRaWAN network")
            return True
        except Exception as e:
            logger.error(f"Disconnect error: {e}")
            return False
    
    def register_device(self, device_config: Dict[str, Any]) -> bool:
        """
        Register a LoRaWAN device
        
        Args:
            device_config: Device configuration with 'dev_eui', 'app_eui', 'app_key'
            
        Returns:
            True if registration successful
        """
        try:
            if not self.is_connected:
                logger.error("Not connected to LoRaWAN network")
                return False
            
            dev_eui = device_config.get('dev_eui')
            app_eui = device_config.get('app_eui')
            app_key = device_config.get('app_key')
            
            if not all([dev_eui, app_eui, app_key]):
                logger.error("Missing required device parameters")
                return False
            
            device = LoRaWANDevice(dev_eui, app_eui, app_key)
            self.devices[dev_eui] = device
            
            logger.info(f"Registered LoRaWAN device: {dev_eui}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register device: {e}")
            return False
    
    def unregister_device(self, dev_eui: str) -> bool:
        """
        Unregister a LoRaWAN device
        
        Args:
            dev_eui: Device EUI
            
        Returns:
            True if unregistration successful
        """
        try:
            if dev_eui in self.devices:
                del self.devices[dev_eui]
                logger.info(f"Unregistered LoRaWAN device: {dev_eui}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to unregister device: {e}")
            return False
    
    def send_uplink(self, dev_eui: str, payload: bytes, port: int = 1) -> bool:
        """
        Send uplink message from device
        
        Args:
            dev_eui: Device EUI
            payload: Message payload
            port: LoRaWAN port (1-223)
            
        Returns:
            True if send successful
        """
        try:
            if not self.is_connected:
                logger.error("Not connected to LoRaWAN network")
                return False
            
            if dev_eui not in self.devices:
                logger.error(f"Device not registered: {dev_eui}")
                return False
            
            device = self.devices[dev_eui]
            device.fcnt_up += 1
            device.last_seen = datetime.utcnow().isoformat()
            
            message = {
                'type': 'uplink',
                'dev_eui': dev_eui,
                'payload': payload.hex(),
                'port': port,
                'fcnt': device.fcnt_up,
                'timestamp': device.last_seen,
                'rssi': -100,  # Simulated RSSI
                'snr': 10.0    # Simulated SNR
            }
            
            self.message_queue.append(message)
            self._record_message()
            
            # Trigger uplink callbacks
            for callback in self.uplink_callbacks:
                try:
                    callback(message)
                except Exception as e:
                    logger.error(f"Uplink callback error: {e}")
            
            logger.debug(f"Uplink sent from {dev_eui}: {payload.hex()}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send uplink: {e}")
            return False
    
    def send_downlink(self, dev_eui: str, payload: bytes, port: int = 1, confirmed: bool = False) -> bool:
        """
        Send downlink message to device
        
        Args:
            dev_eui: Device EUI
            payload: Message payload
            port: LoRaWAN port (1-223)
            confirmed: Whether message requires confirmation
            
        Returns:
            True if send successful
        """
        try:
            if not self.is_connected:
                logger.error("Not connected to LoRaWAN network")
                return False
            
            if dev_eui not in self.devices:
                logger.error(f"Device not registered: {dev_eui}")
                return False
            
            device = self.devices[dev_eui]
            device.fcnt_down += 1
            
            message = {
                'type': 'downlink',
                'dev_eui': dev_eui,
                'payload': payload.hex(),
                'port': port,
                'fcnt': device.fcnt_down,
                'confirmed': confirmed,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            self.message_queue.append(message)
            self._record_message()
            
            # Trigger downlink callbacks
            for callback in self.downlink_callbacks:
                try:
                    callback(message)
                except Exception as e:
                    logger.error(f"Downlink callback error: {e}")
            
            logger.debug(f"Downlink sent to {dev_eui}: {payload.hex()}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send downlink: {e}")
            return False
    
    def get_device_info(self, dev_eui: str) -> Optional[Dict[str, Any]]:
        """
        Get device information
        
        Args:
            dev_eui: Device EUI
            
        Returns:
            Device information or None if not found
        """
        try:
            if dev_eui not in self.devices:
                return None
            
            device = self.devices[dev_eui]
            return {
                'dev_eui': device.dev_eui,
                'app_eui': device.app_eui,
                'fcnt_up': device.fcnt_up,
                'fcnt_down': device.fcnt_down,
                'last_seen': device.last_seen
            }
            
        except Exception as e:
            logger.error(f"Failed to get device info: {e}")
            return None
    
    def list_devices(self) -> List[Dict[str, Any]]:
        """
        List all registered devices
        
        Returns:
            List of device information
        """
        try:
            devices = []
            for dev_eui, device in self.devices.items():
                devices.append({
                    'dev_eui': device.dev_eui,
                    'app_eui': device.app_eui,
                    'fcnt_up': device.fcnt_up,
                    'fcnt_down': device.fcnt_down,
                    'last_seen': device.last_seen
                })
            return devices
        except Exception as e:
            logger.error(f"Failed to list devices: {e}")
            return []
    
    def register_uplink_callback(self, callback: callable) -> None:
        """Register callback for uplink messages"""
        self.uplink_callbacks.append(callback)
        logger.debug("Registered uplink callback")
    
    def register_downlink_callback(self, callback: callable) -> None:
        """Register callback for downlink messages"""
        self.downlink_callbacks.append(callback)
        logger.debug("Registered downlink callback")
    
    def get_message_queue(self) -> List[Dict[str, Any]]:
        """Get message queue"""
        return self.message_queue.copy()
    
    def clear_message_queue(self) -> None:
        """Clear message queue"""
        self.message_queue.clear()
        logger.debug("Cleared message queue")
    
    def send_message(self, message: ProtocolMessage) -> bool:
        """
        Send LoRaWAN message
        
        Args:
            message: Protocol message with dev_eui, payload, and direction
            
        Returns:
            True if send successful
        """
        try:
            dev_eui = message.data.get('dev_eui')
            payload = message.data.get('payload')
            direction = message.data.get('direction', 'uplink')
            port = message.data.get('port', 1)
            confirmed = message.data.get('confirmed', False)
            
            if not dev_eui or not payload:
                logger.error("Invalid message: missing dev_eui or payload")
                return False
            
            # Convert payload to bytes if needed
            if isinstance(payload, str):
                payload = bytes.fromhex(payload)
            
            if direction == 'uplink':
                return self.send_uplink(dev_eui, payload, port)
            elif direction == 'downlink':
                return self.send_downlink(dev_eui, payload, port, confirmed)
            else:
                logger.error(f"Unknown direction: {direction}")
                return False
                
        except Exception as e:
            logger.error(f"Send message error: {e}")
            return False
    
    def receive_message(self, timeout: float = 1.0) -> Optional[ProtocolMessage]:
        """
        Receive LoRaWAN message from queue
        
        Args:
            timeout: Timeout in seconds
            
        Returns:
            Protocol message or None if queue empty
        """
        try:
            if not self.message_queue:
                return None
            
            msg_data = self.message_queue.pop(0)
            
            protocol_msg = ProtocolMessage(
                protocol="lorawan",
                message_id=f"msg-{int(time.time() * 1000)}",
                source=msg_data.get('dev_eui', 'unknown'),
                destination=self.config.app_id if self.config else 'unknown',
                timestamp=time.time(),
                data=msg_data
            )
            
            return protocol_msg
            
        except Exception as e:
            logger.error(f"Receive error: {e}")
            return None
    
    def parse_message(self, data: bytes) -> Dict[str, Any]:
        """Parse LoRaWAN message data"""
        try:
            if len(data) < 13:
                return {}
            
            return {
                'mhdr': data[0],
                'dev_addr': data[1:5].hex(),
                'fctrl': data[5],
                'fcnt': int.from_bytes(data[6:8], 'little'),
                'payload': data[8:].hex()
            }
        except Exception as e:
            logger.error(f"Parse error: {e}")
            return {}
    
    def encode_message(self, message: Dict[str, Any]) -> bytes:
        """Encode LoRaWAN message"""
        try:
            mhdr = bytes([message.get('mhdr', 0x40)])
            dev_addr = bytes.fromhex(message.get('dev_addr', '00000000'))
            fctrl = bytes([message.get('fctrl', 0)])
            fcnt = int(message.get('fcnt', 0)).to_bytes(2, 'little')
            payload = bytes.fromhex(message.get('payload', ''))
            
            return mhdr + dev_addr + fctrl + fcnt + payload
        except Exception as e:
            logger.error(f"Encode error: {e}")
            return b''
    
    def validate_message(self, data: bytes) -> bool:
        """Validate LoRaWAN message"""
        return len(data) >= 13
    
    def get_network_info(self) -> Optional[Dict[str, Any]]:
        """Get LoRaWAN network information"""
        try:
            if not self.config:
                return None
            
            return {
                'gateway_url': self.config.gateway_url,
                'app_id': self.config.app_id,
                'region': self.config.region,
                'class': self.config.class_type,
                'connected': self.is_connected,
                'devices_count': len(self.devices),
                'messages_queued': len(self.message_queue)
            }
        except Exception as e:
            logger.error(f"Failed to get network info: {e}")
            return None
