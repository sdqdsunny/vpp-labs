"""
VPP Data Connector Service

Connects to the VPP simulation system to fetch real-time traffic data
and convert it to visualization events.
"""

import logging
import requests
import threading
import time
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from collections import defaultdict

from models.raw_packet import RawPacket
from models.visualization_event import VisualizationEvent
from services.traffic_classifier import TrafficClassifier

logger = logging.getLogger(__name__)


class VPPDataConnector:
    """
    Connects to VPP simulation system and fetches real-time traffic data
    
    Features:
    - Fetches traffic data from VPP API endpoints
    - Converts traffic data to visualization events
    - Maintains connection to VPP system
    - Handles data transformation and mapping
    """
    
    # VPP API endpoints
    VPP_API_BASE = os.getenv('VPP_API_BASE', "http://localhost:8001")
    VPP_REALTIME_ENDPOINT = "/api/vpp/realtime"
    VPP_ANALYZER_STATS = "/api/analyzer/stats"
    VPP_ANALYZER_PACKETS = "/api/analyzer/packets"
    
    # Component mapping (IP -> Component Name)
    VPP_COMPONENTS = {
        'power_generation': 'Power_Generation',
        'storage': 'Storage',
        'demand': 'Demand',
        'coordinator': 'Coordinator',
    }
    
    def __init__(self, vpp_api_base: str = None):
        """
        Initialize the VPP data connector
        
        Args:
            vpp_api_base: Base URL for VPP API (default: http://localhost:8001)
        """
        self.vpp_api_base = vpp_api_base or self.VPP_API_BASE
        self.classifier = TrafficClassifier()
        self.is_connected = False
        self.last_packet_count = 0
        self.packet_frequency = defaultdict(list)
        self.is_running = False
        self.fetch_thread = None
        
        logger.info(f"VPPDataConnector initialized with API base: {self.vpp_api_base}")
    
    def connect(self) -> bool:
        """
        Test connection to VPP API
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            response = requests.get(
                f"{self.vpp_api_base}/api/vpp/realtime",
                timeout=5
            )
            if response.status_code == 200:
                self.is_connected = True
                logger.info("Successfully connected to VPP API")
                return True
            else:
                logger.error(f"VPP API returned status {response.status_code}")
                self.is_connected = False
                return False
        except Exception as e:
            logger.error(f"Failed to connect to VPP API: {e}")
            self.is_connected = False
            return False
    
    def start_fetching(self):
        """Start fetching data from VPP in background thread"""
        if self.is_running:
            logger.warning("Data fetching already running")
            return
        
        self.is_running = True
        self.fetch_thread = threading.Thread(target=self._fetch_loop, daemon=True)
        self.fetch_thread.start()
        logger.info("Started VPP data fetching thread")
    
    def stop_fetching(self):
        """Stop fetching data from VPP"""
        self.is_running = False
        if self.fetch_thread:
            self.fetch_thread.join(timeout=5)
        logger.info("Stopped VPP data fetching thread")
    
    def _fetch_loop(self):
        """Background loop to fetch data from VPP"""
        while self.is_running:
            try:
                # Fetch traffic statistics
                stats = self.fetch_traffic_stats()
                if stats:
                    logger.debug(f"Fetched traffic stats: {len(stats)} protocols")
                
                # Fetch real-time data
                realtime_data = self.fetch_realtime_data()
                if realtime_data:
                    logger.debug(f"Fetched realtime data: {realtime_data.keys()}")
                
                # Sleep before next fetch
                time.sleep(1)
            
            except Exception as e:
                logger.error(f"Error in fetch loop: {e}")
                time.sleep(2)
    
    def fetch_realtime_data(self) -> Optional[Dict[str, Any]]:
        """
        Fetch real-time VPP data
        
        Returns:
            Dictionary with real-time data or None if fetch fails
        """
        try:
            response = requests.get(
                f"{self.vpp_api_base}{self.VPP_REALTIME_ENDPOINT}",
                timeout=5
            )
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Failed to fetch realtime data: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error fetching realtime data: {e}")
            return None
    
    def fetch_traffic_stats(self) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch traffic statistics from analyzer
        
        Returns:
            List of protocol statistics or None if fetch fails
        """
        try:
            response = requests.get(
                f"{self.vpp_api_base}{self.VPP_ANALYZER_STATS}",
                timeout=5
            )
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Failed to fetch traffic stats: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error fetching traffic stats: {e}")
            return None
    
    def fetch_packets(self, limit: int = 100) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch recent packets from analyzer
        
        Args:
            limit: Maximum number of packets to fetch
        
        Returns:
            List of packets or None if fetch fails
        """
        try:
            response = requests.get(
                f"{self.vpp_api_base}{self.VPP_ANALYZER_PACKETS}",
                params={'limit': limit},
                timeout=5
            )
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Failed to fetch packets: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Error fetching packets: {e}")
            return None
    
    def convert_realtime_to_events(self, realtime_data: Dict[str, Any]) -> List[VisualizationEvent]:
        """
        Convert real-time VPP data to visualization events
        
        Args:
            realtime_data: Real-time data from VPP API
        
        Returns:
            List of VisualizationEvent objects
        """
        events = []
        
        try:
            # Extract component data
            power_data = realtime_data.get('power_generation', {})
            storage_data = realtime_data.get('storage', {})
            demand_data = realtime_data.get('demand', {})
            energy_balance = realtime_data.get('energy_balance', {})
            
            # Create events for energy flows
            # Power -> Storage
            if power_data.get('current_power', 0) > 0:
                event = VisualizationEvent(
                    from_component='Power_01',
                    to_component='Storage_01',
                    traffic_type='Control',
                    intensity=self._calculate_intensity_from_power(power_data.get('current_power', 0)),
                    packet_size=150,
                    timestamp=datetime.now()
                )
                events.append(event)
            
            # Storage -> Demand
            if storage_data.get('current_power', 0) > 0:
                event = VisualizationEvent(
                    from_component='Storage_01',
                    to_component='Demand_01',
                    traffic_type='Telemetry',
                    intensity=self._calculate_intensity_from_power(storage_data.get('current_power', 0)),
                    packet_size=150,
                    timestamp=datetime.now()
                )
                events.append(event)
            
            # Power -> Demand (direct supply)
            if power_data.get('current_power', 0) > 0 and demand_data.get('current_demand', 0) > 0:
                event = VisualizationEvent(
                    from_component='Power_01',
                    to_component='Demand_01',
                    traffic_type='Control',
                    intensity=self._calculate_intensity_from_power(
                        min(power_data.get('current_power', 0), demand_data.get('current_demand', 0))
                    ),
                    packet_size=150,
                    timestamp=datetime.now()
                )
                events.append(event)
            
            # Coordinator monitoring (bidirectional)
            event = VisualizationEvent(
                from_component='Coordinator',
                to_component='Power_01',
                traffic_type='Telemetry',
                intensity=0.3,
                packet_size=80,
                timestamp=datetime.now()
            )
            events.append(event)
            
            event = VisualizationEvent(
                from_component='Coordinator',
                to_component='Storage_01',
                traffic_type='Telemetry',
                intensity=0.3,
                packet_size=80,
                timestamp=datetime.now()
            )
            events.append(event)
            
            event = VisualizationEvent(
                from_component='Coordinator',
                to_component='Demand_01',
                traffic_type='Telemetry',
                intensity=0.3,
                packet_size=80,
                timestamp=datetime.now()
            )
            events.append(event)
            
            logger.debug(f"Converted realtime data to {len(events)} events")
            return events
        
        except Exception as e:
            logger.error(f"Error converting realtime data to events: {e}")
            return []
    
    def convert_packets_to_events(self, packets: List[Dict[str, Any]]) -> List[VisualizationEvent]:
        """
        Convert packet data to visualization events
        
        Args:
            packets: List of packet dictionaries
        
        Returns:
            List of VisualizationEvent objects
        """
        events = []
        
        try:
            for packet_data in packets:
                try:
                    # Normalize packet data (handle both 'size' and 'packet_size' keys)
                    normalized_data = packet_data.copy()
                    if 'size' in normalized_data and 'packet_size' not in normalized_data:
                        normalized_data['packet_size'] = normalized_data['size']
                    
                    # Ensure timestamp is present
                    if 'timestamp' not in normalized_data:
                        normalized_data['timestamp'] = datetime.now().isoformat()
                    
                    # Create RawPacket from data
                    raw_packet = RawPacket.from_dict(normalized_data)
                    
                    # Map to components (using protocol as component indicator)
                    protocol = packet_data.get('protocol', 'Unknown')
                    from_component = self._map_protocol_to_component(protocol, 'source')
                    to_component = self._map_protocol_to_component(protocol, 'dest')
                    
                    # Skip if both components are the same (no flow)
                    if from_component == to_component:
                        continue
                    
                    # Classify traffic
                    traffic_type = self.classifier.classify(
                        packet_data.get('src_ip', ''),
                        packet_data.get('dst_ip', ''),
                        packet_data.get('src_port', 0),
                        packet_data.get('dst_port', 0),
                        protocol
                    )
                    
                    # Calculate intensity
                    flow_key = (from_component, to_component)
                    intensity = self._calculate_packet_intensity(
                        packet_data.get('size', packet_data.get('packet_size', 100)),
                        flow_key
                    )
                    
                    # Create event
                    event = VisualizationEvent(
                        from_component=from_component,
                        to_component=to_component,
                        traffic_type=traffic_type,
                        intensity=intensity,
                        packet_size=packet_data.get('size', packet_data.get('packet_size', 100)),
                        timestamp=datetime.now()
                    )
                    events.append(event)
                
                except Exception as e:
                    logger.debug(f"Error converting packet to event: {e}")
                    continue
            
            logger.debug(f"Converted {len(packets)} packets to {len(events)} events")
            return events
        
        except Exception as e:
            logger.error(f"Error converting packets to events: {e}")
            return []
    
    def _calculate_intensity_from_power(self, power_value: float) -> float:
        """
        Calculate intensity from power value
        
        Args:
            power_value: Power value in kW
        
        Returns:
            Intensity value between 0.0 and 1.0
        """
        # Normalize to 0-200 kW range
        intensity = min(power_value / 200.0, 1.0)
        return max(intensity, 0.0)
    
    def _calculate_packet_intensity(self, packet_size: int, flow_key: tuple) -> float:
        """
        Calculate intensity from packet size and frequency
        
        Args:
            packet_size: Packet size in bytes
            flow_key: Tuple of (from_component, to_component)
        
        Returns:
            Intensity value between 0.0 and 1.0
        """
        # Normalize packet size (64-1500 bytes)
        size_intensity = min((packet_size - 64) / (1500 - 64), 1.0)
        size_intensity = max(size_intensity, 0.0)
        
        # Track frequency
        current_time = time.time()
        cutoff_time = current_time - 1.0  # 1 second window
        
        self.packet_frequency[flow_key] = [
            ts for ts in self.packet_frequency[flow_key]
            if ts > cutoff_time
        ]
        self.packet_frequency[flow_key].append(current_time)
        
        # Calculate frequency intensity
        packet_count = len(self.packet_frequency[flow_key])
        frequency_intensity = min(packet_count / 100.0, 1.0)
        
        # Combine (40% size, 60% frequency)
        combined = (size_intensity * 0.4) + (frequency_intensity * 0.6)
        return min(combined, 1.0)
    
    def _map_protocol_to_component(self, protocol: str, direction: str = 'source') -> str:
        """
        Map protocol to VPP component
        
        Args:
            protocol: Protocol name
            direction: 'source' or 'dest'
        
        Returns:
            Component name or 'Unknown'
        """
        protocol_lower = protocol.lower()
        
        # Map protocols to components based on typical usage patterns
        if 'mqtt' in protocol_lower or 'modbus' in protocol_lower:
            # Power generation typically uses MQTT/Modbus
            if direction == 'source':
                return 'Power_Generation'
            else:
                return 'Coordinator'
        elif 'opc' in protocol_lower or 'dnp3' in protocol_lower:
            # Storage typically uses OPC UA/DNP3
            if direction == 'source':
                return 'Storage'
            else:
                return 'Coordinator'
        elif 'xmpp' in protocol_lower or 'lorawan' in protocol_lower:
            # Demand typically uses XMPP/LoRaWAN
            if direction == 'source':
                return 'Demand'
            else:
                return 'Coordinator'
        else:
            # For unknown protocols, use Coordinator as both source and dest
            # to ensure events are generated
            return 'Coordinator'
    
    def get_connection_status(self) -> Dict[str, Any]:
        """
        Get connection status information
        
        Returns:
            Dictionary with connection status
        """
        return {
            'connected': self.is_connected,
            'api_base': self.vpp_api_base,
            'is_fetching': self.is_running,
            'timestamp': datetime.now().isoformat()
        }
