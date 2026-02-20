"""
Traffic Classifier Service

Classifies network traffic into Control or Telemetry types.
"""

import logging
from typing import Literal, Dict, List, Tuple

logger = logging.getLogger(__name__)


class TrafficClassifier:
    """
    Classifies network traffic based on IP addresses, ports, and protocols
    
    Features:
    - Automatic traffic type detection
    - Custom classification rules
    - Support for control and telemetry traffic
    """
    
    # Default control traffic ports
    DEFAULT_CONTROL_PORTS = {
        5000,   # VCC Master API
        8080,   # WebSocket
        8000,   # Alternative API
        9000,   # Alternative API
    }
    
    # Default telemetry traffic ports
    DEFAULT_TELEMETRY_PORTS = {
        5001,   # Telemetry reporting
        5002,   # Telemetry reporting
        8081,   # Alternative telemetry
    }
    
    # VPP component IP ranges
    VPP_COMPONENTS = {
        '10.0.8.1': 'Master',
        '10.0.8.2': 'Power_01',
        '10.0.8.3': 'Storage_01',
        '10.0.8.4': 'Demand_01',
    }
    
    def __init__(self):
        """Initialize the traffic classifier"""
        self.control_ports = self.DEFAULT_CONTROL_PORTS.copy()
        self.telemetry_ports = self.DEFAULT_TELEMETRY_PORTS.copy()
        logger.info("TrafficClassifier initialized")
    
    def classify(self, src_ip: str, dst_ip: str, src_port: int, dst_port: int, 
                 protocol: str) -> Literal['Control', 'Telemetry']:
        """
        Classify traffic type
        
        Args:
            src_ip: Source IP address
            dst_ip: Destination IP address
            src_port: Source port
            dst_port: Destination port
            protocol: Protocol type (TCP, UDP, etc.)
        
        Returns:
            'Control' or 'Telemetry'
        """
        try:
            # Check if it's control traffic
            if self.is_control_traffic(src_ip, dst_ip, src_port, dst_port, protocol):
                return 'Control'
            
            # Check if it's telemetry traffic
            if self.is_telemetry_traffic(src_ip, dst_ip, src_port, dst_port, protocol):
                return 'Telemetry'
            
            # Default to Telemetry if uncertain
            return 'Telemetry'
        
        except Exception as e:
            logger.error(f"Error classifying traffic: {e}")
            return 'Telemetry'
    
    def is_control_traffic(self, src_ip: str, dst_ip: str, src_port: int, 
                          dst_port: int, protocol: str) -> bool:
        """
        Check if traffic is control traffic
        
        Control traffic characteristics:
        - From/to VCC Master (10.0.8.1)
        - Uses control ports
        - TCP protocol
        
        Args:
            src_ip: Source IP address
            dst_ip: Destination IP address
            src_port: Source port
            dst_port: Destination port
            protocol: Protocol type
        
        Returns:
            True if traffic is control traffic, False otherwise
        """
        try:
            # Check if destination is VCC Master
            if dst_ip == '10.0.8.1':
                # Commands from Master to other components
                if src_ip == '10.0.8.1' and dst_port in self.control_ports:
                    return True
                # Responses from components to Master
                if src_port in self.control_ports:
                    return True
            
            # Check if source is VCC Master sending commands
            if src_ip == '10.0.8.1' and dst_port in self.control_ports:
                return True
            
            # Check protocol
            if protocol not in ('TCP', 'UDP'):
                return False
            
            return False
        
        except Exception as e:
            logger.debug(f"Error checking control traffic: {e}")
            return False
    
    def is_telemetry_traffic(self, src_ip: str, dst_ip: str, src_port: int, 
                            dst_port: int, protocol: str) -> bool:
        """
        Check if traffic is telemetry traffic
        
        Telemetry traffic characteristics:
        - From components to VCC Master (10.0.8.1)
        - Uses telemetry ports
        - Regular data reporting
        
        Args:
            src_ip: Source IP address
            dst_ip: Destination IP address
            src_port: Source port
            dst_port: Destination port
            protocol: Protocol type
        
        Returns:
            True if traffic is telemetry traffic, False otherwise
        """
        try:
            # Check if destination is VCC Master
            if dst_ip == '10.0.8.1':
                # Data reporting from components
                if src_ip in self.VPP_COMPONENTS and src_ip != '10.0.8.1':
                    return True
                # Using telemetry ports
                if dst_port in self.telemetry_ports:
                    return True
            
            # Check if source is component sending telemetry
            if src_ip in self.VPP_COMPONENTS and src_ip != '10.0.8.1':
                if dst_ip == '10.0.8.1':
                    return True
            
            return False
        
        except Exception as e:
            logger.debug(f"Error checking telemetry traffic: {e}")
            return False
    
    def add_control_port(self, port: int):
        """
        Add custom control port
        
        Args:
            port: Port number
        """
        self.control_ports.add(port)
        logger.info(f"Added control port: {port}")
    
    def add_telemetry_port(self, port: int):
        """
        Add custom telemetry port
        
        Args:
            port: Port number
        """
        self.telemetry_ports.add(port)
        logger.info(f"Added telemetry port: {port}")
    
    def remove_control_port(self, port: int):
        """
        Remove control port
        
        Args:
            port: Port number
        """
        self.control_ports.discard(port)
        logger.info(f"Removed control port: {port}")
    
    def remove_telemetry_port(self, port: int):
        """
        Remove telemetry port
        
        Args:
            port: Port number
        """
        self.telemetry_ports.discard(port)
        logger.info(f"Removed telemetry port: {port}")
    
    def get_control_ports(self) -> List[int]:
        """Get list of control ports"""
        return sorted(list(self.control_ports))
    
    def get_telemetry_ports(self) -> List[int]:
        """Get list of telemetry ports"""
        return sorted(list(self.telemetry_ports))
    
    def get_component_name(self, ip: str) -> str:
        """
        Get component name from IP address
        
        Args:
            ip: IP address
        
        Returns:
            Component name or 'Unknown'
        """
        return self.VPP_COMPONENTS.get(ip, 'Unknown')
