"""
Unit tests for WebSocketBroadcaster service

Tests for client registration, event broadcasting, and connection management.
"""

import pytest
import sys
import asyncio
from pathlib import Path
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.websocket_broadcaster import WebSocketBroadcaster


class MockWebSocket:
    """Mock WebSocket for testing"""
    
    def __init__(self):
        self.messages = []
        self.closed = False
    
    async def send(self, message):
        """Mock send method"""
        if self.closed:
            raise Exception("WebSocket is closed")
        self.messages.append(message)
    
    async def close(self):
        """Mock close method"""
        self.closed = True


class TestWebSocketBroadcasterBasics:
    """Test basic WebSocketBroadcaster functionality"""
    
    def test_broadcaster_initialization(self):
        """Test WebSocketBroadcaster initialization"""
        broadcaster = WebSocketBroadcaster()
        
        assert broadcaster is not None
        assert len(broadcaster.clients) == 0
        assert len(broadcaster.client_metadata) == 0
    
    def test_register_client(self):
        """Test registering a client"""
        broadcaster = WebSocketBroadcaster()
        websocket = MockWebSocket()
        
        result = broadcaster.register_client('client_001', websocket)
        
        assert result is True
        assert broadcaster.get_client_count() == 1
        assert broadcaster.is_client_connected('client_001')
    
    def test_register_duplicate_client(self):
        """Test registering duplicate client returns False"""
        broadcaster = WebSocketBroadcaster()
        websocket = MockWebSocket()
        
        result1 = broadcaster.register_client('client_001', websocket)
        result2 = broadcaster.register_client('client_001', websocket)
        
        assert result1 is True
        assert result2 is False
        assert broadcaster.get_client_count() == 1
    
    def test_unregister_client(self):
        """Test unregistering a client"""
        broadcaster = WebSocketBroadcaster()
        websocket = MockWebSocket()
        
        broadcaster.register_client('client_001', websocket)
        assert broadcaster.get_client_count() == 1
        
        result = broadcaster.unregister_client('client_001')
        
        assert result is True
        assert broadcaster.get_client_count() == 0
        assert not broadcaster.is_client_connected('client_001')
    
    def test_unregister_nonexistent_client(self):
        """Test unregistering nonexistent client returns False"""
        broadcaster = WebSocketBroadcaster()
        
        result = broadcaster.unregister_client('nonexistent')
        
        assert result is False
    
    def test_get_client_count(self):
        """Test getting client count"""
        broadcaster = WebSocketBroadcaster()
        
        assert broadcaster.get_client_count() == 0
        
        for i in range(5):
            websocket = MockWebSocket()
            broadcaster.register_client(f'client_{i:03d}', websocket)
        
        assert broadcaster.get_client_count() == 5
    
    def test_get_client_ids(self):
        """Test getting list of client IDs"""
        broadcaster = WebSocketBroadcaster()
        
        client_ids = ['client_001', 'client_002', 'client_003']
        for client_id in client_ids:
            websocket = MockWebSocket()
            broadcaster.register_client(client_id, websocket)
        
        result = broadcaster.get_client_ids()
        
        assert len(result) == 3
        assert set(result) == set(client_ids)


class TestClientMetadata:
    """Test client metadata management"""
    
    def test_register_client_with_metadata(self):
        """Test registering client with metadata"""
        broadcaster = WebSocketBroadcaster()
        websocket = MockWebSocket()
        metadata = {'user_agent': 'Chrome', 'ip': '127.0.0.1'}
        
        broadcaster.register_client('client_001', websocket, metadata)
        
        client_metadata = broadcaster.get_client_metadata('client_001')
        assert client_metadata['user_agent'] == 'Chrome'
        assert client_metadata['ip'] == '127.0.0.1'
        assert 'connected_at' in client_metadata
    
    def test_register_client_without_metadata(self):
        """Test registering client without metadata"""
        broadcaster = WebSocketBroadcaster()
        websocket = MockWebSocket()
        
        broadcaster.register_client('client_001', websocket)
        
        client_metadata = broadcaster.get_client_metadata('client_001')
        assert 'connected_at' in client_metadata
    
    def test_get_nonexistent_client_metadata(self):
        """Test getting metadata for nonexistent client"""
        broadcaster = WebSocketBroadcaster()
        
        result = broadcaster.get_client_metadata('nonexistent')
        
        assert result is None
    
    def test_get_all_metadata(self):
        """Test getting all client metadata"""
        broadcaster = WebSocketBroadcaster()
        
        for i in range(3):
            websocket = MockWebSocket()
            metadata = {'index': i}
            broadcaster.register_client(f'client_{i:03d}', websocket, metadata)
        
        all_metadata = broadcaster.get_all_metadata()
        
        assert len(all_metadata) == 3
        for i in range(3):
            assert all_metadata[f'client_{i:03d}']['index'] == i


class TestBroadcasting:
    """Test event broadcasting"""
    
    def test_broadcast_to_single_client(self):
        """Test broadcasting to single client"""
        broadcaster = WebSocketBroadcaster()
        websocket = MockWebSocket()
        
        broadcaster.register_client('client_001', websocket)
        
        event = {
            'from': 'Master',
            'to': 'Power_01',
            'type': 'Control',
            'intensity': 0.8
        }
        
        count = asyncio.run(broadcaster.broadcast(event))
        
        assert count == 1
        assert len(websocket.messages) == 1
    
    def test_broadcast_to_multiple_clients(self):
        """Test broadcasting to multiple clients"""
        broadcaster = WebSocketBroadcaster()
        websockets = []
        
        for i in range(5):
            websocket = MockWebSocket()
            websockets.append(websocket)
            broadcaster.register_client(f'client_{i:03d}', websocket)
        
        event = {
            'from': 'Master',
            'to': 'Power_01',
            'type': 'Control',
            'intensity': 0.8
        }
        
        count = asyncio.run(broadcaster.broadcast(event))
        
        assert count == 5
        for websocket in websockets:
            assert len(websocket.messages) == 1
    
    def test_broadcast_to_no_clients(self):
        """Test broadcasting with no connected clients"""
        broadcaster = WebSocketBroadcaster()
        
        event = {
            'from': 'Master',
            'to': 'Power_01',
            'type': 'Control',
            'intensity': 0.8
        }
        
        count = asyncio.run(broadcaster.broadcast(event))
        
        assert count == 0
    
    def test_send_to_specific_client(self):
        """Test sending to specific client"""
        broadcaster = WebSocketBroadcaster()
        websocket1 = MockWebSocket()
        websocket2 = MockWebSocket()
        
        broadcaster.register_client('client_001', websocket1)
        broadcaster.register_client('client_002', websocket2)
        
        event = {
            'from': 'Master',
            'to': 'Power_01',
            'type': 'Control',
            'intensity': 0.8
        }
        
        result = asyncio.run(broadcaster.send_to_client('client_001', event))
        
        assert result is True
        assert len(websocket1.messages) == 1
        assert len(websocket2.messages) == 0
    
    def test_send_to_nonexistent_client(self):
        """Test sending to nonexistent client"""
        broadcaster = WebSocketBroadcaster()
        
        event = {
            'from': 'Master',
            'to': 'Power_01',
            'type': 'Control',
            'intensity': 0.8
        }
        
        result = asyncio.run(broadcaster.send_to_client('nonexistent', event))
        
        assert result is False
    
    def test_send_to_multiple_clients(self):
        """Test sending to multiple specific clients"""
        broadcaster = WebSocketBroadcaster()
        websockets = []
        
        for i in range(5):
            websocket = MockWebSocket()
            websockets.append(websocket)
            broadcaster.register_client(f'client_{i:03d}', websocket)
        
        event = {
            'from': 'Master',
            'to': 'Power_01',
            'type': 'Control',
            'intensity': 0.8
        }
        
        target_clients = ['client_001', 'client_003']
        count = asyncio.run(broadcaster.send_to_clients(target_clients, event))
        
        assert count == 2
        assert len(websockets[1].messages) == 1
        assert len(websockets[3].messages) == 1
        assert len(websockets[0].messages) == 0


class TestSystemMessages:
    """Test system message broadcasting"""
    
    def test_broadcast_system_message(self):
        """Test broadcasting system message"""
        broadcaster = WebSocketBroadcaster()
        websocket = MockWebSocket()
        
        broadcaster.register_client('client_001', websocket)
        
        count = asyncio.run(broadcaster.broadcast_system_message('Server is ready'))
        
        assert count == 1
        assert len(websocket.messages) == 1
    
    def test_broadcast_system_message_to_multiple_clients(self):
        """Test broadcasting system message to multiple clients"""
        broadcaster = WebSocketBroadcaster()
        websockets = []
        
        for i in range(3):
            websocket = MockWebSocket()
            websockets.append(websocket)
            broadcaster.register_client(f'client_{i:03d}', websocket)
        
        count = asyncio.run(broadcaster.broadcast_system_message('Server is ready'))
        
        assert count == 3
        for websocket in websockets:
            assert len(websocket.messages) == 1


class TestDisconnection:
    """Test client disconnection"""
    
    def test_disconnect_all_clients(self):
        """Test disconnecting all clients"""
        broadcaster = WebSocketBroadcaster()
        websockets = []
        
        for i in range(3):
            websocket = MockWebSocket()
            websockets.append(websocket)
            broadcaster.register_client(f'client_{i:03d}', websocket)
        
        assert broadcaster.get_client_count() == 3
        
        count = asyncio.run(broadcaster.disconnect_all())
        
        assert count == 3
        assert broadcaster.get_client_count() == 0
        for websocket in websockets:
            assert len(websocket.messages) == 1


class TestStatistics:
    """Test broadcaster statistics"""
    
    def test_get_statistics(self):
        """Test getting broadcaster statistics"""
        broadcaster = WebSocketBroadcaster()
        
        for i in range(3):
            websocket = MockWebSocket()
            metadata = {'index': i}
            broadcaster.register_client(f'client_{i:03d}', websocket, metadata)
        
        stats = broadcaster.get_statistics()
        
        assert stats['total_clients'] == 3
        assert len(stats['client_ids']) == 3
        assert len(stats['metadata']) == 3


class TestMessageFormat:
    """Test message format"""
    
    def test_broadcast_message_format(self):
        """Test that broadcast messages have correct format"""
        broadcaster = WebSocketBroadcaster()
        websocket = MockWebSocket()
        
        broadcaster.register_client('client_001', websocket)
        
        event = {
            'from': 'Master',
            'to': 'Power_01',
            'type': 'Control',
            'intensity': 0.8
        }
        
        asyncio.run(broadcaster.broadcast(event))
        
        import json
        message = json.loads(websocket.messages[0])
        
        assert message['type'] == 'traffic_event'
        assert message['data'] == event
        assert 'timestamp' in message
    
    def test_system_message_format(self):
        """Test that system messages have correct format"""
        broadcaster = WebSocketBroadcaster()
        websocket = MockWebSocket()
        
        broadcaster.register_client('client_001', websocket)
        
        asyncio.run(broadcaster.broadcast_system_message('Test message'))
        
        import json
        message = json.loads(websocket.messages[0])
        
        assert message['type'] == 'system_message'
        assert message['message'] == 'Test message'
        assert 'timestamp' in message


class TestErrorHandling:
    """Test error handling"""
    
    def test_broadcast_with_failed_client(self):
        """Test broadcast handles failed clients"""
        broadcaster = WebSocketBroadcaster()
        
        # Good client
        websocket1 = MockWebSocket()
        broadcaster.register_client('client_001', websocket1)
        
        # Bad client that will fail
        websocket2 = MockWebSocket()
        websocket2.closed = True
        broadcaster.register_client('client_002', websocket2)
        
        # Good client
        websocket3 = MockWebSocket()
        broadcaster.register_client('client_003', websocket3)
        
        event = {'from': 'Master', 'to': 'Power_01'}
        
        count = asyncio.run(broadcaster.broadcast(event))
        
        # Should have sent to 2 clients (1 and 3), failed client should be removed
        # Count is calculated before removal, so it's 3 - 1 = 2, but after removal it's 2
        assert count == 2
        assert broadcaster.get_client_count() == 2
        assert not broadcaster.is_client_connected('client_002')
