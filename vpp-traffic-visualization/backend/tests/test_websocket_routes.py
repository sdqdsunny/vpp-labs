"""
Unit tests for WebSocket routes

Tests for WebSocket event handlers, client management, and message broadcasting.
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


class MockSocketIO:
    """Mock SocketIO for testing"""
    
    def __init__(self):
        self.events = {}
        self.emitted_messages = []
    
    def on_event(self, event_name, handler):
        """Register event handler"""
        self.events[event_name] = handler
    
    def emit(self, event, data, broadcast=False):
        """Mock emit"""
        self.emitted_messages.append({
            'event': event,
            'data': data,
            'broadcast': broadcast
        })


class MockRequest:
    """Mock Flask request"""
    
    def __init__(self, sid='test_client_001', remote_addr='127.0.0.1'):
        self.sid = sid
        self.remote_addr = remote_addr
        self.headers = {'User-Agent': 'Test Client'}


class TestWebSocketRoutesBasics:
    """Test basic WebSocket routes functionality"""
    
    def test_routes_initialization(self):
        """Test WebSocketRoutes initialization"""
        from services.websocket_broadcaster import WebSocketBroadcaster
        from routes.websocket_routes import WebSocketRoutes
        
        socketio = MockSocketIO()
        broadcaster = WebSocketBroadcaster()
        
        routes = WebSocketRoutes(socketio, broadcaster)
        
        assert routes is not None
        assert routes.socketio == socketio
        assert routes.broadcaster == broadcaster
        assert len(routes.connected_clients) == 0
    
    def test_event_handlers_registered(self):
        """Test that all event handlers are registered"""
        from services.websocket_broadcaster import WebSocketBroadcaster
        from routes.websocket_routes import WebSocketRoutes
        
        socketio = MockSocketIO()
        broadcaster = WebSocketBroadcaster()
        
        routes = WebSocketRoutes(socketio, broadcaster)
        
        expected_events = [
            'connect', 'disconnect', 'traffic_event', 'ping',
            'subscribe', 'unsubscribe', 'request_statistics', 'request_components'
        ]
        
        for event in expected_events:
            assert event in socketio.events


class TestClientConnection:
    """Test client connection handling"""
    
    def test_handle_connect(self):
        """Test handling client connection"""
        from services.websocket_broadcaster import WebSocketBroadcaster
        from routes.websocket_routes import WebSocketRoutes
        
        socketio = MockSocketIO()
        broadcaster = WebSocketBroadcaster()
        routes = WebSocketRoutes(socketio, broadcaster)
        
        # Mock request context
        with patch('routes.websocket_routes.request', MockRequest()):
            with patch('routes.websocket_routes.emit') as mock_emit:
                routes.handle_connect()
                
                # Verify client was registered
                assert broadcaster.get_client_count() == 1
                assert 'test_client_001' in routes.connected_clients
    
    def test_handle_disconnect(self):
        """Test handling client disconnection"""
        from services.websocket_broadcaster import WebSocketBroadcaster
        from routes.websocket_routes import WebSocketRoutes
        
        socketio = MockSocketIO()
        broadcaster = WebSocketBroadcaster()
        routes = WebSocketRoutes(socketio, broadcaster)
        
        # First connect a client
        with patch('routes.websocket_routes.request', MockRequest()):
            with patch('routes.websocket_routes.emit'):
                routes.handle_connect()
        
        assert broadcaster.get_client_count() == 1
        
        # Now disconnect
        with patch('routes.websocket_routes.request', MockRequest()):
            routes.handle_disconnect()
        
        assert broadcaster.get_client_count() == 0
        assert 'test_client_001' not in routes.connected_clients
    
    def test_multiple_clients_connection(self):
        """Test handling multiple client connections"""
        from services.websocket_broadcaster import WebSocketBroadcaster
        from routes.websocket_routes import WebSocketRoutes
        
        socketio = MockSocketIO()
        broadcaster = WebSocketBroadcaster()
        routes = WebSocketRoutes(socketio, broadcaster)
        
        # Connect multiple clients
        for i in range(5):
            client_id = f'client_{i:03d}'
            with patch('routes.websocket_routes.request', MockRequest(sid=client_id)):
                with patch('routes.websocket_routes.emit'):
                    routes.handle_connect()
        
        assert broadcaster.get_client_count() == 5
        assert len(routes.connected_clients) == 5


class TestTrafficEventHandling:
    """Test traffic event handling"""
    
    def test_handle_traffic_event(self):
        """Test handling traffic event"""
        from services.websocket_broadcaster import WebSocketBroadcaster
        from routes.websocket_routes import WebSocketRoutes
        
        socketio = MockSocketIO()
        broadcaster = WebSocketBroadcaster()
        routes = WebSocketRoutes(socketio, broadcaster)
        
        # Connect a client first
        with patch('routes.websocket_routes.request', MockRequest()):
            with patch('routes.websocket_routes.emit'):
                routes.handle_connect()
        
        # Send traffic event
        event_data = {
            'from': 'Master',
            'to': 'Power_01',
            'type': 'Control',
            'intensity': 0.8
        }
        
        with patch('routes.websocket_routes.request', MockRequest()):
            with patch('routes.websocket_routes.emit'):
                routes.handle_traffic_event(event_data)
        
        # Verify event was counted
        assert routes.connected_clients['test_client_001']['events_received'] == 1


class TestPingPong:
    """Test ping/pong functionality"""
    
    def test_handle_ping(self):
        """Test handling ping request"""
        from services.websocket_broadcaster import WebSocketBroadcaster
        from routes.websocket_routes import WebSocketRoutes
        
        socketio = MockSocketIO()
        broadcaster = WebSocketBroadcaster()
        routes = WebSocketRoutes(socketio, broadcaster)
        
        with patch('routes.websocket_routes.emit') as mock_emit:
            routes.handle_ping()
            
            # Verify pong was sent
            mock_emit.assert_called_once()
            call_args = mock_emit.call_args
            assert call_args[0][0] == 'pong'


class TestSubscriptionHandling:
    """Test subscription/unsubscription handling"""
    
    def test_handle_subscribe(self):
        """Test handling subscription"""
        from services.websocket_broadcaster import WebSocketBroadcaster
        from routes.websocket_routes import WebSocketRoutes
        
        socketio = MockSocketIO()
        broadcaster = WebSocketBroadcaster()
        routes = WebSocketRoutes(socketio, broadcaster)
        
        # Connect a client first
        with patch('routes.websocket_routes.request', MockRequest()):
            with patch('routes.websocket_routes.emit'):
                routes.handle_connect()
        
        # Subscribe to room
        with patch('routes.websocket_routes.request', MockRequest()):
            with patch('routes.websocket_routes.emit'):
                with patch('routes.websocket_routes.join_room'):
                    routes.handle_subscribe({'room': 'control_traffic'})
        
        # Verify subscription
        assert 'control_traffic' in routes.connected_clients['test_client_001']['subscribed_rooms']
    
    def test_handle_unsubscribe(self):
        """Test handling unsubscription"""
        from services.websocket_broadcaster import WebSocketBroadcaster
        from routes.websocket_routes import WebSocketRoutes
        
        socketio = MockSocketIO()
        broadcaster = WebSocketBroadcaster()
        routes = WebSocketRoutes(socketio, broadcaster)
        
        # Connect and subscribe first
        with patch('routes.websocket_routes.request', MockRequest()):
            with patch('routes.websocket_routes.emit'):
                routes.handle_connect()
        
        routes.connected_clients['test_client_001']['subscribed_rooms'].add('control_traffic')
        
        # Unsubscribe
        with patch('routes.websocket_routes.request', MockRequest()):
            with patch('routes.websocket_routes.emit'):
                with patch('routes.websocket_routes.leave_room'):
                    routes.handle_unsubscribe({'room': 'control_traffic'})
        
        # Verify unsubscription
        assert 'control_traffic' not in routes.connected_clients['test_client_001']['subscribed_rooms']


class TestStatisticsRequest:
    """Test statistics request handling"""
    
    def test_handle_request_statistics(self):
        """Test handling statistics request"""
        from services.websocket_broadcaster import WebSocketBroadcaster
        from routes.websocket_routes import WebSocketRoutes
        
        socketio = MockSocketIO()
        broadcaster = WebSocketBroadcaster()
        routes = WebSocketRoutes(socketio, broadcaster)
        
        # Connect a client
        with patch('routes.websocket_routes.request', MockRequest()):
            with patch('routes.websocket_routes.emit'):
                routes.handle_connect()
        
        # Request statistics
        with patch('routes.websocket_routes.emit') as mock_emit:
            routes.handle_request_statistics()
            
            # Verify statistics were sent
            mock_emit.assert_called_once()
            call_args = mock_emit.call_args
            assert call_args[0][0] == 'statistics_response'
            stats = call_args[0][1]
            assert stats['total_clients'] == 1


class TestComponentsRequest:
    """Test components request handling"""
    
    def test_handle_request_components(self):
        """Test handling components request"""
        from services.websocket_broadcaster import WebSocketBroadcaster
        from routes.websocket_routes import WebSocketRoutes
        
        socketio = MockSocketIO()
        broadcaster = WebSocketBroadcaster()
        routes = WebSocketRoutes(socketio, broadcaster)
        
        with patch('routes.websocket_routes.emit') as mock_emit:
            routes.handle_request_components()
            
            # Verify components were sent
            mock_emit.assert_called_once()
            call_args = mock_emit.call_args
            assert call_args[0][0] == 'components_response'
            response = call_args[0][1]
            assert 'components' in response
            assert len(response['components']) == 4


class TestBroadcasting:
    """Test broadcasting functionality"""
    
    def test_broadcast_traffic_event(self):
        """Test broadcasting traffic event"""
        from services.websocket_broadcaster import WebSocketBroadcaster
        from routes.websocket_routes import WebSocketRoutes
        
        socketio = MockSocketIO()
        broadcaster = WebSocketBroadcaster()
        routes = WebSocketRoutes(socketio, broadcaster)
        
        event = {
            'from': 'Master',
            'to': 'Power_01',
            'type': 'Control',
            'intensity': 0.8
        }
        
        with patch.object(socketio, 'emit') as mock_emit:
            routes.broadcast_traffic_event(event)
            
            mock_emit.assert_called_once()
            call_args = mock_emit.call_args
            assert call_args[0][0] == 'traffic_event'
            assert call_args[1]['broadcast'] is True
    
    def test_broadcast_system_message(self):
        """Test broadcasting system message"""
        from services.websocket_broadcaster import WebSocketBroadcaster
        from routes.websocket_routes import WebSocketRoutes
        
        socketio = MockSocketIO()
        broadcaster = WebSocketBroadcaster()
        routes = WebSocketRoutes(socketio, broadcaster)
        
        with patch.object(socketio, 'emit') as mock_emit:
            routes.broadcast_system_message('Server is ready')
            
            mock_emit.assert_called_once()
            call_args = mock_emit.call_args
            assert call_args[0][0] == 'system_message'
            assert call_args[1]['broadcast'] is True


class TestClientStatistics:
    """Test client statistics"""
    
    def test_get_client_count(self):
        """Test getting client count"""
        from services.websocket_broadcaster import WebSocketBroadcaster
        from routes.websocket_routes import WebSocketRoutes
        
        socketio = MockSocketIO()
        broadcaster = WebSocketBroadcaster()
        routes = WebSocketRoutes(socketio, broadcaster)
        
        # Connect multiple clients
        for i in range(3):
            client_id = f'client_{i:03d}'
            with patch('routes.websocket_routes.request', MockRequest(sid=client_id)):
                with patch('routes.websocket_routes.emit'):
                    routes.handle_connect()
        
        assert routes.get_client_count() == 3
    
    def test_get_client_statistics(self):
        """Test getting client statistics"""
        from services.websocket_broadcaster import WebSocketBroadcaster
        from routes.websocket_routes import WebSocketRoutes
        
        socketio = MockSocketIO()
        broadcaster = WebSocketBroadcaster()
        routes = WebSocketRoutes(socketio, broadcaster)
        
        # Connect a client
        with patch('routes.websocket_routes.request', MockRequest()):
            with patch('routes.websocket_routes.emit'):
                routes.handle_connect()
        
        stats = routes.get_client_statistics()
        
        assert stats['total_clients'] == 1
        assert len(stats['client_ids']) == 1
        assert len(stats['local_clients']) == 1


class TestErrorHandling:
    """Test error handling"""
    
    def test_handle_connect_error(self):
        """Test error handling in connect"""
        from services.websocket_broadcaster import WebSocketBroadcaster
        from routes.websocket_routes import WebSocketRoutes
        
        socketio = MockSocketIO()
        broadcaster = WebSocketBroadcaster()
        routes = WebSocketRoutes(socketio, broadcaster)
        
        # Mock request to raise error
        with patch('routes.websocket_routes.request', side_effect=Exception('Test error')):
            with patch('routes.websocket_routes.emit') as mock_emit:
                routes.handle_connect()
                
                # Verify error was emitted
                mock_emit.assert_called()
    
    def test_handle_traffic_event_error(self):
        """Test error handling in traffic event"""
        from services.websocket_broadcaster import WebSocketBroadcaster
        from routes.websocket_routes import WebSocketRoutes
        
        socketio = MockSocketIO()
        broadcaster = WebSocketBroadcaster()
        routes = WebSocketRoutes(socketio, broadcaster)
        
        with patch('routes.websocket_routes.request', side_effect=Exception('Test error')):
            with patch('routes.websocket_routes.emit') as mock_emit:
                routes.handle_traffic_event({'test': 'data'})
                
                # Verify error was emitted
                mock_emit.assert_called()
    """Mock SocketIO for testing"""
    
    def __init__(self):
        self.events = {}
        self.emitted_messages = []
    
    def on_event(self, event_name, handler):
        """Register event handler"""
        self.events[event_name] = handler
    
    def emit(self, event, data, broadcast=False):
        """Mock emit"""
        self.emitted_messages.append({
            'event': event,
            'data': data,
            'broadcast': broadcast
        })


class MockRequest:
    """Mock Flask request"""
    
    def __init__(self, sid='test_client_001', remote_addr='127.0.0.1'):
        self.sid = sid
        self.remote_addr = remote_addr
        self.headers = {'User-Agent': 'Test Client'}


class TestWebSocketRoutesBasics:
    """Test basic WebSocket routes functionality"""
    
    def test_routes_initialization(self):
        """Test WebSocketRoutes initialization"""
        socketio = MockSocketIO()
        broadcaster = WebSocketBroadcaster()
        
        routes = WebSocketRoutes(socketio, broadcaster)
        
        assert routes is not None
        assert routes.socketio == socketio
        assert routes.broadcaster == broadcaster
        assert len(routes.connected_clients) == 0
    
    def test_event_handlers_registered(self):
        """Test that all event handlers are registered"""
        socketio = MockSocketIO()
        broadcaster = WebSocketBroadcaster()
        
        routes = WebSocketRoutes(socketio, broadcaster)
        
        expected_events = [
            'connect', 'disconnect', 'traffic_event', 'ping',
            'subscribe', 'unsubscribe', 'request_statistics', 'request_components'
        ]
        
        for event in expected_events:
            assert event in socketio.events


class TestClientConnection:
    """Test client connection handling"""
    
    def test_handle_connect(self):
        """Test handling client connection"""
        socketio = MockSocketIO()
        broadcaster = WebSocketBroadcaster()
        routes = WebSocketRoutes(socketio, broadcaster)
        
        # Mock request context
        with patch('routes.websocket_routes.request', MockRequest()):
            with patch('routes.websocket_routes.emit') as mock_emit:
                routes.handle_connect()
                
                # Verify client was registered
                assert broadcaster.get_client_count() == 1
                assert 'test_client_001' in routes.connected_clients
    
    def test_handle_disconnect(self):
        """Test handling client disconnection"""
        socketio = MockSocketIO()
        broadcaster = WebSocketBroadcaster()
        routes = WebSocketRoutes(socketio, broadcaster)
        
        # First connect a client
        with patch('routes.websocket_routes.request', MockRequest()):
            with patch('routes.websocket_routes.emit'):
                routes.handle_connect()
        
        assert broadcaster.get_client_count() == 1
        
        # Now disconnect
        with patch('routes.websocket_routes.request', MockRequest()):
            routes.handle_disconnect()
        
        assert broadcaster.get_client_count() == 0
        assert 'test_client_001' not in routes.connected_clients
    
    def test_multiple_clients_connection(self):
        """Test handling multiple client connections"""
        socketio = MockSocketIO()
        broadcaster = WebSocketBroadcaster()
        routes = WebSocketRoutes(socketio, broadcaster)
        
        # Connect multiple clients
        for i in range(5):
            client_id = f'client_{i:03d}'
            with patch('routes.websocket_routes.request', MockRequest(sid=client_id)):
                with patch('routes.websocket_routes.emit'):
                    routes.handle_connect()
        
        assert broadcaster.get_client_count() == 5
        assert len(routes.connected_clients) == 5


class TestTrafficEventHandling:
    """Test traffic event handling"""
    
    def test_handle_traffic_event(self):
        """Test handling traffic event"""
        socketio = MockSocketIO()
        broadcaster = WebSocketBroadcaster()
        routes = WebSocketRoutes(socketio, broadcaster)
        
        # Connect a client first
        with patch('routes.websocket_routes.request', MockRequest()):
            with patch('routes.websocket_routes.emit'):
                routes.handle_connect()
        
        # Send traffic event
        event_data = {
            'from': 'Master',
            'to': 'Power_01',
            'type': 'Control',
            'intensity': 0.8
        }
        
        with patch('routes.websocket_routes.request', MockRequest()):
            with patch('routes.websocket_routes.emit'):
                routes.handle_traffic_event(event_data)
        
        # Verify event was counted
        assert routes.connected_clients['test_client_001']['events_received'] == 1


class TestPingPong:
    """Test ping/pong functionality"""
    
    def test_handle_ping(self):
        """Test handling ping request"""
        socketio = MockSocketIO()
        broadcaster = WebSocketBroadcaster()
        routes = WebSocketRoutes(socketio, broadcaster)
        
        with patch('routes.websocket_routes.emit') as mock_emit:
            routes.handle_ping()
            
            # Verify pong was sent
            mock_emit.assert_called_once()
            call_args = mock_emit.call_args
            assert call_args[0][0] == 'pong'


class TestSubscriptionHandling:
    """Test subscription/unsubscription handling"""
    
    def test_handle_subscribe(self):
        """Test handling subscription"""
        socketio = MockSocketIO()
        broadcaster = WebSocketBroadcaster()
        routes = WebSocketRoutes(socketio, broadcaster)
        
        # Connect a client first
        with patch('routes.websocket_routes.request', MockRequest()):
            with patch('routes.websocket_routes.emit'):
                routes.handle_connect()
        
        # Subscribe to room
        with patch('routes.websocket_routes.request', MockRequest()):
            with patch('routes.websocket_routes.emit'):
                with patch('routes.websocket_routes.join_room'):
                    routes.handle_subscribe({'room': 'control_traffic'})
        
        # Verify subscription
        assert 'control_traffic' in routes.connected_clients['test_client_001']['subscribed_rooms']
    
    def test_handle_unsubscribe(self):
        """Test handling unsubscription"""
        socketio = MockSocketIO()
        broadcaster = WebSocketBroadcaster()
        routes = WebSocketRoutes(socketio, broadcaster)
        
        # Connect and subscribe first
        with patch('routes.websocket_routes.request', MockRequest()):
            with patch('routes.websocket_routes.emit'):
                routes.handle_connect()
        
        routes.connected_clients['test_client_001']['subscribed_rooms'].add('control_traffic')
        
        # Unsubscribe
        with patch('routes.websocket_routes.request', MockRequest()):
            with patch('routes.websocket_routes.emit'):
                with patch('routes.websocket_routes.leave_room'):
                    routes.handle_unsubscribe({'room': 'control_traffic'})
        
        # Verify unsubscription
        assert 'control_traffic' not in routes.connected_clients['test_client_001']['subscribed_rooms']


class TestStatisticsRequest:
    """Test statistics request handling"""
    
    def test_handle_request_statistics(self):
        """Test handling statistics request"""
        socketio = MockSocketIO()
        broadcaster = WebSocketBroadcaster()
        routes = WebSocketRoutes(socketio, broadcaster)
        
        # Connect a client
        with patch('routes.websocket_routes.request', MockRequest()):
            with patch('routes.websocket_routes.emit'):
                routes.handle_connect()
        
        # Request statistics
        with patch('routes.websocket_routes.emit') as mock_emit:
            routes.handle_request_statistics()
            
            # Verify statistics were sent
            mock_emit.assert_called_once()
            call_args = mock_emit.call_args
            assert call_args[0][0] == 'statistics_response'
            stats = call_args[0][1]
            assert stats['total_clients'] == 1


class TestComponentsRequest:
    """Test components request handling"""
    
    def test_handle_request_components(self):
        """Test handling components request"""
        socketio = MockSocketIO()
        broadcaster = WebSocketBroadcaster()
        routes = WebSocketRoutes(socketio, broadcaster)
        
        with patch('routes.websocket_routes.emit') as mock_emit:
            routes.handle_request_components()
            
            # Verify components were sent
            mock_emit.assert_called_once()
            call_args = mock_emit.call_args
            assert call_args[0][0] == 'components_response'
            response = call_args[0][1]
            assert 'components' in response
            assert len(response['components']) == 4


class TestBroadcasting:
    """Test broadcasting functionality"""
    
    def test_broadcast_traffic_event(self):
        """Test broadcasting traffic event"""
        socketio = MockSocketIO()
        broadcaster = WebSocketBroadcaster()
        routes = WebSocketRoutes(socketio, broadcaster)
        
        event = {
            'from': 'Master',
            'to': 'Power_01',
            'type': 'Control',
            'intensity': 0.8
        }
        
        with patch.object(socketio, 'emit') as mock_emit:
            routes.broadcast_traffic_event(event)
            
            mock_emit.assert_called_once()
            call_args = mock_emit.call_args
            assert call_args[0][0] == 'traffic_event'
            assert call_args[1]['broadcast'] is True
    
    def test_broadcast_system_message(self):
        """Test broadcasting system message"""
        socketio = MockSocketIO()
        broadcaster = WebSocketBroadcaster()
        routes = WebSocketRoutes(socketio, broadcaster)
        
        with patch.object(socketio, 'emit') as mock_emit:
            routes.broadcast_system_message('Server is ready')
            
            mock_emit.assert_called_once()
            call_args = mock_emit.call_args
            assert call_args[0][0] == 'system_message'
            assert call_args[1]['broadcast'] is True


class TestClientStatistics:
    """Test client statistics"""
    
    def test_get_client_count(self):
        """Test getting client count"""
        socketio = MockSocketIO()
        broadcaster = WebSocketBroadcaster()
        routes = WebSocketRoutes(socketio, broadcaster)
        
        # Connect multiple clients
        for i in range(3):
            client_id = f'client_{i:03d}'
            with patch('routes.websocket_routes.request', MockRequest(sid=client_id)):
                with patch('routes.websocket_routes.emit'):
                    routes.handle_connect()
        
        assert routes.get_client_count() == 3
    
    def test_get_client_statistics(self):
        """Test getting client statistics"""
        socketio = MockSocketIO()
        broadcaster = WebSocketBroadcaster()
        routes = WebSocketRoutes(socketio, broadcaster)
        
        # Connect a client
        with patch('routes.websocket_routes.request', MockRequest()):
            with patch('routes.websocket_routes.emit'):
                routes.handle_connect()
        
        stats = routes.get_client_statistics()
        
        assert stats['total_clients'] == 1
        assert len(stats['client_ids']) == 1
        assert len(stats['local_clients']) == 1


class TestErrorHandling:
    """Test error handling"""
    
    def test_handle_connect_error(self):
        """Test error handling in connect"""
        socketio = MockSocketIO()
        broadcaster = WebSocketBroadcaster()
        routes = WebSocketRoutes(socketio, broadcaster)
        
        # Mock request to raise error
        with patch('routes.websocket_routes.request', side_effect=Exception('Test error')):
            with patch('routes.websocket_routes.emit') as mock_emit:
                routes.handle_connect()
                
                # Verify error was emitted
                mock_emit.assert_called()
    
    def test_handle_traffic_event_error(self):
        """Test error handling in traffic event"""
        socketio = MockSocketIO()
        broadcaster = WebSocketBroadcaster()
        routes = WebSocketRoutes(socketio, broadcaster)
        
        with patch('routes.websocket_routes.request', side_effect=Exception('Test error')):
            with patch('routes.websocket_routes.emit') as mock_emit:
                routes.handle_traffic_event({'test': 'data'})
                
                # Verify error was emitted
                mock_emit.assert_called()
