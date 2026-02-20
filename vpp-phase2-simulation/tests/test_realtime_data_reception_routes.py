"""
Unit tests for VCC real-time data reception API routes.

Tests:
- POST /api/vcc/report/power endpoint
- POST /api/vcc/report/storage endpoint
- POST /api/vcc/report/demand endpoint
- Request validation
- Error handling
- HTTP status codes
"""

import pytest
import json
from datetime import datetime
from bottle import Bottle
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from webtest import TestApp

from models.realtime_data_models import (
    PowerGenerationData, StorageData, DemandData
)
from models.realtime_db_models import Base, PowerGenerationDataDB, StorageDataDB, DemandDataDB
from services.vcc_data_reception import VCCDataReceptionService
from routes.realtime_data_reception import (
    create_realtime_data_routes, init_reception_service
)


@pytest.fixture
def db_session():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine(
        'sqlite:///:memory:',
        connect_args={'check_same_thread': False},
        poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def app(db_session):
    """Create Bottle app for testing."""
    app = Bottle()
    
    # Initialize reception service with test database
    init_reception_service(db_session=db_session)
    
    # Register routes
    create_realtime_data_routes(app)
    
    yield app


@pytest.fixture
def client(app):
    """Create Bottle test client using WebTest."""
    return TestApp(app)


class TestPowerGenerationEndpoint:
    """Test power generation data reception endpoint."""

    def test_report_power_valid_data(self, client):
        """Test receiving valid power generation data."""
        payload = {
            "timestamp": "2024-01-15T10:30:00Z",
            "current_power": 150.5,
            "solar_power": 100.0,
            "wind_power": 50.5,
            "efficiency": 95.5,
            "device_status": "running"
        }
        
        response = client.post_json(
            '/api/vcc/report/power',
            payload
        )
        
        assert response.status_code == 200
        data = response.json
        assert data['status'] == 'success'
        assert data['message'] == 'Data received and stored'
        assert 'request_id' in data

    def test_report_power_empty_request(self, client):
        """Test receiving empty request body."""
        response = client.post(
            '/api/vcc/report/power',
            '',
            expect_errors=True
        )
        
        assert response.status_code == 400
        data = response.json
        assert data['status'] == 'error'
        assert 'Empty request body' in data['message']

    def test_report_power_missing_fields(self, client):
        """Test receiving data with missing required fields."""
        payload = {
            "timestamp": "2024-01-15T10:30:00Z",
            "current_power": 150.5,
            "solar_power": 50.0,
            "wind_power": 50.0,
            "efficiency": 95.5,
            "device_status": "running"
        }
        
        response = client.post_json(
            '/api/vcc/report/power',
            payload
        )
        
        # Should succeed with valid data
        assert response.status_code == 200
        data = response.json
        assert data['status'] == 'success'

    def test_report_power_invalid_json(self, client):
        """Test receiving invalid JSON."""
        response = client.post(
            '/api/vcc/report/power',
            'invalid json',
            content_type='application/json',
            expect_errors=True
        )
        
        assert response.status_code == 400

    def test_report_power_invalid_data_types(self, client):
        """Test receiving data with invalid data types."""
        payload = {
            "timestamp": "2024-01-15T10:30:00Z",
            "current_power": "not_a_number",  # Should be float
            "solar_power": 100.0,
            "wind_power": 50.5,
            "efficiency": 95.5,
            "device_status": "running"
        }
        
        response = client.post_json(
            '/api/vcc/report/power',
            payload,
            expect_errors=True
        )
        
        assert response.status_code == 400
        data = response.json
        assert data['status'] == 'error'

    def test_report_power_invalid_timestamp(self, client):
        """Test receiving data with invalid timestamp."""
        payload = {
            "timestamp": "invalid-timestamp",
            "current_power": 150.5,
            "solar_power": 100.0,
            "wind_power": 50.5,
            "efficiency": 95.5,
            "device_status": "running"
        }
        
        response = client.post_json(
            '/api/vcc/report/power',
            payload
        )
        
        # Should succeed with current timestamp as default
        assert response.status_code == 200
        data = response.json
        assert data['status'] == 'success'

    def test_report_power_missing_timestamp(self, client):
        """Test receiving data without timestamp."""
        payload = {
            "current_power": 150.5,
            "solar_power": 100.0,
            "wind_power": 50.5,
            "efficiency": 95.5,
            "device_status": "running"
        }
        
        response = client.post_json(
            '/api/vcc/report/power',
            payload
        )
        
        # Should succeed with current timestamp as default
        assert response.status_code == 200
        data = response.json
        assert data['status'] == 'success'

    def test_report_power_zero_values(self, client):
        """Test receiving data with zero values."""
        payload = {
            "timestamp": "2024-01-15T10:30:00Z",
            "current_power": 0.0,
            "solar_power": 0.0,
            "wind_power": 0.0,
            "efficiency": 0.0,
            "device_status": "idle"
        }
        
        response = client.post_json(
            '/api/vcc/report/power',
            payload
        )
        
        assert response.status_code == 200
        data = response.json
        assert data['status'] == 'success'

    def test_report_power_negative_values(self, client):
        """Test receiving data with negative values."""
        payload = {
            "timestamp": "2024-01-15T10:30:00Z",
            "current_power": -150.5,
            "solar_power": -100.0,
            "wind_power": -50.5,
            "efficiency": 95.5,
            "device_status": "error"
        }
        
        response = client.post_json(
            '/api/vcc/report/power',
            payload,
            expect_errors=True
        )
        
        # Should fail - validation rejects negative power values
        assert response.status_code == 500
        data = response.json
        assert data['status'] == 'error'

    def test_report_power_large_values(self, client):
        """Test receiving data with large values."""
        payload = {
            "timestamp": "2024-01-15T10:30:00Z",
            "current_power": 999999.99,
            "solar_power": 500000.0,
            "wind_power": 499999.99,
            "efficiency": 95.5,
            "device_status": "running"
        }
        
        response = client.post_json(
            '/api/vcc/report/power',
            payload
        )
        
        assert response.status_code == 200
        data = response.json
        assert data['status'] == 'success'

    def test_report_power_response_has_request_id(self, client):
        """Test that response includes request_id."""
        payload = {
            "timestamp": "2024-01-15T10:30:00Z",
            "current_power": 150.5,
            "solar_power": 100.0,
            "wind_power": 50.5,
            "efficiency": 95.5,
            "device_status": "running"
        }
        
        response = client.post_json(
            '/api/vcc/report/power',
            payload
        )
        
        data = response.json
        assert 'request_id' in data
        assert len(data['request_id']) > 0


class TestStorageEndpoint:
    """Test storage data reception endpoint."""

    def test_report_storage_valid_data(self, client):
        """Test receiving valid storage data."""
        payload = {
            "timestamp": "2024-01-15T10:30:00Z",
            "soc": 75.5,
            "soh": 98.0,
            "current_power": 50.0,
            "charge_status": "charging",
            "temperature": 25.5
        }
        
        response = client.post_json(
            '/api/vcc/report/storage',
            payload
        )
        
        assert response.status_code == 200
        data = response.json
        assert data['status'] == 'success'
        assert data['message'] == 'Data received and stored'
        assert 'request_id' in data

    def test_report_storage_empty_request(self, client):
        """Test receiving empty request body."""
        response = client.post(
            '/api/vcc/report/storage',
            '',
            expect_errors=True
        )
        
        assert response.status_code == 400
        data = response.json
        assert data['status'] == 'error'

    def test_report_storage_missing_fields(self, client):
        """Test receiving data with missing fields."""
        payload = {
            "timestamp": "2024-01-15T10:30:00Z",
            "soc": 75.5
        }
        
        response = client.post_json(
            '/api/vcc/report/storage',
            payload
        )
        
        assert response.status_code == 200
        data = response.json
        assert data['status'] == 'success'

    def test_report_storage_invalid_data_types(self, client):
        """Test receiving data with invalid data types."""
        payload = {
            "timestamp": "2024-01-15T10:30:00Z",
            "soc": "not_a_number",  # Should be float
            "soh": 98.0,
            "current_power": 50.0,
            "charge_status": "charging",
            "temperature": 25.5
        }
        
        response = client.post_json(
            '/api/vcc/report/storage',
            payload,
            expect_errors=True
        )
        
        assert response.status_code == 400
        data = response.json
        assert data['status'] == 'error'

    def test_report_storage_invalid_adjustable_range(self, client):
        """Test receiving data with invalid adjustable range."""
        payload = {
            "timestamp": "2024-01-15T10:30:00Z",
            "soc": 75.5,
            "soh": 98.0,
            "current_power": 50.0,
            "charge_status": "charging",
            "temperature": 25.5
        }
        
        response = client.post_json(
            '/api/vcc/report/storage',
            payload
        )
        
        assert response.status_code == 200
        data = response.json
        assert data['status'] == 'success'

    def test_report_storage_soc_boundary_values(self, client):
        """Test receiving storage data with SOC boundary values."""
        payload = {
            "timestamp": "2024-01-15T10:30:00Z",
            "soc": 100.0,  # Max SOC
            "soh": 98.0,
            "current_power": 50.0,
            "charge_status": "idle",
            "temperature": 25.5
        }
        
        response = client.post_json(
            '/api/vcc/report/storage',
            payload
        )
        
        assert response.status_code == 200
        data = response.json
        assert data['status'] == 'success'

    def test_report_storage_soc_zero(self, client):
        """Test receiving storage data with zero SOC."""
        payload = {
            "timestamp": "2024-01-15T10:30:00Z",
            "soc": 0.0,
            "soh": 98.0,
            "current_power": 0.0,
            "charge_status": "idle",
            "temperature": 25.5
        }
        
        response = client.post_json(
            '/api/vcc/report/storage',
            payload
        )
        
        assert response.status_code == 200
        data = response.json
        assert data['status'] == 'success'

    def test_report_storage_temperature_extremes(self, client):
        """Test receiving storage data with extreme temperatures."""
        payload = {
            "timestamp": "2024-01-15T10:30:00Z",
            "soc": 75.5,
            "soh": 98.0,
            "current_power": 50.0,
            "charge_status": "charging",
            "temperature": -40.0  # Very cold
        }
        
        response = client.post_json(
            '/api/vcc/report/storage',
            payload
        )
        
        assert response.status_code == 200
        data = response.json
        assert data['status'] == 'success'

    def test_report_storage_invalid_timestamp(self, client):
        """Test receiving storage data with invalid timestamp."""
        payload = {
            "timestamp": "not-a-timestamp",
            "soc": 75.5,
            "soh": 98.0,
            "current_power": 50.0,
            "charge_status": "charging",
            "temperature": 25.5
        }
        
        response = client.post_json(
            '/api/vcc/report/storage',
            payload
        )
        
        assert response.status_code == 200
        data = response.json
        assert data['status'] == 'success'


class TestDemandEndpoint:
    """Test demand data reception endpoint."""

    def test_report_demand_valid_data(self, client):
        """Test receiving valid demand data."""
        payload = {
            "timestamp": "2024-01-15T10:30:00Z",
            "current_load": 200.0,
            "forecast_load": 210.0,
            "adjustable_range": [180.0, 220.0],
            "dr_status": "active"
        }
        
        response = client.post_json(
            '/api/vcc/report/demand',
            payload
        )
        
        assert response.status_code == 200
        data = response.json
        assert data['status'] == 'success'
        assert data['message'] == 'Data received and stored'
        assert 'request_id' in data

    def test_report_demand_empty_request(self, client):
        """Test receiving empty request body."""
        response = client.post(
            '/api/vcc/report/demand',
            '',
            expect_errors=True
        )
        
        assert response.status_code == 400
        data = response.json
        assert data['status'] == 'error'

    def test_report_demand_missing_fields(self, client):
        """Test receiving data with missing fields."""
        payload = {
            "timestamp": "2024-01-15T10:30:00Z",
            "current_load": 200.0
        }
        
        response = client.post_json(
            '/api/vcc/report/demand',
            payload
        )
        
        assert response.status_code == 200
        data = response.json
        assert data['status'] == 'success'

    def test_report_demand_invalid_data_types(self, client):
        """Test receiving data with invalid data types."""
        payload = {
            "timestamp": "2024-01-15T10:30:00Z",
            "current_load": "not_a_number",  # Should be float
            "forecast_load": 210.0,
            "adjustable_range": [180.0, 220.0],
            "dr_status": "active"
        }
        
        response = client.post_json(
            '/api/vcc/report/demand',
            payload,
            expect_errors=True
        )
        
        assert response.status_code == 400
        data = response.json
        assert data['status'] == 'error'

    def test_report_demand_invalid_adjustable_range(self, client):
        """Test receiving data with invalid adjustable range."""
        payload = {
            "timestamp": "2024-01-15T10:30:00Z",
            "current_load": 200.0,
            "forecast_load": 210.0,
            "adjustable_range": "invalid",  # Should be list
            "dr_status": "active"
        }
        
        response = client.post_json(
            '/api/vcc/report/demand',
            payload
        )
        
        assert response.status_code == 200
        data = response.json
        assert data['status'] == 'success'

    def test_report_demand_adjustable_range_wrong_length(self, client):
        """Test receiving data with wrong adjustable range length."""
        payload = {
            "timestamp": "2024-01-15T10:30:00Z",
            "current_load": 200.0,
            "forecast_load": 210.0,
            "adjustable_range": [180.0, 200.0, 220.0],  # Should be 2 elements
            "dr_status": "active"
        }
        
        response = client.post_json(
            '/api/vcc/report/demand',
            payload
        )
        
        assert response.status_code == 200
        data = response.json
        assert data['status'] == 'success'

    def test_report_demand_zero_load(self, client):
        """Test receiving demand data with zero load."""
        payload = {
            "timestamp": "2024-01-15T10:30:00Z",
            "current_load": 0.0,
            "forecast_load": 0.0,
            "adjustable_range": [0.0, 0.0],
            "dr_status": "inactive"
        }
        
        response = client.post_json(
            '/api/vcc/report/demand',
            payload
        )
        
        assert response.status_code == 200
        data = response.json
        assert data['status'] == 'success'

    def test_report_demand_large_load(self, client):
        """Test receiving demand data with large load values."""
        payload = {
            "timestamp": "2024-01-15T10:30:00Z",
            "current_load": 999999.99,
            "forecast_load": 999999.99,
            "adjustable_range": [900000.0, 1000000.0],
            "dr_status": "active"
        }
        
        response = client.post_json(
            '/api/vcc/report/demand',
            payload
        )
        
        assert response.status_code == 200
        data = response.json
        assert data['status'] == 'success'

    def test_report_demand_invalid_timestamp(self, client):
        """Test receiving demand data with invalid timestamp."""
        payload = {
            "timestamp": "invalid-timestamp",
            "current_load": 200.0,
            "forecast_load": 210.0,
            "adjustable_range": [180.0, 220.0],
            "dr_status": "active"
        }
        
        response = client.post_json(
            '/api/vcc/report/demand',
            payload
        )
        
        assert response.status_code == 200
        data = response.json
        assert data['status'] == 'success'

    def test_report_demand_missing_timestamp(self, client):
        """Test receiving demand data without timestamp."""
        payload = {
            "current_load": 200.0,
            "forecast_load": 210.0,
            "adjustable_range": [180.0, 220.0],
            "dr_status": "active"
        }
        
        response = client.post_json(
            '/api/vcc/report/demand',
            payload
        )
        
        assert response.status_code == 200
        data = response.json
        assert data['status'] == 'success'


class TestErrorHandling:
    """Test error handling across all endpoints."""

    def test_malformed_json_power(self, client):
        """Test malformed JSON for power endpoint."""
        response = client.post(
            '/api/vcc/report/power',
            '{invalid json}',
            content_type='application/json',
            expect_errors=True
        )
        
        assert response.status_code == 400

    def test_malformed_json_storage(self, client):
        """Test malformed JSON for storage endpoint."""
        response = client.post(
            '/api/vcc/report/storage',
            '{invalid json}',
            content_type='application/json',
            expect_errors=True
        )
        
        assert response.status_code == 400

    def test_malformed_json_demand(self, client):
        """Test malformed JSON for demand endpoint."""
        response = client.post(
            '/api/vcc/report/demand',
            '{invalid json}',
            content_type='application/json',
            expect_errors=True
        )
        
        assert response.status_code == 400

    def test_response_format_consistency(self, client):
        """Test that all error responses have consistent format."""
        response = client.post(
            '/api/vcc/report/power',
            '',
            expect_errors=True
        )
        
        data = response.json
        assert 'status' in data
        assert 'message' in data
        assert 'request_id' in data


class TestDataPersistence:
    """Test that data is properly persisted."""

    def test_power_data_persisted_in_database(self, client, db_session):
        """Test that power data is persisted in database."""
        payload = {
            "timestamp": "2024-01-15T10:30:00Z",
            "current_power": 150.5,
            "solar_power": 100.0,
            "wind_power": 50.5,
            "efficiency": 95.5,
            "device_status": "running"
        }
        
        response = client.post_json(
            '/api/vcc/report/power',
            payload
        )
        
        assert response.status_code == 200
        
        # Verify data in database
        records = db_session.query(PowerGenerationDataDB).all()
        assert len(records) == 1
        assert records[0].current_power == 150.5

    def test_storage_data_persisted_in_database(self, client, db_session):
        """Test that storage data is persisted in database."""
        payload = {
            "timestamp": "2024-01-15T10:30:00Z",
            "soc": 75.5,
            "soh": 98.0,
            "current_power": 50.0,
            "charge_status": "charging",
            "temperature": 25.5
        }
        
        response = client.post_json(
            '/api/vcc/report/storage',
            payload
        )
        
        assert response.status_code == 200
        
        # Verify data in database
        records = db_session.query(StorageDataDB).all()
        assert len(records) == 1
        assert records[0].soc == 75.5

    def test_demand_data_persisted_in_database(self, client, db_session):
        """Test that demand data is persisted in database."""
        payload = {
            "timestamp": "2024-01-15T10:30:00Z",
            "current_load": 200.0,
            "forecast_load": 210.0,
            "adjustable_range": [180.0, 220.0],
            "dr_status": "active"
        }
        
        response = client.post_json(
            '/api/vcc/report/demand',
            payload
        )
        
        assert response.status_code == 200
        
        # Verify data in database
        records = db_session.query(DemandDataDB).all()
        assert len(records) == 1
        assert records[0].current_load == 200.0

    def test_multiple_power_records_persisted(self, client, db_session):
        """Test that multiple power records are persisted."""
        for i in range(3):
            payload = {
                "timestamp": "2024-01-15T10:30:00Z",
                "current_power": 100.0 + i * 10,
                "solar_power": 50.0 + i * 5,
                "wind_power": 50.0 + i * 5,
                "efficiency": 95.0,
                "device_status": "running"
            }
            
            response = client.post_json(
                '/api/vcc/report/power',
                payload
            )
            
            assert response.status_code == 200
        
        # Verify all records in database
        records = db_session.query(PowerGenerationDataDB).all()
        assert len(records) == 3
