"""
WebSocket Routes and Handlers

Handles WebSocket connections, events, and real-time communication
with the frontend visualization client.
"""

import logging
from datetime import datetime
from flask import request
from flask_socketio import emit, join_room, leave_room

logger = logging.getLogger(__name__)


class WebSocketRoutes:
    """WebSocket route handlers for traffic visualization"""
    
    def __init__(self, socketio, broadcaster, traffic_collector=None, event_generator=None):
        """
        Initialize WebSocket routes
        
        Args:
            socketio: Flask-SocketIO instance
            broadcaster: WebSocketBroadcaster instance
            traffic_collector: TrafficCollectorService instance (optional)
            event_generator: EventGenerator instance (optional)
        """
        self.socketio = socketio
        self.broadcaster = broadcaster
        self.traffic_collector = traffic_collector
        self.event_generator = event_generator
        self.connected_clients = {}
        
        # Register event handlers
        self._register_handlers()
        
        logger.info("WebSocket routes initialized")
    
    def _register_handlers(self):
        """Register all WebSocket event handlers"""
        self.socketio.on_event('connect', self.handle_connect)
        self.socketio.on_event('disconnect', self.handle_disconnect)
        self.socketio.on_event('traffic_event', self.handle_traffic_event)
        self.socketio.on_event('ping', self.handle_ping)
        self.socketio.on_event('subscribe', self.handle_subscribe)
        self.socketio.on_event('unsubscribe', self.handle_unsubscribe)
        self.socketio.on_event('request_statistics', self.handle_request_statistics)
        self.socketio.on_event('request_components', self.handle_request_components)
    
    def handle_connect(self):
        """
        Handle WebSocket client connection
        
        Registers the client with the broadcaster and sends connection confirmation
        """
        try:
            client_id = request.sid
            
            # Register with broadcaster
            metadata = {
                'connected_at': datetime.now().isoformat(),
                'user_agent': request.headers.get('User-Agent', 'Unknown'),
                'remote_addr': request.remote_addr
            }
            self.broadcaster.register_client(client_id, self.socketio, metadata)
            
            # Track locally
            self.connected_clients[client_id] = {
                'connected_at': datetime.now(),
                'events_received': 0,
                'subscribed_rooms': set()
            }
            
            logger.info(f'Client {client_id} connected from {request.remote_addr}. '
                       f'Total clients: {self.broadcaster.get_client_count()}')
            
            # Send connection confirmation
            emit('connection_response', {
                'status': 'connected',
                'client_id': client_id,
                'timestamp': datetime.now().isoformat(),
                'message': 'Successfully connected to VPP Traffic Visualization Engine'
            })
        
        except Exception as e:
            logger.error(f"Error handling client connection: {e}")
            emit('error', {
                'message': 'Connection failed',
                'error': str(e)
            })
    
    def handle_disconnect(self):
        """
        Handle WebSocket client disconnection
        
        Unregisters the client from the broadcaster and cleans up resources
        """
        try:
            client_id = request.sid
            
            # Unregister from broadcaster
            self.broadcaster.unregister_client(client_id)
            
            # Clean up local tracking
            if client_id in self.connected_clients:
                del self.connected_clients[client_id]
            
            logger.info(f'Client {client_id} disconnected. '
                       f'Total clients: {self.broadcaster.get_client_count()}')
        
        except Exception as e:
            logger.error(f"Error handling client disconnection: {e}")
    
    def handle_traffic_event(self, data):
        """
        Handle incoming traffic event from client
        
        Args:
            data: Event data dictionary
        """
        try:
            client_id = request.sid
            
            if client_id in self.connected_clients:
                self.connected_clients[client_id]['events_received'] += 1
            
            logger.debug(f'Traffic event received from {client_id}: {data}')
            
            # Broadcast to all connected clients
            emit('traffic_event', data, broadcast=True)
        
        except Exception as e:
            logger.error(f"Error handling traffic event: {e}")
            emit('error', {
                'message': 'Failed to process traffic event',
                'error': str(e)
            })
    
    def handle_ping(self):
        """
        Handle ping request from client
        
        Used for connection health check
        """
        try:
            emit('pong', {
                'timestamp': datetime.now().isoformat(),
                'server_time': datetime.now().isoformat()
            })
        
        except Exception as e:
            logger.error(f"Error handling ping: {e}")
    
    def handle_subscribe(self, data):
        """
        Handle client subscription to specific event rooms
        
        Args:
            data: Subscription data with 'room' field
        """
        try:
            client_id = request.sid
            room = data.get('room', 'default')
            
            join_room(room)
            
            if client_id in self.connected_clients:
                self.connected_clients[client_id]['subscribed_rooms'].add(room)
            
            logger.info(f'Client {client_id} subscribed to room: {room}')
            
            emit('subscription_response', {
                'status': 'subscribed',
                'room': room,
                'timestamp': datetime.now().isoformat()
            })
        
        except Exception as e:
            logger.error(f"Error handling subscription: {e}")
            emit('error', {
                'message': 'Subscription failed',
                'error': str(e)
            })
    
    def handle_unsubscribe(self, data):
        """
        Handle client unsubscription from event rooms
        
        Args:
            data: Unsubscription data with 'room' field
        """
        try:
            client_id = request.sid
            room = data.get('room', 'default')
            
            leave_room(room)
            
            if client_id in self.connected_clients:
                self.connected_clients[client_id]['subscribed_rooms'].discard(room)
            
            logger.info(f'Client {client_id} unsubscribed from room: {room}')
            
            emit('unsubscription_response', {
                'status': 'unsubscribed',
                'room': room,
                'timestamp': datetime.now().isoformat()
            })
        
        except Exception as e:
            logger.error(f"Error handling unsubscription: {e}")
            emit('error', {
                'message': 'Unsubscription failed',
                'error': str(e)
            })
    
    def handle_request_statistics(self, data=None):
        """
        Handle client request for traffic statistics
        
        Args:
            data: Optional request parameters
        """
        try:
            # Calculate statistics
            stats = {
                'total_clients': self.broadcaster.get_client_count(),
                'connected_clients': list(self.broadcaster.get_client_ids()),
                'timestamp': datetime.now().isoformat()
            }
            
            # Add local statistics
            total_events = sum(
                client['events_received'] 
                for client in self.connected_clients.values()
            )
            stats['total_events_received'] = total_events
            
            logger.debug(f'Statistics requested: {stats}')
            
            emit('statistics_response', stats)
        
        except Exception as e:
            logger.error(f"Error handling statistics request: {e}")
            emit('error', {
                'message': 'Failed to retrieve statistics',
                'error': str(e)
            })
    
    def handle_request_components(self, data=None):
        """
        Handle client request for component information
        
        Args:
            data: Optional request parameters
        """
        try:
            components = [
                {
                    'name': 'Master',
                    'ip': '10.0.8.1',
                    'type': 'coordinator',
                    'status': 'online',
                    'color': '#FF6B6B'
                },
                {
                    'name': 'Power_01',
                    'ip': '10.0.8.2',
                    'type': 'power',
                    'status': 'online',
                    'color': '#FFA500'
                },
                {
                    'name': 'Storage_01',
                    'ip': '10.0.8.3',
                    'type': 'storage',
                    'status': 'online',
                    'color': '#4ECDC4'
                },
                {
                    'name': 'Demand_01',
                    'ip': '10.0.8.4',
                    'type': 'demand',
                    'status': 'online',
                    'color': '#95E1D3'
                }
            ]
            
            logger.debug(f'Components requested')
            
            emit('components_response', {
                'components': components,
                'timestamp': datetime.now().isoformat()
            })
        
        except Exception as e:
            logger.error(f"Error handling components request: {e}")
            emit('error', {
                'message': 'Failed to retrieve components',
                'error': str(e)
            })
    
    def broadcast_traffic_event(self, event):
        """
        Broadcast a traffic event to all connected clients
        
        Args:
            event: Event dictionary to broadcast
        """
        try:
            self.socketio.emit('traffic_event', event, broadcast=True)
            logger.debug(f'Traffic event broadcasted to all clients')
        
        except Exception as e:
            logger.error(f"Error broadcasting traffic event: {e}")
    
    def broadcast_system_message(self, message):
        """
        Broadcast a system message to all connected clients
        
        Args:
            message: Message text
        """
        try:
            self.socketio.emit('system_message', {
                'message': message,
                'timestamp': datetime.now().isoformat()
            }, broadcast=True)
            logger.info(f'System message broadcasted: {message}')
        
        except Exception as e:
            logger.error(f"Error broadcasting system message: {e}")
    
    def get_client_count(self):
        """Get number of connected clients"""
        return self.broadcaster.get_client_count()
    
    def get_client_statistics(self):
        """Get statistics about connected clients"""
        return {
            'total_clients': self.broadcaster.get_client_count(),
            'client_ids': self.broadcaster.get_client_ids(),
            'local_clients': self.connected_clients.copy()
        }
