"""
Database Tests

Tests for database models and ORM functionality.
"""

import pytest
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.database import Base, engine, SessionLocal, init_db, drop_db
from models.device import Device
from models.dispatch import Dispatch
from models.protocol_mapping import ProtocolMapping
from models.analysis_result import AnalysisResult


@pytest.fixture(scope="function")
def db_session():
    """Create a test database session"""
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    session = SessionLocal()
    yield session
    
    # Cleanup
    session.close()
    Base.metadata.drop_all(bind=engine)


class TestDeviceModel:
    """Test Device model"""
    
    def test_device_creation(self, db_session):
        """Test creating a device"""
        device = Device(
            id="device-001",
            device_type="solar",
            location="Building A",
            status="online",
            capabilities={"power": 100},
            configuration={"mode": "auto"}
        )
        
        db_session.add(device)
        db_session.commit()
        
        # Verify device was created
        retrieved = db_session.query(Device).filter_by(id="device-001").first()
        assert retrieved is not None
        assert retrieved.device_type == "solar"
        assert retrieved.location == "Building A"
    
    def test_device_status_methods(self, db_session):
        """Test device status methods"""
        device = Device(
            id="device-002",
            device_type="wind",
            location="Field B",
            status="online"
        )
        
        assert device.is_online()
        assert not device.is_offline()
        
        device.update_status("offline")
        assert device.is_offline()
        assert not device.is_online()
    
    def test_device_heartbeat_update(self, db_session):
        """Test device heartbeat update"""
        device = Device(
            id="device-003",
            device_type="battery",
            location="Storage C",
            status="offline"
        )
        
        db_session.add(device)
        db_session.commit()
        
        # Update heartbeat
        device.update_heartbeat()
        assert device.is_online()
        assert device.last_heartbeat is not None
    
    def test_device_configuration_update(self, db_session):
        """Test device configuration update"""
        device = Device(
            id="device-004",
            device_type="load",
            location="Building D",
            configuration={"power_limit": 50}
        )
        
        db_session.add(device)
        db_session.commit()
        
        # Update configuration
        device.update_configuration({"mode": "auto"})
        assert device.configuration["power_limit"] == 50
        assert device.configuration["mode"] == "auto"
    
    def test_device_to_dict(self, db_session):
        """Test device to_dict conversion"""
        device = Device(
            id="device-005",
            device_type="solar",
            location="Building E",
            status="online"
        )
        
        device_dict = device.to_dict()
        assert device_dict["id"] == "device-005"
        assert device_dict["device_type"] == "solar"
        assert device_dict["status"] == "online"


class TestDispatchModel:
    """Test Dispatch model"""
    
    def test_dispatch_creation(self, db_session):
        """Test creating a dispatch"""
        dispatch = Dispatch(
            id="dispatch-001",
            device_id="device-001",
            command_type="power_adjust",
            target_value=50.0,
            priority_level=5,
            status="pending"
        )
        
        db_session.add(dispatch)
        db_session.commit()
        
        # Verify dispatch was created
        retrieved = db_session.query(Dispatch).filter_by(id="dispatch-001").first()
        assert retrieved is not None
        assert retrieved.command_type == "power_adjust"
        assert retrieved.target_value == 50.0
    
    def test_dispatch_status_methods(self, db_session):
        """Test dispatch status methods"""
        dispatch = Dispatch(
            id="dispatch-002",
            device_id="device-002",
            command_type="mode_change",
            target_value=0.0,
            status="pending"
        )
        
        assert dispatch.is_pending()
        assert not dispatch.is_executing()
        
        dispatch.mark_executing()
        assert dispatch.is_executing()
        assert not dispatch.is_pending()
    
    def test_dispatch_mark_completed(self, db_session):
        """Test marking dispatch as completed"""
        dispatch = Dispatch(
            id="dispatch-003",
            device_id="device-003",
            command_type="power_adjust",
            target_value=75.0,
            status="pending"
        )
        
        db_session.add(dispatch)
        db_session.commit()
        
        # Mark as completed
        result_data = {"actual_power": 75.0}
        dispatch.mark_completed(result_data)
        
        assert dispatch.is_completed()
        assert dispatch.execution_time is not None
        assert dispatch.result_data == result_data
    
    def test_dispatch_mark_failed(self, db_session):
        """Test marking dispatch as failed"""
        dispatch = Dispatch(
            id="dispatch-004",
            device_id="device-004",
            command_type="power_adjust",
            target_value=100.0,
            status="executing"
        )
        
        db_session.add(dispatch)
        db_session.commit()
        
        # Mark as failed
        dispatch.mark_failed("Device not responding")
        
        assert dispatch.is_failed()
        assert dispatch.error_message == "Device not responding"
    
    def test_dispatch_retry_logic(self, db_session):
        """Test dispatch retry logic"""
        dispatch = Dispatch(
            id="dispatch-005",
            device_id="device-005",
            command_type="power_adjust",
            target_value=50.0,
            retry_count=0
        )
        
        assert dispatch.can_retry(max_retries=3)
        
        dispatch.increment_retry()
        assert dispatch.retry_count == 1
        assert dispatch.can_retry(max_retries=3)
        
        dispatch.increment_retry()
        dispatch.increment_retry()
        assert dispatch.retry_count == 3
        assert not dispatch.can_retry(max_retries=3)
    
    def test_dispatch_to_dict(self, db_session):
        """Test dispatch to_dict conversion"""
        dispatch = Dispatch(
            id="dispatch-006",
            device_id="device-006",
            command_type="power_adjust",
            target_value=60.0,
            status="pending"
        )
        
        dispatch_dict = dispatch.to_dict()
        assert dispatch_dict["id"] == "dispatch-006"
        assert dispatch_dict["command_type"] == "power_adjust"
        assert dispatch_dict["target_value"] == 60.0


class TestProtocolMappingModel:
    """Test ProtocolMapping model"""
    
    def test_protocol_mapping_creation(self, db_session):
        """Test creating a protocol mapping"""
        mapping = ProtocolMapping(
            id="mapping-001",
            source_protocol="iec_104",
            target_protocol="mqtt",
            mapping_rules={"field1": "field2"},
            is_active=True
        )
        
        db_session.add(mapping)
        db_session.commit()
        
        # Verify mapping was created
        retrieved = db_session.query(ProtocolMapping).filter_by(id="mapping-001").first()
        assert retrieved is not None
        assert retrieved.source_protocol == "iec_104"
        assert retrieved.target_protocol == "mqtt"
    
    def test_protocol_mapping_enable_disable(self, db_session):
        """Test enabling/disabling protocol mapping"""
        mapping = ProtocolMapping(
            id="mapping-002",
            source_protocol="mqtt",
            target_protocol="iec_104",
            is_active=True
        )
        
        assert mapping.is_enabled()
        
        mapping.disable()
        assert not mapping.is_enabled()
        
        mapping.enable()
        assert mapping.is_enabled()
    
    def test_protocol_mapping_update_rules(self, db_session):
        """Test updating protocol mapping rules"""
        mapping = ProtocolMapping(
            id="mapping-003",
            source_protocol="iec_104",
            target_protocol="mqtt",
            mapping_rules={"field1": "field2"}
        )
        
        db_session.add(mapping)
        db_session.commit()
        
        # Update rules
        mapping.update_rules({"field3": "field4"})
        assert mapping.mapping_rules["field1"] == "field2"
        assert mapping.mapping_rules["field3"] == "field4"


class TestAnalysisResultModel:
    """Test AnalysisResult model"""
    
    def test_analysis_result_creation(self, db_session):
        """Test creating an analysis result"""
        result = AnalysisResult(
            id="analysis-001",
            analysis_type="power_flow",
            system_state={"devices": 10},
            result_data={"voltage": 230},
            status="completed",
            execution_time_ms=1500
        )
        
        db_session.add(result)
        db_session.commit()
        
        # Verify result was created
        retrieved = db_session.query(AnalysisResult).filter_by(id="analysis-001").first()
        assert retrieved is not None
        assert retrieved.analysis_type == "power_flow"
        assert retrieved.execution_time_ms == 1500
    
    def test_analysis_result_status_methods(self, db_session):
        """Test analysis result status methods"""
        result = AnalysisResult(
            id="analysis-002",
            analysis_type="stability",
            status="completed"
        )
        
        assert result.is_completed()
        assert not result.is_failed()
    
    def test_analysis_result_mark_completed(self, db_session):
        """Test marking analysis as completed"""
        result = AnalysisResult(
            id="analysis-003",
            analysis_type="metrics",
            status="completed"
        )
        
        db_session.add(result)
        db_session.commit()
        
        # Mark as completed
        result_data = {"efficiency": 0.95}
        result.mark_completed(result_data, 2000)
        
        assert result.is_completed()
        assert result.result_data == result_data
        assert result.execution_time_ms == 2000
    
    def test_analysis_result_mark_failed(self, db_session):
        """Test marking analysis as failed"""
        result = AnalysisResult(
            id="analysis-004",
            analysis_type="power_flow",
            status="completed"
        )
        
        db_session.add(result)
        db_session.commit()
        
        # Mark as failed
        result.mark_failed("Convergence failed", 5000)
        
        assert result.is_failed()
        assert result.error_message == "Convergence failed"
        assert result.execution_time_ms == 5000


class TestDatabaseRelationships:
    """Test database relationships"""
    
    def test_device_dispatch_relationship(self, db_session):
        """Test device-dispatch relationship"""
        device = Device(
            id="device-rel-001",
            device_type="solar",
            location="Building A"
        )
        
        dispatch = Dispatch(
            id="dispatch-rel-001",
            device_id="device-rel-001",
            command_type="power_adjust",
            target_value=50.0
        )
        
        db_session.add(device)
        db_session.add(dispatch)
        db_session.commit()
        
        # Verify relationship
        retrieved_device = db_session.query(Device).filter_by(id="device-rel-001").first()
        assert len(retrieved_device.dispatches) == 1
        assert retrieved_device.dispatches[0].id == "dispatch-rel-001"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
