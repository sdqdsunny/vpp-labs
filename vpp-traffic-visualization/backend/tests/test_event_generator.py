"""
Unit tests for EventGenerator service

Tests for event generation, intensity calculation, and IP mapping.
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.raw_packet import RawPacket
from models.visualization_event import VisualizationEvent
from services.event_generator import EventGenerator


class TestEventGeneratorBasics:
    """Test basic EventGenerator functionality"""
    
    def test_event_generator_initialization(self):
        """Test EventGenerator initialization"""
        generator = EventGenerator()
        
        assert generator is not None
        assert len(generator.VPP_COMPONENTS) == 4
        assert generator.VPP_COMPONENTS['10.0.8.1'] == 'Master'
    
    def test_map_ip_to_component_known(self):
        """Test mapping known IP to component"""
        generator = EventGenerator()
        
        assert generator.map_ip_to_component('10.0.8.1') == 'Master'
        assert generator.map_ip_to_component('10.0.8.2') == 'Power_01'
        assert generator.map_ip_to_component('10.0.8.3') == 'Storage_01'
        assert generator.map_ip_to_component('10.0.8.4') == 'Demand_01'
    
    def test_map_ip_to_component_unknown(self):
        """Test mapping unknown IP returns Unknown"""
        generator = EventGenerator()
        
        assert generator.map_ip_to_component('192.168.1.1') == 'Unknown'
        assert generator.map_ip_to_component('10.0.0.1') == 'Unknown'
    
    def test_get_component_ip(self):
        """Test getting IP for component name"""
        generator = EventGenerator()
        
        assert generator.get_component_ip('Master') == '10.0.8.1'
        assert generator.get_component_ip('Power_01') == '10.0.8.2'
        assert generator.get_component_ip('Storage_01') == '10.0.8.3'
        assert generator.get_component_ip('Demand_01') == '10.0.8.4'
    
    def test_get_component_ip_unknown(self):
        """Test getting IP for unknown component"""
        generator = EventGenerator()
        
        assert generator.get_component_ip('Unknown') is None
        assert generator.get_component_ip('NonExistent') is None


class TestEventGeneration:
    """Test event generation from packets"""
    
    def test_generate_event_control_traffic(self):
        """Test generating event for control traffic"""
        generator = EventGenerator()
        
        packet = RawPacket(
            src_ip='10.0.8.1',
            dst_ip='10.0.8.2',
            src_port=5000,
            dst_port=8080,
            protocol='TCP',
            packet_size=512,
            timestamp=datetime.now()
        )
        
        event = generator.generate_event(packet)
        
        assert event is not None
        assert event.from_component == 'Master'
        assert event.to_component == 'Power_01'
        assert event.traffic_type == 'Control'
        assert event.packet_size == 512
        assert 0.0 <= event.intensity <= 1.0
    
    def test_generate_event_telemetry_traffic(self):
        """Test generating event for telemetry traffic"""
        generator = EventGenerator()
        
        packet = RawPacket(
            src_ip='10.0.8.2',
            dst_ip='10.0.8.1',
            src_port=5001,
            dst_port=5001,
            protocol='UDP',
            packet_size=256,
            timestamp=datetime.now()
        )
        
        event = generator.generate_event(packet)
        
        assert event is not None
        assert event.from_component == 'Power_01'
        assert event.to_component == 'Master'
        assert event.traffic_type == 'Telemetry'
        assert event.packet_size == 256
    
    def test_generate_event_unknown_component(self):
        """Test that event is not generated for unknown components"""
        generator = EventGenerator()
        
        packet = RawPacket(
            src_ip='192.168.1.1',
            dst_ip='10.0.8.1',
            src_port=5000,
            dst_port=8080,
            protocol='TCP',
            packet_size=512,
            timestamp=datetime.now()
        )
        
        event = generator.generate_event(packet)
        
        assert event is None
    
    def test_generate_event_preserves_timestamp(self):
        """Test that event preserves packet timestamp"""
        generator = EventGenerator()
        
        now = datetime.now()
        packet = RawPacket(
            src_ip='10.0.8.1',
            dst_ip='10.0.8.2',
            src_port=5000,
            dst_port=8080,
            protocol='TCP',
            packet_size=512,
            timestamp=now
        )
        
        event = generator.generate_event(packet)
        
        assert event.timestamp == now


class TestIntensityCalculation:
    """Test traffic intensity calculation"""
    
    def test_intensity_minimum_packet_size(self):
        """Test intensity for minimum packet size"""
        generator = EventGenerator()
        
        flow_key = ('Master', 'Power_01')
        intensity = generator.calculate_intensity(
            packet_size=64,  # Minimum
            flow_key=flow_key,
            timestamp=datetime.now()
        )
        
        assert 0.0 <= intensity <= 1.0
    
    def test_intensity_maximum_packet_size(self):
        """Test intensity for maximum packet size"""
        generator = EventGenerator()
        
        flow_key = ('Master', 'Power_01')
        intensity = generator.calculate_intensity(
            packet_size=65535,  # Maximum
            flow_key=flow_key,
            timestamp=datetime.now()
        )
        
        assert 0.0 <= intensity <= 1.0
    
    def test_intensity_increases_with_packet_size(self):
        """Test that intensity increases with packet size"""
        generator = EventGenerator()
        
        flow_key = ('Master', 'Power_01')
        now = datetime.now()
        
        intensity_small = generator.calculate_intensity(
            packet_size=100,
            flow_key=flow_key,
            timestamp=now
        )
        
        generator.clear_frequency_data()
        
        intensity_large = generator.calculate_intensity(
            packet_size=10000,
            flow_key=flow_key,
            timestamp=now
        )
        
        assert intensity_large > intensity_small
    
    def test_intensity_increases_with_frequency(self):
        """Test that intensity increases with packet frequency"""
        generator = EventGenerator()
        
        flow_key = ('Master', 'Power_01')
        now = datetime.now()
        
        # First packet
        intensity_1 = generator.calculate_intensity(
            packet_size=512,
            flow_key=flow_key,
            timestamp=now
        )
        
        # Multiple packets in quick succession
        for i in range(10):
            generator.calculate_intensity(
                packet_size=512,
                flow_key=flow_key,
                timestamp=now + timedelta(milliseconds=i*10)
            )
        
        intensity_many = generator.calculate_intensity(
            packet_size=512,
            flow_key=flow_key,
            timestamp=now + timedelta(milliseconds=100)
        )
        
        assert intensity_many > intensity_1
    
    def test_intensity_clears_old_timestamps(self):
        """Test that old timestamps are cleared from frequency tracking"""
        generator = EventGenerator()
        
        flow_key = ('Master', 'Power_01')
        now = datetime.now()
        
        # Add packet outside window first
        old_time = now - timedelta(seconds=2)
        generator.calculate_intensity(
            packet_size=512,
            flow_key=flow_key,
            timestamp=old_time
        )
        
        # Add current packet - this should clean up old timestamps
        generator.calculate_intensity(
            packet_size=512,
            flow_key=flow_key,
            timestamp=now
        )
        
        # Check that old timestamp is not in frequency data
        # Only the current timestamp should remain
        assert len(generator.packet_frequency[flow_key]) == 1


class TestComponentMapping:
    """Test component mapping functionality"""
    
    def test_add_component_mapping(self):
        """Test adding custom component mapping"""
        generator = EventGenerator()
        
        generator.add_component_mapping('192.168.1.100', 'CustomComponent')
        
        assert generator.map_ip_to_component('192.168.1.100') == 'CustomComponent'
    
    def test_remove_component_mapping(self):
        """Test removing component mapping"""
        generator = EventGenerator()
        
        generator.add_component_mapping('192.168.1.100', 'CustomComponent')
        assert generator.map_ip_to_component('192.168.1.100') == 'CustomComponent'
        
        generator.remove_component_mapping('192.168.1.100')
        assert generator.map_ip_to_component('192.168.1.100') == 'Unknown'
    
    def test_get_component_mappings(self):
        """Test getting all component mappings"""
        generator = EventGenerator()
        
        mappings = generator.get_component_mappings()
        
        assert len(mappings) == 4
        assert mappings['10.0.8.1'] == 'Master'
        assert mappings['10.0.8.2'] == 'Power_01'
    
    def test_add_mapping_overwrites_existing(self):
        """Test that adding mapping overwrites existing"""
        generator = EventGenerator()
        
        original = generator.map_ip_to_component('10.0.8.1')
        assert original == 'Master'
        
        generator.add_component_mapping('10.0.8.1', 'NewMaster')
        assert generator.map_ip_to_component('10.0.8.1') == 'NewMaster'
        
        # Restore original mapping for other tests
        generator.add_component_mapping('10.0.8.1', 'Master')


class TestEventGeneratorIntegration:
    """Integration tests for EventGenerator"""
    
    def test_generate_multiple_events(self):
        """Test generating multiple events"""
        generator = EventGenerator()
        
        packets = [
            RawPacket(
                src_ip='10.0.8.1',
                dst_ip='10.0.8.2',
                src_port=5000,
                dst_port=8080,
                protocol='TCP',
                packet_size=512,
                timestamp=datetime.now()
            ),
            RawPacket(
                src_ip='10.0.8.2',
                dst_ip='10.0.8.1',
                src_port=5001,
                dst_port=5001,
                protocol='UDP',
                packet_size=256,
                timestamp=datetime.now()
            ),
            RawPacket(
                src_ip='10.0.8.3',
                dst_ip='10.0.8.1',
                src_port=5001,
                dst_port=5001,
                protocol='UDP',
                packet_size=1024,
                timestamp=datetime.now()
            ),
        ]
        
        events = [generator.generate_event(p) for p in packets]
        
        assert len(events) == 3
        assert all(e is not None for e in events)
        assert events[0].from_component == 'Master'
        assert events[1].from_component == 'Power_01'
        assert events[2].from_component == 'Storage_01'
    
    def test_clear_frequency_data(self):
        """Test clearing frequency data"""
        generator = EventGenerator()
        
        flow_key = ('Master', 'Power_01')
        now = datetime.now()
        
        # Add some packets
        for i in range(5):
            generator.calculate_intensity(
                packet_size=512,
                flow_key=flow_key,
                timestamp=now + timedelta(milliseconds=i*10)
            )
        
        assert len(generator.packet_frequency[flow_key]) > 0
        
        generator.clear_frequency_data()
        
        assert len(generator.packet_frequency) == 0
    
    def test_event_to_dict_conversion(self):
        """Test converting generated event to dictionary"""
        generator = EventGenerator()
        
        packet = RawPacket(
            src_ip='10.0.8.1',
            dst_ip='10.0.8.2',
            src_port=5000,
            dst_port=8080,
            protocol='TCP',
            packet_size=512,
            timestamp=datetime.now()
        )
        
        event = generator.generate_event(packet)
        event_dict = event.to_dict()
        
        assert event_dict['from'] == 'Master'
        assert event_dict['to'] == 'Power_01'
        assert event_dict['type'] == 'Control'
        assert event_dict['packet_size'] == 512
        assert 'timestamp' in event_dict


class TestEventGeneratorEdgeCases:
    """Test edge cases and error handling"""
    
    def test_generate_event_with_zero_packet_size(self):
        """Test generating event with zero packet size"""
        generator = EventGenerator()
        
        packet = RawPacket(
            src_ip='10.0.8.1',
            dst_ip='10.0.8.2',
            src_port=5000,
            dst_port=8080,
            protocol='TCP',
            packet_size=0,
            timestamp=datetime.now()
        )
        
        event = generator.generate_event(packet)
        
        assert event is not None
        assert event.packet_size == 0
        assert 0.0 <= event.intensity <= 1.0
    
    def test_generate_event_with_large_packet_size(self):
        """Test generating event with large packet size"""
        generator = EventGenerator()
        
        packet = RawPacket(
            src_ip='10.0.8.1',
            dst_ip='10.0.8.2',
            src_port=5000,
            dst_port=8080,
            protocol='TCP',
            packet_size=100000,
            timestamp=datetime.now()
        )
        
        event = generator.generate_event(packet)
        
        assert event is not None
        assert event.packet_size == 100000
        assert 0.0 <= event.intensity <= 1.0
    
    def test_intensity_calculation_with_invalid_flow_key(self):
        """Test intensity calculation handles various flow keys"""
        generator = EventGenerator()
        
        now = datetime.now()
        
        # Different flow keys should have independent frequency tracking
        intensity1 = generator.calculate_intensity(
            packet_size=512,
            flow_key=('Master', 'Power_01'),
            timestamp=now
        )
        
        intensity2 = generator.calculate_intensity(
            packet_size=512,
            flow_key=('Master', 'Storage_01'),
            timestamp=now
        )
        
        # Both should be valid
        assert 0.0 <= intensity1 <= 1.0
        assert 0.0 <= intensity2 <= 1.0
