#!/usr/bin/env python3
"""
VPP Protocol Analyzer - Industrial Control Protocol Analysis Tool

Functionality:
- Capture network traffic from OVS mirror port
- Identify industrial control protocols (IEC61850, Modbus, DNP3, MQTT)
- Save captured traffic to pcap files
- Generate real-time statistics
- Provide comprehensive logging

Supported Protocols:
- IEC61850 (port 102) - Power systems protocol
- Modbus (port 502) - Industrial device communication
- DNP3 (port 20000) - Power systems protocol
- MQTT (ports 1883, 8883) - Message queuing protocol
"""

import os
import sys
import json
import logging
import signal
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import time

try:
    from scapy.all import sniff, IP, TCP, UDP, wrpcap
except ImportError:
    print("Error: scapy not installed. Install with: pip install scapy")
    sys.exit(1)

# Try to import MQTT publisher (optional)
try:
    import importlib.util
    mqtt_spec = importlib.util.spec_from_file_location(
        "mqtt_publisher",
        os.path.join(os.path.dirname(__file__), 'mqtt-publisher.py')
    )
    mqtt_module = importlib.util.module_from_spec(mqtt_spec)
    mqtt_spec.loader.exec_module(mqtt_module)
    TrafficPublisher = mqtt_module.TrafficPublisher
    MQTT_AVAILABLE = True
except Exception as e:
    logger_temp = logging.getLogger(__name__)
    logger_temp.warning(f"MQTT publisher not available: {e}")
    MQTT_AVAILABLE = False
    TrafficPublisher = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ProtocolIdentifier:
    """
    Industrial control protocol identifier.
    
    Identifies protocols based on port numbers for TCP and UDP traffic.
    Supports IEC61850, Modbus, DNP3, and MQTT protocols.
    """
    
    # Protocol to port mapping
    PROTOCOL_PORTS = {
        102: 'IEC61850',
        502: 'Modbus',
        20000: 'DNP3',
        1883: 'MQTT',
        8883: 'MQTT-TLS',
    }
    
    @staticmethod
    def identify(packet) -> Optional[str]:
        """
        Identify protocol from packet.
        
        Args:
            packet: Scapy packet object
            
        Returns:
            Protocol name (str) or None if not identified
        """
        try:
            if not packet.haslayer(IP):
                return None
            
            ip_layer = packet[IP]
            
            # TCP protocol
            if ip_layer.proto == 6 and packet.haslayer(TCP):
                tcp_layer = packet[TCP]
                dport = tcp_layer.dport
                sport = tcp_layer.sport
                
                # Check destination port
                if dport in ProtocolIdentifier.PROTOCOL_PORTS:
                    return ProtocolIdentifier.PROTOCOL_PORTS[dport]
                
                # Check source port
                if sport in ProtocolIdentifier.PROTOCOL_PORTS:
                    return ProtocolIdentifier.PROTOCOL_PORTS[sport]
            
            # UDP protocol
            elif ip_layer.proto == 17 and packet.haslayer(UDP):
                udp_layer = packet[UDP]
                dport = udp_layer.dport
                sport = udp_layer.sport
                
                if dport in ProtocolIdentifier.PROTOCOL_PORTS:
                    return ProtocolIdentifier.PROTOCOL_PORTS[dport]
                
                if sport in ProtocolIdentifier.PROTOCOL_PORTS:
                    return ProtocolIdentifier.PROTOCOL_PORTS[sport]
            
            return 'Unknown'
        except Exception as e:
            logger.error(f"Error identifying protocol: {e}")
            return None


class PacketAnalyzer:
    """
    Network packet analyzer for industrial control protocols.
    
    Captures packets from a network interface, identifies protocols,
    collects statistics, and saves traffic to pcap files.
    """
    
    def __init__(self, interface: str, output_dir: str = '/pcap'):
        """
        Initialize packet analyzer.
        
        Args:
            interface (str): Network interface to capture from
            output_dir (str): Directory to save pcap files (default: /pcap)
        """
        self.interface = interface
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.packet_count = 0
        self.protocol_stats: Dict[str, int] = {}
        self.flow_stats: Dict[str, int] = {}
        self.component_stats: Dict[str, Dict] = {
            'master': {'packets': 0, 'bytes': 0, 'protocols': {}},
            'vcc': {'packets': 0, 'bytes': 0, 'protocols': {}},
            'upf': {'packets': 0, 'bytes': 0, 'protocols': {}},
            'gen': {'packets': 0, 'bytes': 0, 'protocols': {}}
        }
        
        self.current_pcap_packets = []
        self.pcap_rotation_count = 100  # Rotate pcap file every 100 packets
        
        self.running = True
        
        # Initialize MQTT publisher if available
        self.mqtt_publisher = None
        if MQTT_AVAILABLE:
            try:
                mqtt_broker = os.getenv('MQTT_BROKER', 'localhost')
                mqtt_port = int(os.getenv('MQTT_PORT', 1883))
                mqtt_topic_prefix = os.getenv('MQTT_TOPIC_PREFIX', 'vpp/traffic')
                
                self.mqtt_publisher = TrafficPublisher(
                    broker_host=mqtt_broker,
                    broker_port=mqtt_port,
                    topic_prefix=mqtt_topic_prefix
                )
                self.mqtt_publisher.connect()
                logger.info(f"MQTT publisher connected to {mqtt_broker}:{mqtt_port}")
            except Exception as e:
                logger.warning(f"Failed to initialize MQTT publisher: {e}")
                self.mqtt_publisher = None
        
        # Track last publish time for rate limiting
        self.last_publish_time = time.time()
        self.publish_interval = float(os.getenv('MQTT_PUBLISH_INTERVAL', 1.0))  # seconds
        
        logger.info(f"PacketAnalyzer initialized on interface: {interface}")
        logger.info(f"Output directory: {output_dir}")
    
    def packet_callback(self, packet):
        """
        Process each captured packet.
        
        Args:
            packet: Scapy packet object
        """
        try:
            self.packet_count += 1
            
            # Identify protocol
            protocol = ProtocolIdentifier.identify(packet)
            
            # Update statistics
            if protocol:
                self.protocol_stats[protocol] = self.protocol_stats.get(protocol, 0) + 1
            
            # Extract flow information and component stats
            if packet.haslayer(IP):
                ip_layer = packet[IP]
                flow_key = f"{ip_layer.src}->{ip_layer.dst}"
                self.flow_stats[flow_key] = self.flow_stats.get(flow_key, 0) + 1
                
                # Track component stats based on IP addresses
                packet_bytes = len(packet)
                self._update_component_stats(ip_layer.src, ip_layer.dst, protocol, packet_bytes)
            
            # Save to pcap buffer
            self.current_pcap_packets.append(packet)
            
            # Log statistics periodically
            if self.packet_count % 100 == 0:
                self._log_stats()
            
            # Publish to MQTT periodically
            if self.mqtt_publisher and (time.time() - self.last_publish_time) >= self.publish_interval:
                self._publish_mqtt_stats()
                self.last_publish_time = time.time()
            
            # Rotate pcap file periodically
            if len(self.current_pcap_packets) >= self.pcap_rotation_count:
                self._save_pcap()
        
        except Exception as e:
            logger.error(f"Error processing packet: {e}")
    
    def _save_pcap(self):
        """
        Save captured packets to pcap file.
        
        Saves buffered packets to a timestamped pcap file and clears buffer.
        """
        try:
            if not self.current_pcap_packets:
                return
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = self.output_dir / f"capture_{timestamp}.pcap"
            
            wrpcap(str(filename), self.current_pcap_packets)
            logger.info(f"Saved {len(self.current_pcap_packets)} packets to {filename}")
            
            self.current_pcap_packets = []
        except Exception as e:
            logger.error(f"Error saving pcap: {e}")
    
    def _update_component_stats(self, src_ip: str, dst_ip: str, protocol: Optional[str], packet_bytes: int):
        """
        Update component statistics based on IP addresses.
        
        Args:
            src_ip (str): Source IP address
            dst_ip (str): Destination IP address
            protocol (str): Protocol name
            packet_bytes (int): Packet size in bytes
        """
        # Map IP addresses to components
        # Assuming: 10.0.1.10=master, 10.0.1.20=vcc, 10.0.1.30=upf, 10.0.1.40=gen
        ip_to_component = {
            '10.0.1.10': 'master',
            '10.0.1.20': 'vcc',
            '10.0.1.30': 'upf',
            '10.0.1.40': 'gen'
        }
        
        # Update stats for source and destination components
        for ip, component in ip_to_component.items():
            if src_ip == ip or dst_ip == ip:
                self.component_stats[component]['packets'] += 1
                self.component_stats[component]['bytes'] += packet_bytes
                
                if protocol:
                    if protocol not in self.component_stats[component]['protocols']:
                        self.component_stats[component]['protocols'][protocol] = 0
                    self.component_stats[component]['protocols'][protocol] += 1
    
    def _publish_mqtt_stats(self):
        """
        Publish statistics to MQTT broker.
        
        Publishes current statistics to MQTT topics for consumption by FUXA.
        """
        if not self.mqtt_publisher or not self.mqtt_publisher.is_connected():
            return
        
        try:
            # Calculate packet rate
            packet_rate = self.packet_count / max(1, time.time())
            
            # Prepare statistics
            stats = {
                'total_packets': self.packet_count,
                'packet_rate': packet_rate,
                'protocol_distribution': self.protocol_stats,
                'top_flows': sorted(
                    self.flow_stats.items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:10],
                'components': self.component_stats
            }
            
            # Publish to MQTT
            self.mqtt_publisher.publish_all(stats)
            logger.debug(f"Published statistics to MQTT (packets: {self.packet_count})")
        
        except Exception as e:
            logger.error(f"Error publishing MQTT stats: {e}")
    
    def _log_stats(self):
        """
        Log current statistics.
        
        Logs packet count, protocol distribution, and top flows.
        """
        stats = {
            'timestamp': datetime.now().isoformat(),
            'total_packets': self.packet_count,
            'protocol_distribution': self.protocol_stats,
            'top_flows': sorted(
                self.flow_stats.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
        }
        logger.info(f"Statistics: {json.dumps(stats, indent=2)}")
    
    def start_capture(self):
        """
        Start packet capture.
        
        Begins capturing packets from the configured interface.
        Blocks until capture is stopped.
        """
        logger.info(f"Starting packet capture on {self.interface}...")
        try:
            sniff(
                iface=self.interface,
                prn=self.packet_callback,
                store=False,
                stop_filter=lambda x: not self.running
            )
        except Exception as e:
            logger.error(f"Capture error: {e}")
            raise
    
    def stop_capture(self):
        """
        Stop packet capture.
        
        Saves any remaining packets and logs final statistics.
        """
        logger.info("Stopping packet capture...")
        self.running = False
        self._save_pcap()
        
        # Publish final statistics
        if self.mqtt_publisher:
            try:
                self._publish_mqtt_stats()
                self.mqtt_publisher.disconnect()
                logger.info("MQTT publisher disconnected")
            except Exception as e:
                logger.warning(f"Error disconnecting MQTT publisher: {e}")
        
        logger.info(f"Total packets captured: {self.packet_count}")
        self._log_stats()


def signal_handler(signum, frame):
    """
    Handle interrupt signals.
    
    Args:
        signum: Signal number
        frame: Current stack frame
    """
    logger.info("Received interrupt signal")
    sys.exit(0)


def main():
    """
    Main entry point.
    
    Initializes analyzer with environment variables and starts packet capture.
    """
    interface = os.getenv('CAPTURE_INTERFACE', 'veth-analyzer')
    output_dir = os.getenv('OUTPUT_DIR', '/pcap')
    
    logger.info("VPP Protocol Analyzer starting...")
    logger.info(f"Interface: {interface}")
    logger.info(f"Output directory: {output_dir}")
    
    analyzer = PacketAnalyzer(interface, output_dir)
    
    # Register signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        analyzer.start_capture()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        analyzer.stop_capture()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
