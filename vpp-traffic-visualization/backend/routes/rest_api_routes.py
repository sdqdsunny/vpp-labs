"""
REST API Routes for VPP Traffic Visualization Engine

Provides REST endpoints for:
- Component information
- Traffic statistics
- System health
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)


class RestAPIRoutes:
    """
    REST API route handlers for traffic visualization
    
    Provides endpoints for:
    - GET /api/visualization/components - Component information
    - GET /api/visualization/statistics - Traffic statistics
    """
    
    def __init__(self, traffic_collector=None, event_generator=None):
        """
        Initialize REST API routes
        
        Args:
            traffic_collector: TrafficCollectorService instance
            event_generator: EventGenerator instance
        """
        self.traffic_collector = traffic_collector
        self.event_generator = event_generator
        self.traffic_stats = defaultdict(lambda: {
            'total_packets': 0,
            'total_bytes': 0,
            'control_packets': 0,
            'telemetry_packets': 0,
            'control_bytes': 0,
            'telemetry_bytes': 0,
            'traffic_by_component': defaultdict(lambda: {
                'packets': 0,
                'bytes': 0,
                'control': 0,
                'telemetry': 0
            })
        })
        logger.info("RestAPIRoutes initialized")
    
    def get_components(self) -> Dict[str, Any]:
        """
        Get VPP system components information
        
        Returns:
            Dictionary with components list
        """
        try:
            components = [
                {
                    'name': 'Master',
                    'ip': '10.0.8.1',
                    'type': 'coordinator',
                    'status': 'online',
                    'color': '#FF6B6B'
                },
                {
                    'name': 'Power_01',
                    'ip': '10.0.8.2',
                    'type': 'power',
                    'status': 'online',
                    'color': '#FFA500'
                },
                {
                    'name': 'Storage_01',
                    'ip': '10.0.8.3',
                    'type': 'storage',
                    'status': 'online',
                    'color': '#4ECDC4'
                },
                {
                    'name': 'Demand_01',
                    'ip': '10.0.8.4',
                    'type': 'demand',
                    'status': 'online',
                    'color': '#95E1D3'
                }
            ]
            
            logger.info(f"Retrieved {len(components)} components")
            return {
                'components': components,
                'timestamp': datetime.now().isoformat(),
                'total_components': len(components)
            }
        
        except Exception as e:
            logger.error(f"Error getting components: {e}")
            return {
                'error': str(e),
                'components': []
            }
    
    def get_statistics(self, start_time: Optional[str] = None, 
                      end_time: Optional[str] = None) -> Dict[str, Any]:
        """
        Get traffic visualization statistics
        
        Args:
            start_time: Start time in ISO format (optional)
            end_time: End time in ISO format (optional)
        
        Returns:
            Dictionary with traffic statistics
        """
        try:
            # Parse time range
            if start_time:
                try:
                    start_dt = datetime.fromisoformat(start_time)
                except ValueError:
                    start_dt = datetime.now() - timedelta(hours=1)
            else:
                start_dt = datetime.now() - timedelta(hours=1)
            
            if end_time:
                try:
                    end_dt = datetime.fromisoformat(end_time)
                except ValueError:
                    end_dt = datetime.now()
            else:
                end_dt = datetime.now()
            
            # Get packets from collector
            packets = []
            if self.traffic_collector:
                packets = self.traffic_collector.get_packets()
            
            # Filter packets by time range
            filtered_packets = [
                p for p in packets
                if start_dt <= p.timestamp <= end_dt
            ]
            
            # Calculate statistics
            stats = self._calculate_statistics(filtered_packets)
            
            logger.info(f"Retrieved statistics for {len(filtered_packets)} packets")
            return {
                'start_time': start_dt.isoformat(),
                'end_time': end_dt.isoformat(),
                'timestamp': datetime.now().isoformat(),
                **stats
            }
        
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {
                'error': str(e),
                'total_packets': 0,
                'total_bytes': 0,
                'control_ratio': 0.0,
                'telemetry_ratio': 0.0
            }
    
    def _calculate_statistics(self, packets: List[Any]) -> Dict[str, Any]:
        """
        Calculate traffic statistics from packets
        
        Args:
            packets: List of RawPacket objects
        
        Returns:
            Dictionary with calculated statistics
        """
        try:
            total_packets = len(packets)
            total_bytes = sum(p.packet_size for p in packets)
            
            # Classify packets
            control_packets = 0
            telemetry_packets = 0
            control_bytes = 0
            telemetry_bytes = 0
            
            traffic_by_component = defaultdict(lambda: {
                'packets': 0,
                'bytes': 0,
                'control': 0,
                'telemetry': 0
            })
            
            for packet in packets:
                # Classify traffic
                if self.event_generator:
                    traffic_type = self.event_generator.classifier.classify(
                        packet.src_ip,
                        packet.dst_ip,
                        packet.src_port,
                        packet.dst_port,
                        packet.protocol
                    )
                else:
                    # Default classification based on port
                    traffic_type = self._default_classify(packet)
                
                if traffic_type == 'Control':
                    control_packets += 1
                    control_bytes += packet.packet_size
                else:
                    telemetry_packets += 1
                    telemetry_bytes += packet.packet_size
                
                # Track by component
                from_component = self._map_ip_to_component(packet.src_ip)
                to_component = self._map_ip_to_component(packet.dst_ip)
                
                flow_key = f"{from_component}->{to_component}"
                traffic_by_component[flow_key]['packets'] += 1
                traffic_by_component[flow_key]['bytes'] += packet.packet_size
                
                if traffic_type == 'Control':
                    traffic_by_component[flow_key]['control'] += 1
                else:
                    traffic_by_component[flow_key]['telemetry'] += 1
            
            # Calculate ratios
            control_ratio = control_packets / total_packets if total_packets > 0 else 0.0
            telemetry_ratio = telemetry_packets / total_packets if total_packets > 0 else 0.0
            
            return {
                'total_packets': total_packets,
                'total_bytes': total_bytes,
                'control_packets': control_packets,
                'telemetry_packets': telemetry_packets,
                'control_bytes': control_bytes,
                'telemetry_bytes': telemetry_bytes,
                'control_ratio': round(control_ratio, 4),
                'telemetry_ratio': round(telemetry_ratio, 4),
                'traffic_by_component': dict(traffic_by_component)
            }
        
        except Exception as e:
            logger.error(f"Error calculating statistics: {e}")
            return {
                'total_packets': 0,
                'total_bytes': 0,
                'control_packets': 0,
                'telemetry_packets': 0,
                'control_bytes': 0,
                'telemetry_bytes': 0,
                'control_ratio': 0.0,
                'telemetry_ratio': 0.0,
                'traffic_by_component': {}
            }
    
    @staticmethod
    def _default_classify(packet: Any) -> str:
        """
        Default traffic classification based on port
        
        Args:
            packet: RawPacket object
        
        Returns:
            'Control' or 'Telemetry'
        """
        # Control ports: 22 (SSH), 23 (Telnet), 80 (HTTP), 443 (HTTPS), 5000-5999
        control_ports = {22, 23, 80, 443, 8080, 8443}
        
        if packet.src_port in control_ports or packet.dst_port in control_ports:
            return 'Control'
        
        # Telemetry ports: 514 (Syslog), 5140-5149, 9000-9999
        if (514 <= packet.src_port <= 514 or 514 <= packet.dst_port <= 514 or
            5140 <= packet.src_port <= 5149 or 5140 <= packet.dst_port <= 5149 or
            9000 <= packet.src_port <= 9999 or 9000 <= packet.dst_port <= 9999):
            return 'Telemetry'
        
        # Default to Telemetry
        return 'Telemetry'
    
    @staticmethod
    def _map_ip_to_component(ip: str) -> str:
        """
        Map IP address to component name
        
        Args:
            ip: IP address
        
        Returns:
            Component name or 'Unknown'
        """
        ip_mapping = {
            '10.0.8.1': 'Master',
            '10.0.8.2': 'Power_01',
            '10.0.8.3': 'Storage_01',
            '10.0.8.4': 'Demand_01',
        }
        return ip_mapping.get(ip, 'Unknown')
    
    def update_statistics(self, event: Any):
        """
        Update statistics with a new event
        
        Args:
            event: VisualizationEvent object
        """
        try:
            flow_key = f"{event.from_component}->{event.to_component}"
            
            stats = self.traffic_stats['current']
            stats['total_packets'] += 1
            stats['total_bytes'] += event.packet_size
            
            if event.traffic_type == 'Control':
                stats['control_packets'] += 1
                stats['control_bytes'] += event.packet_size
            else:
                stats['telemetry_packets'] += 1
                stats['telemetry_bytes'] += event.packet_size
            
            # Update component traffic
            component_stats = stats['traffic_by_component'][flow_key]
            component_stats['packets'] += 1
            component_stats['bytes'] += event.packet_size
            
            if event.traffic_type == 'Control':
                component_stats['control'] += 1
            else:
                component_stats['telemetry'] += 1
        
        except Exception as e:
            logger.error(f"Error updating statistics: {e}")
