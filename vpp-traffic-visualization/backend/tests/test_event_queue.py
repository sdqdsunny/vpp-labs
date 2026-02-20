"""
Unit tests for Event Queue Service

Tests for FIFO queue operations, thread safety, and overflow handling.
"""

import pytest
import sys
import threading
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.event_queue import EventQueue


class TestEventQueue:
    """Test EventQueue"""
    
    def test_initialization(self):
        """Test queue initialization"""
        queue = EventQueue(max_size=100)
        assert queue.max_size == 100
        assert queue.size() == 0
        assert queue.is_empty() is True
        assert queue.is_full() is False
    
    def test_default_max_size(self):
        """Test default max size"""
        queue = EventQueue()
        assert queue.max_size == 10000
    
    def test_put_single_event(self):
        """Test adding single event"""
        queue = EventQueue()
        event = {'from': 'Master', 'to': 'Storage_01', 'type': 'Control'}
        
        result = queue.put(event)
        
        assert result is True
        assert queue.size() == 1
        assert queue.is_empty() is False
    
    def test_put_multiple_events(self):
        """Test adding multiple events"""
        queue = EventQueue()
        
        for i in range(10):
            event = {'id': i, 'data': f'event_{i}'}
            result = queue.put(event)
            assert result is True
        
        assert queue.size() == 10
    
    def test_get_single_event(self):
        """Test getting single event"""
        queue = EventQueue()
        event = {'from': 'Master', 'to': 'Storage_01', 'type': 'Control'}
        
        queue.put(event)
        retrieved = queue.get()
        
        assert retrieved is not None
        assert retrieved['from'] == 'Master'
        assert queue.size() == 0
    
    def test_get_from_empty_queue(self):
        """Test getting from empty queue"""
        queue = EventQueue()
        result = queue.get()
        
        assert result is None
    
    def test_fifo_order(self):
        """Test FIFO order"""
        queue = EventQueue()
        
        for i in range(5):
            queue.put({'id': i})
        
        for i in range(5):
            event = queue.get()
            assert event['id'] == i
    
    def test_get_batch(self):
        """Test getting batch of events"""
        queue = EventQueue()
        
        for i in range(10):
            queue.put({'id': i})
        
        batch = queue.get_batch(5)
        
        assert len(batch) == 5
        assert batch[0]['id'] == 0
        assert batch[4]['id'] == 4
        assert queue.size() == 5
    
    def test_get_batch_partial(self):
        """Test getting batch when fewer events available"""
        queue = EventQueue()
        
        for i in range(3):
            queue.put({'id': i})
        
        batch = queue.get_batch(10)
        
        assert len(batch) == 3
        assert queue.size() == 0
    
    def test_max_size_limit(self):
        """Test queue respects max size"""
        queue = EventQueue(max_size=5)
        
        for i in range(10):
            queue.put({'id': i})
        
        assert queue.size() == 5
        assert queue.is_full() is True
    
    def test_overflow_handling(self):
        """Test overflow handling (FIFO drop)"""
        queue = EventQueue(max_size=3)
        
        queue.put({'id': 1})
        queue.put({'id': 2})
        queue.put({'id': 3})
        queue.put({'id': 4})  # Should drop id=1
        
        assert queue.size() == 3
        assert queue.dropped_count == 1
        
        # Verify oldest was dropped
        event = queue.get()
        assert event['id'] == 2
    
    def test_clear_queue(self):
        """Test clearing queue"""
        queue = EventQueue()
        
        for i in range(10):
            queue.put({'id': i})
        
        assert queue.size() == 10
        
        queue.clear()
        
        assert queue.size() == 0
        assert queue.is_empty() is True
    
    def test_get_stats(self):
        """Test getting queue statistics"""
        queue = EventQueue(max_size=100)
        
        for i in range(50):
            queue.put({'id': i})
        
        stats = queue.get_stats()
        
        assert stats['current_size'] == 50
        assert stats['max_size'] == 100
        assert stats['total_events'] == 50
        assert stats['is_empty'] is False
        assert stats['is_full'] is False
        assert stats['utilization'] == 0.5
    
    def test_thread_safety_put(self):
        """Test thread-safe put operations"""
        queue = EventQueue(max_size=1000)
        
        def add_events(start_id, count):
            for i in range(count):
                queue.put({'id': start_id + i})
        
        threads = []
        for i in range(5):
            t = threading.Thread(target=add_events, args=(i * 100, 100))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        assert queue.size() == 500
    
    def test_thread_safety_get(self):
        """Test thread-safe get operations"""
        queue = EventQueue()
        
        # Add events
        for i in range(100):
            queue.put({'id': i})
        
        retrieved = []
        lock = threading.Lock()
        
        def get_events(count):
            for _ in range(count):
                event = queue.get()
                if event:
                    with lock:
                        retrieved.append(event)
        
        threads = []
        for i in range(5):
            t = threading.Thread(target=get_events, args=(20,))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        assert len(retrieved) == 100
        assert queue.size() == 0
    
    def test_is_empty(self):
        """Test is_empty check"""
        queue = EventQueue()
        
        assert queue.is_empty() is True
        
        queue.put({'id': 1})
        assert queue.is_empty() is False
        
        queue.get()
        assert queue.is_empty() is True
    
    def test_is_full(self):
        """Test is_full check"""
        queue = EventQueue(max_size=2)
        
        assert queue.is_full() is False
        
        queue.put({'id': 1})
        assert queue.is_full() is False
        
        queue.put({'id': 2})
        assert queue.is_full() is True
