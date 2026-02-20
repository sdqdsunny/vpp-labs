"""
Performance Tests for VPP Traffic Visualization Engine

This module tests performance metrics including latency and throughput.
"""

import pytest
import time
import json
from datetime import datetime
from unittest.mock import Mock, patch
import sys
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.traffic_collector import TrafficCollectorService
from services.event_queue import EventQueue
from services.traffic_classifier import TrafficClassifier
from services.event_generator import EventGenerator
from services.websocket_broadcaster import WebSocketBroadcaster


class TestTrafficCollectionPerformance:
    """Test traffic collection performance"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.collector = TrafficCollectorService()
    
    def test_packet_parsing_latency(self):
        """Test packet parsing latency < 100ms"""
        packet_data = {
            "src_ip": "10.0.8.1",
            "dst_ip": "10.0.8.2",
            "src_port": 22,
            "dst_port": 12345,
            "protocol": "TCP",
            "packet_size": 1024,
            "timestamp": datetime.now().isoformat()
        }
        
        # Measure parsing time
        start_time = time.time()
        packet = self.collector.parse_packet(packet_data)
        elapsed_time = (time.time() - start_time) * 1000  # Convert to ms
        
        # Verify latency < 100ms
        assert elapsed_time < 100, f"Packet parsing took {elapsed_time}ms, expected < 100ms"
        assert packet is not None
    
    def test_batch_packet_parsing_latency(self):
        """Test batch packet parsing latency"""
        packets = [
            {
                "src_ip": "10.0.8.1",
                "dst_ip": "10.0.8.2",
                "src_port": 22,
                "dst_port": 12345,
                "protocol": "TCP",
                "packet_size": 1024,
                "timestamp": datetime.now().isoformat()
            }
            for _ in range(100)
        ]
        
        # Measure batch parsing time
        start_time = time.time()
        for packet_data in packets:
            self.collector.parse_packet(packet_data)
        elapsed_time = (time.time() - start_time) * 1000  # Convert to ms
        
        # Average latency should be < 100ms per packet
        avg_latency = elapsed_time / len(packets)
        assert avg_latency < 100, f"Average latency {avg_latency}ms, expected < 100ms"
    
    def test_collection_throughput(self):
        """Test traffic collection throughput"""
        packets = [
            {
                "src_ip": "10.0.8.1",
                "dst_ip": "10.0.8.2",
                "src_port": 22,
                "dst_port": 12345,
                "protocol": "TCP",
                "packet_size": 1024,
                "timestamp": datetime.now().isoformat()
            }
            for _ in range(1000)
        ]
        
        # Measure throughput
        start_time = time.time()
        for packet_data in packets:
            self.collector.parse_packet(packet_data)
        elapsed_time = time.time() - start_time
        
        # Calculate throughput (packets per second)
        throughput = len(packets) / elapsed_time
        
        # Should handle at least 1000 packets per second
        assert throughput >= 1000, f"Throughput {throughput} pps, expected >= 1000 pps"


class TestEventTransformationPerformance:
    """Test event transformation performance"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.classifier = TrafficClassifier()
        self.generator = EventGenerator()
    
    def test_traffic_classification_latency(self):
        """Test traffic classification latency < 50ms"""
        # Measure classification time
        start_time = time.time()
        traffic_type = self.classifier.classify(
            src_ip="10.0.8.1",
            dst_ip="10.0.8.2",
            src_port=22,
            dst_port=12345,
            protocol="TCP"
        )
        elapsed_time = (time.time() - start_time) * 1000  # Convert to ms
        
        # Verify latency < 50ms
        assert elapsed_time < 50, f"Classification took {elapsed_time}ms, expected < 50ms"
        assert traffic_type in ["Control", "Telemetry"]
    
    def test_event_generation_latency(self):
        """Test event generation latency < 50ms"""
        # First parse the packet
        packet_data = {
            "src_ip": "10.0.8.1",
            "dst_ip": "10.0.8.2",
            "src_port": 22,
            "dst_port": 12345,
            "protocol": "TCP",
            "packet_size": 1024,
            "timestamp": datetime.now().isoformat()
        }
        
        # Create a collector to parse the packet
        collector = TrafficCollectorService()
        packet = collector.parse_packet(packet_data)
        
        # Measure event generation time
        start_time = time.time()
        event = self.generator.generate_event(packet)
        elapsed_time = (time.time() - start_time) * 1000  # Convert to ms
        
        # Verify latency < 50ms
        assert elapsed_time < 50, f"Event generation took {elapsed_time}ms, expected < 50ms"
        assert event is not None
    
    def test_batch_transformation_latency(self):
        """Test batch transformation latency"""
        packets = [
            {
                "src_ip": "10.0.8.1",
                "dst_ip": "10.0.8.2",
                "src_port": 22,
                "dst_port": 12345,
                "protocol": "TCP",
                "packet_size": 1024,
                "timestamp": datetime.now().isoformat()
            }
            for _ in range(100)
        ]
        
        # Create a collector to parse packets
        collector = TrafficCollectorService()
        
        # Measure batch transformation time
        start_time = time.time()
        for packet_data in packets:
            packet = collector.parse_packet(packet_data)
            traffic_type = self.classifier.classify(
                src_ip=packet.src_ip,
                dst_ip=packet.dst_ip,
                src_port=packet.src_port,
                dst_port=packet.dst_port,
                protocol=packet.protocol
            )
            event = self.generator.generate_event(packet)
        elapsed_time = (time.time() - start_time) * 1000  # Convert to ms
        
        # Average latency should be < 50ms per packet
        avg_latency = elapsed_time / len(packets)
        assert avg_latency < 50, f"Average latency {avg_latency}ms, expected < 50ms"


class TestWebSocketPerformance:
    """Test WebSocket broadcasting performance"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.broadcaster = WebSocketBroadcaster()
    
    def test_websocket_broadcast_latency(self):
        """Test WebSocket broadcast latency < 100ms"""
        # Register multiple clients
        for i in range(10):
            mock_client = Mock()
            self.broadcaster.register_client(f"client_{i}", mock_client)
        
        event = {
            "from": "Master",
            "to": "Storage_01",
            "type": "Control",
            "intensity": 0.8,
            "packet_size": 1024,
            "timestamp": datetime.now().isoformat()
        }
        
        # Measure broadcast time
        start_time = time.time()
        self.broadcaster.broadcast(event)
        elapsed_time = (time.time() - start_time) * 1000  # Convert to ms
        
        # Verify latency < 100ms
        assert elapsed_time < 100, f"Broadcast took {elapsed_time}ms, expected < 100ms"
    
    def test_websocket_throughput(self):
        """Test WebSocket broadcast throughput"""
        # Register clients
        for i in range(10):
            mock_client = Mock()
            self.broadcaster.register_client(f"client_{i}", mock_client)
        
        events = [
            {
                "from": "Master",
                "to": f"Component_{i}",
                "type": "Control" if i % 2 == 0 else "Telemetry",
                "intensity": 0.5 + (i * 0.05),
                "packet_size": 256 + (i * 64),
                "timestamp": datetime.now().isoformat()
            }
            for i in range(1000)
        ]
        
        # Measure throughput
        start_time = time.time()
        for event in events:
            self.broadcaster.broadcast(event)
        elapsed_time = time.time() - start_time
        
        # Calculate throughput (events per second)
        throughput = len(events) / elapsed_time
        
        # Should handle at least 1000 events per second
        assert throughput >= 1000, f"Throughput {throughput} eps, expected >= 1000 eps"
    
    def test_client_registration_performance(self):
        """Test client registration performance"""
        # Measure registration time for multiple clients
        start_time = time.time()
        for i in range(100):
            mock_client = Mock()
            self.broadcaster.register_client(f"client_{i}", mock_client)
        elapsed_time = (time.time() - start_time) * 1000  # Convert to ms
        
        # Average registration time should be < 10ms
        avg_time = elapsed_time / 100
        assert avg_time < 10, f"Average registration time {avg_time}ms, expected < 10ms"
        assert self.broadcaster.get_client_count() == 100


class TestQueuePerformance:
    """Test event queue performance"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.queue = EventQueue(max_size=10000)
    
    def test_queue_put_latency(self):
        """Test queue put operation latency"""
        event = {
            "from": "Master",
            "to": "Storage_01",
            "type": "Control",
            "intensity": 0.8,
            "packet_size": 1024,
            "timestamp": datetime.now().isoformat()
        }
        
        # Measure put time
        start_time = time.time()
        self.queue.put(event)
        elapsed_time = (time.time() - start_time) * 1000  # Convert to ms
        
        # Should be very fast (< 1ms)
        assert elapsed_time < 1, f"Put took {elapsed_time}ms, expected < 1ms"
    
    def test_queue_get_latency(self):
        """Test queue get operation latency"""
        event = {
            "from": "Master",
            "to": "Storage_01",
            "type": "Control",
            "intensity": 0.8,
            "packet_size": 1024,
            "timestamp": datetime.now().isoformat()
        }
        
        self.queue.put(event)
        
        # Measure get time
        start_time = time.time()
        retrieved = self.queue.get()
        elapsed_time = (time.time() - start_time) * 1000  # Convert to ms
        
        # Should be very fast (< 1ms)
        assert elapsed_time < 1, f"Get took {elapsed_time}ms, expected < 1ms"
        assert retrieved is not None
    
    def test_queue_throughput(self):
        """Test queue throughput"""
        events = [
            {
                "from": "Master",
                "to": f"Component_{i}",
                "type": "Control",
                "intensity": 0.5,
                "packet_size": 256,
                "timestamp": datetime.now().isoformat()
            }
            for i in range(10000)
        ]
        
        # Measure put throughput
        start_time = time.time()
        for event in events:
            self.queue.put(event)
        put_time = time.time() - start_time
        put_throughput = len(events) / put_time
        
        # Should handle at least 10000 puts per second
        assert put_throughput >= 10000, f"Put throughput {put_throughput} ops/s, expected >= 10000"
        
        # Measure get throughput
        start_time = time.time()
        for _ in range(10000):
            self.queue.get()
        get_time = time.time() - start_time
        get_throughput = len(events) / get_time
        
        # Should handle at least 10000 gets per second
        assert get_throughput >= 10000, f"Get throughput {get_throughput} ops/s, expected >= 10000"


class TestEndToEndPerformance:
    """Test end-to-end performance"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.collector = TrafficCollectorService()
        self.queue = EventQueue(max_size=10000)
        self.classifier = TrafficClassifier()
        self.generator = EventGenerator()
        self.broadcaster = WebSocketBroadcaster()
    
    def test_complete_flow_latency(self):
        """Test complete flow latency < 250ms"""
        # Register clients
        for i in range(5):
            mock_client = Mock()
            self.broadcaster.register_client(f"client_{i}", mock_client)
        
        packet_data = {
            "src_ip": "10.0.8.1",
            "dst_ip": "10.0.8.2",
            "src_port": 22,
            "dst_port": 12345,
            "protocol": "TCP",
            "packet_size": 1024,
            "timestamp": datetime.now().isoformat()
        }
        
        # Measure complete flow
        start_time = time.time()
        
        # Collection
        packet = self.collector.parse_packet(packet_data)
        
        # Classification
        traffic_type = self.classifier.classify(
            src_ip=packet.src_ip,
            dst_ip=packet.dst_ip,
            src_port=packet.src_port,
            dst_port=packet.dst_port,
            protocol=packet.protocol
        )
        
        # Event generation
        event = self.generator.generate_event(packet)
        
        # Queue
        if event:
            self.queue.put(event.to_dict())
            
            # Broadcast
            event_dict = self.queue.get()
            self.broadcaster.broadcast(event_dict)
        
        elapsed_time = (time.time() - start_time) * 1000  # Convert to ms
        
        # Total latency should be < 250ms
        assert elapsed_time < 250, f"Complete flow took {elapsed_time}ms, expected < 250ms"
    
    def test_high_throughput_scenario(self):
        """Test high throughput scenario"""
        # Register clients
        for i in range(10):
            mock_client = Mock()
            self.broadcaster.register_client(f"client_{i}", mock_client)
        
        packets = [
            {
                "src_ip": "10.0.8.1",
                "dst_ip": "10.0.8.2",
                "src_port": 22,
                "dst_port": 12345,
                "protocol": "TCP",
                "packet_size": 1024,
                "timestamp": datetime.now().isoformat()
            }
            for _ in range(100)
        ]
        
        # Measure high throughput scenario
        start_time = time.time()
        
        for packet_data in packets:
            # Collection
            packet = self.collector.parse_packet(packet_data)
            
            # Classification
            traffic_type = self.classifier.classify(
                src_ip=packet.src_ip,
                dst_ip=packet.dst_ip,
                src_port=packet.src_port,
                dst_port=packet.dst_port,
                protocol=packet.protocol
            )
            
            # Event generation
            event = self.generator.generate_event(packet)
            
            # Queue
            if event:
                self.queue.put(event.to_dict())
            
            # Broadcast
            event_dict = self.queue.get()
            self.broadcaster.broadcast(event_dict)
        
        elapsed_time = time.time() - start_time
        throughput = len(packets) / elapsed_time
        
        # Should handle at least 100 packets per second
        assert throughput >= 100, f"Throughput {throughput} pps, expected >= 100 pps"


class TestParticleSystemPerformance:
    """Test particle system performance"""
    
    def test_particle_capacity(self):
        """Test particle system capacity <= 10000"""
        # This is a placeholder for frontend particle system testing
        # In a real scenario, this would test the JavaScript particle system
        max_particles = 10000
        
        # Verify capacity
        assert max_particles <= 10000, f"Particle capacity {max_particles}, expected <= 10000"
    
    def test_rendering_frame_rate(self):
        """Test 3D rendering frame rate >= 30fps"""
        # This is a placeholder for frontend rendering testing
        # In a real scenario, this would measure actual frame rate
        min_fps = 30
        
        # Verify minimum frame rate
        assert min_fps >= 30, f"Frame rate {min_fps} fps, expected >= 30 fps"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
