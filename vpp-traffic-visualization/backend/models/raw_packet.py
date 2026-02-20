"""
Raw Packet Data Model

Represents a raw network packet captured from OVS mirror port.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class RawPacket:
    """
    Represents a raw network packet
    
    Attributes:
        src_ip: Source IP address
        dst_ip: Destination IP address
        src_port: Source port number
        dst_port: Destination port number
        protocol: Protocol type (TCP, UDP, ICMP, etc.)
        packet_size: Packet size in bytes
        timestamp: Packet capture timestamp
        payload: Raw packet payload (optional)
    """
    
    src_ip: str
    dst_ip: str
    src_port: int
    dst_port: int
    protocol: str
    packet_size: int
    timestamp: datetime
    payload: Optional[bytes] = None
    
    def to_dict(self) -> dict:
        """Convert to dictionary format"""
        return {
            'src_ip': self.src_ip,
            'dst_ip': self.dst_ip,
            'src_port': self.src_port,
            'dst_port': self.dst_port,
            'protocol': self.protocol,
            'packet_size': self.packet_size,
            'timestamp': self.timestamp.isoformat(),
            'payload': self.payload.hex() if self.payload else None
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'RawPacket':
        """Create from dictionary format"""
        return cls(
            src_ip=data['src_ip'],
            dst_ip=data['dst_ip'],
            src_port=data['src_port'],
            dst_port=data['dst_port'],
            protocol=data['protocol'],
            packet_size=data['packet_size'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            payload=bytes.fromhex(data['payload']) if data.get('payload') else None
        )
    
    def __repr__(self) -> str:
        return (f"RawPacket(src={self.src_ip}:{self.src_port}, "
                f"dst={self.dst_ip}:{self.dst_port}, "
                f"protocol={self.protocol}, size={self.packet_size})")
