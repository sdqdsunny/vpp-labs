"""
Event Generator Service

Converts raw packets into standardized visualization events.
"""

import logging
from datetime import datetime
from typing import Dict, Optional
from collections import defaultdict

from models.raw_packet import RawPacket
from models.visualization_event import VisualizationEvent
from services.traffic_classifier import TrafficClassifier

logger = logging.getLogger(__name__)


class EventGenerator:
    """
    Generates standardized visualization events from raw packets
    
    Features:
    - Converts RawPacket to VisualizationEvent
    - Calculates traffic intensity based on packet size and frequency
    - Maps IP addresses to VPP component names
    - Tracks packet frequency for intensity calculation
    """
    
    # VPP component IP mapping
    VPP_COMPONENTS = {
        '10.0.8.1': 'Master',
        '10.0.8.2': 'Power_01',
        '10.0.8.3': 'Storage_01',
        '10.0.8.4': 'Demand_01',
    }
    
    # Intensity calculation parameters
    MIN_PACKET_SIZE = 64      # Minimum packet size in bytes
    MAX_PACKET_SIZE = 65535   # Maximum packet size in bytes
    INTENSITY_WINDOW = 1.0    # Time window for frequency calculation (seconds)
    
    def __init__(self):
        """Initialize the event generator"""
        self.classifier = TrafficClassifier()
        self.packet_frequency = defaultdict(list)  # Track packet timestamps per flow
        logger.info("EventGenerator initialized")
    
    def generate_event(self, packet: RawPacket) -> Optional[VisualizationEvent]:
        """
        Generate a visualization event from a raw packet
        
        Args:
            packet: RawPacket object
        
        Returns:
            VisualizationEvent or None if event cannot be generated
        """
        try:
            # Map IPs to component names
            from_component = self.map_ip_to_component(packet.src_ip)
            to_component = self.map_ip_to_component(packet.dst_ip)
            
            # Skip if either component is unknown
            if from_component == 'Unknown' or to_component == 'Unknown':
                logger.debug(f"Skipping packet with unknown component: {packet.src_ip} -> {packet.dst_ip}")
                return None
            
            # Classify traffic type
            traffic_type = self.classifier.classify(
                packet.src_ip,
                packet.dst_ip,
                packet.src_port,
                packet.dst_port,
                packet.protocol
            )
            
            # Calculate intensity
            flow_key = (from_component, to_component)
            intensity = self.calculate_intensity(packet.packet_size, flow_key, packet.timestamp)
            
            # Create visualization event
            event = VisualizationEvent(
                from_component=from_component,
                to_component=to_component,
                traffic_type=traffic_type,
                intensity=intensity,
                packet_size=packet.packet_size,
                timestamp=packet.timestamp
            )
            
            logger.debug(f"Generated event: {event}")
            return event
        
        except Exception as e:
            logger.error(f"Error generating event from packet: {e}")
            return None
    
    def calculate_intensity(self, packet_size: int, flow_key: tuple, 
                           timestamp: datetime) -> float:
        """
        Calculate traffic intensity (0.0-1.0)
        
        Intensity is based on:
        - Packet size (larger packets = higher intensity)
        - Packet frequency (more frequent packets = higher intensity)
        
        Args:
            packet_size: Packet size in bytes
            flow_key: Tuple of (from_component, to_component)
            timestamp: Packet timestamp
        
        Returns:
            Intensity value between 0.0 and 1.0
        """
        try:
            # Normalize packet size to 0.0-1.0
            size_intensity = min(
                (packet_size - self.MIN_PACKET_SIZE) / 
                (self.MAX_PACKET_SIZE - self.MIN_PACKET_SIZE),
                1.0
            )
            size_intensity = max(size_intensity, 0.0)
            
            # Calculate frequency intensity
            # Clean up old timestamps outside the window
            cutoff_time = timestamp.timestamp() - self.INTENSITY_WINDOW
            self.packet_frequency[flow_key] = [
                ts for ts in self.packet_frequency[flow_key]
                if ts > cutoff_time
            ]
            
            # Add current packet timestamp
            self.packet_frequency[flow_key].append(timestamp.timestamp())
            
            # Calculate frequency (packets per second)
            packet_count = len(self.packet_frequency[flow_key])
            frequency_intensity = min(packet_count / 100.0, 1.0)  # Normalize to 100 packets/sec
            
            # Combine size and frequency (weighted average)
            # Size: 40%, Frequency: 60%
            combined_intensity = (size_intensity * 0.4) + (frequency_intensity * 0.6)
            
            return min(combined_intensity, 1.0)
        
        except Exception as e:
            logger.error(f"Error calculating intensity: {e}")
            return 0.5  # Default to medium intensity on error
    
    def map_ip_to_component(self, ip: str) -> str:
        """
        Map IP address to VPP component name
        
        Args:
            ip: IP address
        
        Returns:
            Component name or 'Unknown'
        """
        return self.VPP_COMPONENTS.get(ip, 'Unknown')
    
    def get_component_ip(self, component_name: str) -> Optional[str]:
        """
        Get IP address for a component name
        
        Args:
            component_name: Component name
        
        Returns:
            IP address or None
        """
        for ip, name in self.VPP_COMPONENTS.items():
            if name == component_name:
                return ip
        return None
    
    def add_component_mapping(self, ip: str, component_name: str):
        """
        Add custom IP to component mapping
        
        Args:
            ip: IP address
            component_name: Component name
        """
        self.VPP_COMPONENTS[ip] = component_name
        logger.info(f"Added component mapping: {ip} -> {component_name}")
    
    def remove_component_mapping(self, ip: str):
        """
        Remove IP to component mapping
        
        Args:
            ip: IP address
        """
        if ip in self.VPP_COMPONENTS:
            del self.VPP_COMPONENTS[ip]
            logger.info(f"Removed component mapping for {ip}")
    
    def get_component_mappings(self) -> Dict[str, str]:
        """Get all IP to component mappings"""
        return self.VPP_COMPONENTS.copy()
    
    def clear_frequency_data(self):
        """Clear packet frequency tracking data"""
        self.packet_frequency.clear()
        logger.info("Cleared packet frequency data")
