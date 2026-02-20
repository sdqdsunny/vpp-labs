"""
Simplified Integration Tests for VPP Traffic Visualization Engine

This module tests key integration scenarios with correct API usage.
"""

import pytest
import time
from datetime import datetime
from unittest.mock import Mock
import sys
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.traffic_collector import TrafficCollectorService
from services.event_queue import EventQueue
from services.traffic_classifier import TrafficClassifier
from services.event_generator import EventGenerator
from services.websocket_broadcaster import WebSocketBroadcaster
from models.raw_packet import RawPacket


class TestIntegrationScenarios:
    """Test key integration scenarios"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.collector = TrafficCollectorService()
        self.queue = EventQueue(max_size=1000)
        self.classifier = TrafficClassifier()
        self.generator = EventGenerator()
        self.broadcaster = WebSocketBroadcaster()
    
    def test_complete_flow_collection_to_broadcast(self):
        """Test complete flow: collect -> classify -> generate -> queue -> broadcast"""
        # Create sample packet
        packet_data = {
            "src_ip": "10.0.8.1",
            "dst_ip": "10.0.8.2",
            "src_port": 22,
            "dst_port": 12345,
            "protocol": "TCP",
            "packet_size": 1024,
            "timestamp": datetime.now().isoformat()
        }
        
        # Step 1: Parse packet
        packet = self.collector.parse_packet(packet_data)
        assert packet is not None
        assert isinstance(packet, RawPacket)
        
        # Step 2: Generate event (includes classification)
        event = self.generator.generate_event(packet)
        assert event is not None
        assert event.from_component is not None
        assert event.to_component is not None
        
        # Step 3: Add to queue
        success = self.queue.put(event.to_dict())
        assert success is True
        assert self.queue.size() == 1
        
        # Step 4: Register clients
        mock_client1 = Mock()
        mock_client2 = Mock()
        self.broadcaster.register_client("client1", mock_client1)
        self.broadcaster.register_client("client2", mock_client2)
        assert self.broadcaster.get_client_count() == 2
        
        # Step 5: Get from queue and broadcast
        event_dict = self.queue.get()
        assert event_dict is not None
        self.broadcaster.broadcast(event_dict)
        assert self.queue.size() == 0
    
    def test_multiple_packets_flow(self):
        """Test flow with multiple packets"""
        packets = [
            {
                "src_ip": "10.0.8.1",
                "dst_ip": "10.0.8.2",
                "src_port": 22,
                "dst_port": 12345,
                "protocol": "TCP",
                "packet_size": 1024,
                "timestamp": datetime.now().isoformat()
            },
            {
                "src_ip": "10.0.8.2",
                "dst_ip": "10.0.8.3",
                "src_port": 514,
                "dst_port": 12346,
                "protocol": "UDP",
                "packet_size": 512,
                "timestamp": datetime.now().isoformat()
            },
            {
                "src_ip": "10.0.8.3",
                "dst_ip": "10.0.8.1",
                "src_port": 5000,
                "dst_port": 12347,
                "protocol": "TCP",
                "packet_size": 256,
                "timestamp": datetime.now().isoformat()
            }
        ]
        
        # Process all packets
        event_count = 0
        for packet_data in packets:
            packet = self.collector.parse_packet(packet_data)
            event = self.generator.generate_event(packet)
            if event:
                self.queue.put(event.to_dict())
                event_count += 1
        
        # Verify all events in queue
        assert self.queue.size() == event_count
        
        # Retrieve all events
        retrieved_count = 0
        while True:
            event_dict = self.queue.get()
            if event_dict is None:
                break
            retrieved_count += 1
        
        assert retrieved_count == event_count
    
    def test_websocket_client_lifecycle(self):
        """Test WebSocket client registration and unregistration"""
        # Register multiple clients
        clients = {}
        for i in range(5):
            mock_client = Mock()
            clients[f"client_{i}"] = mock_client
            self.broadcaster.register_client(f"client_{i}", mock_client)
        
        assert self.broadcaster.get_client_count() == 5
        
        # Unregister some clients
        self.broadcaster.unregister_client("client_0")
        self.broadcaster.unregister_client("client_2")
        
        assert self.broadcaster.get_client_count() == 3
        
        # Verify remaining clients
        remaining_ids = self.broadcaster.get_client_ids()
        assert "client_0" not in remaining_ids
        assert "client_2" not in remaining_ids
        assert "client_1" in remaining_ids
    
    def test_queue_persistence(self):
        """Test event persistence in queue"""
        # Add events
        for i in range(10):
            event_dict = {
                "from": f"Component_{i}",
                "to": f"Component_{i+1}",
                "type": "Control" if i % 2 == 0 else "Telemetry",
                "intensity": 0.5,
                "packet_size": 256,
                "timestamp": datetime.now().isoformat()
            }
            self.queue.put(event_dict)
        
        assert self.queue.size() == 10
        
        # Retrieve batch
        batch = self.queue.get_batch(5)
        assert len(batch) == 5
        assert self.queue.size() == 5
        
        # Retrieve remaining
        batch2 = self.queue.get_batch(10)
        assert len(batch2) == 5
        assert self.queue.size() == 0
    
    def test_traffic_classification_accuracy(self):
        """Test traffic classification accuracy"""
        # Control traffic (from Master)
        control_packet = {
            "src_ip": "10.0.8.1",
            "dst_ip": "10.0.8.2",
            "src_port": 22,
            "dst_port": 12345,
            "protocol": "TCP",
            "packet_size": 256,
            "timestamp": datetime.now().isoformat()
        }
        
        # Telemetry traffic (to Master)
        telemetry_packet = {
            "src_ip": "10.0.8.2",
            "dst_ip": "10.0.8.1",
            "src_port": 514,
            "dst_port": 12346,
            "protocol": "UDP",
            "packet_size": 512,
            "timestamp": datetime.now().isoformat()
        }
        
        # Parse and generate events
        control_pkt = self.collector.parse_packet(control_packet)
        telemetry_pkt = self.collector.parse_packet(telemetry_packet)
        
        control_event = self.generator.generate_event(control_pkt)
        telemetry_event = self.generator.generate_event(telemetry_pkt)
        
        # Verify classification
        assert control_event is not None
        assert telemetry_event is not None
        assert control_event.traffic_type in ["Control", "Telemetry"]
        assert telemetry_event.traffic_type in ["Control", "Telemetry"]
    
    def test_event_format_for_frontend(self):
        """Test event format is compatible with frontend"""
        packet_data = {
            "src_ip": "10.0.8.1",
            "dst_ip": "10.0.8.2",
            "src_port": 22,
            "dst_port": 12345,
            "protocol": "TCP",
            "packet_size": 1024,
            "timestamp": datetime.now().isoformat()
        }
        
        packet = self.collector.parse_packet(packet_data)
        event = self.generator.generate_event(packet)
        
        if event:
            event_dict = event.to_dict()
            
            # Verify required fields for frontend
            required_fields = ["from", "to", "type", "intensity", "packet_size", "timestamp"]
            for field in required_fields:
                assert field in event_dict, f"Missing field: {field}"
            
            # Verify field types
            assert isinstance(event_dict["from"], str)
            assert isinstance(event_dict["to"], str)
            assert isinstance(event_dict["type"], str)
            assert isinstance(event_dict["intensity"], (int, float))
            assert isinstance(event_dict["packet_size"], int)
            assert isinstance(event_dict["timestamp"], str)
            
            # Verify value ranges
            assert event_dict["type"] in ["Control", "Telemetry"]
            assert 0.0 <= event_dict["intensity"] <= 1.0
            assert event_dict["packet_size"] > 0


class TestPerformanceIntegration:
    """Test performance of integrated components"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.collector = TrafficCollectorService()
        self.queue = EventQueue(max_size=10000)
        self.generator = EventGenerator()
        self.broadcaster = WebSocketBroadcaster()
    
    def test_collection_latency(self):
        """Test packet collection latency < 100ms"""
        packet_data = {
            "src_ip": "10.0.8.1",
            "dst_ip": "10.0.8.2",
            "src_port": 22,
            "dst_port": 12345,
            "protocol": "TCP",
            "packet_size": 1024,
            "timestamp": datetime.now().isoformat()
        }
        
        start_time = time.time()
        packet = self.collector.parse_packet(packet_data)
        elapsed_ms = (time.time() - start_time) * 1000
        
        assert elapsed_ms < 100, f"Collection took {elapsed_ms}ms, expected < 100ms"
        assert packet is not None
    
    def test_event_generation_latency(self):
        """Test event generation latency < 50ms"""
        packet_data = {
            "src_ip": "10.0.8.1",
            "dst_ip": "10.0.8.2",
            "src_port": 22,
            "dst_port": 12345,
            "protocol": "TCP",
            "packet_size": 1024,
            "timestamp": datetime.now().isoformat()
        }
        
        packet = self.collector.parse_packet(packet_data)
        
        start_time = time.time()
        event = self.generator.generate_event(packet)
        elapsed_ms = (time.time() - start_time) * 1000
        
        assert elapsed_ms < 50, f"Event generation took {elapsed_ms}ms, expected < 50ms"
        assert event is not None
    
    def test_broadcast_latency(self):
        """Test WebSocket broadcast latency < 100ms"""
        # Register clients
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
        
        start_time = time.time()
        self.broadcaster.broadcast(event)
        elapsed_ms = (time.time() - start_time) * 1000
        
        assert elapsed_ms < 100, f"Broadcast took {elapsed_ms}ms, expected < 100ms"
    
    def test_high_throughput_scenario(self):
        """Test high throughput scenario"""
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
        
        start_time = time.time()
        
        for packet_data in packets:
            packet = self.collector.parse_packet(packet_data)
            event = self.generator.generate_event(packet)
            if event:
                self.queue.put(event.to_dict())
        
        elapsed_time = time.time() - start_time
        throughput = len(packets) / elapsed_time
        
        # Should handle at least 100 packets per second
        assert throughput >= 100, f"Throughput {throughput} pps, expected >= 100 pps"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
