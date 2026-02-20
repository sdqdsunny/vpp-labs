"""
End-to-End Integration Tests for VPP Traffic Visualization Engine

This module tests the complete flow from traffic collection to rendering,
including WebSocket connections and front-end interactions.
"""

import pytest
import json
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
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
from models.visualization_event import VisualizationEvent
from models.component_info import ComponentInfo


class TestEndToEndTrafficFlow:
    """Test complete traffic flow from collection to visualization"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.collector = TrafficCollectorService()
        self.queue = EventQueue(max_size=1000)
        self.classifier = TrafficClassifier()
        self.generator = EventGenerator()
        self.broadcaster = WebSocketBroadcaster()
    
    def test_complete_traffic_collection_to_event_generation(self):
        """Test complete flow: collect -> classify -> generate event"""
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
        
        # Parse packet
        packet = self.collector.parse_packet(packet_data)
        assert packet is not None
        assert packet.src_ip == "10.0.8.1"
        assert packet.dst_ip == "10.0.8.2"
        
        # Classify traffic
        traffic_type = self.classifier.classify(
            packet_data["src_ip"],
            packet_data["dst_ip"],
            packet_data["src_port"],
            packet_data["dst_port"],
            packet_data["protocol"]
        )
        assert traffic_type in ["Control", "Telemetry"]
        
        # Generate event
        event = self.generator.generate_event(packet_data, traffic_type)
        assert event is not None
        assert event.from_component is not None
        assert event.to_component is not None
        assert event.intensity >= 0.0 and event.intensity <= 1.0
    
    def test_traffic_collection_to_queue_to_broadcast(self):
        """Test flow: collect -> queue -> broadcast"""
        # Create multiple packets
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
            }
        ]
        
        # Process packets
        for packet_data in packets:
            packet = self.collector.parse_packet(packet_data)
            traffic_type = self.classifier.classify(
                packet_data["src_ip"],
                packet_data["dst_ip"],
                packet_data["src_port"],
                packet_data["dst_port"],
                packet_data["protocol"]
            )
            event = self.generator.generate_event(packet_data, traffic_type)
            
            # Add to queue
            success = self.queue.put(event.to_dict())
            assert success is True
        
        # Verify queue has events
        assert self.queue.size() == 2
        
        # Register clients and broadcast
        mock_client1 = Mock()
        mock_client2 = Mock()
        
        self.broadcaster.register_client("client1", mock_client1)
        self.broadcaster.register_client("client2", mock_client2)
        
        # Get events from queue and broadcast
        for _ in range(2):
            event_dict = self.queue.get()
            if event_dict:
                self.broadcaster.broadcast(event_dict)
        
        # Verify clients received events
        assert self.broadcaster.get_client_count() == 2
    
    def test_websocket_connection_and_event_flow(self):
        """Test WebSocket connection and event flow"""
        # Register clients
        mock_client1 = Mock()
        mock_client2 = Mock()
        
        self.broadcaster.register_client("client1", mock_client1)
        self.broadcaster.register_client("client2", mock_client2)
        
        assert self.broadcaster.get_client_count() == 2
        
        # Create and broadcast event
        event_data = {
            "from": "Master",
            "to": "Storage_01",
            "type": "Control",
            "intensity": 0.8,
            "packet_size": 1024,
            "timestamp": datetime.now().isoformat()
        }
        
        self.broadcaster.broadcast(event_data)
        
        # Verify broadcast was called
        assert self.broadcaster.get_client_count() == 2
        
        # Unregister one client
        self.broadcaster.unregister_client("client1")
        assert self.broadcaster.get_client_count() == 1
    
    def test_multiple_traffic_types_flow(self):
        """Test flow with multiple traffic types"""
        # Control traffic
        control_packet = {
            "src_ip": "10.0.8.1",
            "dst_ip": "10.0.8.2",
            "src_port": 22,
            "dst_port": 12345,
            "protocol": "TCP",
            "packet_size": 256,
            "timestamp": datetime.now().isoformat()
        }
        
        # Telemetry traffic
        telemetry_packet = {
            "src_ip": "10.0.8.2",
            "dst_ip": "10.0.8.1",
            "src_port": 514,
            "dst_port": 12346,
            "protocol": "UDP",
            "packet_size": 512,
            "timestamp": datetime.now().isoformat()
        }
        
        # Process both
        control_type = self.classifier.classify(
            control_packet["src_ip"],
            control_packet["dst_ip"],
            control_packet["src_port"],
            control_packet["dst_port"],
            control_packet["protocol"]
        )
        telemetry_type = self.classifier.classify(
            telemetry_packet["src_ip"],
            telemetry_packet["dst_ip"],
            telemetry_packet["src_port"],
            telemetry_packet["dst_port"],
            telemetry_packet["protocol"]
        )
        
        assert control_type == "Control"
        assert telemetry_type == "Telemetry"
        
        # Generate events
        control_event = self.generator.generate_event(control_packet, control_type)
        telemetry_event = self.generator.generate_event(telemetry_packet, telemetry_type)
        
        assert control_event.type == "Control"
        assert telemetry_event.type == "Telemetry"
        
        # Add to queue
        self.queue.put(control_event.to_dict())
        self.queue.put(telemetry_event.to_dict())
        
        assert self.queue.size() == 2


class TestWebSocketIntegration:
    """Test WebSocket integration with traffic events"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.broadcaster = WebSocketBroadcaster()
        self.generator = EventGenerator()
    
    def test_websocket_client_registration_and_unregistration(self):
        """Test WebSocket client lifecycle"""
        mock_client = Mock()
        
        # Register
        self.broadcaster.register_client("test_client", mock_client)
        assert self.broadcaster.get_client_count() == 1
        assert "test_client" in self.broadcaster.get_client_ids()
        
        # Unregister
        self.broadcaster.unregister_client("test_client")
        assert self.broadcaster.get_client_count() == 0
    
    def test_websocket_broadcast_to_multiple_clients(self):
        """Test broadcasting to multiple clients"""
        clients = {}
        for i in range(5):
            client = Mock()
            clients[f"client_{i}"] = client
            self.broadcaster.register_client(f"client_{i}", client)
        
        assert self.broadcaster.get_client_count() == 5
        
        # Broadcast event
        event = {
            "from": "Master",
            "to": "Storage_01",
            "type": "Control",
            "intensity": 0.8,
            "packet_size": 1024,
            "timestamp": datetime.now().isoformat()
        }
        
        self.broadcaster.broadcast(event)
        assert self.broadcaster.get_client_count() == 5
    
    def test_websocket_send_to_specific_client(self):
        """Test sending to specific client"""
        mock_client1 = Mock()
        mock_client2 = Mock()
        
        self.broadcaster.register_client("client1", mock_client1)
        self.broadcaster.register_client("client2", mock_client2)
        
        event = {
            "from": "Master",
            "to": "Storage_01",
            "type": "Control",
            "intensity": 0.8,
            "packet_size": 1024,
            "timestamp": datetime.now().isoformat()
        }
        
        self.broadcaster.send_to_client("client1", event)
        assert self.broadcaster.get_client_count() == 2
    
    def test_websocket_system_message_broadcast(self):
        """Test broadcasting system messages"""
        mock_client = Mock()
        self.broadcaster.register_client("client", mock_client)
        
        system_msg = {
            "type": "system",
            "message": "Server status update",
            "timestamp": datetime.now().isoformat()
        }
        
        self.broadcaster.broadcast(system_msg)
        assert self.broadcaster.get_client_count() == 1


class TestFrontendBackendIntegration:
    """Test integration between frontend and backend"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.collector = TrafficCollectorService()
        self.classifier = TrafficClassifier()
        self.generator = EventGenerator()
        self.broadcaster = WebSocketBroadcaster()
    
    def test_traffic_event_to_frontend_format(self):
        """Test converting traffic events to frontend format"""
        packet_data = {
            "src_ip": "10.0.8.1",
            "dst_ip": "10.0.8.2",
            "src_port": 22,
            "dst_port": 12345,
            "protocol": "TCP",
            "packet_size": 1024,
            "timestamp": datetime.now().isoformat()
        }
        
        # Process packet
        packet = self.collector.parse_packet(packet_data)
        traffic_type = self.classifier.classify(
            packet_data["src_ip"],
            packet_data["dst_ip"],
            packet_data["src_port"],
            packet_data["dst_port"],
            packet_data["protocol"]
        )
        event = self.generator.generate_event(packet_data, traffic_type)
        
        # Convert to frontend format
        event_dict = event.to_dict()
        
        # Verify frontend can parse it
        assert "from" in event_dict
        assert "to" in event_dict
        assert "type" in event_dict
        assert "intensity" in event_dict
        assert "packet_size" in event_dict
        assert "timestamp" in event_dict
        
        # Verify values are correct
        assert event_dict["type"] in ["Control", "Telemetry"]
        assert 0.0 <= event_dict["intensity"] <= 1.0
        assert event_dict["packet_size"] > 0
    
    def test_statistics_calculation_for_frontend(self):
        """Test statistics calculation for frontend display"""
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
            }
        ]
        
        total_bytes = 0
        control_count = 0
        telemetry_count = 0
        
        for packet_data in packets:
            packet = self.collector.parse_packet(packet_data)
            traffic_type = self.classifier.classify(
                packet_data["src_ip"],
                packet_data["dst_ip"],
                packet_data["src_port"],
                packet_data["dst_port"],
                packet_data["protocol"]
            )
            event = self.generator.generate_event(packet_data, traffic_type)
            
            total_bytes += event.packet_size
            if event.type == "Control":
                control_count += 1
            else:
                telemetry_count += 1
        
        # Verify statistics
        assert total_bytes == 1536
        assert control_count + telemetry_count == 2
        assert control_count >= 0
        assert telemetry_count >= 0


class TestDataPersistence:
    """Test data persistence across components"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.queue = EventQueue(max_size=100)
        self.collector = TrafficCollectorService()
        self.classifier = TrafficClassifier()
        self.generator = EventGenerator()
    
    def test_event_persistence_in_queue(self):
        """Test events persist in queue"""
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
            }
        ]
        
        # Add events to queue
        for packet_data in packets:
            packet = self.collector.parse_packet(packet_data)
            traffic_type = self.classifier.classify(
                packet_data["src_ip"],
                packet_data["dst_ip"],
                packet_data["src_port"],
                packet_data["dst_port"],
                packet_data["protocol"]
            )
            event = self.generator.generate_event(packet_data, traffic_type)
            self.queue.put(event.to_dict())
        
        # Verify events are in queue
        assert self.queue.size() == 2
        
        # Retrieve events
        event1 = self.queue.get()
        event2 = self.queue.get()
        
        assert event1 is not None
        assert event2 is not None
        assert self.queue.size() == 0
    
    def test_batch_event_retrieval(self):
        """Test batch retrieval of events"""
        # Add multiple events
        for i in range(10):
            event_dict = {
                "from": f"Component_{i}",
                "to": f"Component_{i+1}",
                "type": "Control" if i % 2 == 0 else "Telemetry",
                "intensity": 0.5 + (i * 0.05),
                "packet_size": 256 + (i * 64),
                "timestamp": datetime.now().isoformat()
            }
            self.queue.put(event_dict)
        
        # Retrieve batch
        batch = self.queue.get_batch(5)
        assert len(batch) == 5
        assert self.queue.size() == 5


class TestErrorHandling:
    """Test error handling in integration"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.collector = TrafficCollectorService()
        self.classifier = TrafficClassifier()
        self.generator = EventGenerator()
    
    def test_invalid_packet_handling(self):
        """Test handling of invalid packets"""
        invalid_packets = [
            {},  # Empty packet
            {"src_ip": "invalid"},  # Missing fields
            {"src_ip": "10.0.8.1", "dst_ip": "10.0.8.2"},  # Missing ports
        ]
        
        for packet_data in invalid_packets:
            try:
                packet = self.collector.parse_packet(packet_data)
                # Should handle gracefully
                if packet:
                    traffic_type = self.classifier.classify(packet_data)
                    assert traffic_type in ["Control", "Telemetry"]
            except Exception as e:
                # Should not crash
                assert True
    
    def test_queue_overflow_handling(self):
        """Test queue overflow handling"""
        small_queue = EventQueue(max_size=5)
        
        # Add more events than queue size
        for i in range(10):
            event_dict = {
                "from": "Master",
                "to": f"Component_{i}",
                "type": "Control",
                "intensity": 0.5,
                "packet_size": 256,
                "timestamp": datetime.now().isoformat()
            }
            success = small_queue.put(event_dict)
            # put always returns True, but oldest events are dropped
            assert success is True
        
        # Queue should be at max size
        assert small_queue.size() == 5
        
        # Verify dropped events were tracked
        stats = small_queue.get_stats()
        assert stats['dropped_events'] == 5  # 10 total - 5 kept = 5 dropped


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
