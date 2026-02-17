#!/usr/bin/env python3
"""
MQTT Publisher for VPP Traffic Statistics

Publishes real-time traffic statistics from the network analyzer to MQTT broker.
Enables FUXA and other systems to consume traffic data in real-time.

Topics Published:
- vpp/traffic/stats - Overall statistics
- vpp/traffic/rate - Packet rate
- vpp/traffic/protocols - Protocol distribution
- vpp/traffic/flows - Top flows
- vpp/components/{component} - Component-specific stats
"""

import json
import logging
from typing import Dict, List, Optional
from datetime import datetime

try:
    import paho.mqtt.client as mqtt
except ImportError:
    print("Error: paho-mqtt not installed. Install with: pip install paho-mqtt")
    raise

logger = logging.getLogger(__name__)


class TrafficPublisher:
    """
    MQTT publisher for traffic statistics.
    
    Publishes analyzer statistics to MQTT broker for consumption by FUXA
    and other visualization systems.
    """
    
    def __init__(
        self,
        broker_host: str = 'localhost',
        broker_port: int = 1883,
        topic_prefix: str = 'vpp/traffic',
        client_id: str = 'vpp-analyzer'
    ):
        """
        Initialize MQTT publisher.
        
        Args:
            broker_host (str): MQTT broker hostname
            broker_port (int): MQTT broker port
            topic_prefix (str): Topic prefix for all published messages
            client_id (str): MQTT client ID
        """
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.topic_prefix = topic_prefix
        self.client_id = client_id
        
        self.client = mqtt.Client(client_id=client_id)
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_publish = self._on_publish
        
        self.connected = False
        
        logger.info(f"TrafficPublisher initialized: {broker_host}:{broker_port}")
    
    def _on_connect(self, client, userdata, flags, rc):
        """
        MQTT connection callback.
        
        Args:
            client: MQTT client instance
            userdata: User data
            flags: Connection flags
            rc: Return code
        """
        if rc == 0:
            self.connected = True
            logger.info(f"Connected to MQTT broker: {self.broker_host}:{self.broker_port}")
        else:
            logger.error(f"Failed to connect to MQTT broker: {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        """
        MQTT disconnection callback.
        
        Args:
            client: MQTT client instance
            userdata: User data
            rc: Return code
        """
        self.connected = False
        if rc != 0:
            logger.warning(f"Unexpected disconnection from MQTT broker: {rc}")
        else:
            logger.info("Disconnected from MQTT broker")
    
    def _on_publish(self, client, userdata, mid):
        """
        MQTT publish callback.
        
        Args:
            client: MQTT client instance
            userdata: User data
            mid: Message ID
        """
        logger.debug(f"Message published: {mid}")
    
    def connect(self):
        """
        Connect to MQTT broker.
        
        Raises:
            Exception: If connection fails
        """
        try:
            self.client.connect(self.broker_host, self.broker_port, keepalive=60)
            self.client.loop_start()
            logger.info("MQTT client loop started")
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            raise
    
    def disconnect(self):
        """
        Disconnect from MQTT broker.
        """
        try:
            self.client.loop_stop()
            self.client.disconnect()
            logger.info("MQTT client disconnected")
        except Exception as e:
            logger.error(f"Error disconnecting from MQTT broker: {e}")
    
    def publish_stats(self, stats: Dict) -> bool:
        """
        Publish overall traffic statistics.
        
        Args:
            stats (Dict): Statistics dictionary containing:
                - total_packets: Total packet count
                - packet_rate: Packets per second
                - protocol_distribution: Dict of protocol counts
                - top_flows: List of top flows
                - components: Dict of component statistics
        
        Returns:
            bool: True if published successfully
        """
        try:
            payload = {
                'timestamp': datetime.now().isoformat(),
                'total_packets': stats.get('total_packets', 0),
                'packet_rate': stats.get('packet_rate', 0),
                'protocol_distribution': stats.get('protocol_distribution', {}),
                'top_flows': stats.get('top_flows', []),
                'components': stats.get('components', {})
            }
            
            topic = f"{self.topic_prefix}/stats"
            result = self.client.publish(topic, json.dumps(payload), qos=1)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.debug(f"Published stats to {topic}")
                return True
            else:
                logger.error(f"Failed to publish stats: {result.rc}")
                return False
        except Exception as e:
            logger.error(f"Error publishing stats: {e}")
            return False
    
    def publish_packet_rate(self, rate: float) -> bool:
        """
        Publish current packet rate.
        
        Args:
            rate (float): Packets per second
        
        Returns:
            bool: True if published successfully
        """
        try:
            payload = {
                'timestamp': datetime.now().isoformat(),
                'rate': rate
            }
            
            topic = f"{self.topic_prefix}/rate"
            result = self.client.publish(topic, json.dumps(payload), qos=1)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.debug(f"Published packet rate to {topic}")
                return True
            else:
                logger.error(f"Failed to publish packet rate: {result.rc}")
                return False
        except Exception as e:
            logger.error(f"Error publishing packet rate: {e}")
            return False
    
    def publish_protocols(self, protocols: Dict[str, int]) -> bool:
        """
        Publish protocol distribution.
        
        Args:
            protocols (Dict[str, int]): Protocol name to count mapping
        
        Returns:
            bool: True if published successfully
        """
        try:
            payload = {
                'timestamp': datetime.now().isoformat(),
                'protocols': protocols
            }
            
            topic = f"{self.topic_prefix}/protocols"
            result = self.client.publish(topic, json.dumps(payload), qos=1)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.debug(f"Published protocols to {topic}")
                return True
            else:
                logger.error(f"Failed to publish protocols: {result.rc}")
                return False
        except Exception as e:
            logger.error(f"Error publishing protocols: {e}")
            return False
    
    def publish_flows(self, flows: List[tuple]) -> bool:
        """
        Publish top flows.
        
        Args:
            flows (List[tuple]): List of (flow_key, packet_count) tuples
        
        Returns:
            bool: True if published successfully
        """
        try:
            flow_list = [
                {
                    'flow': flow[0],
                    'packets': flow[1]
                }
                for flow in flows[:10]  # Top 10 flows
            ]
            
            payload = {
                'timestamp': datetime.now().isoformat(),
                'flows': flow_list
            }
            
            topic = f"{self.topic_prefix}/flows"
            result = self.client.publish(topic, json.dumps(payload), qos=1)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.debug(f"Published flows to {topic}")
                return True
            else:
                logger.error(f"Failed to publish flows: {result.rc}")
                return False
        except Exception as e:
            logger.error(f"Error publishing flows: {e}")
            return False
    
    def publish_component_stats(self, component: str, stats: Dict) -> bool:
        """
        Publish component-specific statistics.
        
        Args:
            component (str): Component name (master, vcc, upf, gen)
            stats (Dict): Component statistics
        
        Returns:
            bool: True if published successfully
        """
        try:
            payload = {
                'timestamp': datetime.now().isoformat(),
                'component': component,
                'packets': stats.get('packets', 0),
                'bytes': stats.get('bytes', 0),
                'protocols': stats.get('protocols', {})
            }
            
            topic = f"{self.topic_prefix}/components/{component}"
            result = self.client.publish(topic, json.dumps(payload), qos=1)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.debug(f"Published component stats to {topic}")
                return True
            else:
                logger.error(f"Failed to publish component stats: {result.rc}")
                return False
        except Exception as e:
            logger.error(f"Error publishing component stats: {e}")
            return False
    
    def publish_all(self, stats: Dict) -> bool:
        """
        Publish all statistics to respective topics.
        
        Args:
            stats (Dict): Complete statistics dictionary
        
        Returns:
            bool: True if all publishes successful
        """
        try:
            results = []
            
            # Publish overall stats
            results.append(self.publish_stats(stats))
            
            # Publish packet rate
            results.append(self.publish_packet_rate(stats.get('packet_rate', 0)))
            
            # Publish protocols
            results.append(self.publish_protocols(stats.get('protocol_distribution', {})))
            
            # Publish flows
            results.append(self.publish_flows(stats.get('top_flows', [])))
            
            # Publish component stats
            components = stats.get('components', {})
            for component, comp_stats in components.items():
                results.append(self.publish_component_stats(component, comp_stats))
            
            return all(results)
        except Exception as e:
            logger.error(f"Error publishing all stats: {e}")
            return False
    
    def is_connected(self) -> bool:
        """
        Check if connected to MQTT broker.
        
        Returns:
            bool: True if connected
        """
        return self.connected


# Example usage
if __name__ == '__main__':
    import time
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create publisher
    publisher = TrafficPublisher(
        broker_host='localhost',
        broker_port=1883,
        topic_prefix='vpp/traffic'
    )
    
    # Connect
    publisher.connect()
    time.sleep(1)
    
    # Publish sample data
    sample_stats = {
        'total_packets': 1234567,
        'packet_rate': 12.3,
        'protocol_distribution': {
            'IEC61850': 450000,
            'Modbus': 370000,
            'MQTT': 250000,
            'DNP3': 150000,
            'Unknown': 14567
        },
        'top_flows': [
            ('10.0.1.10->10.0.1.20', 450000),
            ('10.0.1.20->10.0.1.30', 370000),
            ('10.0.1.30->10.0.1.40', 250000)
        ],
        'components': {
            'master': {'packets': 450000, 'bytes': 123456789},
            'vcc': {'packets': 370000, 'bytes': 98765432},
            'upf': {'packets': 250000, 'bytes': 87654321},
            'gen': {'packets': 150000, 'bytes': 65432109}
        }
    }
    
    publisher.publish_all(sample_stats)
    time.sleep(2)
    
    # Disconnect
    publisher.disconnect()
