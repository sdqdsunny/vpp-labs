"""
Unit tests for Traffic Collector Service

Tests for PCAP reading, JSON reading, and packet parsing.
"""

import pytest
import sys
import json
import tempfile
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.traffic_collector import TrafficCollectorService
from models.raw_packet import RawPacket


class TestTrafficCollectorService:
    """Test TrafficCollectorService"""
    
    def test_initialization(self):
        """Test service initialization"""
        collector = TrafficCollectorService()
        assert collector.pcap_file is None
        assert collector.json_source is None
        assert collector.packets == []
        assert collector.is_collecting is False
    
    def test_initialization_with_files(self):
        """Test service initialization with file paths"""
        collector = TrafficCollectorService(
            pcap_file='/path/to/file.pcap',
            json_source='/path/to/file.json'
        )
        assert collector.pcap_file == '/path/to/file.pcap'
        assert collector.json_source == '/path/to/file.json'
    
    def test_start_collection(self):
        """Test starting traffic collection"""
        collector = TrafficCollectorService()
        result = collector.start_collection()
        assert result is True
        assert collector.is_collecting is True
    
    def test_stop_collection(self):
        """Test stopping traffic collection"""
        collector = TrafficCollectorService()
        collector.start_collection()
        result = collector.stop_collection()
        assert result is True
        assert collector.is_collecting is False
    
    def test_read_json_single_packet(self):
        """Test reading single packet from JSON"""
        collector = TrafficCollectorService()
        
        packet_data = {
            'src_ip': '10.0.8.1',
            'dst_ip': '10.0.8.2',
            'src_port': 5000,
            'dst_port': 8080,
            'protocol': 'TCP',
            'packet_size': 1024,
            'timestamp': datetime.now().isoformat(),
            'payload': None
        }
        
        collector.json_source = json.dumps(packet_data)
        packets = collector.read_json()
        
        assert len(packets) == 1
        assert packets[0].src_ip == '10.0.8.1'
        assert packets[0].dst_ip == '10.0.8.2'
        assert packets[0].packet_size == 1024
    
    def test_read_json_multiple_packets(self):
        """Test reading multiple packets from JSON"""
        collector = TrafficCollectorService()
        
        packets_data = [
            {
                'src_ip': '10.0.8.1',
                'dst_ip': '10.0.8.2',
                'src_port': 5000,
                'dst_port': 8080,
                'protocol': 'TCP',
                'packet_size': 1024,
                'timestamp': datetime.now().isoformat(),
                'payload': None
            },
            {
                'src_ip': '10.0.8.2',
                'dst_ip': '10.0.8.3',
                'src_port': 8080,
                'dst_port': 5000,
                'protocol': 'UDP',
                'packet_size': 512,
                'timestamp': datetime.now().isoformat(),
                'payload': None
            }
        ]
        
        collector.json_source = json.dumps(packets_data)
        packets = collector.read_json()
        
        assert len(packets) == 2
        assert packets[0].protocol == 'TCP'
        assert packets[1].protocol == 'UDP'
    
    def test_read_json_from_file(self):
        """Test reading JSON from file"""
        collector = TrafficCollectorService()
        
        packet_data = {
            'src_ip': '10.0.8.1',
            'dst_ip': '10.0.8.2',
            'src_port': 5000,
            'dst_port': 8080,
            'protocol': 'TCP',
            'packet_size': 1024,
            'timestamp': datetime.now().isoformat(),
            'payload': None
        }
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(packet_data, f)
            temp_file = f.name
        
        try:
            collector.json_source = temp_file
            packets = collector.read_json()
            
            assert len(packets) == 1
            assert packets[0].src_ip == '10.0.8.1'
        finally:
            Path(temp_file).unlink()
    
    def test_read_json_invalid_format(self):
        """Test reading invalid JSON"""
        collector = TrafficCollectorService()
        collector.json_source = "invalid json {{"
        packets = collector.read_json()
        
        assert len(packets) == 0
    
    def test_parse_packet_from_dict(self):
        """Test parsing packet from dictionary"""
        collector = TrafficCollectorService()
        
        packet_data = {
            'src_ip': '10.0.8.1',
            'dst_ip': '10.0.8.2',
            'src_port': 5000,
            'dst_port': 8080,
            'protocol': 'TCP',
            'packet_size': 1024,
            'timestamp': datetime.now().isoformat(),
            'payload': None
        }
        
        packet = collector.parse_packet(packet_data)
        
        assert packet is not None
        assert packet.src_ip == '10.0.8.1'
        assert packet.dst_ip == '10.0.8.2'
    
    def test_get_packets(self):
        """Test getting collected packets"""
        collector = TrafficCollectorService()
        
        packet_data = {
            'src_ip': '10.0.8.1',
            'dst_ip': '10.0.8.2',
            'src_port': 5000,
            'dst_port': 8080,
            'protocol': 'TCP',
            'packet_size': 1024,
            'timestamp': datetime.now().isoformat(),
            'payload': None
        }
        
        collector.json_source = json.dumps(packet_data)
        collector.read_json()
        
        packets = collector.get_packets()
        assert len(packets) == 1
    
    def test_clear_packets(self):
        """Test clearing collected packets"""
        collector = TrafficCollectorService()
        
        packet_data = {
            'src_ip': '10.0.8.1',
            'dst_ip': '10.0.8.2',
            'src_port': 5000,
            'dst_port': 8080,
            'protocol': 'TCP',
            'packet_size': 1024,
            'timestamp': datetime.now().isoformat(),
            'payload': None
        }
        
        collector.json_source = json.dumps(packet_data)
        collector.read_json()
        
        assert len(collector.get_packets()) == 1
        
        collector.clear_packets()
        assert len(collector.get_packets()) == 0
    
    def test_protocol_name_mapping(self):
        """Test protocol number to name mapping"""
        assert TrafficCollectorService._get_protocol_name(1) == 'ICMP'
        assert TrafficCollectorService._get_protocol_name(6) == 'TCP'
        assert TrafficCollectorService._get_protocol_name(17) == 'UDP'
        assert TrafficCollectorService._get_protocol_name(999) == 'Protocol_999'
