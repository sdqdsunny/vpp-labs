"""
Unit tests for Database Service.

Tests:
- Database service initialization
- Save power generation data
- Save storage data
- Save demand data
- Save coordination results
- Save commands
- Query operations
- Error handling
"""

import pytest
from datetime import datetime, timedelta

from services.database_service import DatabaseService
from models.realtime_data_models import (
    PowerGenerationData, StorageData, DemandData,
    CoordinationResult, PowerCommand, StorageCommand, DemandCommand
)


class TestDatabaseServiceInitialization:
    """Test database service initialization."""

    def test_service_initialization_with_memory_db(self):
        """Test that service initializes with in-memory database."""
        service = DatabaseService(use_memory_db=True)
        
        assert service.db_session is not None
        assert service.save_count == 0
        assert service.error_count == 0
        
        # Cleanup
        service.close()

    def test_service_stats_on_init(self):
        """Test that stats are correct on initialization."""
        service = DatabaseService(use_memory_db=True)
        stats = service.get_stats()
        
        assert stats['save_count'] == 0
        assert stats['error_count'] == 0
        assert stats['has_session'] is True
        
        # Cleanup
        service.close()


class TestSavePowerData:
    """Test saving power generation data."""

    def test_save_valid_power_data(self):
        """Test saving valid power generation data."""
        service = DatabaseService(use_memory_db=True)
        
        data = PowerGenerationData(
            timestamp=datetime.now(),
            current_power=150.0,
            solar_power=100.0,
            wind_power=50.0,
            efficiency=95.5,
            device_status="running"
        )
        
        result = service.save_power_data(data)
        
        assert result is True
        assert service.save_count == 1
        assert service.error_count == 0
        
        # Cleanup
        service.close()

    def test_save_multiple_power_data(self):
        """Test saving multiple power generation data."""
        service = DatabaseService(use_memory_db=True)
        
        for i in range(5):
            data = PowerGenerationData(
                timestamp=datetime.now() + timedelta(seconds=i),
                current_power=100.0 + i * 10,
                solar_power=80.0 + i * 5,
                wind_power=20.0 + i * 5,
                efficiency=95.0 + i,
                device_status="running"
            )
            result = service.save_power_data(data)
            assert result is True
        
        assert service.save_count == 5
        
        # Cleanup
        service.close()

    def test_save_invalid_power_data(self):
        """Test saving invalid power generation data."""
        service = DatabaseService(use_memory_db=True)
        
        data = PowerGenerationData(
            timestamp=datetime.now(),
            current_power=-10.0,  # Invalid
            solar_power=100.0,
            wind_power=50.0,
            efficiency=95.5,
            device_status="running"
        )
        
        result = service.save_power_data(data)
        
        assert result is False
        assert service.error_count == 1
        
        # Cleanup
        service.close()


class TestSaveStorageData:
    """Test saving storage data."""

    def test_save_valid_storage_data(self):
        """Test saving valid storage data."""
        service = DatabaseService(use_memory_db=True)
        
        data = StorageData(
            timestamp=datetime.now(),
            soc=75.5,
            soh=98.0,
            current_power=50.0,
            charge_status="charging",
            temperature=25.5
        )
        
        result = service.save_storage_data(data)
        
        assert result is True
        assert service.save_count == 1
        assert service.error_count == 0
        
        # Cleanup
        service.close()

    def test_save_multiple_storage_data(self):
        """Test saving multiple storage data."""
        service = DatabaseService(use_memory_db=True)
        
        for i in range(5):
            data = StorageData(
                timestamp=datetime.now() + timedelta(seconds=i),
                soc=70.0 + i * 2,
                soh=98.0 - i * 0.5,
                current_power=50.0 + i * 5,
                charge_status="charging",
                temperature=25.0 + i * 0.5
            )
            result = service.save_storage_data(data)
            assert result is True
        
        assert service.save_count == 5
        
        # Cleanup
        service.close()

    def test_save_invalid_storage_data(self):
        """Test saving invalid storage data."""
        service = DatabaseService(use_memory_db=True)
        
        data = StorageData(
            timestamp=datetime.now(),
            soc=150.0,  # Invalid (> 100)
            soh=98.0,
            current_power=50.0,
            charge_status="charging",
            temperature=25.5
        )
        
        result = service.save_storage_data(data)
        
        assert result is False
        assert service.error_count == 1
        
        # Cleanup
        service.close()


class TestSaveDemandData:
    """Test saving demand data."""

    def test_save_valid_demand_data(self):
        """Test saving valid demand data."""
        service = DatabaseService(use_memory_db=True)
        
        data = DemandData(
            timestamp=datetime.now(),
            current_load=200.0,
            forecast_load=210.0,
            adjustable_range=(180.0, 220.0),
            dr_status="active"
        )
        
        result = service.save_demand_data(data)
        
        assert result is True
        assert service.save_count == 1
        assert service.error_count == 0
        
        # Cleanup
        service.close()

    def test_save_multiple_demand_data(self):
        """Test saving multiple demand data."""
        service = DatabaseService(use_memory_db=True)
        
        for i in range(5):
            data = DemandData(
                timestamp=datetime.now() + timedelta(seconds=i),
                current_load=200.0 + i * 5,
                forecast_load=210.0 + i * 5,
                adjustable_range=(180.0 + i * 5, 220.0 + i * 5),
                dr_status="active"
            )
            result = service.save_demand_data(data)
            assert result is True
        
        assert service.save_count == 5
        
        # Cleanup
        service.close()

    def test_save_invalid_demand_data(self):
        """Test saving invalid demand data."""
        service = DatabaseService(use_memory_db=True)
        
        data = DemandData(
            timestamp=datetime.now(),
            current_load=-50.0,  # Invalid
            forecast_load=210.0,
            adjustable_range=(180.0, 220.0),
            dr_status="active"
        )
        
        result = service.save_demand_data(data)
        
        assert result is False
        assert service.error_count == 1
        
        # Cleanup
        service.close()


class TestSaveCoordinationResult:
    """Test saving coordination results."""

    def test_save_coordination_result(self):
        """Test saving coordination result."""
        service = DatabaseService(use_memory_db=True)
        
        power_cmd = PowerCommand(
            command_id="power_001",
            target_power=150.0,
            duration=300,
            priority=1
        )
        storage_cmd = StorageCommand(
            command_id="storage_001",
            action="charging",
            target_power=80.0,
            duration=300
        )
        demand_cmd = DemandCommand(
            command_id="demand_001",
            action="maintain",
            target_load=200.0,
            duration=300
        )
        
        result = CoordinationResult(
            timestamp=datetime.now(),
            power_command=power_cmd,
            storage_command=storage_cmd,
            demand_command=demand_cmd,
            optimization_score=92.5,
            status="success"
        )
        
        save_result = service.save_coordination_result(result)
        
        assert save_result is True
        assert service.save_count == 1
        
        # Cleanup
        service.close()

    def test_save_multiple_coordination_results(self):
        """Test saving multiple coordination results."""
        service = DatabaseService(use_memory_db=True)
        
        for i in range(3):
            power_cmd = PowerCommand(
                command_id=f"power_{i:03d}",
                target_power=150.0 + i * 10,
                duration=300,
                priority=1
            )
            storage_cmd = StorageCommand(
                command_id=f"storage_{i:03d}",
                action="charging",
                target_power=80.0 + i * 5,
                duration=300
            )
            demand_cmd = DemandCommand(
                command_id=f"demand_{i:03d}",
                action="maintain",
                target_load=200.0 + i * 5,
                duration=300
            )
            
            result = CoordinationResult(
                timestamp=datetime.now() + timedelta(seconds=i),
                power_command=power_cmd,
                storage_command=storage_cmd,
                demand_command=demand_cmd,
                optimization_score=90.0 + i * 2,
                status="success"
            )
            
            save_result = service.save_coordination_result(result)
            assert save_result is True
        
        assert service.save_count == 3
        
        # Cleanup
        service.close()


class TestSaveCommand:
    """Test saving commands."""

    def test_save_command(self):
        """Test saving command."""
        service = DatabaseService(use_memory_db=True)
        
        result = service.save_command(
            command_id="cmd_001",
            command_type="power",
            target_module="vpp-power-generation",
            command_data={"target_power": 150.0, "duration": 300},
            status="pending"
        )
        
        assert result is True
        assert service.save_count == 1
        
        # Cleanup
        service.close()

    def test_save_multiple_commands(self):
        """Test saving multiple commands."""
        service = DatabaseService(use_memory_db=True)
        
        for i in range(5):
            result = service.save_command(
                command_id=f"cmd_{i:03d}",
                command_type="power",
                target_module="vpp-power-generation",
                command_data={"target_power": 150.0 + i * 10},
                status="pending"
            )
            assert result is True
        
        assert service.save_count == 5
        
        # Cleanup
        service.close()


class TestUpdateCommandStatus:
    """Test updating command status."""

    def test_update_command_status(self):
        """Test updating command status."""
        service = DatabaseService(use_memory_db=True)
        
        # Save command first
        service.save_command(
            command_id="cmd_001",
            command_type="power",
            target_module="vpp-power-generation",
            command_data={"target_power": 150.0},
            status="pending"
        )
        
        # Update status
        result = service.update_command_status(
            command_id="cmd_001",
            status="completed",
            result={"actual_power": 150.0}
        )
        
        assert result is True
        
        # Cleanup
        service.close()

    def test_update_nonexistent_command_status(self):
        """Test updating nonexistent command status."""
        service = DatabaseService(use_memory_db=True)
        
        result = service.update_command_status(
            command_id="nonexistent",
            status="completed"
        )
        
        assert result is False
        
        # Cleanup
        service.close()


class TestQueryOperations:
    """Test query operations."""

    def test_query_power_data(self):
        """Test querying power data."""
        service = DatabaseService(use_memory_db=True)
        
        # Save some data
        for i in range(5):
            data = PowerGenerationData(
                timestamp=datetime.now() + timedelta(seconds=i),
                current_power=100.0 + i * 10,
                solar_power=80.0,
                wind_power=20.0,
                efficiency=95.0,
                device_status="running"
            )
            service.save_power_data(data)
        
        # Query data
        records = service.query_power_data(limit=10)
        
        assert len(records) == 5
        
        # Cleanup
        service.close()

    def test_query_power_data_with_time_range(self):
        """Test querying power data with time range."""
        service = DatabaseService(use_memory_db=True)
        
        now = datetime.now()
        
        # Save data with different timestamps
        for i in range(5):
            data = PowerGenerationData(
                timestamp=now + timedelta(seconds=i),
                current_power=100.0 + i * 10,
                solar_power=80.0,
                wind_power=20.0,
                efficiency=95.0,
                device_status="running"
            )
            service.save_power_data(data)
        
        # Query with time range
        start_time = now + timedelta(seconds=1)
        end_time = now + timedelta(seconds=3)
        records = service.query_power_data(start_time=start_time, end_time=end_time)
        
        assert len(records) <= 3
        
        # Cleanup
        service.close()

    def test_query_storage_data(self):
        """Test querying storage data."""
        service = DatabaseService(use_memory_db=True)
        
        # Save some data
        for i in range(5):
            data = StorageData(
                timestamp=datetime.now() + timedelta(seconds=i),
                soc=70.0 + i * 2,
                soh=98.0,
                current_power=50.0,
                charge_status="charging",
                temperature=25.0
            )
            service.save_storage_data(data)
        
        # Query data
        records = service.query_storage_data(limit=10)
        
        assert len(records) == 5
        
        # Cleanup
        service.close()

    def test_query_demand_data(self):
        """Test querying demand data."""
        service = DatabaseService(use_memory_db=True)
        
        # Save some data
        for i in range(5):
            data = DemandData(
                timestamp=datetime.now() + timedelta(seconds=i),
                current_load=200.0 + i * 5,
                forecast_load=210.0 + i * 5,
                adjustable_range=(180.0, 220.0),
                dr_status="active"
            )
            service.save_demand_data(data)
        
        # Query data
        records = service.query_demand_data(limit=10)
        
        assert len(records) == 5
        
        # Cleanup
        service.close()

    def test_query_coordination_results(self):
        """Test querying coordination results."""
        service = DatabaseService(use_memory_db=True)
        
        # Save some results
        for i in range(3):
            power_cmd = PowerCommand(
                command_id=f"power_{i:03d}",
                target_power=150.0,
                duration=300,
                priority=1
            )
            storage_cmd = StorageCommand(
                command_id=f"storage_{i:03d}",
                action="charging",
                target_power=80.0,
                duration=300
            )
            demand_cmd = DemandCommand(
                command_id=f"demand_{i:03d}",
                action="maintain",
                target_load=200.0,
                duration=300
            )
            
            result = CoordinationResult(
                timestamp=datetime.now() + timedelta(seconds=i),
                power_command=power_cmd,
                storage_command=storage_cmd,
                demand_command=demand_cmd,
                optimization_score=90.0 + i * 2,
                status="success"
            )
            
            service.save_coordination_result(result)
        
        # Query results
        records = service.query_coordination_results(limit=10)
        
        assert len(records) == 3
        
        # Cleanup
        service.close()


class TestDatabaseStatistics:
    """Test database statistics."""

    def test_stats_after_saves(self):
        """Test statistics after saves."""
        service = DatabaseService(use_memory_db=True)
        
        # Save some data
        for i in range(3):
            data = PowerGenerationData(
                timestamp=datetime.now(),
                current_power=100.0 + i * 10,
                solar_power=80.0,
                wind_power=20.0,
                efficiency=95.0,
                device_status="running"
            )
            service.save_power_data(data)
        
        stats = service.get_stats()
        
        assert stats['save_count'] == 3
        assert stats['error_count'] == 0
        assert stats['has_session'] is True
        
        # Cleanup
        service.close()

    def test_stats_with_errors(self):
        """Test statistics with errors."""
        service = DatabaseService(use_memory_db=True)
        
        # Save valid data
        data = PowerGenerationData(
            timestamp=datetime.now(),
            current_power=100.0,
            solar_power=80.0,
            wind_power=20.0,
            efficiency=95.0,
            device_status="running"
        )
        service.save_power_data(data)
        
        # Try to save invalid data
        invalid_data = PowerGenerationData(
            timestamp=datetime.now(),
            current_power=-10.0,
            solar_power=80.0,
            wind_power=20.0,
            efficiency=95.0,
            device_status="running"
        )
        service.save_power_data(invalid_data)
        
        stats = service.get_stats()
        
        assert stats['save_count'] == 1
        assert stats['error_count'] == 1
        
        # Cleanup
        service.close()


class TestErrorHandling:
    """Test error handling."""

    def test_save_without_session(self):
        """Test saving without database session."""
        service = DatabaseService(db_session=None, use_memory_db=False)
        
        data = PowerGenerationData(
            timestamp=datetime.now(),
            current_power=100.0,
            solar_power=80.0,
            wind_power=20.0,
            efficiency=95.0,
            device_status="running"
        )
        
        result = service.save_power_data(data)
        
        assert result is False
        assert service.error_count == 1

    def test_query_without_session(self):
        """Test querying without database session."""
        service = DatabaseService(db_session=None, use_memory_db=False)
        
        records = service.query_power_data()
        
        assert records == []
