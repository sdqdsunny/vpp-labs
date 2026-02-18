"""
Tests for Protocol Analyzer Service

Tests the protocol traffic analysis functionality
"""

import pytest
import json
from datetime import datetime
from services.protocol_analyzer import (
    ProtocolAnalyzer, PacketInfo, ProtocolType, get_analyzer
)


class TestProtocolAnalyzer:
    """Test cases for ProtocolAnalyzer"""
    
    @pytest.fixture
    def analyzer(self):
        """Create a fresh analyzer for each test"""
        analyzer = ProtocolAnalyzer(max_packets=1000)
        yield analyzer
        analyzer.reset()
    
    def test_analyzer_initialization(self, analyzer):
        """Test analyzer initialization"""
        assert analyzer.max_packets == 1000
        assert len(analyzer.packets) == 0
        assert len(analyzer.stats) == 0
        assert len(analyzer.flows) == 0
    
    def test_add_single_packet(self, analyzer):
        """Test adding a single packet"""
        packet = PacketInfo(
            timestamp=datetime.now().isoformat(),
            protocol="Modbus",
            src_ip="192.168.1.100",
            dst_ip="192.168.1.200",
            src_port=502,
            dst_port=502,
            size=256,
            payload_preview="01 03 00 00 00 0A",
            direction="outbound"
        )
        
        analyzer.add_packet(packet)
        
        assert len(analyzer.packets) == 1
        assert analyzer.stats["Modbus"]["packet_count"] == 1
        assert analyzer.stats["Modbus"]["total_bytes"] == 256
    
    def test_add_multiple_packets(self, analyzer):
        """Test adding multiple packets"""
        protocols = ["Modbus", "MQTT", "OPC_UA", "IEC61850"]
        
        for i, protocol in enumerate(protocols):
            packet = PacketInfo(
                timestamp=datetime.now().isoformat(),
                protocol=protocol,
                src_ip=f"192.168.1.{100+i}",
                dst_ip=f"192.168.1.{200+i}",
                src_port=5000 + i,
                dst_port=5000 + i,
                size=256 + i * 10,
                payload_preview=f"Protocol {protocol}",
                direction="inbound"
            )
            analyzer.add_packet(packet)
        
        assert len(analyzer.packets) == 4
        assert len(analyzer.stats) == 4
        assert analyzer.stats["Modbus"]["packet_count"] == 1
        assert analyzer.stats["MQTT"]["packet_count"] == 1
    
    def test_protocol_statistics(self, analyzer):
        """Test protocol statistics calculation"""
        # Add packets for same protocol
        for i in range(5):
            packet = PacketInfo(
                timestamp=datetime.now().isoformat(),
                protocol="Modbus",
                src_ip="192.168.1.100",
                dst_ip="192.168.1.200",
                src_port=502,
                dst_port=502,
                size=100,
                payload_preview="test",
                direction="inbound"
            )
            analyzer.add_packet(packet)
        
        stats = analyzer.get_protocol_stats()
        assert len(stats) == 1
        assert stats[0].protocol == "Modbus"
        assert stats[0].packet_count == 5
        assert stats[0].total_bytes == 500
        assert stats[0].avg_packet_size == 100.0
    
    def test_flow_tracking(self, analyzer):
        """Test flow tracking"""
        # Add packets for same flow
        for i in range(3):
            packet = PacketInfo(
                timestamp=datetime.now().isoformat(),
                protocol="MQTT",
                src_ip="192.168.1.100",
                dst_ip="192.168.1.200",
                src_port=1883,
                dst_port=1883,
                size=128,
                payload_preview="MQTT message",
                direction="inbound"
            )
            analyzer.add_packet(packet)
        
        flows = analyzer.get_flows()
        assert len(flows) == 1
        assert flows[0]["packet_count"] == 3
        assert flows[0]["total_bytes"] == 384
        assert flows[0]["protocol"] == "MQTT"
    
    def test_get_recent_packets(self, analyzer):
        """Test retrieving recent packets"""
        # Add 10 packets
        for i in range(10):
            packet = PacketInfo(
                timestamp=datetime.now().isoformat(),
                protocol="Modbus",
                src_ip="192.168.1.100",
                dst_ip="192.168.1.200",
                src_port=502,
                dst_port=502,
                size=100,
                payload_preview=f"packet_{i}",
                direction="inbound"
            )
            analyzer.add_packet(packet)
        
        # Get last 5
        recent = analyzer.get_recent_packets(limit=5)
        assert len(recent) == 5
        assert recent[0]["payload_preview"] == "packet_9"  # Most recent first
    
    def test_filter_packets_by_protocol(self, analyzer):
        """Test filtering packets by protocol"""
        # Add mixed protocols
        for protocol in ["Modbus", "MQTT", "Modbus"]:
            packet = PacketInfo(
                timestamp=datetime.now().isoformat(),
                protocol=protocol,
                src_ip="192.168.1.100",
                dst_ip="192.168.1.200",
                src_port=5000,
                dst_port=5000,
                size=100,
                payload_preview="test",
                direction="inbound"
            )
            analyzer.add_packet(packet)
        
        modbus_packets = analyzer.get_recent_packets(protocol="Modbus")
        assert len(modbus_packets) == 2
        assert all(p["protocol"] == "Modbus" for p in modbus_packets)
    
    def test_summary(self, analyzer):
        """Test summary generation"""
        # Add some packets
        for i in range(5):
            packet = PacketInfo(
                timestamp=datetime.now().isoformat(),
                protocol="Modbus",
                src_ip="192.168.1.100",
                dst_ip="192.168.1.200",
                src_port=502,
                dst_port=502,
                size=100,
                payload_preview="test",
                direction="inbound"
            )
            analyzer.add_packet(packet)
        
        summary = analyzer.get_summary()
        assert summary["total_packets"] == 5
        assert summary["total_bytes"] == 500
        assert summary["total_protocols"] == 1
        assert summary["total_flows"] == 1
    
    def test_reset(self, analyzer):
        """Test analyzer reset"""
        # Add packets
        packet = PacketInfo(
            timestamp=datetime.now().isoformat(),
            protocol="Modbus",
            src_ip="192.168.1.100",
            dst_ip="192.168.1.200",
            src_port=502,
            dst_port=502,
            size=100,
            payload_preview="test",
            direction="inbound"
        )
        analyzer.add_packet(packet)
        
        assert len(analyzer.packets) == 1
        
        # Reset
        analyzer.reset()
        
        assert len(analyzer.packets) == 0
        assert len(analyzer.stats) == 0
        assert len(analyzer.flows) == 0
    
    def test_max_packets_limit(self):
        """Test max packets limit"""
        analyzer = ProtocolAnalyzer(max_packets=5)
        
        # Add 10 packets
        for i in range(10):
            packet = PacketInfo(
                timestamp=datetime.now().isoformat(),
                protocol="Modbus",
                src_ip="192.168.1.100",
                dst_ip="192.168.1.200",
                src_port=502,
                dst_port=502,
                size=100,
                payload_preview=f"packet_{i}",
                direction="inbound"
            )
            analyzer.add_packet(packet)
        
        # Should only keep last 5
        assert len(analyzer.packets) == 5
        analyzer.reset()
    
    def test_global_analyzer_instance(self):
        """Test global analyzer instance"""
        analyzer1 = get_analyzer()
        analyzer2 = get_analyzer()
        
        # Should be same instance
        assert analyzer1 is analyzer2
        
        analyzer1.reset()


class TestProtocolTypes:
    """Test protocol type enumeration"""
    
    def test_all_protocol_types(self):
        """Test all supported protocol types"""
        protocols = [
            ProtocolType.IEC61850,
            ProtocolType.MODBUS,
            ProtocolType.DNP3,
            ProtocolType.MQTT,
            ProtocolType.OPC_UA,
            ProtocolType.CAN,
            ProtocolType.RS232,
            ProtocolType.RS485,
            ProtocolType.LORAWAN,
            ProtocolType.XMPP,
            ProtocolType.DLT,
            ProtocolType.PROFINET,
            ProtocolType.UNKNOWN
        ]
        
        assert len(protocols) == 13
        assert ProtocolType.MODBUS.value == "Modbus"
        assert ProtocolType.MQTT.value == "MQTT"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
