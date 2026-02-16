"""
Event Emitter Service

Handles event publishing and subscription for system-wide event notifications.
"""

from typing import Callable, List, Dict, Any
from datetime import datetime
from utils.logger import setup_logger

logger = setup_logger(__name__)


class EventEmitter:
    """Manages event publishing and subscription"""
    
    # Event types
    DISPATCH_CREATED = "dispatch.created"
    DISPATCH_COMPLETED = "dispatch.completed"
    DISPATCH_FAILED = "dispatch.failed"
    DEVICE_REGISTERED = "device.registered"
    DEVICE_STATUS_CHANGED = "device.status_changed"
    
    def __init__(self):
        """Initialize event emitter"""
        self._listeners: Dict[str, List[Callable]] = {}
        self._event_history: List[Dict[str, Any]] = []
    
    def subscribe(self, event_type: str, callback: Callable) -> None:
        """
        Subscribe to an event
        
        Args:
            event_type: Type of event to subscribe to
            callback: Callback function to invoke when event is emitted
        """
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        
        self._listeners[event_type].append(callback)
        logger.debug(f"Subscribed to event: {event_type}")
    
    def unsubscribe(self, event_type: str, callback: Callable) -> None:
        """
        Unsubscribe from an event
        
        Args:
            event_type: Type of event to unsubscribe from
            callback: Callback function to remove
        """
        if event_type in self._listeners:
            try:
                self._listeners[event_type].remove(callback)
                logger.debug(f"Unsubscribed from event: {event_type}")
            except ValueError:
                logger.warning(f"Callback not found for event: {event_type}")
    
    def emit(self, event_type: str, data: Dict[str, Any]) -> None:
        """
        Emit an event
        
        Args:
            event_type: Type of event to emit
            data: Event data
        """
        event_record = {
            "event_type": event_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Store in history
        self._event_history.append(event_record)
        
        logger.info(
            f"Event emitted: {event_type}",
            extra={
                "event_type": event_type,
                "data": data
            }
        )
        
        # Invoke all listeners
        if event_type in self._listeners:
            for callback in self._listeners[event_type]:
                try:
                    callback(data)
                except Exception as e:
                    logger.error(f"Error invoking callback for event {event_type}: {str(e)}")
    
    def get_event_history(self, event_type: str = None) -> List[Dict[str, Any]]:
        """
        Get event history
        
        Args:
            event_type: Optional filter by event type
        
        Returns:
            List of event records
        """
        if event_type:
            return [e for e in self._event_history if e["event_type"] == event_type]
        return self._event_history
    
    def clear_history(self) -> None:
        """Clear event history"""
        self._event_history = []
        logger.debug("Event history cleared")


# Global event emitter instance
_event_emitter = None


def get_event_emitter() -> EventEmitter:
    """Get or create global event emitter instance"""
    global _event_emitter
    if _event_emitter is None:
        _event_emitter = EventEmitter()
    return _event_emitter
