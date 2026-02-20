"""
WebSocket Broadcaster Service

Manages WebSocket client connections and broadcasts events to all connected clients.
"""

import logging
import json
import asyncio
from typing import Dict, Optional, Callable, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class WebSocketBroadcaster:
    """
    Manages WebSocket client connections and broadcasts events
    
    Features:
    - Client registration and unregistration
    - Event broadcasting to all connected clients
    - Individual client messaging
    - Connection management
    - Error handling and logging
    """
    
    def __init__(self):
        """Initialize the WebSocket broadcaster"""
        self.clients: Dict[str, Any] = {}  # client_id -> websocket
        self.client_metadata: Dict[str, Dict] = {}  # client_id -> metadata
        logger.info("WebSocketBroadcaster initialized")
    
    def register_client(self, client_id: str, websocket: Any, metadata: Optional[Dict] = None) -> bool:
        """
        Register a WebSocket client
        
        Args:
            client_id: Unique client identifier
            websocket: WebSocket connection object
            metadata: Optional metadata about the client
        
        Returns:
            True if registration successful, False if client already exists
        """
        try:
            if client_id in self.clients:
                logger.warning(f"Client {client_id} already registered")
                return False
            
            self.clients[client_id] = websocket
            self.client_metadata[client_id] = metadata or {}
            self.client_metadata[client_id]['connected_at'] = datetime.now().isoformat()
            
            logger.info(f"Client {client_id} registered. Total clients: {len(self.clients)}")
            return True
        
        except Exception as e:
            logger.error(f"Error registering client {client_id}: {e}")
            return False
    
    def unregister_client(self, client_id: str) -> bool:
        """
        Unregister a WebSocket client
        
        Args:
            client_id: Client identifier
        
        Returns:
            True if unregistration successful, False if client not found
        """
        try:
            if client_id not in self.clients:
                logger.warning(f"Client {client_id} not found")
                return False
            
            del self.clients[client_id]
            del self.client_metadata[client_id]
            
            logger.info(f"Client {client_id} unregistered. Total clients: {len(self.clients)}")
            return True
        
        except Exception as e:
            logger.error(f"Error unregistering client {client_id}: {e}")
            return False
    
    async def broadcast(self, event: Dict) -> int:
        """
        Broadcast event to all connected clients
        
        Args:
            event: Event dictionary to broadcast
        
        Returns:
            Number of clients that received the event
        """
        try:
            if not self.clients:
                logger.debug("No clients connected, skipping broadcast")
                return 0
            
            # Prepare message
            message = {
                'type': 'traffic_event',
                'data': event,
                'timestamp': datetime.now().isoformat()
            }
            
            message_json = json.dumps(message)
            
            # Send to all clients
            failed_clients = []
            successful_count = 0
            for client_id, websocket in list(self.clients.items()):
                try:
                    await websocket.send(message_json)
                    successful_count += 1
                except Exception as e:
                    logger.error(f"Error sending to client {client_id}: {e}")
                    failed_clients.append(client_id)
            
            # Remove failed clients
            for client_id in failed_clients:
                self.unregister_client(client_id)
            
            logger.debug(f"Broadcast sent to {successful_count} clients")
            
            return successful_count
        
        except Exception as e:
            logger.error(f"Error broadcasting event: {e}")
            return 0
    
    async def send_to_client(self, client_id: str, event: Dict) -> bool:
        """
        Send event to specific client
        
        Args:
            client_id: Target client identifier
            event: Event dictionary to send
        
        Returns:
            True if send successful, False otherwise
        """
        try:
            if client_id not in self.clients:
                logger.warning(f"Client {client_id} not found")
                return False
            
            websocket = self.clients[client_id]
            
            # Prepare message
            message = {
                'type': 'traffic_event',
                'data': event,
                'timestamp': datetime.now().isoformat()
            }
            
            message_json = json.dumps(message)
            
            await websocket.send(message_json)
            logger.debug(f"Event sent to client {client_id}")
            
            return True
        
        except Exception as e:
            logger.error(f"Error sending to client {client_id}: {e}")
            # Remove failed client
            self.unregister_client(client_id)
            return False
    
    async def send_to_clients(self, client_ids: list, event: Dict) -> int:
        """
        Send event to multiple specific clients
        
        Args:
            client_ids: List of target client identifiers
            event: Event dictionary to send
        
        Returns:
            Number of clients that received the event
        """
        try:
            successful_count = 0
            
            for client_id in client_ids:
                if await self.send_to_client(client_id, event):
                    successful_count += 1
            
            logger.debug(f"Event sent to {successful_count}/{len(client_ids)} clients")
            return successful_count
        
        except Exception as e:
            logger.error(f"Error sending to multiple clients: {e}")
            return 0
    
    def get_client_count(self) -> int:
        """Get number of connected clients"""
        return len(self.clients)
    
    def get_client_ids(self) -> list:
        """Get list of all connected client IDs"""
        return list(self.clients.keys())
    
    def get_client_metadata(self, client_id: str) -> Optional[Dict]:
        """
        Get metadata for a specific client
        
        Args:
            client_id: Client identifier
        
        Returns:
            Client metadata or None if not found
        """
        return self.client_metadata.get(client_id)
    
    def get_all_metadata(self) -> Dict[str, Dict]:
        """Get metadata for all connected clients"""
        return self.client_metadata.copy()
    
    def is_client_connected(self, client_id: str) -> bool:
        """Check if a client is connected"""
        return client_id in self.clients
    
    async def broadcast_system_message(self, message: str) -> int:
        """
        Broadcast a system message to all clients
        
        Args:
            message: System message text
        
        Returns:
            Number of clients that received the message
        """
        try:
            if not self.clients:
                return 0
            
            system_message = {
                'type': 'system_message',
                'message': message,
                'timestamp': datetime.now().isoformat()
            }
            
            message_json = json.dumps(system_message)
            
            failed_clients = []
            successful_count = 0
            for client_id, websocket in list(self.clients.items()):
                try:
                    await websocket.send(message_json)
                    successful_count += 1
                except Exception as e:
                    logger.error(f"Error sending system message to client {client_id}: {e}")
                    failed_clients.append(client_id)
            
            # Remove failed clients
            for client_id in failed_clients:
                self.unregister_client(client_id)
            
            logger.info(f"System message sent to {successful_count} clients")
            
            return successful_count
        
        except Exception as e:
            logger.error(f"Error broadcasting system message: {e}")
            return 0
    
    async def disconnect_all(self) -> int:
        """
        Disconnect all clients
        
        Returns:
            Number of clients disconnected
        """
        try:
            count = len(self.clients)
            
            # Send disconnect message to all clients
            disconnect_message = {
                'type': 'disconnect',
                'message': 'Server is shutting down',
                'timestamp': datetime.now().isoformat()
            }
            
            message_json = json.dumps(disconnect_message)
            
            for client_id, websocket in list(self.clients.items()):
                try:
                    await websocket.send(message_json)
                except Exception as e:
                    logger.debug(f"Error sending disconnect to client {client_id}: {e}")
            
            # Clear all clients
            self.clients.clear()
            self.client_metadata.clear()
            
            logger.info(f"Disconnected {count} clients")
            return count
        
        except Exception as e:
            logger.error(f"Error disconnecting all clients: {e}")
            return 0
    
    def get_statistics(self) -> Dict:
        """Get broadcaster statistics"""
        return {
            'total_clients': len(self.clients),
            'client_ids': list(self.clients.keys()),
            'metadata': self.client_metadata.copy()
        }
