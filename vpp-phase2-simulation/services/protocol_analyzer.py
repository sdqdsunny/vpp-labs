"""
Protocol Traffic Analyzer Service

Analyzes network traffic for various industrial control protocols:
- IEC 61850, Modbus, DNP3, MQTT, OPC UA, CAN, RS-232/485, LoRaWAN, XMPP, DL/T
"""

import logging
import threading
import time
import json
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class ProtocolType(Enum):
    """Supported protocol types"""
    IEC61850 = "IEC61850"
    MODBUS = "Modbus"
    DNP3 = "DNP3"
    MQTT = "MQTT"
    OPC_UA = "OPC_UA"
    CAN = "CAN"
    RS232 = "RS-232"
    RS485 = "RS-485"
    LORAWAN = "LoRaWAN"
    XMPP = "XMPP"
    DLT = "DL/T"
    PROFINET = "PROFINET"
    UNKNOWN = "Unknown"


@dataclass
class PacketInfo:
    """Information about a captured packet"""
    timestamp: str
    protocol: str
    src_ip: str
    dst_ip: str
    src_port: int
    dst_port: int
    size: int
    payload_preview: str
    direction: str  # "inbound" or "outbound"


@dataclass
class ProtocolStats:
    """Statistics for a protocol"""
    protocol: str
    packet_count: int
    total_bytes: int
    avg_packet_size: float
    packets_per_second: float
    last_seen: str
    error_count: int


class ProtocolAnalyzer:
    """Main protocol traffic analyzer"""
    
    def __init__(self, max_packets: int = 10000, history_duration: int = 3600):
        """
        Initialize the protocol analyzer
        
        Args:
            max_packets: Maximum packets to keep in memory
            history_duration: Duration to keep statistics (seconds)
        """
        self.max_packets = max_packets
        self.history_duration = history_duration
        
        # Packet storage
        self.packets: deque = deque(maxlen=max_packets)
        
        # Statistics
        self.stats: Dict[str, Dict] = defaultdict(lambda: {
            'packet_count': 0,
            'total_bytes': 0,
            'packets': deque(maxlen=1000),
            'errors': 0,
            'last_seen': None,
            'first_seen': None
        })
        
        # Flow tracking (src -> dst)
        self.flows: Dict[Tuple, Dict] = {}
        
        # Analysis state
        self.is_analyzing = False
        self.analysis_thread = None
        self.lock = threading.RLock()
        
        logger.info(f"Protocol Analyzer initialized (max_packets={max_packets})")
    
    def add_packet(self, packet_info: PacketInfo) -> None:
        """Add a captured packet to analysis"""
        with self.lock:
            self.packets.append(packet_info)
            
            # Update protocol statistics
            protocol = packet_info.protocol
            self.stats[protocol]['packet_count'] += 1
            self.stats[protocol]['total_bytes'] += packet_info.size
            self.stats[protocol]['packets'].append(packet_info)
            self.stats[protocol]['last_seen'] = packet_info.timestamp
            
            if self.stats[protocol]['first_seen'] is None:
                self.stats[protocol]['first_seen'] = packet_info.timestamp
            
            # Track flows
            flow_key = (packet_info.src_ip, packet_info.dst_ip, protocol)
            if flow_key not in self.flows:
                self.flows[flow_key] = {
                    'packet_count': 0,
                    'total_bytes': 0,
                    'start_time': packet_info.timestamp,
                    'last_seen': packet_info.timestamp
                }
            
            self.flows[flow_key]['packet_count'] += 1
            self.flows[flow_key]['total_bytes'] += packet_info.size
            self.flows[flow_key]['last_seen'] = packet_info.timestamp
    
    def get_protocol_stats(self) -> List[ProtocolStats]:
        """Get statistics for all protocols"""
        with self.lock:
            stats_list = []
            current_time = datetime.now()
            
            for protocol, data in self.stats.items():
                if data['packet_count'] == 0:
                    continue
                
                # Calculate packets per second
                if data['first_seen'] and data['last_seen']:
                    try:
                        first = datetime.fromisoformat(data['first_seen'])
                        last = datetime.fromisoformat(data['last_seen'])
                        duration = (last - first).total_seconds()
                        pps = data['packet_count'] / max(duration, 1)
                    except:
                        pps = 0
                else:
                    pps = 0
                
                avg_size = data['total_bytes'] / max(data['packet_count'], 1)
                
                stats_list.append(ProtocolStats(
                    protocol=protocol,
                    packet_count=data['packet_count'],
                    total_bytes=data['total_bytes'],
                    avg_packet_size=round(avg_size, 2),
                    packets_per_second=round(pps, 2),
                    last_seen=data['last_seen'] or "N/A",
                    error_count=data['errors']
                ))
            
            return sorted(stats_list, key=lambda x: x.packet_count, reverse=True)
    
    def get_recent_packets(self, limit: int = 100, protocol: Optional[str] = None) -> List[Dict]:
        """Get recent packets, optionally filtered by protocol"""
        with self.lock:
            packets = list(self.packets)
            
            if protocol:
                packets = [p for p in packets if p.protocol == protocol]
            
            # Return most recent first
            return [asdict(p) for p in packets[-limit:][::-1]]
    
    def get_flows(self, limit: int = 50) -> List[Dict]:
        """Get active flows"""
        with self.lock:
            flows_list = []
            for (src, dst, protocol), data in list(self.flows.items())[:limit]:
                flows_list.append({
                    'source': src,
                    'destination': dst,
                    'protocol': protocol,
                    'packet_count': data['packet_count'],
                    'total_bytes': data['total_bytes'],
                    'start_time': data['start_time'],
                    'last_seen': data['last_seen']
                })
            
            return sorted(flows_list, key=lambda x: x['packet_count'], reverse=True)
    
    def get_summary(self) -> Dict:
        """Get overall analysis summary"""
        with self.lock:
            total_packets = len(self.packets)
            total_bytes = sum(p.size for p in self.packets)
            protocols = len(self.stats)
            flows = len(self.flows)
            
            return {
                'total_packets': total_packets,
                'total_bytes': total_bytes,
                'total_protocols': protocols,
                'total_flows': flows,
                'timestamp': datetime.now().isoformat(),
                'is_analyzing': self.is_analyzing
            }
    
    def clear_old_data(self) -> None:
        """Clear data older than history_duration"""
        with self.lock:
            cutoff_time = datetime.now() - timedelta(seconds=self.history_duration)
            
            # Clear old packets
            while self.packets and len(self.packets) > 0:
                try:
                    first_packet_time = datetime.fromisoformat(self.packets[0].timestamp)
                    if first_packet_time < cutoff_time:
                        self.packets.popleft()
                    else:
                        break
                except:
                    break
            
            # Clear old flows
            flows_to_remove = []
            for flow_key, data in self.flows.items():
                try:
                    last_seen = datetime.fromisoformat(data['last_seen'])
                    if last_seen < cutoff_time:
                        flows_to_remove.append(flow_key)
                except:
                    pass
            
            for flow_key in flows_to_remove:
                del self.flows[flow_key]
    
    def reset(self) -> None:
        """Reset all statistics"""
        with self.lock:
            self.packets.clear()
            self.stats.clear()
            self.flows.clear()
            logger.info("Protocol analyzer reset")
    
    def start_cleanup_thread(self) -> None:
        """Start background thread to clean old data"""
        def cleanup_loop():
            while self.is_analyzing:
                time.sleep(60)  # Clean every minute
                self.clear_old_data()
        
        if not self.is_analyzing:
            self.is_analyzing = True
            self.analysis_thread = threading.Thread(target=cleanup_loop, daemon=True)
            self.analysis_thread.start()
            logger.info("Cleanup thread started")
    
    def stop_cleanup_thread(self) -> None:
        """Stop background cleanup thread"""
        self.is_analyzing = False
        if self.analysis_thread:
            self.analysis_thread.join(timeout=5)
            logger.info("Cleanup thread stopped")


# Global analyzer instance
_analyzer_instance: Optional[ProtocolAnalyzer] = None


def get_analyzer() -> ProtocolAnalyzer:
    """Get or create the global analyzer instance"""
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = ProtocolAnalyzer()
        _analyzer_instance.start_cleanup_thread()
    return _analyzer_instance
