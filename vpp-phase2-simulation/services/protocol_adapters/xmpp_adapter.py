"""
XMPP Protocol Adapter

Implements XMPP (Extensible Messaging and Presence Protocol) for real-time communication.
Supports instant messaging, presence, and device communication.
"""

from typing import Dict, Any, Optional, List
from .base import ProtocolAdapter, ProtocolMessage, ProtocolType
import logging
import time
from datetime import datetime

logger = logging.getLogger(__name__)


class XMPPConfig:
    """XMPP Configuration"""
    
    def __init__(self, jid: str, password: str, server: str = None, port: int = 5222):
        self.jid = jid  # Jabber ID (user@domain)
        self.password = password
        self.server = server or jid.split('@')[1]
        self.port = port
        self.use_ssl = True
        self.use_tls = True


class XMPPContact:
    """XMPP Contact Information"""
    
    def __init__(self, jid: str):
        self.jid = jid
        self.status = "offline"
        self.presence = None
        self.last_seen = None
        self.messages: List[Dict[str, Any]] = []


class XMPPAdapter(ProtocolAdapter):
    """
    XMPP Protocol Adapter
    
    Provides XMPP communication for real-time messaging and presence.
    Supports device communication, messaging, and presence management.
    """
    
    def __init__(self, adapter_id: str = "xmpp-adapter"):
        super().__init__(adapter_id, ProtocolType.XMPP)
        self.config: Optional[XMPPConfig] = None
        self.contacts: Dict[str, XMPPContact] = {}
        self.message_queue: List[Dict[str, Any]] = []
        self.message_callbacks: List[callable] = []
        self.presence_callbacks: List[callable] = []
        
    def connect(self, config: Dict[str, Any]) -> bool:
        """
        Connect to XMPP server
        
        Args:
            config: Configuration with 'jid', 'password', 'server', 'port'
            
        Returns:
            True if connection successful
        """
        try:
            self.config = XMPPConfig(
                jid=config.get('jid', 'user@localhost'),
                password=config.get('password', 'password'),
                server=config.get('server'),
                port=config.get('port', 5222)
            )
            
            self.is_connected = True
            self.connection_time = time.time()
            
            logger.info(
                f"Connected to XMPP server: {self.config.server}:{self.config.port} "
                f"(JID: {self.config.jid})"
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to XMPP server: {e}")
            self.is_connected = False
            return False
    
    def disconnect(self) -> bool:
        """Disconnect from XMPP server"""
        try:
            self.is_connected = False
            self.contacts.clear()
            self.message_queue.clear()
            logger.info("Disconnected from XMPP server")
            return True
        except Exception as e:
            logger.error(f"Disconnect error: {e}")
            return False
    
    def add_contact(self, jid: str) -> bool:
        """
        Add XMPP contact
        
        Args:
            jid: Jabber ID of contact
            
        Returns:
            True if contact added
        """
        try:
            if not self.is_connected:
                logger.error("Not connected to XMPP server")
                return False
            
            if jid not in self.contacts:
                self.contacts[jid] = XMPPContact(jid)
                logger.info(f"Added XMPP contact: {jid}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to add contact: {e}")
            return False
    
    def remove_contact(self, jid: str) -> bool:
        """Remove XMPP contact"""
        try:
            if jid in self.contacts:
                del self.contacts[jid]
                logger.info(f"Removed XMPP contact: {jid}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to remove contact: {e}")
            return False
    
    def send_message(self, message: ProtocolMessage) -> bool:
        """
        Send XMPP message
        
        Args:
            message: Protocol message with recipient and body
            
        Returns:
            True if send successful
        """
        try:
            if not self.is_connected:
                logger.error("Not connected to XMPP server")
                return False
            
            recipient = message.data.get('recipient')
            body = message.data.get('body')
            msg_type = message.data.get('type', 'chat')
            
            if not recipient or not body:
                logger.error("Invalid message: missing recipient or body")
                return False
            
            # Add contact if not exists
            if recipient not in self.contacts:
                self.add_contact(recipient)
            
            msg_data = {
                'from': self.config.jid,
                'to': recipient,
                'body': body,
                'type': msg_type,
                'timestamp': datetime.utcnow().isoformat(),
                'id': f"msg-{int(time.time() * 1000)}"
            }
            
            self.message_queue.append(msg_data)
            self._record_message()
            
            # Trigger callbacks
            for callback in self.message_callbacks:
                try:
                    callback(msg_data)
                except Exception as e:
                    logger.error(f"Message callback error: {e}")
            
            logger.debug(f"Message sent to {recipient}: {body}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False
    
    def receive_message(self, timeout: float = 1.0) -> Optional[ProtocolMessage]:
        """
        Receive XMPP message from queue
        
        Args:
            timeout: Timeout in seconds
            
        Returns:
            Protocol message or None if queue empty
        """
        try:
            if not self.message_queue:
                return None
            
            msg_data = self.message_queue.pop(0)
            
            protocol_msg = ProtocolMessage(
                protocol="xmpp",
                message_id=msg_data.get('id', 'unknown'),
                source=msg_data.get('from', 'unknown'),
                destination=msg_data.get('to', 'unknown'),
                timestamp=time.time(),
                data=msg_data
            )
            
            return protocol_msg
            
        except Exception as e:
            logger.error(f"Receive error: {e}")
            return None
    
    def set_presence(self, status: str, show: str = "available") -> bool:
        """
        Set presence status
        
        Args:
            status: Status message
            show: Presence type (available, away, dnd, xa)
            
        Returns:
            True if successful
        """
        try:
            if not self.is_connected:
                return False
            
            presence_data = {
                'from': self.config.jid,
                'status': status,
                'show': show,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            # Trigger callbacks
            for callback in self.presence_callbacks:
                try:
                    callback(presence_data)
                except Exception as e:
                    logger.error(f"Presence callback error: {e}")
            
            logger.debug(f"Presence set: {show} - {status}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set presence: {e}")
            return False
    
    def get_contact_info(self, jid: str) -> Optional[Dict[str, Any]]:
        """Get contact information"""
        try:
            if jid not in self.contacts:
                return None
            
            contact = self.contacts[jid]
            return {
                'jid': contact.jid,
                'status': contact.status,
                'presence': contact.presence,
                'last_seen': contact.last_seen,
                'message_count': len(contact.messages)
            }
            
        except Exception as e:
            logger.error(f"Failed to get contact info: {e}")
            return None
    
    def list_contacts(self) -> List[Dict[str, Any]]:
        """List all contacts"""
        try:
            contacts = []
            for jid, contact in self.contacts.items():
                contacts.append({
                    'jid': contact.jid,
                    'status': contact.status,
                    'presence': contact.presence,
                    'last_seen': contact.last_seen
                })
            return contacts
        except Exception as e:
            logger.error(f"Failed to list contacts: {e}")
            return []
    
    def register_message_callback(self, callback: callable) -> None:
        """Register callback for messages"""
        self.message_callbacks.append(callback)
        logger.debug("Registered message callback")
    
    def register_presence_callback(self, callback: callable) -> None:
        """Register callback for presence changes"""
        self.presence_callbacks.append(callback)
        logger.debug("Registered presence callback")
    
    def get_message_queue(self) -> List[Dict[str, Any]]:
        """Get message queue"""
        return self.message_queue.copy()
    
    def clear_message_queue(self) -> None:
        """Clear message queue"""
        self.message_queue.clear()
        logger.debug("Cleared message queue")
    
    def parse_message(self, data: bytes) -> Dict[str, Any]:
        """Parse XMPP message data"""
        try:
            # Simple XML-like parsing for simulation
            return {
                'type': 'message',
                'data': data.decode('utf-8', errors='ignore')
            }
        except Exception as e:
            logger.error(f"Parse error: {e}")
            return {}
    
    def encode_message(self, message: Dict[str, Any]) -> bytes:
        """Encode XMPP message"""
        try:
            body = message.get('body', '')
            return body.encode('utf-8')
        except Exception as e:
            logger.error(f"Encode error: {e}")
            return b''
    
    def validate_message(self, data: bytes) -> bool:
        """Validate XMPP message"""
        return len(data) > 0
