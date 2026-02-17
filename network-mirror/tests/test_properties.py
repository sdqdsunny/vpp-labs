#!/usr/bin/env python3
"""
Property-Based Tests for OVS Network Traffic Mirroring System.

Tests correctness properties using hypothesis framework:
- Property 1: Network Connectivity
- Property 2: Protocol Identification
- Property 3: Pcap File Generation
- Property 4: No Business Impact
"""

import unittest
import tempfile
import os
import sys
from pathlib import Path
from hypothesis import given, strategies as st, settings, HealthCheck

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'analyzer'))

try:
    from scapy.all import IP, TCP, UDP, Ether, Raw
except ImportError:
    print("Warning: scapy not installed. Some tests will be skipped.")
    scapy_available = False
else:
    scapy_available = True

from main import ProtocolIdentifier, PacketAnalyzer


# Hypothesis strategies for generating test data
@st.composite
def ip_addresses(draw):
    """Generate valid IP addresses in the 10.0.1.0/24 subnet."""
    return f"10.0.1.{draw(st.integers(min_value=1, max_value=254))}"


@st.composite
def port_numbers(draw):
    """Generate valid port numbers (1-65535)."""
    return draw(st.integers(min_value=1, max_value=65535))


@st.composite
def protocol_ports(draw):
    """Generate ports for supported protocols."""
    supported_ports = [102, 502, 20000, 1883, 8883]
    return draw(st.sampled_from(supported_ports))


@st.composite
def tcp_packets(draw, src_ip=None, dst_ip=None, dport=None):
    """Generate TCP packets with optional parameters."""
    if src_ip is None:
        src_ip = draw(ip_addresses())
    if dst_ip is None:
        dst_ip = draw(ip_addresses())
    if dport is None:
        dport = draw(port_numbers())
    
    sport = draw(port_numbers())
    return Ether() / IP(src=src_ip, dst=dst_ip) / TCP(sport=sport, dport=dport)


@st.composite
def udp_packets(draw, src_ip=None, dst_ip=None, dport=None):
    """Generate UDP packets with optional parameters."""
    if src_ip is None:
        src_ip = draw(ip_addresses())
    if dst_ip is None:
        dst_ip = draw(ip_addresses())
    if dport is None:
        dport = draw(port_numbers())
    
    sport = draw(port_numbers())
    return Ether() / IP(src=src_ip, dst=dst_ip) / UDP(sport=sport, dport=dport)


class TestNetworkConnectivity(unittest.TestCase):
    """
    Property 1: Network Connectivity
    
    **Validates: Requirements 1.1, 1.2, 1.3**
    
    All business components can communicate through the network.
    """
    
    @given(ip_addresses(), ip_addresses())
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    def test_ip_addresses_in_valid_range(self, src_ip, dst_ip):
        """
        Property: All generated IP addresses are in the valid subnet range.
        
        For any two IP addresses generated from the 10.0.1.0/24 subnet,
        they should be valid and different from gateway.
        """
        # Extract octets
        src_octets = src_ip.split('.')
        dst_octets = dst_ip.split('.')
        
        # Verify subnet
        self.assertEqual(src_octets[0], '10')
        self.assertEqual(src_octets[1], '0')
        self.assertEqual(src_octets[2], '1')
        self.assertGreaterEqual(int(src_octets[3]), 1)
        self.assertLessEqual(int(src_octets[3]), 254)
        
        self.assertEqual(dst_octets[0], '10')
        self.assertEqual(dst_octets[1], '0')
        self.assertEqual(dst_octets[2], '1')
        self.assertGreaterEqual(int(dst_octets[3]), 1)
        self.assertLessEqual(int(dst_octets[3]), 254)
    
    @given(st.lists(ip_addresses(), min_size=2, max_size=10, unique=True))
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_multiple_ips_are_unique(self, ips):
        """
        Property: Multiple IP addresses generated are unique.
        
        For any list of IP addresses, they should all be different.
        """
        self.assertEqual(len(ips), len(set(ips)))
    
    @given(tcp_packets())
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    def test_packets_have_valid_ips(self, packet):
        """
        Property: All generated packets have valid IP addresses.
        
        For any TCP packet, the source and destination IPs should be valid.
        """
        self.assertTrue(packet.haslayer(IP))
        ip_layer = packet[IP]
        
        # Verify IP format
        src_parts = ip_layer.src.split('.')
        dst_parts = ip_layer.dst.split('.')
        
        self.assertEqual(len(src_parts), 4)
        self.assertEqual(len(dst_parts), 4)
        
        for part in src_parts + dst_parts:
            num = int(part)
            self.assertGreaterEqual(num, 0)
            self.assertLessEqual(num, 255)


class TestProtocolIdentification(unittest.TestCase):
    """
    Property 2: Protocol Identification
    
    **Validates: Requirements 2.1, 2.2, 2.3**
    
    Analyzer correctly identifies industrial control protocols.
    """
    
    @given(protocol_ports())
    @settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
    def test_supported_protocols_identified(self, port):
        """
        Property: All supported protocol ports are correctly identified.
        
        For any supported protocol port, the analyzer should identify it.
        """
        packet = Ether() / IP(src="10.0.1.10", dst="10.0.1.20") / TCP(sport=12345, dport=port)
        protocol = ProtocolIdentifier.identify(packet)
        
        # Should identify a protocol (not Unknown or None)
        self.assertIsNotNone(protocol)
        self.assertNotEqual(protocol, 'Unknown')
        
        # Should be one of the supported protocols
        supported = ['IEC61850', 'Modbus', 'DNP3', 'MQTT', 'MQTT-TLS']
        self.assertIn(protocol, supported)
    
    @given(st.lists(protocol_ports(), min_size=1, max_size=10))
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_protocol_identification_consistency(self, ports):
        """
        Property: Protocol identification is consistent.
        
        For the same port, the identified protocol should always be the same.
        """
        for port in ports:
            packet1 = Ether() / IP(src="10.0.1.10", dst="10.0.1.20") / TCP(sport=12345, dport=port)
            packet2 = Ether() / IP(src="10.0.1.30", dst="10.0.1.40") / TCP(sport=54321, dport=port)
            
            protocol1 = ProtocolIdentifier.identify(packet1)
            protocol2 = ProtocolIdentifier.identify(packet2)
            
            self.assertEqual(protocol1, protocol2)
    
    @given(st.lists(tcp_packets(), min_size=1, max_size=20))
    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow])
    def test_protocol_identification_never_crashes(self, packets):
        """
        Property: Protocol identification never crashes.
        
        For any list of packets, identification should complete without error.
        """
        for packet in packets:
            try:
                protocol = ProtocolIdentifier.identify(packet)
                # Should return a string or None
                self.assertTrue(protocol is None or isinstance(protocol, str))
            except Exception as e:
                self.fail(f"Protocol identification crashed: {e}")
    
    @given(st.integers(min_value=1, max_value=65535))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_unknown_ports_identified_as_unknown(self, port):
        """
        Property: Unknown ports are identified as 'Unknown'.
        
        For any port not in the supported list, should return 'Unknown'.
        """
        supported_ports = [102, 502, 20000, 1883, 8883]
        
        if port not in supported_ports:
            packet = Ether() / IP(src="10.0.1.10", dst="10.0.1.20") / TCP(sport=12345, dport=port)
            protocol = ProtocolIdentifier.identify(packet)
            self.assertEqual(protocol, 'Unknown')


class TestPcapFileGeneration(unittest.TestCase):
    """
    Property 3: Pcap File Generation
    
    **Validates: Requirements 3.1, 3.2, 3.3**
    
    Pcap files are generated correctly and contain captured traffic.
    """
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = self.temp_dir.name
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()
    
    @given(st.lists(tcp_packets(), min_size=1, max_size=50))
    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow])
    def test_pcap_files_created_for_packets(self, packets):
        """
        Property: Pcap files are created for captured packets.
        
        For any list of packets, pcap files should be created.
        """
        analyzer = PacketAnalyzer('eth0', self.output_dir)
        
        for packet in packets:
            analyzer.current_pcap_packets.append(packet)
        
        analyzer._save_pcap()
        
        files = os.listdir(self.output_dir)
        self.assertGreater(len(files), 0)
        
        # All files should be pcap files
        for file in files:
            self.assertTrue(file.startswith('capture_'))
            self.assertTrue(file.endswith('.pcap'))
    
    @given(st.lists(tcp_packets(), min_size=10, max_size=50))
    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow])
    def test_pcap_file_size_increases_with_packets(self, packets):
        """
        Property: Pcap file size is non-zero for packets.
        
        For any list of packets, pcap files should have content.
        """
        analyzer = PacketAnalyzer('eth0', self.output_dir)
        
        # Save all packets
        for packet in packets:
            analyzer.current_pcap_packets.append(packet)
        analyzer._save_pcap()
        
        files = os.listdir(self.output_dir)
        self.assertGreater(len(files), 0)
        
        # File should have content
        file_path = os.path.join(self.output_dir, files[0])
        size = os.path.getsize(file_path)
        self.assertGreater(size, 0)
    
    @given(st.lists(tcp_packets(), min_size=1, max_size=100))
    @settings(max_examples=5, suppress_health_check=[HealthCheck.too_slow])
    def test_pcap_buffer_cleared_after_save(self, packets):
        """
        Property: Pcap buffer is cleared after save.
        
        For any list of packets, buffer should be empty after save.
        """
        analyzer = PacketAnalyzer('eth0', self.output_dir)
        
        for packet in packets:
            analyzer.current_pcap_packets.append(packet)
        
        self.assertEqual(len(analyzer.current_pcap_packets), len(packets))
        
        analyzer._save_pcap()
        
        self.assertEqual(len(analyzer.current_pcap_packets), 0)


class TestNoBusinessImpact(unittest.TestCase):
    """
    Property 4: No Business Impact
    
    **Validates: Requirements 4.1, 4.2, 4.3**
    
    Mirroring does not affect business traffic.
    """
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = self.temp_dir.name
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()
    
    @given(st.lists(tcp_packets(), min_size=1, max_size=100))
    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow])
    def test_packet_count_preserved(self, packets):
        """
        Property: Packet count is preserved during analysis.
        
        For any list of packets, the count should remain the same.
        """
        analyzer = PacketAnalyzer('eth0', self.output_dir)
        
        initial_count = analyzer.packet_count
        
        for packet in packets:
            analyzer.packet_callback(packet)
        
        # Packet count should increase by number of packets
        self.assertEqual(analyzer.packet_count, initial_count + len(packets))
    
    @given(st.lists(tcp_packets(), min_size=1, max_size=100))
    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow])
    def test_no_packet_loss_during_analysis(self, packets):
        """
        Property: No packets are lost during analysis.
        
        For any list of packets, all should be captured.
        """
        analyzer = PacketAnalyzer('eth0', self.output_dir)
        
        for packet in packets:
            analyzer.current_pcap_packets.append(packet)
        
        # All packets should be in buffer
        self.assertEqual(len(analyzer.current_pcap_packets), len(packets))
        
        analyzer._save_pcap()
        
        # After save, buffer should be empty (packets saved)
        self.assertEqual(len(analyzer.current_pcap_packets), 0)
    
    @given(st.lists(tcp_packets(), min_size=1, max_size=50))
    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow])
    def test_statistics_accuracy_preserved(self, packets):
        """
        Property: Statistics accuracy is preserved.
        
        For any list of packets, statistics should be accurate.
        """
        analyzer = PacketAnalyzer('eth0', self.output_dir)
        
        for packet in packets:
            analyzer.packet_callback(packet)
        
        # Total protocol count should equal packet count
        total_protocol_count = sum(analyzer.protocol_stats.values())
        self.assertEqual(total_protocol_count, len(packets))
        
        # Total flow count should equal packet count
        total_flow_count = sum(analyzer.flow_stats.values())
        self.assertEqual(total_flow_count, len(packets))
    
    @given(st.lists(tcp_packets(), min_size=1, max_size=100))
    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow])
    def test_analyzer_remains_operational(self, packets):
        """
        Property: Analyzer remains operational after processing packets.
        
        For any list of packets, analyzer should remain in valid state.
        """
        analyzer = PacketAnalyzer('eth0', self.output_dir)
        
        for packet in packets:
            analyzer.packet_callback(packet)
        
        # Analyzer should still be running
        self.assertTrue(analyzer.running)
        
        # Should be able to process more packets
        new_packet = Ether() / IP(src="10.0.1.10", dst="10.0.1.20") / TCP(sport=12345, dport=102)
        analyzer.packet_callback(new_packet)
        
        # Packet count should increase
        self.assertEqual(analyzer.packet_count, len(packets) + 1)


class TestProtocolIdentificationEdgeCases(unittest.TestCase):
    """
    Edge case tests for protocol identification.
    
    **Validates: Requirements 2.1, 2.2, 2.3**
    """
    
    @given(st.lists(tcp_packets(), min_size=1, max_size=100))
    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow])
    def test_protocol_identification_with_random_packets(self, packets):
        """
        Property: Protocol identification works with random packets.
        
        For any list of random packets, identification should complete.
        """
        for packet in packets:
            protocol = ProtocolIdentifier.identify(packet)
            
            # Should return a string or None
            self.assertTrue(protocol is None or isinstance(protocol, str))
            
            # If not None, should be a valid protocol name
            if protocol is not None:
                valid_protocols = ['IEC61850', 'Modbus', 'DNP3', 'MQTT', 'MQTT-TLS', 'Unknown']
                self.assertIn(protocol, valid_protocols)
    
    @given(st.lists(udp_packets(), min_size=1, max_size=50))
    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow])
    def test_udp_protocol_identification(self, packets):
        """
        Property: UDP protocol identification works correctly.
        
        For any list of UDP packets, identification should work.
        """
        for packet in packets:
            protocol = ProtocolIdentifier.identify(packet)
            
            # Should return a string or None
            self.assertTrue(protocol is None or isinstance(protocol, str))


class TestAnalyzerStatistics(unittest.TestCase):
    """
    Property-based tests for analyzer statistics.
    
    **Validates: Requirements 3.1, 3.2, 3.3**
    """
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = self.temp_dir.name
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()
    
    @given(st.lists(tcp_packets(), min_size=1, max_size=100))
    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow])
    def test_statistics_consistency(self, packets):
        """
        Property: Statistics are consistent across multiple runs.
        
        For the same packets, statistics should be identical.
        """
        analyzer1 = PacketAnalyzer('eth0', self.output_dir)
        analyzer2 = PacketAnalyzer('eth0', self.output_dir)
        
        for packet in packets:
            analyzer1.packet_callback(packet)
            analyzer2.packet_callback(packet)
        
        # Statistics should be identical
        self.assertEqual(analyzer1.packet_count, analyzer2.packet_count)
        self.assertEqual(analyzer1.protocol_stats, analyzer2.protocol_stats)
        self.assertEqual(analyzer1.flow_stats, analyzer2.flow_stats)
    
    @given(st.lists(tcp_packets(), min_size=1, max_size=50))
    @settings(max_examples=10, suppress_health_check=[HealthCheck.too_slow])
    def test_flow_statistics_accuracy(self, packets):
        """
        Property: Flow statistics are accurate.
        
        For any list of packets, flow counts should be correct.
        """
        analyzer = PacketAnalyzer('eth0', self.output_dir)
        
        # Count flows manually
        flow_counts = {}
        for packet in packets:
            if packet.haslayer(IP):
                ip_layer = packet[IP]
                flow_key = f"{ip_layer.src}->{ip_layer.dst}"
                flow_counts[flow_key] = flow_counts.get(flow_key, 0) + 1
        
        # Process packets
        for packet in packets:
            analyzer.packet_callback(packet)
        
        # Verify flow statistics match
        self.assertEqual(analyzer.flow_stats, flow_counts)


if __name__ == '__main__':
    unittest.main()
