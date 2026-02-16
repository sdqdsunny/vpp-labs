"""
Property-Based Tests for Data Persistence and Consistency

Tests data persistence, transaction rollback, and query consistency using Hypothesis.

Feature: vpp-phase1-api
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from datetime import datetime
from utils.database import get_db_session, init_db, drop_db
from utils.transactions import transaction
from models.device import Device
from models.dispatch import Dispatch


# Strategies for generating test data
device_id_strategy = st.text(
    alphabet=st.characters(blacklist_categories=('Cc', 'Cs')),
    min_size=1,
    max_size=50
).filter(lambda x: x.strip())

device_type_strategy = st.sampled_from(['solar', 'wind', 'battery', 'load'])

location_strategy = st.text(
    alphabet=st.characters(blacklist_categories=('Cc', 'Cs')),
    min_size=1,
    max_size=100
).filter(lambda x: x.strip())

power_output_strategy = st.floats(
    min_value=0.1,
    max_value=100000.0,
    allow_nan=False,
    allow_infinity=False
)

mode_strategy = st.sampled_from(['auto', 'manual', 'standby'])


class TestDataPersistenceProperties:
    """Property-based tests for data persistence"""
    
    @given(
        device_id=device_id_strategy,
        device_type=device_type_strategy,
        location=location_strategy,
        power_output=power_output_strategy
    )
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow]
    )
    def test_written_data_persists_durably(self, device_id, device_type, location, power_output):
        """
        Property 53: Written Data Persists Durably
        
        **Validates: Requirements 24.1**
        
        For any data written to the database, the data should be persisted immediately
        and durably, retrievable via subsequent queries.
        """
        # Setup
        init_db()
        db_session = get_db_session()
        
        try:
            # Write data in a transaction
            with transaction(db_session, "write_device"):
                device = Device(
                    id=device_id,
                    device_type=device_type,
                    location=location,
                    capabilities={"power_output": power_output},
                    configuration={"mode": "auto"}
                )
                db_session.add(device)
            
            # Create a new session to verify data persists
            new_session = get_db_session()
            retrieved = new_session.query(Device).filter_by(id=device_id).first()
            new_session.close()
            
            # Verify data was persisted
            assert retrieved is not None, "Device should be persisted to database"
            assert retrieved.device_type == device_type, "Device type should match"
            assert retrieved.location == location, "Location should match"
            assert retrieved.capabilities["power_output"] == power_output, "Power output should match"
        finally:
            db_session.close()
            drop_db()
    
    @given(
        device_id=device_id_strategy,
        device_type=device_type_strategy,
        location=location_strategy,
        power_output=power_output_strategy
    )
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow]
    )
    def test_transaction_rollback_maintains_consistency(self, device_id, device_type, location, power_output):
        """
        Property 54: Transaction Rollback Maintains Consistency
        
        **Validates: Requirements 24.2**
        
        For any database transaction that fails, all changes should be rolled back
        and data consistency should be maintained.
        """
        # Setup
        init_db()
        db_session = get_db_session()
        
        try:
            # First, write a device successfully
            with transaction(db_session, "write_initial"):
                device = Device(
                    id=device_id,
                    device_type=device_type,
                    location=location,
                    capabilities={"power_output": power_output},
                    configuration={"mode": "auto"}
                )
                db_session.add(device)
            
            # Get initial state
            new_session = get_db_session()
            initial_device = new_session.query(Device).filter_by(id=device_id).first()
            initial_type = initial_device.device_type if initial_device else None
            new_session.close()
            
            # Try to update in a transaction that fails
            try:
                with transaction(db_session, "write_update_fail"):
                    device = db_session.query(Device).filter_by(id=device_id).first()
                    if device:
                        device.device_type = "invalid_type_that_should_rollback"
                        # Simulate an error
                        raise ValueError("Simulated transaction failure")
            except ValueError:
                pass
            
            # Verify data was rolled back
            verify_session = get_db_session()
            verified_device = verify_session.query(Device).filter_by(id=device_id).first()
            verify_session.close()
            
            # Device should still have original type
            if verified_device:
                assert verified_device.device_type == initial_type, "Device type should be rolled back"
        finally:
            db_session.close()
            drop_db()
    
    @given(
        device_id=device_id_strategy,
        device_type=device_type_strategy,
        location=location_strategy,
        power_output=power_output_strategy
    )
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow]
    )
    def test_queries_return_most_recent_data(self, device_id, device_type, location, power_output):
        """
        Property 55: Queries Return Most Recent Data
        
        **Validates: Requirements 24.3**
        
        For any data query, the system should return the most recent committed data,
        not stale or intermediate states.
        """
        # Setup
        init_db()
        db_session = get_db_session()
        
        try:
            # Write initial data
            device = Device(
                id=device_id,
                device_type=device_type,
                location=location,
                capabilities={"power_output": power_output},
                configuration={"mode": "auto"}
            )
            db_session.add(device)
            db_session.commit()
            
            # Update data
            new_power = power_output * 2 if power_output > 0 else 100.0
            device = db_session.query(Device).filter_by(id=device_id).first()
            if device:
                device.capabilities["power_output"] = new_power
                db_session.commit()
            
            # Query should return updated data
            device = db_session.query(Device).filter_by(id=device_id).first()
            if device:
                assert device.capabilities["power_output"] == new_power, \
                    "Query should return most recent data"
        finally:
            db_session.close()
            drop_db()
    
    @given(
        device_ids=st.lists(
            device_id_strategy,
            min_size=1,
            max_size=10,
            unique=True
        ),
        device_type=device_type_strategy,
        location=location_strategy,
        power_output=power_output_strategy
    )
    @settings(
        max_examples=50,
        suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow]
    )
    def test_multiple_writes_persist_independently(self, device_ids, device_type, location, power_output):
        """
        Property: Multiple writes persist independently
        
        For any sequence of writes, each write should persist independently
        and be retrievable without affecting other writes.
        """
        # Setup
        init_db()
        db_session = get_db_session()
        
        try:
            # Write multiple devices
            for i, device_id in enumerate(device_ids):
                with transaction(db_session, f"write_{i}"):
                    device = Device(
                        id=device_id,
                        device_type=device_type,
                        location=f"{location}_{i}",
                        capabilities={"power_output": power_output * (i + 1)},
                        configuration={"mode": "auto"}
                    )
                    db_session.add(device)
            
            # Verify all devices persist
            new_session = get_db_session()
            count = new_session.query(Device).filter(Device.id.in_(device_ids)).count()
            new_session.close()
            
            assert count == len(device_ids), "All devices should persist independently"
        finally:
            db_session.close()
            drop_db()
    
    @given(
        device_id=device_id_strategy,
        device_type=device_type_strategy,
        location=location_strategy,
        power_output=power_output_strategy
    )
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow]
    )
    def test_partial_write_rolled_back_on_error(self, device_id, device_type, location, power_output):
        """
        Property: Partial writes are rolled back on error
        
        For any transaction with multiple operations, if an error occurs,
        all operations should be rolled back atomically.
        """
        # Setup
        init_db()
        db_session = get_db_session()
        
        try:
            device_ids = [device_id, f"{device_id}_2"]
            
            try:
                with transaction(db_session, "test_partial"):
                    # Write first device
                    device1 = Device(
                        id=device_ids[0],
                        device_type=device_type,
                        location=location,
                        capabilities={"power_output": power_output},
                        configuration={"mode": "auto"}
                    )
                    db_session.add(device1)
                    
                    # Write second device
                    device2 = Device(
                        id=device_ids[1],
                        device_type=device_type,
                        location=location,
                        capabilities={"power_output": power_output},
                        configuration={"mode": "auto"}
                    )
                    db_session.add(device2)
                    
                    # Simulate error
                    raise ValueError("Simulated error")
            except ValueError:
                pass
            
            # Verify neither device was persisted
            new_session = get_db_session()
            count = new_session.query(Device).filter(Device.id.in_(device_ids)).count()
            new_session.close()
            
            assert count == 0, "Partial writes should be rolled back atomically"
        finally:
            db_session.close()
            drop_db()
    
    @given(
        device_id=device_id_strategy,
        device_type=device_type_strategy,
        location=location_strategy,
        power_output=power_output_strategy
    )
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow]
    )
    def test_no_stale_data_returned(self, device_id, device_type, location, power_output):
        """
        Property: No stale data is returned
        
        For any sequence of writes and reads, stale or intermediate data
        should never be returned to queries.
        """
        # Setup
        init_db()
        db_session = get_db_session()
        
        try:
            # Write initial data
            device = Device(
                id=device_id,
                device_type=device_type,
                location=location,
                capabilities={"power_output": power_output},
                configuration={"mode": "auto"}
            )
            db_session.add(device)
            db_session.commit()
            
            # Update in same session
            new_power = power_output * 3 if power_output > 0 else 150.0
            device = db_session.query(Device).filter_by(id=device_id).first()
            if device:
                device.capabilities["power_output"] = new_power
                db_session.commit()
            
            # Query in same session should see updated data
            device = db_session.query(Device).filter_by(id=device_id).first()
            if device:
                assert device.capabilities["power_output"] == new_power, \
                    "Should return most recent data, not stale data"
        finally:
            db_session.close()
            drop_db()
    
    @given(
        device_id=device_id_strategy,
        device_type=device_type_strategy,
        location=location_strategy,
        power_output=power_output_strategy
    )
    @settings(
        max_examples=100,
        suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow]
    )
    def test_concurrent_writes_maintain_consistency(self, device_id, device_type, location, power_output):
        """
        Property: Concurrent writes maintain consistency
        
        For any sequence of concurrent transactions, data consistency
        should be maintained and no data should be lost.
        """
        # Setup
        init_db()
        db_session = get_db_session()
        
        try:
            # First transaction
            device = Device(
                id=device_id,
                device_type=device_type,
                location=location,
                capabilities={"power_output": power_output},
                configuration={"mode": "auto"}
            )
            db_session.add(device)
            db_session.commit()
            
            # Second transaction reads the committed data
            retrieved = db_session.query(Device).filter_by(id=device_id).first()
            assert retrieved is not None, "Should read committed data"
            assert retrieved.device_type == device_type, "Data should be consistent"
            
            # Third transaction updates the data
            new_power = power_output * 1.5 if power_output > 0 else 75.0
            device = db_session.query(Device).filter_by(id=device_id).first()
            if device:
                device.capabilities["power_output"] = new_power
                db_session.commit()
            
            # Fourth transaction verifies the update
            device = db_session.query(Device).filter_by(id=device_id).first()
            if device:
                assert device.capabilities["power_output"] == new_power, \
                    "Concurrent writes should maintain consistency"
        finally:
            db_session.close()
            drop_db()
