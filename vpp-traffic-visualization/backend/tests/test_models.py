"""
Unit tests for data models

Tests for RawPacket, VisualizationEvent, and ComponentInfo models.
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.raw_packet import RawPacket
from models.visualization_event import VisualizationEvent
from models.component_info import ComponentInfo


class TestRawPacket:
    """Test RawPacket model"""
    
    def test_raw_packet_creation(self):
        """Test creating a RawPacket"""
        packet = RawPacket(
            src_ip='10.0.8.1',
            dst_ip='10.0.8.2',
            src_port=5000,
            dst_port=8080,
            protocol='TCP',
            packet_size=1024,
            timestamp=datetime.now()
        )
        
        assert packet.src_ip == '10.0.8.1'
        assert packet.dst_ip == '10.0.8.2'
        assert packet.src_port == 5000
        assert packet.dst_port == 8080
        assert packet.protocol == 'TCP'
        assert packet.packet_size == 1024
    
    def test_raw_packet_to_dict(self):
        """Test converting RawPacket to dictionary"""
        now = datetime.now()
        packet = RawPacket(
            src_ip='10.0.8.1',
            dst_ip='10.0.8.2',
            src_port=5000,
            dst_port=8080,
            protocol='TCP',
            packet_size=1024,
            timestamp=now
        )
        
        packet_dict = packet.to_dict()
        
        assert packet_dict['src_ip'] == '10.0.8.1'
        assert packet_dict['dst_ip'] == '10.0.8.2'
        assert packet_dict['packet_size'] == 1024
        assert packet_dict['protocol'] == 'TCP'
    
    def test_raw_packet_from_dict(self):
        """Test creating RawPacket from dictionary"""
        now = datetime.now()
        data = {
            'src_ip': '10.0.8.1',
            'dst_ip': '10.0.8.2',
            'src_port': 5000,
            'dst_port': 8080,
            'protocol': 'TCP',
            'packet_size': 1024,
            'timestamp': now.isoformat(),
            'payload': None
        }
        
        packet = RawPacket.from_dict(data)
        
        assert packet.src_ip == '10.0.8.1'
        assert packet.dst_ip == '10.0.8.2'
        assert packet.packet_size == 1024


class TestVisualizationEvent:
    """Test VisualizationEvent model"""
    
    def test_visualization_event_creation(self):
        """Test creating a VisualizationEvent"""
        event = VisualizationEvent(
            from_component='Master',
            to_component='Storage_01',
            traffic_type='Control',
            intensity=0.8,
            packet_size=512,
            timestamp=datetime.now()
        )
        
        assert event.from_component == 'Master'
        assert event.to_component == 'Storage_01'
        assert event.traffic_type == 'Control'
        assert event.intensity == 0.8
        assert event.packet_size == 512
    
    def test_visualization_event_invalid_intensity(self):
        """Test that invalid intensity raises error"""
        with pytest.raises(ValueError):
            VisualizationEvent(
                from_component='Master',
                to_component='Storage_01',
                traffic_type='Control',
                intensity=1.5,  # Invalid: > 1.0
                packet_size=512,
                timestamp=datetime.now()
            )
    
    def test_visualization_event_invalid_type(self):
        """Test that invalid traffic type raises error"""
        with pytest.raises(ValueError):
            VisualizationEvent(
                from_component='Master',
                to_component='Storage_01',
                traffic_type='Invalid',  # Invalid type
                intensity=0.8,
                packet_size=512,
                timestamp=datetime.now()
            )
    
    def test_visualization_event_to_dict(self):
        """Test converting VisualizationEvent to dictionary"""
        now = datetime.now()
        event = VisualizationEvent(
            from_component='Master',
            to_component='Storage_01',
            traffic_type='Control',
            intensity=0.8,
            packet_size=512,
            timestamp=now
        )
        
        event_dict = event.to_dict()
        
        assert event_dict['from'] == 'Master'
        assert event_dict['to'] == 'Storage_01'
        assert event_dict['type'] == 'Control'
        assert event_dict['intensity'] == 0.8
        assert event_dict['packet_size'] == 512
    
    def test_visualization_event_from_dict(self):
        """Test creating VisualizationEvent from dictionary"""
        now = datetime.now()
        data = {
            'from': 'Master',
            'to': 'Storage_01',
            'type': 'Control',
            'intensity': 0.8,
            'packet_size': 512,
            'timestamp': now.isoformat()
        }
        
        event = VisualizationEvent.from_dict(data)
        
        assert event.from_component == 'Master'
        assert event.to_component == 'Storage_01'
        assert event.traffic_type == 'Control'


class TestComponentInfo:
    """Test ComponentInfo model"""
    
    def test_component_info_creation(self):
        """Test creating a ComponentInfo"""
        component = ComponentInfo(
            name='Master',
            ip_address='10.0.8.1',
            component_type='coordinator',
            position=(0, 0, 0),
            status='online',
            color='#FF6B6B'
        )
        
        assert component.name == 'Master'
        assert component.ip_address == '10.0.8.1'
        assert component.component_type == 'coordinator'
        assert component.status == 'online'
        assert component.color == '#FF6B6B'
    
    def test_component_info_invalid_type(self):
        """Test that invalid component type raises error"""
        with pytest.raises(ValueError):
            ComponentInfo(
                name='Master',
                ip_address='10.0.8.1',
                component_type='invalid',  # Invalid type
                position=(0, 0, 0),
                status='online',
                color='#FF6B6B'
            )
    
    def test_component_info_invalid_status(self):
        """Test that invalid status raises error"""
        with pytest.raises(ValueError):
            ComponentInfo(
                name='Master',
                ip_address='10.0.8.1',
                component_type='coordinator',
                position=(0, 0, 0),
                status='invalid',  # Invalid status
                color='#FF6B6B'
            )
    
    def test_component_info_invalid_color(self):
        """Test that invalid color raises error"""
        with pytest.raises(ValueError):
            ComponentInfo(
                name='Master',
                ip_address='10.0.8.1',
                component_type='coordinator',
                position=(0, 0, 0),
                status='online',
                color='invalid'  # Invalid color
            )
    
    def test_component_info_to_dict(self):
        """Test converting ComponentInfo to dictionary"""
        component = ComponentInfo(
            name='Master',
            ip_address='10.0.8.1',
            component_type='coordinator',
            position=(0, 0, 0),
            status='online',
            color='#FF6B6B'
        )
        
        component_dict = component.to_dict()
        
        assert component_dict['name'] == 'Master'
        assert component_dict['ip'] == '10.0.8.1'
        assert component_dict['type'] == 'coordinator'
        assert component_dict['status'] == 'online'
        assert component_dict['color'] == '#FF6B6B'
    
    def test_component_info_from_dict(self):
        """Test creating ComponentInfo from dictionary"""
        data = {
            'name': 'Master',
            'ip': '10.0.8.1',
            'type': 'coordinator',
            'position': (0, 0, 0),
            'status': 'online',
            'color': '#FF6B6B'
        }
        
        component = ComponentInfo.from_dict(data)
        
        assert component.name == 'Master'
        assert component.ip_address == '10.0.8.1'
        assert component.component_type == 'coordinator'
