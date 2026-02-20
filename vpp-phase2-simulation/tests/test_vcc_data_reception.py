"""
Unit tests for VCC data reception service.

Tests:
- Data reception and validation
- Database persistence
- Cache management
- Error handling
"""

import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from models.realtime_data_models import (
    PowerGenerationData, StorageData, DemandData
)
from models.realtime_db_models import Base, PowerGenerationDataDB, StorageDataDB, DemandDataDB
from services.vcc_data_reception import VCCDataReceptionService


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
def reception_service(db_session):
    """Create a data reception service with in-memory database."""
    service = VCCDataReceptionService(db_session=db_session)
    yield service
    service.close()


class TestPowerGenerationDataReception:
    """Test power generation data reception."""

    def test_receive_valid_power_data(self, reception_service):
        """Test receiving valid power generation data."""
        data = PowerGenerationData(
            timestamp=datetime.now(),
            current_power=150.5,
            solar_power=100.0,
            wind_power=50.5,
            efficiency=95.5,
            device_status="running"
        )
        
        result = reception_service.receive_power_generation_data(data)
        assert result is True

    def test_receive_power_data_stored_in_cache(self, reception_service):
        """Test that received power data is stored in cache."""
        data = PowerGenerationData(
            timestamp=datetime.now(),
            current_power=150.5,
            solar_power=100.0,
            wind_power=50.5,
            efficiency=95.5,
            device_status="running"
        )
        
        reception_service.receive_power_generation_data(data)
        cached_data = reception_service.get_latest_power_data()
        
        assert cached_data is not None
        assert cached_data.current_power == 150.5
        assert cached_data.solar_power == 100.0

    def test_receive_power_data_stored_in_db(self, reception_service, db_session):
        """Test that received power data is stored in database."""
        data = PowerGenerationData(
            timestamp=datetime.now(),
            current_power=150.5,
            solar_power=100.0,
            wind_power=50.5,
            efficiency=95.5,
            device_status="running"
        )
        
        reception_service.receive_power_generation_data(data)
        
        # Query database
        records = db_session.query(PowerGenerationDataDB).all()
        assert len(records) == 1
        assert records[0].current_power == 150.5

    def test_receive_invalid_power_data(self, reception_service):
        """Test receiving invalid power generation data."""
        data = PowerGenerationData(
            timestamp=datetime.now(),
            current_power=-10.0,  # Invalid: negative
            solar_power=100.0,
            wind_power=50.5,
            efficiency=95.5,
            device_status="running"
        )
        
        result = reception_service.receive_power_generation_data(data)
        assert result is False

    def test_receive_multiple_power_data_updates(self, reception_service):
        """Test receiving multiple power data updates."""
        data1 = PowerGenerationData(
            timestamp=datetime.now(),
            current_power=150.5,
            solar_power=100.0,
            wind_power=50.5,
            efficiency=95.5,
            device_status="running"
        )
        
        data2 = PowerGenerationData(
            timestamp=datetime.now(),
            current_power=160.0,
            solar_power=110.0,
            wind_power=50.0,
            efficiency=96.0,
            device_status="running"
        )
        
        result1 = reception_service.receive_power_generation_data(data1)
        result2 = reception_service.receive_power_generation_data(data2)
        
        assert result1 is True
        assert result2 is True
        
        # Cache should have the latest data
        cached_data = reception_service.get_latest_power_data()
        assert cached_data.current_power == 160.0


class TestStorageDataReception:
    """Test storage data reception."""

    def test_receive_valid_storage_data(self, reception_service):
        """Test receiving valid storage data."""
        data = StorageData(
            timestamp=datetime.now(),
            soc=75.5,
            soh=98.0,
            current_power=50.0,
            charge_status="charging",
            temperature=25.5
        )
        
        result = reception_service.receive_storage_data(data)
        assert result is True

    def test_receive_storage_data_stored_in_cache(self, reception_service):
        """Test that received storage data is stored in cache."""
        data = StorageData(
            timestamp=datetime.now(),
            soc=75.5,
            soh=98.0,
            current_power=50.0,
            charge_status="charging",
            temperature=25.5
        )
        
        reception_service.receive_storage_data(data)
        cached_data = reception_service.get_latest_storage_data()
        
        assert cached_data is not None
        assert cached_data.soc == 75.5
        assert cached_data.soh == 98.0

    def test_receive_storage_data_stored_in_db(self, reception_service, db_session):
        """Test that received storage data is stored in database."""
        data = StorageData(
            timestamp=datetime.now(),
            soc=75.5,
            soh=98.0,
            current_power=50.0,
            charge_status="charging",
            temperature=25.5
        )
        
        reception_service.receive_storage_data(data)
        
        # Query database
        records = db_session.query(StorageDataDB).all()
        assert len(records) == 1
        assert records[0].soc == 75.5

    def test_receive_invalid_storage_data(self, reception_service):
        """Test receiving invalid storage data."""
        data = StorageData(
            timestamp=datetime.now(),
            soc=150.0,  # Invalid: > 100
            soh=98.0,
            current_power=50.0,
            charge_status="charging",
            temperature=25.5
        )
        
        result = reception_service.receive_storage_data(data)
        assert result is False

    def test_receive_multiple_storage_data_updates(self, reception_service):
        """Test receiving multiple storage data updates."""
        data1 = StorageData(
            timestamp=datetime.now(),
            soc=75.5,
            soh=98.0,
            current_power=50.0,
            charge_status="charging",
            temperature=25.5
        )
        
        data2 = StorageData(
            timestamp=datetime.now(),
            soc=80.0,
            soh=97.5,
            current_power=55.0,
            charge_status="charging",
            temperature=26.0
        )
        
        result1 = reception_service.receive_storage_data(data1)
        result2 = reception_service.receive_storage_data(data2)
        
        assert result1 is True
        assert result2 is True
        
        # Cache should have the latest data
        cached_data = reception_service.get_latest_storage_data()
        assert cached_data.soc == 80.0


class TestDemandDataReception:
    """Test demand data reception."""

    def test_receive_valid_demand_data(self, reception_service):
        """Test receiving valid demand data."""
        data = DemandData(
            timestamp=datetime.now(),
            current_load=200.0,
            forecast_load=210.0,
            adjustable_range=(180.0, 220.0),
            dr_status="active"
        )
        
        result = reception_service.receive_demand_data(data)
        assert result is True

    def test_receive_demand_data_stored_in_cache(self, reception_service):
        """Test that received demand data is stored in cache."""
        data = DemandData(
            timestamp=datetime.now(),
            current_load=200.0,
            forecast_load=210.0,
            adjustable_range=(180.0, 220.0),
            dr_status="active"
        )
        
        reception_service.receive_demand_data(data)
        cached_data = reception_service.get_latest_demand_data()
        
        assert cached_data is not None
        assert cached_data.current_load == 200.0
        assert cached_data.forecast_load == 210.0

    def test_receive_demand_data_stored_in_db(self, reception_service, db_session):
        """Test that received demand data is stored in database."""
        data = DemandData(
            timestamp=datetime.now(),
            current_load=200.0,
            forecast_load=210.0,
            adjustable_range=(180.0, 220.0),
            dr_status="active"
        )
        
        reception_service.receive_demand_data(data)
        
        # Query database
        records = db_session.query(DemandDataDB).all()
        assert len(records) == 1
        assert records[0].current_load == 200.0

    def test_receive_invalid_demand_data(self, reception_service):
        """Test receiving invalid demand data."""
        data = DemandData(
            timestamp=datetime.now(),
            current_load=200.0,
            forecast_load=210.0,
            adjustable_range=(220.0, 180.0),  # Invalid: min > max
            dr_status="active"
        )
        
        result = reception_service.receive_demand_data(data)
        assert result is False

    def test_receive_multiple_demand_data_updates(self, reception_service):
        """Test receiving multiple demand data updates."""
        data1 = DemandData(
            timestamp=datetime.now(),
            current_load=200.0,
            forecast_load=210.0,
            adjustable_range=(180.0, 220.0),
            dr_status="active"
        )
        
        data2 = DemandData(
            timestamp=datetime.now(),
            current_load=205.0,
            forecast_load=215.0,
            adjustable_range=(185.0, 225.0),
            dr_status="active"
        )
        
        result1 = reception_service.receive_demand_data(data1)
        result2 = reception_service.receive_demand_data(data2)
        
        assert result1 is True
        assert result2 is True
        
        # Cache should have the latest data
        cached_data = reception_service.get_latest_demand_data()
        assert cached_data.current_load == 205.0


class TestDataReceptionIntegration:
    """Test data reception integration."""

    def test_receive_all_data_types(self, reception_service):
        """Test receiving all data types."""
        power_data = PowerGenerationData(
            timestamp=datetime.now(),
            current_power=150.5,
            solar_power=100.0,
            wind_power=50.5,
            efficiency=95.5,
            device_status="running"
        )
        
        storage_data = StorageData(
            timestamp=datetime.now(),
            soc=75.5,
            soh=98.0,
            current_power=50.0,
            charge_status="charging",
            temperature=25.5
        )
        
        demand_data = DemandData(
            timestamp=datetime.now(),
            current_load=200.0,
            forecast_load=210.0,
            adjustable_range=(180.0, 220.0),
            dr_status="active"
        )
        
        result1 = reception_service.receive_power_generation_data(power_data)
        result2 = reception_service.receive_storage_data(storage_data)
        result3 = reception_service.receive_demand_data(demand_data)
        
        assert result1 is True
        assert result2 is True
        assert result3 is True
        
        # Verify all data in cache
        assert reception_service.get_latest_power_data() is not None
        assert reception_service.get_latest_storage_data() is not None
        assert reception_service.get_latest_demand_data() is not None

    def test_cache_clear(self, reception_service):
        """Test cache clearing."""
        power_data = PowerGenerationData(
            timestamp=datetime.now(),
            current_power=150.5,
            solar_power=100.0,
            wind_power=50.5,
            efficiency=95.5,
            device_status="running"
        )
        
        reception_service.receive_power_generation_data(power_data)
        assert reception_service.get_latest_power_data() is not None
        
        reception_service.clear_cache()
        assert reception_service.get_latest_power_data() is None

    def test_receive_data_without_db_session(self):
        """Test receiving data without database session."""
        service = VCCDataReceptionService(db_session=None)
        
        data = PowerGenerationData(
            timestamp=datetime.now(),
            current_power=150.5,
            solar_power=100.0,
            wind_power=50.5,
            efficiency=95.5,
            device_status="running"
        )
        
        result = service.receive_power_generation_data(data)
        assert result is True
        assert service.get_latest_power_data() is not None


class TestDataReceptionErrorHandling:
    """Test error handling in data reception."""

    def test_receive_power_data_with_invalid_type(self, reception_service):
        """Test receiving power data with invalid type."""
        # This should raise an error or return False
        try:
            result = reception_service.receive_power_generation_data(None)
            assert result is False
        except (AttributeError, TypeError):
            # Expected behavior
            pass

    def test_receive_storage_data_with_invalid_type(self, reception_service):
        """Test receiving storage data with invalid type."""
        try:
            result = reception_service.receive_storage_data(None)
            assert result is False
        except (AttributeError, TypeError):
            # Expected behavior
            pass

    def test_receive_demand_data_with_invalid_type(self, reception_service):
        """Test receiving demand data with invalid type."""
        try:
            result = reception_service.receive_demand_data(None)
            assert result is False
        except (AttributeError, TypeError):
            # Expected behavior
            pass


class TestDataPersistence:
    """Test data persistence across multiple operations."""

    def test_multiple_records_in_database(self, reception_service, db_session):
        """Test storing multiple records in database."""
        for i in range(5):
            data = PowerGenerationData(
                timestamp=datetime.now(),
                current_power=150.0 + i,
                solar_power=100.0 + i,
                wind_power=50.0 + i,
                efficiency=95.0 + i,
                device_status="running"
            )
            reception_service.receive_power_generation_data(data)
        
        records = db_session.query(PowerGenerationDataDB).all()
        assert len(records) == 5

    def test_data_retrieval_from_database(self, reception_service, db_session):
        """Test retrieving data from database."""
        data = PowerGenerationData(
            timestamp=datetime.now(),
            current_power=150.5,
            solar_power=100.0,
            wind_power=50.5,
            efficiency=95.5,
            device_status="running"
        )
        
        reception_service.receive_power_generation_data(data)
        
        # Retrieve from database
        records = db_session.query(PowerGenerationDataDB).filter_by(
            current_power=150.5
        ).all()
        
        assert len(records) == 1
        assert records[0].solar_power == 100.0
        assert records[0].wind_power == 50.5
