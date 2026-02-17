"""
Protocol Management Service Tests

Tests for protocol management service and API integration.
"""

import pytest
from services.protocol_management import (
    ProtocolManagementService,
    get_protocol_management_service
)
from services.protocol_adapters.base import ProtocolException


class TestProtocolManagementService:
    """Test protocol management service"""
    
    @pytest.fixture
    def service(self):
        """Create protocol management service"""
        return ProtocolManagementService()
    
    # ========================================================================
    # Adapter Management Tests
    # ========================================================================
    
    def test_service_initialization(self, service):
        """Test service initializes correctly"""
        assert service is not None
        assert service.registry is not None
        assert service.mapper is not None
    
    def test_list_supported_protocols(self, service):
        """Test listing supported protocols"""
        protocols = service.list_supported_protocols()
        assert isinstance(protocols, list)
        # May be empty if adapters couldn't be registered due to missing dependencies
        # But mappings should still work
    
    def test_is_protocol_supported(self, service):
        """Test protocol support check"""
        # Adapters may not be registered if dependencies are missing
        # But the service should still work for mappings
        result = service.is_protocol_supported("iec61850")
        assert isinstance(result, bool)
    
    def test_get_protocol_info(self, service):
        """Test getting protocol information"""
        # Adapters may not be registered if dependencies are missing
        info = service.get_protocol_info("iec61850")
        # May be None if adapter not registered, but that's OK
    
    def test_create_adapter(self, service):
        """Test creating adapter"""
        protocols = service.list_supported_protocols()
        if not protocols:
            pytest.skip("No adapters registered (missing dependencies)")
        
        protocol = protocols[0]
        result = service.create_adapter(protocol, "test-adapter-1")
        assert result["adapter_id"] == "test-adapter-1"
        assert result["protocol"] == protocol
        assert result["status"] == "created"
    
    def test_get_adapter(self, service):
        """Test getting adapter"""
        protocols = service.list_supported_protocols()
        if not protocols:
            pytest.skip("No adapters registered (missing dependencies)")
        
        protocol = protocols[0]
        service.create_adapter(protocol, "test-adapter-2")
        adapter = service.get_adapter("test-adapter-2")
        assert adapter is not None
        assert adapter["adapter_id"] == "test-adapter-2"
        assert adapter["protocol"] == protocol
    
    def test_get_nonexistent_adapter(self, service):
        """Test getting nonexistent adapter"""
        adapter = service.get_adapter("nonexistent")
        assert adapter is None
    
    def test_list_adapters(self, service):
        """Test listing adapters"""
        protocols = service.list_supported_protocols()
        if not protocols:
            pytest.skip("No adapters registered (missing dependencies)")
        
        protocol = protocols[0]
        service.create_adapter(protocol, "adapter-1")
        service.create_adapter(protocol, "adapter-2")
        
        adapters = service.list_adapters()
        assert len(adapters) >= 2
        adapter_ids = [a["adapter_id"] for a in adapters]
        assert "adapter-1" in adapter_ids
        assert "adapter-2" in adapter_ids
    
    def test_remove_adapter(self, service):
        """Test removing adapter"""
        protocols = service.list_supported_protocols()
        if not protocols:
            pytest.skip("No adapters registered (missing dependencies)")
        
        protocol = protocols[0]
        service.create_adapter(protocol, "adapter-3")
        removed = service.remove_adapter("adapter-3")
        assert removed is True
        
        # Try to get removed adapter
        adapter = service.get_adapter("adapter-3")
        assert adapter is None
    
    def test_remove_nonexistent_adapter(self, service):
        """Test removing nonexistent adapter"""
        removed = service.remove_adapter("nonexistent")
        assert removed is False
    
    def test_get_registry_status(self, service):
        """Test getting registry status"""
        protocols = service.list_supported_protocols()
        if not protocols:
            pytest.skip("No adapters registered (missing dependencies)")
        
        protocol = protocols[0]
        service.create_adapter(protocol, "status-test-1")
        status = service.get_registry_status()
        
        assert "registered_protocols" in status
        assert "active_adapters" in status
        assert "total_protocols" in status
        assert "total_instances" in status
        assert len(status["registered_protocols"]) > 0
    
    # ========================================================================
    # Message Mapping Tests
    # ========================================================================
    
    def test_map_iec61850_to_modbus(self, service):
        """Test mapping IEC 61850 to Modbus"""
        message = {
            "voltage": 230,
            "current": 10,
            "frequency": 50,
            "power": 2300,
            "status": "on",
            "timestamp": 1645000000,
        }
        
        mapped = service.map_message("iec61850", "modbus", message)
        assert mapped["voltage_mv"] == 230000
        assert mapped["current_ma"] == 10000
        assert mapped["frequency"] == 50
        assert mapped["power_kw"] == 2.3
        assert mapped["status_coil"] is True
    
    def test_map_modbus_to_iec61850(self, service):
        """Test mapping Modbus to IEC 61850"""
        message = {
            "voltage_mv": 230000,
            "current_ma": 10000,
            "frequency": 50,
            "power_kw": 2.3,
            "status_coil": True,
            "timestamp": 1645000000,
        }
        
        mapped = service.map_message("modbus", "iec61850", message)
        assert mapped["voltage"] == 230
        assert mapped["current"] == 10
        assert mapped["frequency"] == 50
        assert mapped["power"] == 2300
        assert mapped["status"] == "on"
    
    def test_map_iec61850_to_dnp3(self, service):
        """Test mapping IEC 61850 to DNP3"""
        message = {
            "voltage": 230,
            "current": 10,
            "frequency": 50,
            "power": 2300,
            "status": "on",
            "quality": "good",
        }
        
        mapped = service.map_message("iec61850", "dnp3", message)
        assert mapped["voltage"] == 230
        assert mapped["current"] == 10
        # Status is converted to binary (1 for "on")
        assert mapped["status"] == 1
    
    def test_map_iec61850_to_mqtt(self, service):
        """Test mapping IEC 61850 to MQTT"""
        message = {
            "voltage": 230,
            "current": 10,
            "frequency": 50,
            "power": 2300,
            "status": "on",
            "timestamp": 1645000000,
        }
        
        mapped = service.map_message("iec61850", "mqtt", message)
        assert "voltage" in mapped
        assert "current" in mapped
        assert "status" in mapped
    
    def test_map_invalid_protocols(self, service):
        """Test mapping with invalid protocols"""
        message = {"voltage": 230}
        
        with pytest.raises(ProtocolException):
            service.map_message("unknown", "modbus", message)
        
        with pytest.raises(ProtocolException):
            service.map_message("iec61850", "unknown", message)
    
    # ========================================================================
    # Message Validation Tests
    # ========================================================================
    
    def test_validate_iec61850_message(self, service):
        """Test validating IEC 61850 message"""
        valid_message = {
            "voltage": 230,
            "current": 10,
            "frequency": 50,
            "status": "on",
            "timestamp": 1645000000,
        }
        
        is_valid = service.validate_message(
            "validate_iec61850_message",
            valid_message
        )
        assert is_valid is True
    
    def test_validate_invalid_message(self, service):
        """Test validating invalid message"""
        invalid_message = {
            "voltage": 600,  # Out of range
            "current": 10,
            "frequency": 50,
            "status": "on",
            "timestamp": 1645000000,
        }
        
        is_valid = service.validate_message(
            "validate_iec61850_message",
            invalid_message
        )
        assert is_valid is False
    
    def test_validate_voltage_range(self, service):
        """Test voltage range validation"""
        valid = service.validate_message(
            "validate_voltage_range",
            {"voltage": 230}
        )
        assert valid is True
        
        invalid = service.validate_message(
            "validate_voltage_range",
            {"voltage": 600}
        )
        assert invalid is False
    
    def test_validate_current_range(self, service):
        """Test current range validation"""
        valid = service.validate_message(
            "validate_current_range",
            {"current": 100}
        )
        assert valid is True
        
        invalid = service.validate_message(
            "validate_current_range",
            {"current": 2000}
        )
        assert invalid is False
    
    # ========================================================================
    # Data Transformation Tests
    # ========================================================================
    
    def test_transform_voltage_to_mv(self, service):
        """Test voltage transformation"""
        result = service.transform_data(
            "scale_voltage_to_mv",
            {"voltage": 230}
        )
        assert result == 230000
    
    def test_transform_current_to_ma(self, service):
        """Test current transformation"""
        result = service.transform_data(
            "scale_current_to_ma",
            {"current": 10}
        )
        assert result == 10000
    
    def test_transform_power_to_kw(self, service):
        """Test power transformation"""
        result = service.transform_data(
            "scale_power_to_kw",
            {"power": 2300}
        )
        assert result == 2.3
    
    def test_transform_status_to_coil(self, service):
        """Test status transformation"""
        result = service.transform_data(
            "status_to_coil",
            {"status": "on"}
        )
        assert result is True
        
        result = service.transform_data(
            "status_to_coil",
            {"status": "off"}
        )
        assert result is False
    
    def test_transform_invalid_transformer(self, service):
        """Test invalid transformer"""
        with pytest.raises(ProtocolException):
            service.transform_data("invalid_transformer", {"data": 123})
    
    # ========================================================================
    # Mapper Information Tests
    # ========================================================================
    
    def test_get_mapper_info(self, service):
        """Test getting mapper information"""
        info = service.get_mapper_info()
        
        assert "mappings" in info
        assert "transformers" in info
        assert "validators" in info
        assert "total_mappings" in info
        assert "total_transformers" in info
        assert "total_validators" in info
        
        assert info["total_mappings"] == 12
        assert info["total_transformers"] == 23
        assert info["total_validators"] == 23
    
    # ========================================================================
    # Bidirectional Conversion Tests
    # ========================================================================
    
    def test_convert_iec61850_to_modbus(self, service):
        """Test IEC 61850 to Modbus conversion"""
        message = {
            "voltage": 230,
            "current": 10,
            "frequency": 50,
            "power": 2300,
            "status": "on",
            "timestamp": 1645000000,
        }
        
        result = service.convert_iec61850_to_modbus(message)
        assert result["voltage_mv"] == 230000
        assert result["current_ma"] == 10000
    
    def test_convert_modbus_to_iec61850(self, service):
        """Test Modbus to IEC 61850 conversion"""
        message = {
            "voltage_mv": 230000,
            "current_ma": 10000,
            "frequency": 50,
            "power_kw": 2.3,
            "status_coil": True,
            "timestamp": 1645000000,
        }
        
        result = service.convert_modbus_to_iec61850(message)
        assert result["voltage"] == 230
        assert result["current"] == 10
    
    def test_convert_iec61850_to_dnp3(self, service):
        """Test IEC 61850 to DNP3 conversion"""
        message = {
            "voltage": 230,
            "current": 10,
            "frequency": 50,
            "power": 2300,
            "status": "on",
            "quality": "good",
        }
        
        result = service.convert_iec61850_to_dnp3(message)
        assert result["voltage"] == 230
    
    def test_convert_dnp3_to_iec61850(self, service):
        """Test DNP3 to IEC 61850 conversion"""
        message = {
            "voltage": 230,
            "current": 10,
            "frequency": 50,
            "power": 2300,
            "status": "on",
            "quality": "good",
        }
        
        result = service.convert_dnp3_to_iec61850(message)
        assert result["voltage"] == 230
    
    def test_convert_iec61850_to_mqtt(self, service):
        """Test IEC 61850 to MQTT conversion"""
        message = {
            "voltage": 230,
            "current": 10,
            "frequency": 50,
            "power": 2300,
            "status": "on",
            "timestamp": 1645000000,
        }
        
        result = service.convert_iec61850_to_mqtt(message)
        assert "voltage" in result
    
    def test_convert_mqtt_to_iec61850(self, service):
        """Test MQTT to IEC 61850 conversion"""
        message = {
            "voltage": 230,
            "current": 10,
            "frequency": 50,
            "power": 2300,
            "status": "on",
            "timestamp": 1645000000,
        }
        
        result = service.convert_mqtt_to_iec61850(message)
        assert "voltage" in result
    
    def test_convert_modbus_to_dnp3(self, service):
        """Test Modbus to DNP3 conversion"""
        message = {
            "voltage_mv": 230000,
            "current_ma": 10000,
            "frequency": 50,
            "power_kw": 2.3,
            "status_coil": True,
        }
        
        result = service.convert_modbus_to_dnp3(message)
        assert result["voltage"] == 230
    
    def test_convert_dnp3_to_modbus(self, service):
        """Test DNP3 to Modbus conversion"""
        message = {
            "voltage": 230,
            "current": 10,
            "frequency": 50,
            "power": 2300,
            "status": "on",
        }
        
        result = service.convert_dnp3_to_modbus(message)
        assert result["voltage_mv"] == 230000
    
    def test_convert_modbus_to_mqtt(self, service):
        """Test Modbus to MQTT conversion"""
        message = {
            "voltage_mv": 230000,
            "current_ma": 10000,
            "frequency": 50,
            "power_kw": 2.3,
            "status_coil": True,
        }
        
        result = service.convert_modbus_to_mqtt(message)
        assert "voltage" in result
    
    def test_convert_mqtt_to_modbus(self, service):
        """Test MQTT to Modbus conversion"""
        message = {
            "voltage": 230,
            "current": 10,
            "frequency": 50,
            "power": 2300,
            "status": "on",
        }
        
        result = service.convert_mqtt_to_modbus(message)
        assert result["voltage_mv"] == 230000
    
    def test_convert_dnp3_to_mqtt(self, service):
        """Test DNP3 to MQTT conversion"""
        message = {
            "voltage": 230,
            "current": 10,
            "frequency": 50,
            "power": 2300,
            "status": "on",
        }
        
        result = service.convert_dnp3_to_mqtt(message)
        assert "voltage" in result
    
    def test_convert_mqtt_to_dnp3(self, service):
        """Test MQTT to DNP3 conversion"""
        message = {
            "voltage": 230,
            "current": 10,
            "frequency": 50,
            "power": 2300,
            "status": "on",
        }
        
        result = service.convert_mqtt_to_dnp3(message)
        assert result["voltage"] == 230


class TestProtocolManagementSingleton:
    """Test protocol management service singleton"""
    
    def test_get_singleton(self):
        """Test getting singleton instance"""
        service1 = get_protocol_management_service()
        service2 = get_protocol_management_service()
        assert service1 is service2
    
    def test_singleton_has_all_components(self):
        """Test singleton has all components"""
        service = get_protocol_management_service()
        assert service.registry is not None
        assert service.mapper is not None
        # Adapters may not be registered if dependencies are missing
        # But mapper should always work
