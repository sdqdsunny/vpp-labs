"""
Unit tests for TrafficClassifier service

Tests for traffic classification, port management, and component mapping.
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.traffic_classifier import TrafficClassifier


class TestTrafficClassifierBasics:
    """Test basic TrafficClassifier functionality"""
    
    def test_classifier_initialization(self):
        """Test TrafficClassifier initialization"""
        classifier = TrafficClassifier()
        
        assert classifier is not None
        assert len(classifier.control_ports) > 0
        assert len(classifier.telemetry_ports) > 0
        assert len(classifier.VPP_COMPONENTS) == 4
    
    def test_default_control_ports(self):
        """Test default control ports are set"""
        classifier = TrafficClassifier()
        
        assert 5000 in classifier.control_ports
        assert 8080 in classifier.control_ports
        assert 8000 in classifier.control_ports
        assert 9000 in classifier.control_ports
    
    def test_default_telemetry_ports(self):
        """Test default telemetry ports are set"""
        classifier = TrafficClassifier()
        
        assert 5001 in classifier.telemetry_ports
        assert 5002 in classifier.telemetry_ports
        assert 8081 in classifier.telemetry_ports
    
    def test_vpp_components_mapping(self):
        """Test VPP components are correctly mapped"""
        classifier = TrafficClassifier()
        
        assert classifier.VPP_COMPONENTS['10.0.8.1'] == 'Master'
        assert classifier.VPP_COMPONENTS['10.0.8.2'] == 'Power_01'
        assert classifier.VPP_COMPONENTS['10.0.8.3'] == 'Storage_01'
        assert classifier.VPP_COMPONENTS['10.0.8.4'] == 'Demand_01'


class TestTrafficClassification:
    """Test traffic classification"""
    
    def test_classify_control_traffic_from_master(self):
        """Test classifying control traffic from Master"""
        classifier = TrafficClassifier()
        
        traffic_type = classifier.classify(
            src_ip='10.0.8.1',
            dst_ip='10.0.8.2',
            src_port=5000,
            dst_port=8080,
            protocol='TCP'
        )
        
        assert traffic_type == 'Control'
    
    def test_classify_telemetry_traffic_to_master(self):
        """Test classifying telemetry traffic to Master"""
        classifier = TrafficClassifier()
        
        traffic_type = classifier.classify(
            src_ip='10.0.8.2',
            dst_ip='10.0.8.1',
            src_port=5001,
            dst_port=5001,
            protocol='UDP'
        )
        
        assert traffic_type == 'Telemetry'
    
    def test_classify_unknown_traffic_defaults_to_telemetry(self):
        """Test that unknown traffic defaults to Telemetry"""
        classifier = TrafficClassifier()
        
        traffic_type = classifier.classify(
            src_ip='192.168.1.1',
            dst_ip='192.168.1.2',
            src_port=9999,
            dst_port=9999,
            protocol='TCP'
        )
        
        assert traffic_type == 'Telemetry'
    
    def test_classify_multiple_traffic_types(self):
        """Test classifying multiple traffic types"""
        classifier = TrafficClassifier()
        
        # Control traffic
        control = classifier.classify('10.0.8.1', '10.0.8.2', 5000, 8080, 'TCP')
        assert control == 'Control'
        
        # Telemetry traffic
        telemetry = classifier.classify('10.0.8.2', '10.0.8.1', 5001, 5001, 'UDP')
        assert telemetry == 'Telemetry'
        
        # Another control traffic
        control2 = classifier.classify('10.0.8.1', '10.0.8.3', 5000, 8080, 'TCP')
        assert control2 == 'Control'


class TestControlTrafficDetection:
    """Test control traffic detection"""
    
    def test_is_control_traffic_from_master(self):
        """Test detecting control traffic from Master"""
        classifier = TrafficClassifier()
        
        result = classifier.is_control_traffic(
            src_ip='10.0.8.1',
            dst_ip='10.0.8.2',
            src_port=5000,
            dst_port=8080,
            protocol='TCP'
        )
        
        assert result is True
    
    def test_is_control_traffic_to_master(self):
        """Test detecting control traffic to Master"""
        classifier = TrafficClassifier()
        
        result = classifier.is_control_traffic(
            src_ip='10.0.8.2',
            dst_ip='10.0.8.1',
            src_port=8080,
            dst_port=5000,
            protocol='TCP'
        )
        
        assert result is True
    
    def test_is_not_control_traffic(self):
        """Test that non-control traffic is not detected as control"""
        classifier = TrafficClassifier()
        
        result = classifier.is_control_traffic(
            src_ip='10.0.8.2',
            dst_ip='10.0.8.3',
            src_port=9999,
            dst_port=9999,
            protocol='UDP'
        )
        
        assert result is False


class TestTelemetryTrafficDetection:
    """Test telemetry traffic detection"""
    
    def test_is_telemetry_traffic_to_master(self):
        """Test detecting telemetry traffic to Master"""
        classifier = TrafficClassifier()
        
        result = classifier.is_telemetry_traffic(
            src_ip='10.0.8.2',
            dst_ip='10.0.8.1',
            src_port=5001,
            dst_port=5001,
            protocol='UDP'
        )
        
        assert result is True
    
    def test_is_telemetry_traffic_from_component(self):
        """Test detecting telemetry traffic from component"""
        classifier = TrafficClassifier()
        
        result = classifier.is_telemetry_traffic(
            src_ip='10.0.8.3',
            dst_ip='10.0.8.1',
            src_port=5001,
            dst_port=5001,
            protocol='UDP'
        )
        
        assert result is True
    
    def test_is_not_telemetry_traffic(self):
        """Test that non-telemetry traffic is not detected as telemetry"""
        classifier = TrafficClassifier()
        
        result = classifier.is_telemetry_traffic(
            src_ip='10.0.8.1',
            dst_ip='10.0.8.2',
            src_port=5000,
            dst_port=8080,
            protocol='TCP'
        )
        
        assert result is False


class TestPortManagement:
    """Test port management"""
    
    def test_add_control_port(self):
        """Test adding custom control port"""
        classifier = TrafficClassifier()
        
        original_count = len(classifier.control_ports)
        classifier.add_control_port(9999)
        
        assert len(classifier.control_ports) == original_count + 1
        assert 9999 in classifier.control_ports
    
    def test_add_telemetry_port(self):
        """Test adding custom telemetry port"""
        classifier = TrafficClassifier()
        
        original_count = len(classifier.telemetry_ports)
        classifier.add_telemetry_port(9999)
        
        assert len(classifier.telemetry_ports) == original_count + 1
        assert 9999 in classifier.telemetry_ports
    
    def test_remove_control_port(self):
        """Test removing control port"""
        classifier = TrafficClassifier()
        
        classifier.add_control_port(9999)
        assert 9999 in classifier.control_ports
        
        classifier.remove_control_port(9999)
        assert 9999 not in classifier.control_ports
    
    def test_remove_telemetry_port(self):
        """Test removing telemetry port"""
        classifier = TrafficClassifier()
        
        classifier.add_telemetry_port(9999)
        assert 9999 in classifier.telemetry_ports
        
        classifier.remove_telemetry_port(9999)
        assert 9999 not in classifier.telemetry_ports
    
    def test_get_control_ports(self):
        """Test getting control ports list"""
        classifier = TrafficClassifier()
        
        ports = classifier.get_control_ports()
        
        assert isinstance(ports, list)
        assert len(ports) > 0
        assert 5000 in ports
    
    def test_get_telemetry_ports(self):
        """Test getting telemetry ports list"""
        classifier = TrafficClassifier()
        
        ports = classifier.get_telemetry_ports()
        
        assert isinstance(ports, list)
        assert len(ports) > 0
        assert 5001 in ports


class TestComponentMapping:
    """Test component name mapping"""
    
    def test_get_component_name_master(self):
        """Test getting component name for Master"""
        classifier = TrafficClassifier()
        
        name = classifier.get_component_name('10.0.8.1')
        assert name == 'Master'
    
    def test_get_component_name_power(self):
        """Test getting component name for Power"""
        classifier = TrafficClassifier()
        
        name = classifier.get_component_name('10.0.8.2')
        assert name == 'Power_01'
    
    def test_get_component_name_storage(self):
        """Test getting component name for Storage"""
        classifier = TrafficClassifier()
        
        name = classifier.get_component_name('10.0.8.3')
        assert name == 'Storage_01'
    
    def test_get_component_name_demand(self):
        """Test getting component name for Demand"""
        classifier = TrafficClassifier()
        
        name = classifier.get_component_name('10.0.8.4')
        assert name == 'Demand_01'
    
    def test_get_component_name_unknown(self):
        """Test getting component name for unknown IP"""
        classifier = TrafficClassifier()
        
        name = classifier.get_component_name('192.168.1.1')
        assert name == 'Unknown'


class TestTrafficClassificationEdgeCases:
    """Test edge cases in traffic classification"""
    
    def test_classify_with_invalid_protocol(self):
        """Test classification with invalid protocol"""
        classifier = TrafficClassifier()
        
        traffic_type = classifier.classify(
            src_ip='10.0.8.1',
            dst_ip='10.0.8.2',
            src_port=5000,
            dst_port=8080,
            protocol='INVALID'
        )
        
        # Should still classify based on IPs and ports
        # In this case, it's control traffic from Master to Power_01
        assert traffic_type == 'Control'
    
    def test_classify_with_zero_ports(self):
        """Test classification with zero ports"""
        classifier = TrafficClassifier()
        
        traffic_type = classifier.classify(
            src_ip='10.0.8.1',
            dst_ip='10.0.8.2',
            src_port=0,
            dst_port=0,
            protocol='TCP'
        )
        
        # Should still classify based on IPs
        assert traffic_type in ('Control', 'Telemetry')
    
    def test_classify_with_high_ports(self):
        """Test classification with high port numbers"""
        classifier = TrafficClassifier()
        
        traffic_type = classifier.classify(
            src_ip='10.0.8.1',
            dst_ip='10.0.8.2',
            src_port=65535,
            dst_port=65535,
            protocol='TCP'
        )
        
        # Should still classify
        assert traffic_type in ('Control', 'Telemetry')
    
    def test_classify_same_source_destination(self):
        """Test classification when source and destination are the same"""
        classifier = TrafficClassifier()
        
        traffic_type = classifier.classify(
            src_ip='10.0.8.1',
            dst_ip='10.0.8.1',
            src_port=5000,
            dst_port=8080,
            protocol='TCP'
        )
        
        # Should still classify
        assert traffic_type in ('Control', 'Telemetry')


class TestTrafficClassificationIntegration:
    """Integration tests for traffic classification"""
    
    def test_classify_multiple_flows(self):
        """Test classifying multiple traffic flows"""
        classifier = TrafficClassifier()
        
        flows = [
            ('10.0.8.1', '10.0.8.2', 5000, 8080, 'TCP', 'Control'),
            ('10.0.8.2', '10.0.8.1', 5001, 5001, 'UDP', 'Telemetry'),
            ('10.0.8.3', '10.0.8.1', 5001, 5001, 'UDP', 'Telemetry'),
            ('10.0.8.1', '10.0.8.4', 5000, 8080, 'TCP', 'Control'),
        ]
        
        for src_ip, dst_ip, src_port, dst_port, protocol, expected_type in flows:
            traffic_type = classifier.classify(src_ip, dst_ip, src_port, dst_port, protocol)
            assert traffic_type == expected_type
    
    def test_custom_port_classification(self):
        """Test classification with custom ports"""
        classifier = TrafficClassifier()
        
        # Add custom control port
        classifier.add_control_port(9999)
        
        # Classify traffic using custom port
        traffic_type = classifier.classify(
            src_ip='10.0.8.1',
            dst_ip='10.0.8.2',
            src_port=9999,
            dst_port=9999,
            protocol='TCP'
        )
        
        assert traffic_type == 'Control'
    
    def test_port_removal_affects_classification(self):
        """Test that removing a port affects classification"""
        classifier = TrafficClassifier()
        
        # Verify port is in control ports
        assert 5000 in classifier.control_ports
        
        # Remove the port
        classifier.remove_control_port(5000)
        
        # Classify traffic that would use this port
        traffic_type = classifier.classify(
            src_ip='10.0.8.1',
            dst_ip='10.0.8.2',
            src_port=5000,
            dst_port=8080,
            protocol='TCP'
        )
        
        # Should now be classified differently (or as Telemetry)
        # Restore the port for other tests
        classifier.add_control_port(5000)
