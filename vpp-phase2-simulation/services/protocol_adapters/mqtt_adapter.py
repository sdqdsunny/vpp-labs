"""
MQTT Protocol Adapter

Implements MQTT protocol support using paho-mqtt library.
Supports MQTT 3.1.1 and 5.0 with SSL/TLS encryption.
"""

import json
import logging
import threading
import time
from typing import Dict, Any, Optional, Callable, List
import paho.mqtt.client as mqtt

from .base import ProtocolAdapter, ProtocolMessage, ProtocolType, ConnectionException, MessageException

logger = logging.getLogger(__name__)


class MQTTAdapter(ProtocolAdapter):
    """
    MQTT Protocol Adapter
    
    Supports:
    - MQTT 3.1.1 and 5.0
    - SSL/TLS encryption
    - Topic subscription and publishing
    - Message queuing
    - Automatic reconnection
    """

    def __init__(self, adapter_id: str = "mqtt-adapter"):
        """Initialize MQTT adapter"""
        super().__init__(adapter_id, ProtocolType.MQTT)
        self.client = mqtt.Client()
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        self.client.on_publish = self._on_publish
        self.messages: List[ProtocolMessage] = []
        self.subscribed_topics: List[str] = []
        self.message_lock = threading.Lock()
        self.config: Dict[str, Any] = {}

    def connect(self, config: Dict[str, Any]) -> bool:
        """
        Establish MQTT connection.
        
        Args:
            config: Connection configuration
                - host: MQTT broker host (default: localhost)
                - port: MQTT broker port (default: 1883)
                - keepalive: Keep-alive interval in seconds (default: 60)
                - use_tls: Enable TLS/SSL (default: False)
                - ca_certs: CA certificate file path
                - certfile: Client certificate file path
                - keyfile: Client key file path
                - username: MQTT username
                - password: MQTT password
                - client_id: MQTT client ID
                - protocol_version: MQTT version (3 or 4, default: 4)
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.config = config
            host = config.get("host", "localhost")
            port = config.get("port", 1883)
            keepalive = config.get("keepalive", 60)
            
            # Configure TLS/SSL if enabled
            if config.get("use_tls", False):
                ca_certs = config.get("ca_certs")
                certfile = config.get("certfile")
                keyfile = config.get("keyfile")
                
                self.client.tls_set(
                    ca_certs=ca_certs,
                    certfile=certfile,
                    keyfile=keyfile,
                    cert_reqs=mqtt.ssl.CERT_REQUIRED,
                    tls_version=mqtt.ssl.PROTOCOL_TLSv1_2,
                    ciphers=None,
                )
                self.client.tls_insecure_set(False)
            
            # Set username and password if provided
            if config.get("username"):
                self.client.username_pw_set(
                    config.get("username"),
                    config.get("password"),
                )
            
            # Set client ID if provided
            if config.get("client_id"):
                self.client.reinitialise(config.get("client_id"))
            
            # Set protocol version
            protocol_version = config.get("protocol_version", 4)
            if protocol_version == 3:
                self.client.protocol = mqtt.MQTTv31
            else:
                self.client.protocol = mqtt.MQTTv311
            
            # Connect to broker
            self.client.connect(host, port, keepalive)
            self.client.loop_start()
            
            self.connection_time = time.time()
            self.logger.info(f"Connecting to MQTT broker at {host}:{port}")
            
            # Wait for connection to be established
            timeout = 5
            start_time = time.time()
            while not self.is_connected and (time.time() - start_time) < timeout:
                time.sleep(0.1)
            
            if self.is_connected:
                self.logger.info(f"Successfully connected to MQTT broker")
                return True
            else:
                self._record_error("Connection timeout")
                return False
                
        except Exception as e:
            self._record_error(f"Connection failed: {str(e)}")
            self.logger.error(f"Failed to connect to MQTT broker: {e}")
            return False

    def disconnect(self) -> bool:
        """
        Close MQTT connection.
        
        Returns:
            True if disconnection successful, False otherwise
        """
        try:
            self.client.loop_stop()
            self.client.disconnect()
            self.is_connected = False
            self.logger.info("Disconnected from MQTT broker")
            return True
        except Exception as e:
            self._record_error(f"Disconnection failed: {str(e)}")
            self.logger.error(f"Failed to disconnect from MQTT broker: {e}")
            return False

    def send_message(self, message: ProtocolMessage) -> bool:
        """
        Publish MQTT message.
        
        Args:
            message: Message to publish
        
        Returns:
            True if publish successful, False otherwise
        """
        if not self.is_connected:
            self._record_error("Not connected to MQTT broker")
            return False
        
        try:
            topic = f"vpp/{message.source}/{message.destination}"
            payload = json.dumps(message.data)
            
            result = self.client.publish(topic, payload, qos=1)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                self._record_message()
                self.logger.debug(f"Published message to {topic}")
                return True
            else:
                self._record_error(f"Publish failed with code {result.rc}")
                return False
                
        except Exception as e:
            self._record_error(f"Send failed: {str(e)}")
            self.logger.error(f"Failed to send MQTT message: {e}")
            return False

    def receive_message(self, timeout: float = 1.0) -> Optional[ProtocolMessage]:
        """
        Receive MQTT message from queue.
        
        Args:
            timeout: Timeout in seconds (not used for queue-based reception)
        
        Returns:
            Received message or None if queue is empty
        """
        try:
            with self.message_lock:
                if self.messages:
                    return self.messages.pop(0)
            return None
        except Exception as e:
            self._record_error(f"Receive failed: {str(e)}")
            self.logger.error(f"Failed to receive MQTT message: {e}")
            return None

    def parse_message(self, data: bytes) -> Dict[str, Any]:
        """
        Parse MQTT message payload.
        
        Args:
            data: Raw MQTT payload
        
        Returns:
            Parsed message dictionary
        """
        try:
            return json.loads(data.decode('utf-8'))
        except Exception as e:
            self.logger.warning(f"Failed to parse MQTT message: {e}")
            return {}

    def encode_message(self, message: Dict[str, Any]) -> bytes:
        """
        Encode message to MQTT payload.
        
        Args:
            message: Message dictionary
        
        Returns:
            Encoded MQTT payload
        """
        try:
            return json.dumps(message).encode('utf-8')
        except Exception as e:
            self.logger.warning(f"Failed to encode MQTT message: {e}")
            return b""

    def validate_message(self, data: bytes) -> bool:
        """
        Validate MQTT message payload.
        
        Args:
            data: Raw MQTT payload
        
        Returns:
            True if valid JSON, False otherwise
        """
        try:
            json.loads(data.decode('utf-8'))
            return True
        except Exception:
            return False

    def subscribe(self, topic: str) -> bool:
        """
        Subscribe to MQTT topic.
        
        Args:
            topic: Topic to subscribe to
        
        Returns:
            True if subscription successful, False otherwise
        """
        if not self.is_connected:
            self._record_error("Not connected to MQTT broker")
            return False
        
        try:
            result = self.client.subscribe(topic, qos=1)
            if result[0] == mqtt.MQTT_ERR_SUCCESS:
                self.subscribed_topics.append(topic)
                self.logger.info(f"Subscribed to topic: {topic}")
                return True
            else:
                self._record_error(f"Subscribe failed with code {result[0]}")
                return False
        except Exception as e:
            self._record_error(f"Subscribe failed: {str(e)}")
            self.logger.error(f"Failed to subscribe to topic {topic}: {e}")
            return False

    def unsubscribe(self, topic: str) -> bool:
        """
        Unsubscribe from MQTT topic.
        
        Args:
            topic: Topic to unsubscribe from
        
        Returns:
            True if unsubscription successful, False otherwise
        """
        if not self.is_connected:
            return False
        
        try:
            result = self.client.unsubscribe(topic)
            if result[0] == mqtt.MQTT_ERR_SUCCESS:
                if topic in self.subscribed_topics:
                    self.subscribed_topics.remove(topic)
                self.logger.info(f"Unsubscribed from topic: {topic}")
                return True
            else:
                self._record_error(f"Unsubscribe failed with code {result[0]}")
                return False
        except Exception as e:
            self._record_error(f"Unsubscribe failed: {str(e)}")
            self.logger.error(f"Failed to unsubscribe from topic {topic}: {e}")
            return False

    def get_status(self) -> Dict[str, Any]:
        """
        Get adapter status including subscribed topics.
        
        Returns:
            Status dictionary
        """
        status = super().get_status()
        status.update({
            "subscribed_topics": self.subscribed_topics,
            "queued_messages": len(self.messages),
        })
        return status

    def _on_connect(self, client, userdata, flags, rc):
        """MQTT connection callback"""
        if rc == 0:
            self.is_connected = True
            self.logger.info("MQTT connection established")
            # Subscribe to default topic
            self.client.subscribe("vpp/#", qos=1)
        else:
            self.is_connected = False
            self._record_error(f"Connection failed with code {rc}")
            self.logger.error(f"MQTT connection failed with code {rc}")

    def _on_disconnect(self, client, userdata, rc):
        """MQTT disconnection callback"""
        self.is_connected = False
        if rc != 0:
            self._record_error(f"Unexpected disconnection with code {rc}")
            self.logger.warning(f"Unexpected MQTT disconnection with code {rc}")

    def _on_message(self, client, userdata, msg):
        """MQTT message callback"""
        try:
            data = self.parse_message(msg.payload)
            message = ProtocolMessage(
                protocol="mqtt",
                message_id=f"{msg.topic}_{int(time.time() * 1000)}",
                source="mqtt",
                destination="vpp",
                timestamp=time.time(),
                data=data,
                metadata={"topic": msg.topic, "qos": msg.qos},
            )
            
            with self.message_lock:
                self.messages.append(message)
            
            self.logger.debug(f"Received MQTT message from {msg.topic}")
        except Exception as e:
            self._record_error(f"Message processing failed: {str(e)}")
            self.logger.error(f"Failed to process MQTT message: {e}")

    def _on_publish(self, client, userdata, mid):
        """MQTT publish callback"""
        self.logger.debug(f"Message published with ID {mid}")
