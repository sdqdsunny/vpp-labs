"""
Pytest Configuration and Fixtures

Provides test database setup, fixtures, and configuration for all tests.
"""

import sys
import os
import pytest
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set test environment
os.environ['ENVIRONMENT'] = 'test'
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ['DEBUG'] = 'False'

from utils.database import Base, engine, SessionLocal, init_db, drop_db
from models.device import Device
from models.dispatch import Dispatch
from models.protocol_mapping import ProtocolMapping
from models.analysis_result import AnalysisResult


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """
    Setup test database for the entire test session
    
    Creates all tables and cleans up after tests complete.
    """
    # Create all tables
    init_db()
    
    yield
    
    # Cleanup after all tests
    drop_db()


@pytest.fixture(autouse=True)
def clear_database():
    """
    Clear database before each test
    
    Ensures test isolation by removing all data before each test.
    """
    # Clear all tables
    try:
        for table in reversed(Base.metadata.sorted_tables):
            SessionLocal.execute(table.delete())
        SessionLocal.commit()
    except Exception:
        # If tables don't exist yet, just continue
        SessionLocal.rollback()
    
    yield
    
    # Cleanup after test
    try:
        SessionLocal.rollback()
    except Exception:
        pass


@pytest.fixture
def db_session():
    """
    Provide a database session for tests
    
    Yields:
        SQLAlchemy Session instance
    """
    session = SessionLocal()
    
    yield session
    
    session.close()


@pytest.fixture
def sample_device(db_session):
    """
    Create a sample device for testing
    
    Returns:
        Device instance
    """
    device = Device(
        id="test-device-001",
        device_type="solar",
        location="Test Location",
        capabilities={"power": 100.0},
        configuration={},
        status="offline"
    )
    db_session.add(device)
    db_session.commit()
    
    return device


@pytest.fixture
def sample_devices(db_session):
    """
    Create multiple sample devices for testing
    
    Returns:
        List of Device instances
    """
    devices = []
    for i in range(5):
        device = Device(
            id=f"test-device-{i:03d}",
            device_type="solar" if i % 2 == 0 else "wind",
            location=f"Test Location {i}",
            capabilities={"power": 100.0 * (i + 1)},
            configuration={},
            status="offline"
        )
        db_session.add(device)
        devices.append(device)
    
    db_session.commit()
    
    return devices


@pytest.fixture
def sample_dispatch(db_session, sample_device):
    """
    Create a sample dispatch for testing
    
    Returns:
        Dispatch instance
    """
    dispatch = Dispatch(
        id="test-dispatch-001",
        device_id=sample_device.id,
        command="start",
        parameters={"power": 50.0},
        status="pending",
        retry_count=0,
        max_retries=3
    )
    db_session.add(dispatch)
    db_session.commit()
    
    return dispatch


@pytest.fixture
def sample_protocol_mapping(db_session):
    """
    Create a sample protocol mapping for testing
    
    Returns:
        ProtocolMapping instance
    """
    mapping = ProtocolMapping(
        id="test-mapping-001",
        source_protocol="iec104",
        target_protocol="mqtt",
        mapping_rules={"field1": "field2"},
        is_active=True
    )
    db_session.add(mapping)
    db_session.commit()
    
    return mapping


@pytest.fixture
def sample_analysis_result(db_session, sample_device):
    """
    Create a sample analysis result for testing
    
    Returns:
        AnalysisResult instance
    """
    result = AnalysisResult(
        id="test-analysis-001",
        device_id=sample_device.id,
        analysis_type="power_flow",
        result_data={"voltage": 380, "current": 100},
        status="completed"
    )
    db_session.add(result)
    db_session.commit()
    
    return result
