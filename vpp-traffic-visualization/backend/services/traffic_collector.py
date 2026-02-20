"""
Traffic Collector Service

Collects network traffic from OVS mirror port and parses packets.
Supports both PCAP files and JSON data sources.
"""

import json
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path

try:
    from scapy.all import rdpcap, IP, TCP, UDP, ICMP
    SCAPY_AVAILABLE = True
except ImportError:
    SCAPY_AVAILABLE = False

from models.raw_packet import RawPacket

logger = logging.getLogger(__name__)


class TrafficCollectorService:
    """
    Service for collecting and parsing network traffic
    
    Supports:
    - PCAP file reading
    - JSON data source reading
    - Packet parsing and extraction
    """
    
    def __init__(self, pcap_file: Optional[str] = None, json_source: Optional[str] = None):
        """
        Initialize the traffic collector
        
        Args:
            pcap_file: Path to PCAP file
            json_source: Path to JSON file or URL
        """
        self.pcap_file = pcap_file
        self.json_source = json_source
        self.packets: List[RawPacket] = []
        self.is_collecting = False
        
        logger.info(f"TrafficCollectorService initialized with pcap_file={pcap_file}, json_source={json_source}")
    
    def start_collection(self) -> bool:
        """
        Start traffic collection
        
        Returns:
            True if collection started successfully, False otherwise
        """
        try:
            self.is_collecting = True
            logger.info("Traffic collection started")
            return True
        except Exception as e:
            logger.error(f"Failed to start traffic collection: {e}")
            self.is_collecting = False
            return False
    
    def stop_collection(self) -> bool:
        """
        Stop traffic collection
        
        Returns:
            True if collection stopped successfully
        """
        try:
            self.is_collecting = False
            logger.info("Traffic collection stopped")
            return True
        except Exception as e:
            logger.error(f"Failed to stop traffic collection: {e}")
            return False
    
    def read_pcap(self) -> List[RawPacket]:
        """
        Read and parse PCAP file
        
        Returns:
            List of RawPacket objects
        """
        if not self.pcap_file:
            logger.warning("No PCAP file specified")
            return []
        
        if not SCAPY_AVAILABLE:
            logger.error("Scapy is not available. Cannot read PCAP files.")
            return []
        
        try:
            pcap_path = Path(self.pcap_file)
            if not pcap_path.exists():
                logger.error(f"PCAP file not found: {self.pcap_file}")
                return []
            
            packets = rdpcap(str(pcap_path))
            logger.info(f"Read {len(packets)} packets from {self.pcap_file}")
            
            raw_packets = []
            for packet in packets:
                raw_packet = self._parse_packet(packet)
                if raw_packet:
                    raw_packets.append(raw_packet)
            
            self.packets = raw_packets
            logger.info(f"Parsed {len(raw_packets)} packets from PCAP file")
            return raw_packets
        
        except Exception as e:
            logger.error(f"Error reading PCAP file: {e}")
            return []
    
    def read_json(self) -> List[RawPacket]:
        """
        Read and parse JSON data source
        
        Returns:
            List of RawPacket objects
        """
        if not self.json_source:
            logger.warning("No JSON source specified")
            return []
        
        try:
            json_path = Path(self.json_source)
            
            if json_path.exists():
                # Read from file
                with open(json_path, 'r') as f:
                    data = json.load(f)
            else:
                # Try to parse as JSON string
                data = json.loads(self.json_source)
            
            raw_packets = []
            
            # Handle both single packet and list of packets
            if isinstance(data, list):
                packets_data = data
            elif isinstance(data, dict):
                packets_data = [data]
            else:
                logger.error(f"Invalid JSON format: {type(data)}")
                return []
            
            for packet_data in packets_data:
                raw_packet = RawPacket.from_dict(packet_data)
                raw_packets.append(raw_packet)
            
            self.packets = raw_packets
            logger.info(f"Parsed {len(raw_packets)} packets from JSON source")
            return raw_packets
        
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON format: {e}")
            return []
        except Exception as e:
            logger.error(f"Error reading JSON source: {e}")
            return []
    
    def _parse_packet(self, packet: Any) -> Optional[RawPacket]:
        """
        Parse a single packet from Scapy
        
        Args:
            packet: Scapy packet object
        
        Returns:
            RawPacket object or None if parsing fails
        """
        try:
            if not packet.haslayer(IP):
                return None
            
            ip_layer = packet[IP]
            src_ip = ip_layer.src
            dst_ip = ip_layer.dst
            protocol = ip_layer.proto
            
            # Determine protocol name
            protocol_name = self._get_protocol_name(protocol)
            
            # Extract port information
            src_port = 0
            dst_port = 0
            
            if packet.haslayer(TCP):
                tcp_layer = packet[TCP]
                src_port = tcp_layer.sport
                dst_port = tcp_layer.dport
            elif packet.haslayer(UDP):
                udp_layer = packet[UDP]
                src_port = udp_layer.sport
                dst_port = udp_layer.dport
            
            # Get packet size
            packet_size = len(packet)
            
            # Create RawPacket
            raw_packet = RawPacket(
                src_ip=src_ip,
                dst_ip=dst_ip,
                src_port=src_port,
                dst_port=dst_port,
                protocol=protocol_name,
                packet_size=packet_size,
                timestamp=datetime.now(),
                payload=bytes(packet.payload) if packet.payload else None
            )
            
            return raw_packet
        
        except Exception as e:
            logger.debug(f"Error parsing packet: {e}")
            return None
    
    @staticmethod
    def _get_protocol_name(protocol_num: int) -> str:
        """
        Get protocol name from protocol number
        
        Args:
            protocol_num: Protocol number
        
        Returns:
            Protocol name
        """
        protocol_map = {
            1: 'ICMP',
            6: 'TCP',
            17: 'UDP',
            41: 'IPv6',
            47: 'GRE',
            50: 'ESP',
            51: 'AH'
        }
        return protocol_map.get(protocol_num, f'Protocol_{protocol_num}')
    
    def parse_packet(self, packet_data: Dict[str, Any]) -> Optional[RawPacket]:
        """
        Parse a packet from dictionary format
        
        Args:
            packet_data: Packet data as dictionary
        
        Returns:
            RawPacket object or None if parsing fails
        """
        try:
            return RawPacket.from_dict(packet_data)
        except Exception as e:
            logger.error(f"Error parsing packet data: {e}")
            return None
    
    def get_packets(self) -> List[RawPacket]:
        """
        Get collected packets
        
        Returns:
            List of RawPacket objects
        """
        return self.packets
    
    def clear_packets(self):
        """Clear collected packets"""
        self.packets = []
        logger.info("Cleared collected packets")
