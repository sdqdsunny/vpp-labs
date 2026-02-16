"""
Property-Based Tests for Performance and Scalability

Tests performance properties using Hypothesis for property-based testing.
Feature: vpp-phase1-api
"""

import pytest
import time
from datetime import datetime
from hypothesis import given, strategies as st, settings, HealthCheck
from models.device import Device
from models.dispatch import Dispatch
from utils.database import get_db_session, init_db, drop_db
from utils.query_optimizer import QueryOptimizer
from utils.query_cache import clear_all_cache
import uuid


class TestPerformanceProperties:
    """Property-based tests for performance and scalability."""
    
    @given(
        num_devices=st.integers(min_value=100, max_value=1000),
        query_count=st.integers(min_value=1, max_value=10)
    )
    @settings(
        max_examples=10,
        suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture]
    )
    def test_device_queries_scale_to_1000_devices(self, num_devices, query_count):
        """
        Property 56: Device Queries Scale to 1000 Devices
        
        **Validates: Requirements 25.1**
        
        For any number of devices up to 1000, device queries should complete
        within 500ms response time.
        """
        # Setup fresh database for each example
        clear_all_cache()
        drop_db()
        init_db()
        
        session = get_db_session()
        
        # Create devices
        for i in range(num_devices):
            device = Device(
                id=f"device-{i}",
                device_type="solar" if i % 3 == 0 else ("wind" if i % 3 == 1 else "battery"),
                location=f"location-{i % 10}",
                status="online" if i % 2 == 0 else "offline",
                capabilities={"power_rating": 100 + i},
                configuration={"mode": "auto"}
            )
            session.add(device)
        
        session.commit()
        
        # Execute multiple queries and measure time
        total_time = 0
        for _ in range(query_count):
            start_time = time.time()
            devices = QueryOptimizer.get_all_devices(session)
            query_time = time.time() - start_time
            total_time += query_time
            
            # Each query should complete within 500ms
            assert query_time < 0.5, f"Query took {query_time}s, expected < 0.5s"
            assert len(devices) == num_devices
        
        # Average query time should be reasonable
        avg_time = total_time / query_count
        assert avg_time < 0.5, f"Average query time {avg_time}s, expected < 0.5s"
        
        session.close()
        drop_db()
        clear_all_cache()
    
    @given(
        num_devices=st.integers(min_value=10, max_value=100),
        commands_per_second=st.integers(min_value=10, max_value=100),
        duration_seconds=st.integers(min_value=1, max_value=5)
    )
    @settings(
        max_examples=5,
        suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture]
    )
    def test_high_frequency_dispatch_commands_process_without_loss(
        self, num_devices, commands_per_second, duration_seconds
    ):
        """
        Property 57: High-Frequency Dispatch Commands Process Without Loss
        
        **Validates: Requirements 25.2**
        
        For any sequence of dispatch commands issued at high frequency (up to 100/second),
        all commands should be processed and persisted without data loss.
        """
        # Setup fresh database for each example
        clear_all_cache()
        drop_db()
        init_db()
        
        session = get_db_session()
        
        # Create devices
        for i in range(num_devices):
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
        
        # Submit dispatch commands at high frequency
        total_commands = commands_per_second * duration_seconds
        submitted_commands = []
        
        start_time = time.time()
        for i in range(total_commands):
            device_id = f"device-{i % num_devices}"
            dispatch = Dispatch(
                id=f"dispatch-{i}",
                device_id=device_id,
                command_type="power_adjust",
                target_value=100.0 + i,
                priority_level=0,
                status="pending"
            )
            session.add(dispatch)
            submitted_commands.append(dispatch.id)
            
            # Commit periodically to simulate real-world behavior
            if (i + 1) % 10 == 0:
                session.commit()
        
        session.commit()
        elapsed_time = time.time() - start_time
        
        # Verify all commands were persisted
        persisted_count = session.query(Dispatch).count()
        assert persisted_count == total_commands, \
            f"Expected {total_commands} commands, got {persisted_count}"
        
        # Verify no data loss
        for dispatch_id in submitted_commands:
            dispatch = session.query(Dispatch).filter(Dispatch.id == dispatch_id).first()
            assert dispatch is not None, f"Dispatch {dispatch_id} not found"
        
        # Calculate throughput
        throughput = total_commands / elapsed_time
        assert throughput >= (commands_per_second * 0.8), \
            f"Throughput {throughput} commands/s, expected >= {commands_per_second * 0.8}"
        
        session.close()
        drop_db()
        clear_all_cache()
    
    @given(
        num_devices=st.integers(min_value=100, max_value=1000)
    )
    @settings(
        max_examples=10,
        suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture]
    )
    def test_status_query_completes_within_500ms(self, num_devices):
        """
        Property 58: Status Query Completes Within 500ms
        
        **Validates: Requirements 2.5**
        
        For any system with 1000+ devices, status queries for all devices
        should complete within 500ms response time.
        """
        # Setup fresh database for each example
        clear_all_cache()
        drop_db()
        init_db()
        
        session = get_db_session()
        
        # Create devices
        for i in range(num_devices):
            device = Device(
                id=f"device-{i}",
                device_type="solar",
                location="location-1",
                status="online" if i % 2 == 0 else "offline",
                capabilities={},
                configuration={}
            )
            session.add(device)
        
        session.commit()
        
        # Query all device statuses
        start_time = time.time()
        devices = QueryOptimizer.get_all_devices(session)
        query_time = time.time() - start_time
        
        # Verify query completed within 500ms
        assert query_time < 0.5, f"Status query took {query_time}s, expected < 0.5s"
        
        # Verify all devices were returned
        assert len(devices) == num_devices
        
        # Verify status information is present
        for device in devices:
            assert device.status in ["online", "offline", "error"]
        
        session.close()
        drop_db()
        clear_all_cache()
    
    @given(
        num_devices=st.integers(min_value=50, max_value=500),
        num_queries=st.integers(min_value=5, max_value=20)
    )
    @settings(
        max_examples=5,
        suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture]
    )
    def test_query_performance_consistency(self, num_devices, num_queries):
        """
        Property: Query Performance Consistency
        
        For any number of devices, repeated queries should have consistent
        performance (no significant degradation).
        """
        # Setup fresh database for each example
        clear_all_cache()
        drop_db()
        init_db()
        
        session = get_db_session()
        
        # Create devices
        for i in range(num_devices):
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
        
        # Execute multiple queries and track times
        query_times = []
        for idx in range(num_queries):
            session.expunge_all()  # Clear session cache
            start_time = time.time()
            devices = QueryOptimizer.get_all_devices(session)
            query_time = time.time() - start_time
            query_times.append(query_time)
            assert len(devices) == num_devices
        
        # Skip first query (it's often slower due to cache misses)
        if len(query_times) > 1:
            query_times = query_times[1:]
        
        # Calculate statistics
        if len(query_times) > 1:
            min_time = min(query_times)
            max_time = max(query_times)
            
            # Verify consistency: max time should not be more than 5x min time
            # (allowing for some variance due to system load)
            if min_time > 0:
                time_ratio = max_time / min_time
                assert time_ratio < 5.0, \
                    f"Query time variance too high: {time_ratio}x (min={min_time}s, max={max_time}s)"
        
        session.close()
        drop_db()
        clear_all_cache()
    
    @given(
        num_devices=st.integers(min_value=100, max_value=500),
        num_dispatches_per_device=st.integers(min_value=5, max_value=20)
    )
    @settings(
        max_examples=5,
        suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture]
    )
    def test_dispatch_history_query_performance(
        self, num_devices, num_dispatches_per_device
    ):
        """
        Property: Dispatch History Query Performance
        
        For any number of devices and dispatches, history queries should
        complete efficiently even with large datasets.
        """
        # Setup fresh database for each example
        clear_all_cache()
        drop_db()
        init_db()
        
        session = get_db_session()
        
        # Create devices
        for i in range(num_devices):
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
        
        # Create dispatches
        total_dispatches = 0
        for device_idx in range(num_devices):
            for dispatch_idx in range(num_dispatches_per_device):
                dispatch = Dispatch(
                    id=f"dispatch-{device_idx}-{dispatch_idx}",
                    device_id=f"device-{device_idx}",
                    command_type="power_adjust",
                    target_value=100.0,
                    priority_level=0,
                    status="completed"
                )
                session.add(dispatch)
                total_dispatches += 1
        
        session.commit()
        
        # Query dispatch history
        start_time = time.time()
        history = QueryOptimizer.get_dispatch_history(session, days=7)
        query_time = time.time() - start_time
        
        # Verify query completed efficiently (relaxed constraint for large datasets)
        assert query_time < 2.0, f"History query took {query_time}s, expected < 2.0s"
        assert len(history) == total_dispatches
        
        session.close()
        drop_db()
        clear_all_cache()
    
    @given(
        num_devices=st.integers(min_value=100, max_value=500)
    )
    @settings(
        max_examples=5,
        suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture]
    )
    def test_filtered_device_query_performance(self, num_devices):
        """
        Property: Filtered Device Query Performance
        
        For any number of devices, filtered queries (by type, status, location)
        should complete efficiently using indexes.
        """
        # Setup fresh database for each example
        clear_all_cache()
        drop_db()
        init_db()
        
        session = get_db_session()
        
        # Create devices with various types
        for i in range(num_devices):
            device = Device(
                id=f"device-{i}",
                device_type="solar" if i % 3 == 0 else ("wind" if i % 3 == 1 else "battery"),
                location=f"location-{i % 5}",
                status="online" if i % 2 == 0 else "offline",
                capabilities={},
                configuration={}
            )
            session.add(device)
        
        session.commit()
        
        # Test various filtered queries
        queries = [
            ("by_type", lambda: QueryOptimizer.get_devices_by_type(session, "solar")),
            ("by_status", lambda: QueryOptimizer.get_devices_by_status(session, "online")),
            ("by_location", lambda: QueryOptimizer.get_devices_by_location(session, "location-0")),
        ]
        
        for query_name, query_func in queries:
            start_time = time.time()
            results = query_func()
            query_time = time.time() - start_time
            
            # Each filtered query should complete within 500ms
            assert query_time < 0.5, \
                f"Filtered query ({query_name}) took {query_time}s, expected < 0.5s"
            assert len(results) > 0, f"Filtered query ({query_name}) returned no results"
        
        session.close()
        drop_db()
        clear_all_cache()
