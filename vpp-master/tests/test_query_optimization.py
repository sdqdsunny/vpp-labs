"""
Unit Tests for Query Optimization

Tests database query optimization including indexes, caching, and performance.
"""

import pytest
import time
from datetime import datetime, timedelta
from utils.query_cache import QueryCache, cached_query, clear_all_cache, get_cache_stats
from utils.query_optimizer import QueryOptimizer
from models.device import Device
from models.dispatch import Dispatch
from models.protocol_mapping import ProtocolMapping
from models.analysis_result import AnalysisResult
from utils.database import get_db_session, init_db, drop_db
import uuid


@pytest.fixture(scope="function")
def setup_db():
    """Setup and teardown database for tests."""
    drop_db()
    init_db()
    yield
    drop_db()


class TestQueryCache:
    """Test query caching functionality."""
    
    def test_cache_set_and_get(self):
        """Test basic cache set and get operations."""
        cache = QueryCache(default_ttl_seconds=300)
        
        cache.set("test_key", "test_value")
        result = cache.get("test_key")
        
        assert result == "test_value"
    
    def test_cache_miss(self):
        """Test cache miss returns None."""
        cache = QueryCache(default_ttl_seconds=300)
        
        result = cache.get("nonexistent_key")
        
        assert result is None
    
    def test_cache_expiration(self):
        """Test cache entries expire after TTL."""
        cache = QueryCache(default_ttl_seconds=1)
        
        cache.set("test_key", "test_value")
        assert cache.get("test_key") == "test_value"
        
        # Wait for expiration
        time.sleep(1.1)
        result = cache.get("test_key")
        
        assert result is None
    
    def test_cache_invalidation(self):
        """Test cache entry invalidation."""
        cache = QueryCache(default_ttl_seconds=300)
        
        cache.set("test_key", "test_value")
        cache.invalidate("test_key")
        result = cache.get("test_key")
        
        assert result is None
    
    def test_cache_clear(self):
        """Test clearing all cache entries."""
        cache = QueryCache(default_ttl_seconds=300)
        
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.clear()
        
        assert cache.get("key1") is None
        assert cache.get("key2") is None
    
    def test_cache_statistics(self):
        """Test cache statistics tracking."""
        cache = QueryCache(default_ttl_seconds=300)
        
        cache.set("test_key", "test_value")
        cache.get("test_key")  # Hit
        cache.get("test_key")  # Hit
        cache.get("nonexistent")  # Miss
        
        stats = cache.get_stats()
        
        assert stats['hits'] == 2
        assert stats['misses'] == 1
        assert stats['total_requests'] == 3
        assert stats['hit_rate'] == pytest.approx(66.67, rel=1)
    
    def test_cache_key_generation(self):
        """Test cache key generation from function arguments."""
        cache = QueryCache()
        
        key1 = cache._generate_key("func", (1, 2), {"a": 1})
        key2 = cache._generate_key("func", (1, 2), {"a": 1})
        key3 = cache._generate_key("func", (1, 3), {"a": 1})
        
        assert key1 == key2  # Same arguments should generate same key
        assert key1 != key3  # Different arguments should generate different key


class TestQueryOptimization:
    """Test query optimization with database."""
    
    def test_device_query_with_index(self, setup_db):
        """Test device queries use indexes efficiently."""
        session = get_db_session()
        
        # Create test devices
        for i in range(10):
            device = Device(
                id=f"device-{i}",
                device_type="solar" if i % 2 == 0 else "wind",
                location=f"location-{i % 3}",
                status="online" if i % 2 == 0 else "offline",
                capabilities={},
                configuration={}
            )
            session.add(device)
        
        session.commit()
        
        # Query by indexed field
        start_time = time.time()
        devices = session.query(Device).filter(Device.device_type == "solar").all()
        query_time = time.time() - start_time
        
        assert len(devices) == 5
        assert query_time < 0.1  # Should be fast with index
        
        session.close()
    
    def test_dispatch_query_with_index(self, setup_db):
        """Test dispatch queries use indexes efficiently."""
        session = get_db_session()
        
        # Create test device
        device = Device(
            id="device-1",
            device_type="solar",
            location="location-1",
            status="online",
            capabilities={},
            configuration={}
        )
        session.add(device)
        session.commit()
        
        # Create test dispatches
        for i in range(20):
            dispatch = Dispatch(
                id=f"dispatch-{i}",
                device_id="device-1",
                command_type="power_adjust",
                target_value=100.0,
                priority_level=0,
                status="pending" if i % 2 == 0 else "completed"
            )
            session.add(dispatch)
        
        session.commit()
        
        # Query by indexed field
        start_time = time.time()
        dispatches = session.query(Dispatch).filter(Dispatch.status == "pending").all()
        query_time = time.time() - start_time
        
        assert len(dispatches) == 10
        assert query_time < 0.1  # Should be fast with index
        
        session.close()
    
    def test_protocol_mapping_query_with_index(self, setup_db):
        """Test protocol mapping queries use indexes efficiently."""
        session = get_db_session()
        
        # Create test protocol mappings
        for i in range(10):
            mapping = ProtocolMapping(
                id=f"mapping-{i}",
                source_protocol="iec_104",
                target_protocol="mqtt",
                mapping_rules={},
                is_active=True
            )
            session.add(mapping)
        
        session.commit()
        
        # Query by indexed field
        start_time = time.time()
        mappings = session.query(ProtocolMapping).filter(
            ProtocolMapping.source_protocol == "iec_104"
        ).all()
        query_time = time.time() - start_time
        
        assert len(mappings) == 10
        assert query_time < 0.1  # Should be fast with index
        
        session.close()
    
    def test_analysis_result_query_with_index(self, setup_db):
        """Test analysis result queries use indexes efficiently."""
        session = get_db_session()
        
        # Create test analysis results
        for i in range(15):
            result = AnalysisResult(
                id=f"analysis-{i}",
                analysis_type="power_flow" if i % 2 == 0 else "stability",
                system_state={},
                result_data={},
                status="completed",
                execution_time_ms=100
            )
            session.add(result)
        
        session.commit()
        
        # Query by indexed field
        start_time = time.time()
        results = session.query(AnalysisResult).filter(
            AnalysisResult.analysis_type == "power_flow"
        ).all()
        query_time = time.time() - start_time
        
        assert len(results) == 8
        assert query_time < 0.1  # Should be fast with index
        
        session.close()
    
    def test_composite_index_query(self, setup_db):
        """Test queries using composite indexes."""
        session = get_db_session()
        
        # Create test device
        device = Device(
            id="device-1",
            device_type="solar",
            location="location-1",
            status="online",
            capabilities={},
            configuration={}
        )
        session.add(device)
        session.commit()
        
        # Create test dispatches
        for i in range(20):
            dispatch = Dispatch(
                id=f"dispatch-{i}",
                device_id="device-1",
                command_type="power_adjust",
                target_value=100.0,
                priority_level=0,
                status="pending" if i % 2 == 0 else "completed"
            )
            session.add(dispatch)
        
        session.commit()
        
        # Query using composite index (device_id, status)
        start_time = time.time()
        dispatches = session.query(Dispatch).filter(
            Dispatch.device_id == "device-1",
            Dispatch.status == "pending"
        ).all()
        query_time = time.time() - start_time
        
        assert len(dispatches) == 10
        assert query_time < 0.1  # Should be fast with composite index
        
        session.close()
    
    def test_cached_query_decorator(self, setup_db):
        """Test cached query decorator functionality."""
        clear_all_cache()
        
        session = get_db_session()
        
        # Create test devices
        for i in range(5):
            device = Device(
                id=f"device-{i}",
                device_type="solar",
                location="location-1",
                status="online",
                capabilities={},
                configuration={}
            )
            session.add(device)
        
        session.commit()
        
        # First call should hit database
        start_time = time.time()
        devices1 = QueryOptimizer.get_all_devices(session)
        first_call_time = time.time() - start_time
        
        # Second call should hit cache
        start_time = time.time()
        devices2 = QueryOptimizer.get_all_devices(session)
        second_call_time = time.time() - start_time
        
        assert len(devices1) == 5
        assert len(devices2) == 5
        assert second_call_time < first_call_time  # Cache should be faster
        
        stats = get_cache_stats()
        assert stats['hits'] >= 1
        
        session.close()
        clear_all_cache()
    
    def test_cache_invalidation_on_update(self, setup_db):
        """Test cache invalidation when data is updated."""
        clear_all_cache()
        
        session = get_db_session()
        
        # Create test device
        device = Device(
            id="device-1",
            device_type="solar",
            location="location-1",
            status="online",
            capabilities={},
            configuration={}
        )
        session.add(device)
        session.commit()
        
        # Get devices (should cache)
        devices1 = QueryOptimizer.get_all_devices(session)
        assert len(devices1) == 1
        
        # Invalidate cache
        QueryOptimizer.invalidate_device_cache()
        
        # Add another device
        device2 = Device(
            id="device-2",
            device_type="wind",
            location="location-2",
            status="online",
            capabilities={},
            configuration={}
        )
        session.add(device2)
        session.commit()
        
        # Get devices again (should not use stale cache)
        devices2 = QueryOptimizer.get_all_devices(session)
        assert len(devices2) == 2
        
        session.close()
        clear_all_cache()
    
    def test_query_performance_with_large_dataset(self, setup_db):
        """Test query performance with larger dataset."""
        session = get_db_session()
        
        # Create 100 devices
        for i in range(100):
            device = Device(
                id=f"device-{i}",
                device_type="solar" if i % 3 == 0 else ("wind" if i % 3 == 1 else "battery"),
                location=f"location-{i % 10}",
                status="online" if i % 2 == 0 else "offline",
                capabilities={},
                configuration={}
            )
            session.add(device)
        
        session.commit()
        
        # Query should complete quickly even with 100 devices
        start_time = time.time()
        devices = session.query(Device).filter(Device.device_type == "solar").all()
        query_time = time.time() - start_time
        
        assert len(devices) > 0
        assert query_time < 0.5  # Should be fast with index
        
        session.close()
    
    def test_dispatch_history_query_performance(self, setup_db):
        """Test dispatch history query performance."""
        session = get_db_session()
        
        # Create test device
        device = Device(
            id="device-1",
            device_type="solar",
            location="location-1",
            status="online",
            capabilities={},
            configuration={}
        )
        session.add(device)
        session.commit()
        
        # Create 100 dispatches
        for i in range(100):
            dispatch = Dispatch(
                id=f"dispatch-{i}",
                device_id="device-1",
                command_type="power_adjust",
                target_value=100.0,
                priority_level=0,
                status="completed"
            )
            session.add(dispatch)
        
        session.commit()
        
        # Query history should be fast
        start_time = time.time()
        history = QueryOptimizer.get_dispatch_history(session, device_id="device-1", days=7)
        query_time = time.time() - start_time
        
        assert len(history) == 100
        assert query_time < 0.5  # Should complete within 500ms
        
        session.close()
