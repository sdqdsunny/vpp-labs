"""
Event Queue Service

Thread-safe FIFO queue for buffering traffic events.
"""

import logging
import threading
from collections import deque
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class EventQueue:
    """
    Thread-safe FIFO queue for buffering events
    
    Features:
    - Thread-safe operations
    - Maximum size limit
    - FIFO behavior with overflow handling
    """
    
    def __init__(self, max_size: int = 10000):
        """
        Initialize the event queue
        
        Args:
            max_size: Maximum queue size (default: 10000)
        """
        self.max_size = max_size
        self.queue: deque = deque(maxlen=max_size)
        self.lock = threading.RLock()
        self.event_count = 0
        self.dropped_count = 0
        
        logger.info(f"EventQueue initialized with max_size={max_size}")
    
    def put(self, event: Dict[str, Any]) -> bool:
        """
        Add event to queue
        
        Args:
            event: Event data as dictionary
        
        Returns:
            True if event was added, False if queue is full and event was dropped
        """
        with self.lock:
            try:
                if len(self.queue) >= self.max_size:
                    # Queue is full, drop oldest event (FIFO)
                    self.queue.popleft()
                    self.dropped_count += 1
                    logger.debug(f"Queue full, dropped oldest event. Total dropped: {self.dropped_count}")
                
                self.queue.append(event)
                self.event_count += 1
                
                if self.event_count % 1000 == 0:
                    logger.debug(f"EventQueue: {self.event_count} events processed, "
                               f"{len(self.queue)} in queue, {self.dropped_count} dropped")
                
                return True
            
            except Exception as e:
                logger.error(f"Error adding event to queue: {e}")
                return False
    
    def get(self) -> Optional[Dict[str, Any]]:
        """
        Get event from queue
        
        Returns:
            Event data or None if queue is empty
        """
        with self.lock:
            try:
                if len(self.queue) > 0:
                    return self.queue.popleft()
                return None
            except Exception as e:
                logger.error(f"Error getting event from queue: {e}")
                return None
    
    def get_batch(self, batch_size: int = 100) -> list:
        """
        Get multiple events from queue
        
        Args:
            batch_size: Number of events to retrieve
        
        Returns:
            List of events (may be smaller than batch_size if queue has fewer events)
        """
        with self.lock:
            try:
                batch = []
                for _ in range(min(batch_size, len(self.queue))):
                    event = self.queue.popleft()
                    batch.append(event)
                return batch
            except Exception as e:
                logger.error(f"Error getting batch from queue: {e}")
                return []
    
    def size(self) -> int:
        """
        Get current queue size
        
        Returns:
            Number of events in queue
        """
        with self.lock:
            return len(self.queue)
    
    def is_empty(self) -> bool:
        """
        Check if queue is empty
        
        Returns:
            True if queue is empty, False otherwise
        """
        with self.lock:
            return len(self.queue) == 0
    
    def is_full(self) -> bool:
        """
        Check if queue is full
        
        Returns:
            True if queue is at max capacity, False otherwise
        """
        with self.lock:
            return len(self.queue) >= self.max_size
    
    def clear(self):
        """Clear all events from queue"""
        with self.lock:
            try:
                self.queue.clear()
                logger.info("EventQueue cleared")
            except Exception as e:
                logger.error(f"Error clearing queue: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get queue statistics
        
        Returns:
            Dictionary with queue statistics
        """
        with self.lock:
            return {
                'current_size': len(self.queue),
                'max_size': self.max_size,
                'total_events': self.event_count,
                'dropped_events': self.dropped_count,
                'is_empty': len(self.queue) == 0,
                'is_full': len(self.queue) >= self.max_size,
                'utilization': len(self.queue) / self.max_size if self.max_size > 0 else 0
            }
