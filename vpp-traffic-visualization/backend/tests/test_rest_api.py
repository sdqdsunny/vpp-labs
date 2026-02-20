"""
Unit tests for REST API routes

Tests for:
- GET /api/visualization/components
- GET /api/visualization/statistics
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch

import sys
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from routes.rest_api_routes import RestAPIRoutes
from models.raw_packet import RawPacket
from models.visualization_event import VisualizationEvent


class TestRestAPIRoutes:
    """Test suite for RestAPIRoutes"""
    
    @pytest.fixture
    def rest_api(self):
        """Create RestAPIRoutes instance for testing"""
        return RestAPIRoutes()
    
    @pytest.fixture
    def mock_traffic_collector(self):
        """Create mock traffic collector"""
        collector = Mock()
        collector.get_packets.return_value = []
        return collector
    
    @pytest.fixture
    def mock_event_generator(self):
        """Create mock event generator"""
        generator = Mock()
        generator.classifier = Mock()
        return generator
    
    @pytest.fixture
    def sample_packets(self):
        """Create sample packets for testing"""
        packets = [
            RawPacket(
                src_ip='10.0.8.1',
                dst_ip='10.0.8.2',
                src_port=22,
                dst_port=5000,
                protocol='TCP',
                packet_size=1024,
                timestamp=datetime.now()
            ),
            RawPacket(
                src_ip='10.0.8.2',
                dst_ip='10.0.8.3',
                src_port=9000,
                dst_port=9001,
                protocol='UDP',
                packet_size=512,
                timestamp=datetime.now()
            ),
            RawPacket(
                src_ip='10.0.8.3',
                dst_ip='10.0.8.4',
                src_port=5140,
                dst_port=5141,
                protocol='TCP',
                packet_size=256,
                timestamp=datetime.now()
            ),
        ]
        return packets
    
    # Tests for get_components
    
    def test_get_components_returns_list(self, rest_api):
        """Test that get_components returns a list of components"""
        result = rest_api.get_components()
        
        assert 'components' in result
        assert isinstance(result['components'], list)
        assert len(result['components']) == 4
    
    def test_get_components_has_required_fields(self, rest_api):
        """Test that each component has required fields"""
        result = rest_api.get_components()
        
        for component in result['components']:
            assert 'name' in component
            assert 'ip' in component
            assert 'type' in component
            assert 'status' in component
            assert 'color' in component
    
    def test_get_components_has_correct_names(self, rest_api):
        """Test that components have correct names"""
        result = rest_api.get_components()
        
        names = [c['name'] for c in result['components']]
        assert 'Master' in names
        assert 'Power_01' in names
        assert 'Storage_01' in names
        assert 'Demand_01' in names
    
    def test_get_components_has_correct_ips(self, rest_api):
        """Test that components have correct IPs"""
        result = rest_api.get_components()
        
        ips = {c['name']: c['ip'] for c in result['components']}
        assert ips['Master'] == '10.0.8.1'
        assert ips['Power_01'] == '10.0.8.2'
        assert ips['Storage_01'] == '10.0.8.3'
        assert ips['Demand_01'] == '10.0.8.4'
    
    def test_get_components_all_online(self, rest_api):
        """Test that all components are online"""
        result = rest_api.get_components()
        
        for component in result['components']:
            assert component['status'] == 'online'
    
    def test_get_components_has_timestamp(self, rest_api):
        """Test that response includes timestamp"""
        result = rest_api.get_components()
        
        assert 'timestamp' in result
        assert isinstance(result['timestamp'], str)
    
    def test_get_components_has_total_count(self, rest_api):
        """Test that response includes total component count"""
        result = rest_api.get_components()
        
        assert 'total_components' in result
        assert result['total_components'] == 4
    
    # Tests for get_statistics
    
    def test_get_statistics_without_time_range(self, rest_api, mock_traffic_collector, sample_packets):
        """Test get_statistics without time range"""
        rest_api.traffic_collector = mock_traffic_collector
        mock_traffic_collector.get_packets.return_value = sample_packets
        
        result = rest_api.get_statistics()
        
        assert 'total_packets' in result
        assert 'total_bytes' in result
        assert 'control_ratio' in result
        assert 'telemetry_ratio' in result
    
    def test_get_statistics_with_time_range(self, rest_api, mock_traffic_collector, sample_packets):
        """Test get_statistics with time range"""
        rest_api.traffic_collector = mock_traffic_collector
        mock_traffic_collector.get_packets.return_value = sample_packets
        
        start_time = (datetime.now() - timedelta(hours=1)).isoformat()
        end_time = datetime.now().isoformat()
        
        result = rest_api.get_statistics(start_time, end_time)
        
        assert 'start_time' in result
        assert 'end_time' in result
        assert 'total_packets' in result
    
    def test_get_statistics_calculates_total_packets(self, rest_api, mock_traffic_collector, sample_packets):
        """Test that statistics correctly count total packets"""
        rest_api.traffic_collector = mock_traffic_collector
        mock_traffic_collector.get_packets.return_value = sample_packets
        
        result = rest_api.get_statistics()
        
        assert result['total_packets'] == 3
    
    def test_get_statistics_calculates_total_bytes(self, rest_api, mock_traffic_collector, sample_packets):
        """Test that statistics correctly sum total bytes"""
        rest_api.traffic_collector = mock_traffic_collector
        mock_traffic_collector.get_packets.return_value = sample_packets
        
        result = rest_api.get_statistics()
        
        expected_bytes = 1024 + 512 + 256
        assert result['total_bytes'] == expected_bytes
    
    def test_get_statistics_classifies_control_traffic(self, rest_api, mock_traffic_collector, sample_packets):
        """Test that statistics correctly classify control traffic"""
        rest_api.traffic_collector = mock_traffic_collector
        mock_traffic_collector.get_packets.return_value = sample_packets
        
        result = rest_api.get_statistics()
        
        # Packets with ports 22, 5140 should be classified as control
        # Port 22 (SSH) is control, port 5140 is telemetry (in 5140-5149 range)
        # So we expect at least 1 control packet
        assert result['control_packets'] >= 1
    
    def test_get_statistics_classifies_telemetry_traffic(self, rest_api, mock_traffic_collector, sample_packets):
        """Test that statistics correctly classify telemetry traffic"""
        rest_api.traffic_collector = mock_traffic_collector
        mock_traffic_collector.get_packets.return_value = sample_packets
        
        result = rest_api.get_statistics()
        
        # Packets with ports 9000-9999 should be classified as telemetry
        assert result['telemetry_packets'] >= 1
    
    def test_get_statistics_calculates_ratios(self, rest_api, mock_traffic_collector, sample_packets):
        """Test that statistics correctly calculate control/telemetry ratios"""
        rest_api.traffic_collector = mock_traffic_collector
        mock_traffic_collector.get_packets.return_value = sample_packets
        
        result = rest_api.get_statistics()
        
        # Ratios should sum to approximately 1.0
        total_ratio = result['control_ratio'] + result['telemetry_ratio']
        assert 0.99 <= total_ratio <= 1.01
    
    def test_get_statistics_tracks_by_component(self, rest_api, mock_traffic_collector, sample_packets):
        """Test that statistics track traffic by component"""
        rest_api.traffic_collector = mock_traffic_collector
        mock_traffic_collector.get_packets.return_value = sample_packets
        
        result = rest_api.get_statistics()
        
        assert 'traffic_by_component' in result
        assert isinstance(result['traffic_by_component'], dict)
        assert len(result['traffic_by_component']) > 0
    
    def test_get_statistics_empty_packets(self, rest_api, mock_traffic_collector):
        """Test get_statistics with no packets"""
        rest_api.traffic_collector = mock_traffic_collector
        mock_traffic_collector.get_packets.return_value = []
        
        result = rest_api.get_statistics()
        
        assert result['total_packets'] == 0
        assert result['total_bytes'] == 0
        assert result['control_ratio'] == 0.0
        assert result['telemetry_ratio'] == 0.0
    
    def test_get_statistics_no_collector(self, rest_api):
        """Test get_statistics without traffic collector"""
        rest_api.traffic_collector = None
        
        result = rest_api.get_statistics()
        
        assert result['total_packets'] == 0
        assert result['total_bytes'] == 0
    
    def test_get_statistics_invalid_start_time(self, rest_api, mock_traffic_collector, sample_packets):
        """Test get_statistics with invalid start time"""
        rest_api.traffic_collector = mock_traffic_collector
        mock_traffic_collector.get_packets.return_value = sample_packets
        
        result = rest_api.get_statistics(start_time='invalid-time')
        
        # Should use default time range
        assert 'start_time' in result
        assert 'total_packets' in result
    
    def test_get_statistics_invalid_end_time(self, rest_api, mock_traffic_collector, sample_packets):
        """Test get_statistics with invalid end time"""
        rest_api.traffic_collector = mock_traffic_collector
        mock_traffic_collector.get_packets.return_value = sample_packets
        
        result = rest_api.get_statistics(end_time='invalid-time')
        
        # Should use default time range
        assert 'end_time' in result
        assert 'total_packets' in result
    
    # Tests for helper methods
    
    def test_map_ip_to_component_master(self, rest_api):
        """Test IP to component mapping for Master"""
        component = rest_api._map_ip_to_component('10.0.8.1')
        assert component == 'Master'
    
    def test_map_ip_to_component_power(self, rest_api):
        """Test IP to component mapping for Power_01"""
        component = rest_api._map_ip_to_component('10.0.8.2')
        assert component == 'Power_01'
    
    def test_map_ip_to_component_storage(self, rest_api):
        """Test IP to component mapping for Storage_01"""
        component = rest_api._map_ip_to_component('10.0.8.3')
        assert component == 'Storage_01'
    
    def test_map_ip_to_component_demand(self, rest_api):
        """Test IP to component mapping for Demand_01"""
        component = rest_api._map_ip_to_component('10.0.8.4')
        assert component == 'Demand_01'
    
    def test_map_ip_to_component_unknown(self, rest_api):
        """Test IP to component mapping for unknown IP"""
        component = rest_api._map_ip_to_component('192.168.1.1')
        assert component == 'Unknown'
    
    def test_default_classify_control_ssh(self, rest_api):
        """Test default classification for SSH traffic"""
        packet = Mock()
        packet.src_port = 22
        packet.dst_port = 5000
        
        traffic_type = rest_api._default_classify(packet)
        assert traffic_type == 'Control'
    
    def test_default_classify_control_http(self, rest_api):
        """Test default classification for HTTP traffic"""
        packet = Mock()
        packet.src_port = 80
        packet.dst_port = 5000
        
        traffic_type = rest_api._default_classify(packet)
        assert traffic_type == 'Control'
    
    def test_default_classify_telemetry_syslog(self, rest_api):
        """Test default classification for Syslog traffic"""
        packet = Mock()
        packet.src_port = 514
        packet.dst_port = 5000
        
        traffic_type = rest_api._default_classify(packet)
        assert traffic_type == 'Telemetry'
    
    def test_default_classify_telemetry_high_port(self, rest_api):
        """Test default classification for high port traffic"""
        packet = Mock()
        packet.src_port = 9000
        packet.dst_port = 9001
        
        traffic_type = rest_api._default_classify(packet)
        assert traffic_type == 'Telemetry'
    
    def test_default_classify_default_telemetry(self, rest_api):
        """Test default classification defaults to Telemetry"""
        packet = Mock()
        packet.src_port = 12345
        packet.dst_port = 54321
        
        traffic_type = rest_api._default_classify(packet)
        assert traffic_type == 'Telemetry'
    
    # Tests for update_statistics
    
    def test_update_statistics_increments_total(self, rest_api):
        """Test that update_statistics increments total packets"""
        event = Mock()
        event.from_component = 'Master'
        event.to_component = 'Power_01'
        event.traffic_type = 'Control'
        event.packet_size = 1024
        
        rest_api.update_statistics(event)
        
        assert rest_api.traffic_stats['current']['total_packets'] == 1
        assert rest_api.traffic_stats['current']['total_bytes'] == 1024
    
    def test_update_statistics_tracks_control(self, rest_api):
        """Test that update_statistics tracks control traffic"""
        event = Mock()
        event.from_component = 'Master'
        event.to_component = 'Power_01'
        event.traffic_type = 'Control'
        event.packet_size = 1024
        
        rest_api.update_statistics(event)
        
        assert rest_api.traffic_stats['current']['control_packets'] == 1
        assert rest_api.traffic_stats['current']['control_bytes'] == 1024
    
    def test_update_statistics_tracks_telemetry(self, rest_api):
        """Test that update_statistics tracks telemetry traffic"""
        event = Mock()
        event.from_component = 'Master'
        event.to_component = 'Power_01'
        event.traffic_type = 'Telemetry'
        event.packet_size = 512
        
        rest_api.update_statistics(event)
        
        assert rest_api.traffic_stats['current']['telemetry_packets'] == 1
        assert rest_api.traffic_stats['current']['telemetry_bytes'] == 512
    
    def test_update_statistics_tracks_by_flow(self, rest_api):
        """Test that update_statistics tracks traffic by flow"""
        event = Mock()
        event.from_component = 'Master'
        event.to_component = 'Power_01'
        event.traffic_type = 'Control'
        event.packet_size = 1024
        
        rest_api.update_statistics(event)
        
        flow_key = 'Master->Power_01'
        assert flow_key in rest_api.traffic_stats['current']['traffic_by_component']
        assert rest_api.traffic_stats['current']['traffic_by_component'][flow_key]['packets'] == 1
    
    def test_update_statistics_multiple_events(self, rest_api):
        """Test that update_statistics handles multiple events"""
        event1 = Mock()
        event1.from_component = 'Master'
        event1.to_component = 'Power_01'
        event1.traffic_type = 'Control'
        event1.packet_size = 1024
        
        event2 = Mock()
        event2.from_component = 'Power_01'
        event2.to_component = 'Storage_01'
        event2.traffic_type = 'Telemetry'
        event2.packet_size = 512
        
        rest_api.update_statistics(event1)
        rest_api.update_statistics(event2)
        
        assert rest_api.traffic_stats['current']['total_packets'] == 2
        assert rest_api.traffic_stats['current']['total_bytes'] == 1536
        assert rest_api.traffic_stats['current']['control_packets'] == 1
        assert rest_api.traffic_stats['current']['telemetry_packets'] == 1


class TestRestAPIIntegration:
    """Integration tests for REST API"""
    
    def test_calculate_statistics_with_real_packets(self):
        """Test statistics calculation with real packet data"""
        rest_api = RestAPIRoutes()
        
        packets = [
            RawPacket(
                src_ip='10.0.8.1',
                dst_ip='10.0.8.2',
                src_port=22,
                dst_port=5000,
                protocol='TCP',
                packet_size=1024,
                timestamp=datetime.now()
            ),
            RawPacket(
                src_ip='10.0.8.2',
                dst_ip='10.0.8.3',
                src_port=9000,
                dst_port=9001,
                protocol='UDP',
                packet_size=512,
                timestamp=datetime.now()
            ),
        ]
        
        stats = rest_api._calculate_statistics(packets)
        
        assert stats['total_packets'] == 2
        assert stats['total_bytes'] == 1536
        assert stats['control_packets'] >= 1
        assert stats['telemetry_packets'] >= 1
    
    def test_statistics_with_time_filtering(self):
        """Test statistics with time range filtering"""
        rest_api = RestAPIRoutes()
        
        now = datetime.now()
        old_time = now - timedelta(hours=2)
        
        packets = [
            RawPacket(
                src_ip='10.0.8.1',
                dst_ip='10.0.8.2',
                src_port=22,
                dst_port=5000,
                protocol='TCP',
                packet_size=1024,
                timestamp=old_time
            ),
            RawPacket(
                src_ip='10.0.8.2',
                dst_ip='10.0.8.3',
                src_port=9000,
                dst_port=9001,
                protocol='UDP',
                packet_size=512,
                timestamp=now
            ),
        ]
        
        collector = Mock()
        collector.get_packets.return_value = packets
        rest_api.traffic_collector = collector
        
        # Query for last hour
        start_time = (now - timedelta(hours=1)).isoformat()
        result = rest_api.get_statistics(start_time=start_time)
        
        # Should only include recent packet
        assert result['total_packets'] == 1
        assert result['total_bytes'] == 512
