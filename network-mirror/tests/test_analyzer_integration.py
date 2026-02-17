#!/usr/bin/env python3
"""
Integration tests for VPP Protocol Analyzer with Docker containers.

Tests the analyzer's ability to capture and analyze traffic from
the Docker network in a real environment.
"""

import unittest
import tempfile
import time
import subprocess
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'analyzer'))

try:
    from scapy.all import IP, TCP, UDP, Ether, send
    import docker
except ImportError:
    print("Warning: scapy or docker not installed. Some tests will be skipped.")
    scapy_available = False
    docker_available = False
else:
    scapy_available = True
    try:
        docker_available = True
    except:
        docker_available = False

from main import ProtocolIdentifier, PacketAnalyzer


class TestAnalyzerInitialization(unittest.TestCase):
    """Test analyzer initialization in Docker environment."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = self.temp_dir.name
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()
    
    def test_analyzer_initializes_with_docker_interface(self):
        """Test analyzer initializes with Docker interface."""
        analyzer = PacketAnalyzer('eth0', self.output_dir)
        
        self.assertEqual(analyzer.interface, 'eth0')
        self.assertTrue(analyzer.running)
        self.assertEqual(analyzer.packet_count, 0)
    
    def test_analyzer_creates_output_directory(self):
        """Test analyzer creates output directory."""
        new_dir = os.path.join(self.output_dir, 'pcap_output')
        analyzer = PacketAnalyzer('eth0', new_dir)
        
        self.assertTrue(os.path.exists(new_dir))
    
    def test_analyzer_initializes_statistics(self):
        """Test analyzer initializes statistics correctly."""
        analyzer = PacketAnalyzer('eth0', self.output_dir)
        
        self.assertEqual(analyzer.protocol_stats, {})
        self.assertEqual(analyzer.flow_stats, {})
        self.assertEqual(analyzer.packet_count, 0)
        self.assertEqual(len(analyzer.current_pcap_packets), 0)


class TestPacketCaptureAndAnalysis(unittest.TestCase):
    """Test packet capture and analysis functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = self.temp_dir.name
        self.analyzer = PacketAnalyzer('eth0', self.output_dir)
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()
    
    @unittest.skipUnless(scapy_available, "scapy not installed")
    def test_packet_capture_increments_count(self):
        """Test that packet capture increments packet count."""
        packet = Ether() / IP(src="10.0.1.10", dst="10.0.1.20") / TCP(sport=12345, dport=102)
        
        self.analyzer.packet_callback(packet)
        self.assertEqual(self.analyzer.packet_count, 1)
    
    @unittest.skipUnless(scapy_available, "scapy not installed")
    def test_packet_capture_identifies_protocol(self):
        """Test that packet capture identifies protocol."""
        packet = Ether() / IP(src="10.0.1.10", dst="10.0.1.20") / TCP(sport=12345, dport=102)
        
        self.analyzer.packet_callback(packet)
        self.assertIn('IEC61850', self.analyzer.protocol_stats)
        self.assertEqual(self.analyzer.protocol_stats['IEC61850'], 1)
    
    @unittest.skipUnless(scapy_available, "scapy not installed")
    def test_packet_capture_tracks_flows(self):
        """Test that packet capture tracks flows."""
        packet = Ether() / IP(src="10.0.1.10", dst="10.0.1.20") / TCP(sport=12345, dport=102)
        
        self.analyzer.packet_callback(packet)
        self.assertIn('10.0.1.10->10.0.1.20', self.analyzer.flow_stats)
        self.assertEqual(self.analyzer.flow_stats['10.0.1.10->10.0.1.20'], 1)
    
    @unittest.skipUnless(scapy_available, "scapy not installed")
    def test_multiple_protocol_identification(self):
        """Test identification of multiple protocols."""
        packets = [
            Ether() / IP(src="10.0.1.10", dst="10.0.1.20") / TCP(sport=12345, dport=102),  # IEC61850
            Ether() / IP(src="10.0.1.10", dst="10.0.1.20") / TCP(sport=12346, dport=502),  # Modbus
            Ether() / IP(src="10.0.1.10", dst="10.0.1.20") / TCP(sport=12347, dport=20000),  # DNP3
            Ether() / IP(src="10.0.1.10", dst="10.0.1.20") / TCP(sport=12348, dport=1883),  # MQTT
        ]
        
        for packet in packets:
            self.analyzer.packet_callback(packet)
        
        self.assertEqual(self.analyzer.packet_count, 4)
        self.assertEqual(self.analyzer.protocol_stats['IEC61850'], 1)
        self.assertEqual(self.analyzer.protocol_stats['Modbus'], 1)
        self.assertEqual(self.analyzer.protocol_stats['DNP3'], 1)
        self.assertEqual(self.analyzer.protocol_stats['MQTT'], 1)
    
    @unittest.skipUnless(scapy_available, "scapy not installed")
    def test_flow_aggregation(self):
        """Test that flows are aggregated correctly."""
        # Same flow, multiple packets
        for i in range(5):
            packet = Ether() / IP(src="10.0.1.10", dst="10.0.1.20") / TCP(sport=12345+i, dport=102)
            self.analyzer.packet_callback(packet)
        
        self.assertEqual(self.analyzer.packet_count, 5)
        self.assertEqual(self.analyzer.flow_stats['10.0.1.10->10.0.1.20'], 5)


class TestPcapFileGeneration(unittest.TestCase):
    """Test pcap file generation and rotation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = self.temp_dir.name
        self.analyzer = PacketAnalyzer('eth0', self.output_dir)
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()
    
    @unittest.skipUnless(scapy_available, "scapy not installed")
    def test_pcap_file_creation(self):
        """Test that pcap files are created."""
        packet = Ether() / IP(src="10.0.1.10", dst="10.0.1.20") / TCP(sport=12345, dport=102)
        self.analyzer.current_pcap_packets.append(packet)
        
        self.analyzer._save_pcap()
        
        files = os.listdir(self.output_dir)
        self.assertEqual(len(files), 1)
        self.assertTrue(files[0].startswith('capture_'))
        self.assertTrue(files[0].endswith('.pcap'))
    
    @unittest.skipUnless(scapy_available, "scapy not installed")
    def test_pcap_file_contains_packets(self):
        """Test that pcap file contains captured packets."""
        packets = [
            Ether() / IP(src="10.0.1.10", dst="10.0.1.20") / TCP(sport=12345, dport=102),
            Ether() / IP(src="10.0.1.10", dst="10.0.1.20") / TCP(sport=12346, dport=502),
        ]
        
        for packet in packets:
            self.analyzer.current_pcap_packets.append(packet)
        
        self.analyzer._save_pcap()
        
        files = os.listdir(self.output_dir)
        self.assertEqual(len(files), 1)
        
        # Verify file is not empty
        pcap_file = os.path.join(self.output_dir, files[0])
        self.assertGreater(os.path.getsize(pcap_file), 0)
    
    @unittest.skipUnless(scapy_available, "scapy not installed")
    def test_pcap_buffer_cleared_after_save(self):
        """Test that pcap buffer is cleared after save."""
        packet = Ether() / IP(src="10.0.1.10", dst="10.0.1.20") / TCP(sport=12345, dport=102)
        self.analyzer.current_pcap_packets.append(packet)
        
        self.assertEqual(len(self.analyzer.current_pcap_packets), 1)
        self.analyzer._save_pcap()
        self.assertEqual(len(self.analyzer.current_pcap_packets), 0)
    
    @unittest.skipUnless(scapy_available, "scapy not installed")
    def test_multiple_pcap_files(self):
        """Test that multiple pcap files are created on rotation."""
        packet = Ether() / IP(src="10.0.1.10", dst="10.0.1.20") / TCP(sport=12345, dport=102)
        
        # Create first pcap file
        self.analyzer.current_pcap_packets.append(packet)
        self.analyzer._save_pcap()
        
        # Wait to ensure different timestamp (at least 1 second)
        time.sleep(1.1)
        
        # Create second pcap file
        self.analyzer.current_pcap_packets.append(packet)
        self.analyzer._save_pcap()
        
        files = os.listdir(self.output_dir)
        self.assertEqual(len(files), 2)


class TestStatisticsCollection(unittest.TestCase):
    """Test statistics collection and logging."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = self.temp_dir.name
        self.analyzer = PacketAnalyzer('eth0', self.output_dir)
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()
    
    @unittest.skipUnless(scapy_available, "scapy not installed")
    def test_protocol_statistics_accuracy(self):
        """Test that protocol statistics are accurate."""
        packets = [
            Ether() / IP(src="10.0.1.10", dst="10.0.1.20") / TCP(sport=12345, dport=102),  # IEC61850
            Ether() / IP(src="10.0.1.10", dst="10.0.1.20") / TCP(sport=12346, dport=102),  # IEC61850
            Ether() / IP(src="10.0.1.10", dst="10.0.1.20") / TCP(sport=12347, dport=502),  # Modbus
        ]
        
        for packet in packets:
            self.analyzer.packet_callback(packet)
        
        self.assertEqual(self.analyzer.protocol_stats['IEC61850'], 2)
        self.assertEqual(self.analyzer.protocol_stats['Modbus'], 1)
    
    @unittest.skipUnless(scapy_available, "scapy not installed")
    def test_flow_statistics_accuracy(self):
        """Test that flow statistics are accurate."""
        packets = [
            Ether() / IP(src="10.0.1.10", dst="10.0.1.20") / TCP(sport=12345, dport=102),
            Ether() / IP(src="10.0.1.10", dst="10.0.1.20") / TCP(sport=12346, dport=102),
            Ether() / IP(src="10.0.1.20", dst="10.0.1.30") / TCP(sport=12347, dport=102),
        ]
        
        for packet in packets:
            self.analyzer.packet_callback(packet)
        
        self.assertEqual(self.analyzer.flow_stats['10.0.1.10->10.0.1.20'], 2)
        self.assertEqual(self.analyzer.flow_stats['10.0.1.20->10.0.1.30'], 1)
    
    def test_log_stats_does_not_raise_exception(self):
        """Test that _log_stats does not raise exception."""
        self.analyzer.packet_count = 100
        self.analyzer.protocol_stats = {'IEC61850': 50, 'Modbus': 50}
        self.analyzer.flow_stats = {'10.0.1.10->10.0.1.20': 100}
        
        # Should not raise exception
        self.analyzer._log_stats()


class TestAnalyzerStopCapture(unittest.TestCase):
    """Test analyzer stop capture functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = self.temp_dir.name
        self.analyzer = PacketAnalyzer('eth0', self.output_dir)
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()
    
    @unittest.skipUnless(scapy_available, "scapy not installed")
    def test_stop_capture_saves_remaining_packets(self):
        """Test that stop_capture saves remaining packets."""
        packet = Ether() / IP(src="10.0.1.10", dst="10.0.1.20") / TCP(sport=12345, dport=102)
        self.analyzer.current_pcap_packets.append(packet)
        
        self.analyzer.stop_capture()
        
        files = os.listdir(self.output_dir)
        self.assertEqual(len(files), 1)
    
    def test_stop_capture_sets_running_false(self):
        """Test that stop_capture sets running to False."""
        self.assertTrue(self.analyzer.running)
        self.analyzer.stop_capture()
        self.assertFalse(self.analyzer.running)


class TestProtocolIdentificationAccuracy(unittest.TestCase):
    """Test protocol identification accuracy with various packet types."""
    
    @unittest.skipUnless(scapy_available, "scapy not installed")
    def test_identify_all_supported_protocols(self):
        """Test identification of all supported protocols."""
        test_cases = [
            (102, 'IEC61850'),
            (502, 'Modbus'),
            (20000, 'DNP3'),
            (1883, 'MQTT'),
            (8883, 'MQTT-TLS'),
        ]
        
        for port, expected_protocol in test_cases:
            packet = Ether() / IP(src="10.0.1.10", dst="10.0.1.20") / TCP(sport=12345, dport=port)
            protocol = ProtocolIdentifier.identify(packet)
            self.assertEqual(protocol, expected_protocol, f"Failed for port {port}")
    
    @unittest.skipUnless(scapy_available, "scapy not installed")
    def test_identify_unknown_protocol(self):
        """Test identification of unknown protocol."""
        packet = Ether() / IP(src="10.0.1.10", dst="10.0.1.20") / TCP(sport=12345, dport=9999)
        protocol = ProtocolIdentifier.identify(packet)
        self.assertEqual(protocol, 'Unknown')
    
    @unittest.skipUnless(scapy_available, "scapy not installed")
    def test_identify_udp_protocols(self):
        """Test identification of UDP protocols."""
        packet = Ether() / IP(src="10.0.1.10", dst="10.0.1.20") / UDP(sport=12345, dport=502)
        protocol = ProtocolIdentifier.identify(packet)
        self.assertEqual(protocol, 'Modbus')


if __name__ == '__main__':
    unittest.main()
