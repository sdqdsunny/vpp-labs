"""
Unit tests for VPP Data Connector Service

Tests the integration between 3D visualization and VPP simulation system.
"""

import pytest
import json
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from collections import defaultdict

# Add parent directory to path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.vpp_data_connector import VPPDataConnector
from models.visualization_event import VisualizationEvent


class TestVPPDataConnector:
    """Test suite for VPPDataConnector"""
    
    @pytest.fixture
    def connector(self):
        """Create a VPPDataConnector instance for testing"""
        return VPPDataConnector(vpp_api_base="http://localhost:8001")
    
    @pytest.fixture
    def mock_realtime_data(self):
        """Mock real-time data from VPP API"""
        return {
            'timestamp': '2026-02-20T13:38:46.568000',
            'power_generation': {
                'current_power': 150.5,
                'solar_power': 100.0,
                'wind_power': 50.5,
                'efficiency': 95.5,
                'device_status': 'running',
                'timestamp': '2026-02-20T13:38:43.497582'
            },
            'storage': {
                'soc': 65.4,
                'soh': 98.5,
                'current_power': 25.3,
                'charge_status': 'charging',
                'temperature': 24.8,
                'timestamp': '2026-02-20T13:38:43.499464'
            },
            'demand': {
                'current_demand': 131.5,
                'flexible_demand': 29.0,
                'dr_status': 'active',
                'timestamp': '2026-02-20T13:38:43.500810'
            },
            'coordinator': {
                'status': 'operational',
                'active_connections': 0,
                'last_coordination': '2026-02-20T11:16:12.131633',
                'timestamp': '2026-02-20T11:16:12.131634'
            },
            'energy_balance': {
                'total_supply': 175.8,
                'demand': 131.5,
                'balance': 44.3,
                'status': 'surplus'
            },
            'system_status': {
                'power_status': 'running',
                'storage_status': 'charging',
                'demand_status': 'active',
                'overall_status': 'operational'
            }
        }
    
    @pytest.fixture
    def mock_packets(self):
        """Mock packet data from analyzer"""
        return [
            {
                'timestamp': '2026-02-20T13:23:18.560526',
                'protocol': 'MQTT',
                'src_ip': '192.168.1.10',
                'dst_ip': '192.168.1.20',
                'src_port': 12345,
                'dst_port': 1883,
                'size': 256,
                'direction': 'upstream'
            },
            {
                'timestamp': '2026-02-20T13:23:19.560526',
                'protocol': 'Modbus',
                'src_ip': '10.0.0.5',
                'dst_ip': '10.0.0.10',
                'src_port': 54321,
                'dst_port': 502,
                'size': 512,
                'direction': 'downstream'
            }
        ]
    
    def test_initialization(self, connector):
        """Test VPPDataConnector initialization"""
        assert connector.vpp_api_base == "http://localhost:8001"
        assert connector.is_connected == False
        assert connector.is_running == False
        assert connector.last_packet_count == 0
        assert isinstance(connector.packet_frequency, defaultdict)
    
    def test_initialization_with_custom_base(self):
        """Test initialization with custom API base"""
        custom_base = "http://vpp-simulation:8001"
        connector = VPPDataConnector(vpp_api_base=custom_base)
        assert connector.vpp_api_base == custom_base
    
    @patch('services.vpp_data_connector.requests.get')
    def test_connect_success(self, mock_get, connector):
        """Test successful connection to VPP API"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'status': 'ok'}
        mock_get.return_value = mock_response
        
        result = connector.connect()
        
        assert result == True
        assert connector.is_connected == True
        mock_get.assert_called_once()
    
    @patch('services.vpp_data_connector.requests.get')
    def test_connect_failure_status_code(self, mock_get, connector):
        """Test connection failure due to bad status code"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response
        
        result = connector.connect()
        
        assert result == False
        assert connector.is_connected == False
    
    @patch('services.vpp_data_connector.requests.get')
    def test_connect_failure_exception(self, mock_get, connector):
        """Test connection failure due to exception"""
        mock_get.side_effect = Exception("Connection refused")
        
        result = connector.connect()
        
        assert result == False
        assert connector.is_connected == False
    
    @patch('services.vpp_data_connector.requests.get')
    def test_fetch_realtime_data_success(self, mock_get, connector, mock_realtime_data):
        """Test successful fetch of real-time data"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_realtime_data
        mock_get.return_value = mock_response
        
        result = connector.fetch_realtime_data()
        
        assert result is not None
        assert result['power_generation']['current_power'] == 150.5
        assert result['storage']['soc'] == 65.4
        assert result['demand']['current_demand'] == 131.5
    
    @patch('services.vpp_data_connector.requests.get')
    def test_fetch_realtime_data_failure(self, mock_get, connector):
        """Test fetch real-time data failure"""
        mock_get.side_effect = Exception("Network error")
        
        result = connector.fetch_realtime_data()
        
        assert result is None
    
    @patch('services.vpp_data_connector.requests.get')
    def test_fetch_traffic_stats_success(self, mock_get, connector):
        """Test successful fetch of traffic statistics"""
        mock_stats = [
            {'protocol': 'MQTT', 'packet_count': 39, 'total_bytes': 32156},
            {'protocol': 'Modbus', 'packet_count': 35, 'total_bytes': 29451}
        ]
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_stats
        mock_get.return_value = mock_response
        
        result = connector.fetch_traffic_stats()
        
        assert result is not None
        assert len(result) == 2
        assert result[0]['protocol'] == 'MQTT'
    
    @patch('services.vpp_data_connector.requests.get')
    def test_fetch_packets_success(self, mock_get, connector, mock_packets):
        """Test successful fetch of packets"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_packets
        mock_get.return_value = mock_response
        
        result = connector.fetch_packets(limit=100)
        
        assert result is not None
        assert len(result) == 2
        assert result[0]['protocol'] == 'MQTT'
    
    def test_convert_realtime_to_events_valid_data(self, connector, mock_realtime_data):
        """Test conversion of real-time data to visualization events"""
        events = connector.convert_realtime_to_events(mock_realtime_data)
        
        assert events is not None
        assert len(events) > 0
        
        # Check that all events are VisualizationEvent instances
        for event in events:
            assert isinstance(event, VisualizationEvent)
            assert event.from_component in ['Power_Generation', 'Storage', 'Coordinator']
            assert event.to_component in ['Power_Generation', 'Storage', 'Demand', 'Coordinator']
            assert event.traffic_type in ['Control', 'Telemetry']
            assert 0.0 <= event.intensity <= 1.0
    
    def test_convert_realtime_to_events_zero_power(self, connector):
        """Test conversion with zero power values"""
        data = {
            'power_generation': {'current_power': 0},
            'storage': {'current_power': 0},
            'demand': {'current_demand': 0},
            'coordinator': {'status': 'operational'}
        }
        
        events = connector.convert_realtime_to_events(data)
        
        # Should still generate coordinator events
        assert len(events) > 0
    
    def test_convert_realtime_to_events_missing_fields(self, connector):
        """Test conversion with missing fields"""
        data = {
            'power_generation': {},
            'storage': {},
            'demand': {},
            'coordinator': {}
        }
        
        events = connector.convert_realtime_to_events(data)
        
        # Should handle gracefully
        assert isinstance(events, list)
    
    def test_convert_packets_to_events_valid_data(self, connector, mock_packets):
        """Test conversion of packets to visualization events"""
        events = connector.convert_packets_to_events(mock_packets)
        
        assert events is not None
        assert len(events) > 0
        
        for event in events:
            assert isinstance(event, VisualizationEvent)
            assert event.traffic_type in ['Control', 'Telemetry']
            assert 0.0 <= event.intensity <= 1.0
    
    def test_convert_packets_to_events_empty_list(self, connector):
        """Test conversion of empty packet list"""
        events = connector.convert_packets_to_events([])
        
        assert events == []
    
    def test_calculate_intensity_from_power_zero(self, connector):
        """Test intensity calculation with zero power"""
        intensity = connector._calculate_intensity_from_power(0)
        
        assert intensity == 0.0
    
    def test_calculate_intensity_from_power_max(self, connector):
        """Test intensity calculation with max power"""
        intensity = connector._calculate_intensity_from_power(200)
        
        assert intensity == 1.0
    
    def test_calculate_intensity_from_power_mid(self, connector):
        """Test intensity calculation with mid-range power"""
        intensity = connector._calculate_intensity_from_power(100)
        
        assert 0.4 < intensity < 0.6
    
    def test_calculate_intensity_from_power_overflow(self, connector):
        """Test intensity calculation with power > 200"""
        intensity = connector._calculate_intensity_from_power(300)
        
        assert intensity == 1.0  # Should be capped at 1.0
    
    def test_calculate_packet_intensity(self, connector):
        """Test packet intensity calculation"""
        flow_key = ('Power_Generation', 'Storage')
        intensity = connector._calculate_packet_intensity(100, flow_key)
        
        assert 0.0 <= intensity <= 1.0
    
    def test_map_protocol_to_component_mqtt(self, connector):
        """Test protocol to component mapping for MQTT"""
        component = connector._map_protocol_to_component('MQTT', 'source')
        assert component == 'Power_Generation'
        
        component = connector._map_protocol_to_component('MQTT', 'dest')
        assert component == 'Coordinator'
    
    def test_map_protocol_to_component_modbus(self, connector):
        """Test protocol to component mapping for Modbus"""
        component = connector._map_protocol_to_component('Modbus', 'source')
        assert component == 'Power_Generation'
    
    def test_map_protocol_to_component_opc_ua(self, connector):
        """Test protocol to component mapping for OPC UA"""
        component = connector._map_protocol_to_component('OPC UA', 'source')
        assert component == 'Storage'
    
    def test_map_protocol_to_component_dnp3(self, connector):
        """Test protocol to component mapping for DNP3"""
        component = connector._map_protocol_to_component('DNP3', 'source')
        assert component == 'Storage'
    
    def test_map_protocol_to_component_unknown(self, connector):
        """Test protocol to component mapping for unknown protocol"""
        component = connector._map_protocol_to_component('Unknown', 'source')
        assert component == 'Coordinator'
    
    def test_get_connection_status(self, connector):
        """Test getting connection status"""
        connector.is_connected = True
        connector.is_running = False
        
        status = connector.get_connection_status()
        
        assert status['connected'] == True
        assert status['is_fetching'] == False
        assert 'api_base' in status
        assert 'timestamp' in status
    
    def test_traffic_type_validation(self, connector, mock_realtime_data):
        """Test that traffic types are properly capitalized"""
        events = connector.convert_realtime_to_events(mock_realtime_data)
        
        for event in events:
            # Traffic type must be exactly 'Control' or 'Telemetry'
            assert event.traffic_type in ['Control', 'Telemetry'], \
                f"Invalid traffic type: {event.traffic_type}"
    
    def test_component_names_consistency(self, connector, mock_realtime_data):
        """Test that component names are consistent"""
        events = connector.convert_realtime_to_events(mock_realtime_data)
        
        valid_components = {
            'Power_Generation', 'Storage', 'Demand', 'Coordinator'
        }
        
        for event in events:
            assert event.from_component in valid_components, \
                f"Invalid from_component: {event.from_component}"
            assert event.to_component in valid_components, \
                f"Invalid to_component: {event.to_component}"
    
    def test_intensity_bounds(self, connector, mock_realtime_data):
        """Test that all intensities are within valid bounds"""
        events = connector.convert_realtime_to_events(mock_realtime_data)
        
        for event in events:
            assert 0.0 <= event.intensity <= 1.0, \
                f"Intensity out of bounds: {event.intensity}"
    
    def test_timestamp_validity(self, connector, mock_realtime_data):
        """Test that all events have valid timestamps"""
        events = connector.convert_realtime_to_events(mock_realtime_data)
        
        for event in events:
            assert isinstance(event.timestamp, datetime), \
                f"Invalid timestamp type: {type(event.timestamp)}"


class TestVPPDataConnectorIntegration:
    """Integration tests for VPPDataConnector"""
    
    @pytest.fixture
    def connector(self):
        """Create a VPPDataConnector instance for testing"""
        return VPPDataConnector(vpp_api_base="http://localhost:8001")
    
    @patch('services.vpp_data_connector.requests.get')
    def test_full_workflow_realtime_data(self, mock_get, connector):
        """Test full workflow: fetch -> convert -> validate"""
        mock_realtime_data = {
            'power_generation': {'current_power': 150.5},
            'storage': {'current_power': 25.3},
            'demand': {'current_demand': 131.5},
            'coordinator': {'status': 'operational'}
        }
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_realtime_data
        mock_get.return_value = mock_response
        
        # Fetch data
        data = connector.fetch_realtime_data()
        assert data is not None
        
        # Convert to events
        events = connector.convert_realtime_to_events(data)
        assert len(events) > 0
        
        # Validate events
        for event in events:
            assert event.traffic_type in ['Control', 'Telemetry']
            assert 0.0 <= event.intensity <= 1.0
    
    @patch('services.vpp_data_connector.requests.get')
    def test_full_workflow_packets(self, mock_get, connector):
        """Test full workflow for packets: fetch -> convert -> validate"""
        mock_packets = [
            {
                'protocol': 'MQTT',
                'src_ip': '192.168.1.10',
                'dst_ip': '192.168.1.20',
                'src_port': 12345,
                'dst_port': 1883,
                'size': 256
            }
        ]
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_packets
        mock_get.return_value = mock_response
        
        # Fetch packets
        packets = connector.fetch_packets()
        assert packets is not None
        
        # Convert to events
        events = connector.convert_packets_to_events(packets)
        assert len(events) > 0
        
        # Validate events
        for event in events:
            assert event.traffic_type in ['Control', 'Telemetry']
            assert 0.0 <= event.intensity <= 1.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
