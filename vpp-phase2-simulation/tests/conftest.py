"""
Pytest configuration and fixtures for VPP Phase 2 Simulation Framework.

Provides common fixtures for testing.
"""

import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Set testing environment BEFORE importing config
os.environ["ENV"] = "testing"

from config import config
from models.base import Base
from models.scenario import Scenario, ScenarioStatus
from utils.database import SessionLocal, engine as db_engine, init_db
from datetime import datetime


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Set up test database for all tests."""
    # Initialize database tables on the global engine
    init_db()
    yield
    # Clean up after all tests
    from utils.database import drop_db
    drop_db()


@pytest.fixture
def db_session():
    """Create test database session."""
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def test_scenario(db_session, request):
    """Create a test scenario in the database."""
    import uuid
    scenario = Scenario(
        id=f"test-scenario-{uuid.uuid4().hex[:8]}",
        name="Test Scenario",
        description="Test scenario for metrics",
        definition={},
        status=ScenarioStatus.RUNNING.value,
        start_time=datetime.utcnow()
    )
    db_session.add(scenario)
    db_session.commit()
    
    yield scenario
    
    # Clean up after test
    try:
        db_session.delete(scenario)
        db_session.commit()
    except:
        pass


@pytest.fixture
def app():
    """Create test app."""
    import sys
    import importlib.util
    
    # Load app.py directly
    spec = importlib.util.spec_from_file_location("app_module", os.path.join(os.path.dirname(os.path.dirname(__file__)), "app.py"))
    app_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(app_module)
    
    test_app = app_module.create_app()
    test_app.catchall = False
    return test_app


@pytest.fixture
def client(app):
    """Create test client."""
    from bottle import request as bottle_request
    
    class TestClient:
        def __init__(self, app):
            self.app = app
        
        def get(self, path, **kwargs):
            return self.app.get(path, **kwargs)
        
        def post(self, path, **kwargs):
            return self.app.post(path, **kwargs)
        
        def put(self, path, **kwargs):
            return self.app.put(path, **kwargs)
        
        def delete(self, path, **kwargs):
            return self.app.delete(path, **kwargs)
    
    return TestClient(app)
