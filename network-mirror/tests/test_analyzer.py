#!/usr/bin/env python3
"""
Unit tests for VPP Protocol Analyzer.

Tests the ProtocolIdentifier and PacketAnalyzer classes.
"""

import unittest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'analyzer'))

try:
    from scapy.all import IP, TCP, UDP, Ether
except ImportError:
    print("Warning: scapy not installed. Some tests will be skipped.")
    scapy_available = False
else:
    scapy_available = True

# Import analyzer components
from main import ProtocolIdentifier, PacketAnalyzer


class TestProtocolIdentifier(unittest.TestCase):
    """Test cases for ProtocolIdentifier class."""
    
    @unittest.skipUnless(scapy_available, "scapy not installed")
    def test_identify_iec61850_tcp(self):
        """Test identification of IEC61850 protocol on TCP port 102."""
        packet = Ether() / IP(src="10.0.1.10", dst="10.0.1.20") / TCP(sport=12345, dport=102)
        protocol = ProtocolIdentifier.identify(packet)
        self.assertEqual(protocol, 'IEC61850')
    
    @unittest.skipUnless(scapy_available, "scapy not installed")
    def test_identify_modbus_tcp(self):
        """Test identification of Modbus protocol on TCP port 502."""
        packet = Ether() / IP(src="10.0.1.10", dst="10.0.1.20") / TCP(sport=12345, dport=502)
        protocol = ProtocolIdentifier.identify(packet)
        self.assertEqual(protocol, 'Modbus')
    
    @unittest.skipUnless(scapy_available, "scapy not installed")
    def test_identify_dnp3_tcp(self):
        """Test identification of DNP3 protocol on TCP port 20000."""
        packet = Ether() / IP(src="10.0.1.10", dst="10.0.1.20") / TCP(sport=12345, dport=20000)
        protocol = ProtocolIdentifier.identify(packet)
        self.assertEqual(protocol, 'DNP3')
    
    @unittest.skipUnless(scapy_available, "scapy not installed")
    def test_identify_mqtt_tcp(self):
        """Test identification of MQTT protocol on TCP port 1883."""
        packet = Ether() / IP(src="10.0.1.10", dst="10.0.1.20") / TCP(sport=12345, dport=1883)
        protocol = ProtocolIdentifier.identify(packet)
        self.assertEqual(protocol, 'MQTT')
    
    @unittest.skipUnless(scapy_available, "scapy not installed")
    def test_identify_mqtt_tls_tcp(self):
        """Test identification of MQTT-TLS protocol on TCP port 8883."""
        packet = Ether() / IP(src="10.0.1.10", dst="10.0.1.20") / TCP(sport=12345, dport=8883)
        protocol = ProtocolIdentifier.identify(packet)
        self.assertEqual(protocol, 'MQTT-TLS')
    
    @unittest.skipUnless(scapy_available, "scapy not installed")
    def test_identify_modbus_udp(self):
        """Test identification of Modbus protocol on UDP port 502."""
        packet = Ether() / IP(src="10.0.1.10", dst="10.0.1.20") / UDP(sport=12345, dport=502)
        protocol = ProtocolIdentifier.identify(packet)
        self.assertEqual(protocol, 'Modbus')
    
    @unittest.skipUnless(scapy_available, "scapy not installed")
    def test_identify_unknown_protocol(self):
        """Test identification of unknown protocol."""
        packet = Ether() / IP(src="10.0.1.10", dst="10.0.1.20") / TCP(sport=12345, dport=9999)
        protocol = ProtocolIdentifier.identify(packet)
        self.assertEqual(protocol, 'Unknown')
    
    @unittest.skipUnless(scapy_available, "scapy not installed")
    def test_identify_non_ip_packet(self):
        """Test identification of non-IP packet."""
        packet = Ether()
        protocol = ProtocolIdentifier.identify(packet)
        self.assertIsNone(protocol)
    
    @unittest.skipUnless(scapy_available, "scapy not installed")
    def test_identify_source_port_match(self):
        """Test identification using source port."""
        packet = Ether() / IP(src="10.0.1.10", dst="10.0.1.20") / TCP(sport=102, dport=12345)
        protocol = ProtocolIdentifier.identify(packet)
        self.assertEqual(protocol, 'IEC61850')
    
    def test_protocol_ports_mapping(self):
        """Test protocol ports mapping."""
        expected_ports = {
            102: 'IEC61850',
            502: 'Modbus',
            20000: 'DNP3',
            1883: 'MQTT',
            8883: 'MQTT-TLS',
        }
        self.assertEqual(ProtocolIdentifier.PROTOCOL_PORTS, expected_ports)


class TestPacketAnalyzer(unittest.TestCase):
    """Test cases for PacketAnalyzer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = self.temp_dir.name
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()
    
    def test_analyzer_initialization(self):
        """Test PacketAnalyzer initialization."""
        analyzer = PacketAnalyzer('eth0', self.output_dir)
        
        self.assertEqual(analyzer.interface, 'eth0')
        self.assertEqual(str(analyzer.output_dir), self.output_dir)
        self.assertEqual(analyzer.packet_count, 0)
        self.assertEqual(analyzer.protocol_stats, {})
        self.assertEqual(analyzer.flow_stats, {})
        self.assertTrue(analyzer.running)
    
    def test_analyzer_output_dir_creation(self):
        """Test that output directory is created if it doesn't exist."""
        new_dir = os.path.join(self.output_dir, 'subdir')
        analyzer = PacketAnalyzer('eth0', new_dir)
        
        self.assertTrue(os.path.exists(new_dir))
    
    def test_analyzer_default_output_dir(self):
        """Test PacketAnalyzer with default output directory."""
        with patch('pathlib.Path.mkdir'):
            analyzer = PacketAnalyzer('eth0')
            self.assertEqual(str(analyzer.output_dir), '/pcap')
    
    @unittest.skipUnless(scapy_available, "scapy not installed")
    def test_packet_callback_increments_count(self):
        """Test that packet_callback increments packet count."""
        analyzer = PacketAnalyzer('eth0', self.output_dir)
        packet = Ether() / IP(src="10.0.1.10", dst="10.0.1.20") / TCP(sport=12345, dport=102)
        
        analyzer.packet_callback(packet)
        self.assertEqual(analyzer.packet_count, 1)
    
    @unittest.skipUnless(scapy_available, "scapy not installed")
    def test_packet_callback_updates_protocol_stats(self):
        """Test that packet_callback updates protocol statistics."""
        analyzer = PacketAnalyzer('eth0', self.output_dir)
        packet = Ether() / IP(src="10.0.1.10", dst="10.0.1.20") / TCP(sport=12345, dport=102)
        
        analyzer.packet_callback(packet)
        self.assertEqual(analyzer.protocol_stats['IEC61850'], 1)
    
    @unittest.skipUnless(scapy_available, "scapy not installed")
    def test_packet_callback_updates_flow_stats(self):
        """Test that packet_callback updates flow statistics."""
        analyzer = PacketAnalyzer('eth0', self.output_dir)
        packet = Ether() / IP(src="10.0.1.10", dst="10.0.1.20") / TCP(sport=12345, dport=102)
        
        analyzer.packet_callback(packet)
        self.assertEqual(analyzer.flow_stats['10.0.1.10->10.0.1.20'], 1)
    
    @unittest.skipUnless(scapy_available, "scapy not installed")
    def test_packet_callback_multiple_packets(self):
        """Test packet_callback with multiple packets."""
        analyzer = PacketAnalyzer('eth0', self.output_dir)
        
        # Create multiple packets
        packet1 = Ether() / IP(src="10.0.1.10", dst="10.0.1.20") / TCP(sport=12345, dport=102)
        packet2 = Ether() / IP(src="10.0.1.10", dst="10.0.1.20") / TCP(sport=12346, dport=502)
        packet3 = Ether() / IP(src="10.0.1.20", dst="10.0.1.30") / TCP(sport=12347, dport=102)
        
        analyzer.packet_callback(packet1)
        analyzer.packet_callback(packet2)
        analyzer.packet_callback(packet3)
        
        self.assertEqual(analyzer.packet_count, 3)
        self.assertEqual(analyzer.protocol_stats['IEC61850'], 2)
        self.assertEqual(analyzer.protocol_stats['Modbus'], 1)
        self.assertEqual(analyzer.flow_stats['10.0.1.10->10.0.1.20'], 2)
        self.assertEqual(analyzer.flow_stats['10.0.1.20->10.0.1.30'], 1)
    
    def test_save_pcap_with_empty_buffer(self):
        """Test _save_pcap with empty buffer."""
        analyzer = PacketAnalyzer('eth0', self.output_dir)
        
        # Should not raise exception
        analyzer._save_pcap()
        
        # No files should be created
        files = os.listdir(self.output_dir)
        self.assertEqual(len(files), 0)
    
    @unittest.skipUnless(scapy_available, "scapy not installed")
    def test_save_pcap_creates_file(self):
        """Test that _save_pcap creates pcap file."""
        analyzer = PacketAnalyzer('eth0', self.output_dir)
        packet = Ether() / IP(src="10.0.1.10", dst="10.0.1.20") / TCP(sport=12345, dport=102)
        
        analyzer.current_pcap_packets.append(packet)
        analyzer._save_pcap()
        
        # Check that pcap file was created
        files = os.listdir(self.output_dir)
        self.assertEqual(len(files), 1)
        self.assertTrue(files[0].startswith('capture_'))
        self.assertTrue(files[0].endswith('.pcap'))
    
    @unittest.skipUnless(scapy_available, "scapy not installed")
    def test_save_pcap_clears_buffer(self):
        """Test that _save_pcap clears the packet buffer."""
        analyzer = PacketAnalyzer('eth0', self.output_dir)
        packet = Ether() / IP(src="10.0.1.10", dst="10.0.1.20") / TCP(sport=12345, dport=102)
        
        analyzer.current_pcap_packets.append(packet)
        self.assertEqual(len(analyzer.current_pcap_packets), 1)
        
        analyzer._save_pcap()
        self.assertEqual(len(analyzer.current_pcap_packets), 0)
    
    def test_stop_capture_sets_running_false(self):
        """Test that stop_capture sets running to False."""
        analyzer = PacketAnalyzer('eth0', self.output_dir)
        self.assertTrue(analyzer.running)
        
        analyzer.stop_capture()
        self.assertFalse(analyzer.running)
    
    def test_pcap_rotation_count(self):
        """Test pcap rotation count."""
        analyzer = PacketAnalyzer('eth0', self.output_dir)
        self.assertEqual(analyzer.pcap_rotation_count, 100)


class TestProtocolIdentifierEdgeCases(unittest.TestCase):
    """Test edge cases for ProtocolIdentifier."""
    
    @unittest.skipUnless(scapy_available, "scapy not installed")
    def test_identify_with_invalid_packet(self):
        """Test identification with invalid packet."""
        analyzer = PacketAnalyzer('eth0', tempfile.gettempdir())
        
        # Should not raise exception
        try:
            protocol = ProtocolIdentifier.identify(None)
            self.assertIsNone(protocol)
        except AttributeError:
            # Expected if packet is None
            pass
    
    @unittest.skipUnless(scapy_available, "scapy not installed")
    def test_identify_ipv6_packet(self):
        """Test identification of IPv6 packet (should return None)."""
        from scapy.all import IPv6
        packet = Ether() / IPv6(src="::1", dst="::2") / TCP(sport=12345, dport=102)
        protocol = ProtocolIdentifier.identify(packet)
        # IPv6 packets don't have IP layer, so should return None
        self.assertIsNone(protocol)


if __name__ == '__main__':
    unittest.main()
