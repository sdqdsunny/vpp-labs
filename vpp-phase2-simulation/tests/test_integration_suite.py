"""
Integration Test Suite for VPP Phase 2 Simulation Framework

Tests complete workflows across all components:
- Device simulator → VCC → protocol simulator flow
- Scenario execution → metrics collection flow
- Power flow calculation → stability assessment flow
- Error handling across components

Requirements:
- All 12 requirement groups (1-12)
- Properties 41-60 for correctness validation
- Error handling across components
"""

import pytest
import json
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any

from hypothesis import given, strategies as st, settings, HealthCheck

from services.device_emulator import DeviceEmulator
from services.power_gen_simulator import SolarSimulator, WindSimulator
from services.storage_simulator import BatterySimulator
from services.demand_simulator import LoadSimulator
from services.vcc_coordinator import VCCCoordinator, VPPCommand, ProtocolMessage
from services.protocol_simulator import ProtocolSimulator
from services.power_flow_engine import PowerFlowEngine
from services.scenario_engine import ScenarioEngine, Event, EventType
from services.metrics_collector import MetricsCollector
from services.network_simulator import NetworkSimulator
from utils.errors import ValidationError, SimulatorError
from utils.database import get_session, close_session
from models import Scenario, Metric


class TestDeviceSimulatorVCCProtocolFlow:
    """Test device simulator → VCC → protocol simulator flow."""
    
    @pytest.fixture
    def vcc(self):
        """Create VCC coordinator."""
        return VCCCoordinator()
    
    @pytest.fixture
    def protocol_sim(self):
        """Create protocol simulator."""
        return ProtocolSimulator()
    
    @pytest.fixture
    def solar_device(self):
        """Create solar device."""
        return SolarSimulator(
            device_id="solar-001",
            parameters={
                "capacity_kw": 100.0,
                "efficiency": 0.18,
                "location": "test-location"
            }
        )
    
    def test_solar_device_to_vcc_to_protocol_flow(self, vcc, protocol_sim, solar_device):
        """
        Test complete flow: Solar device → VCC → Protocol simulator
        
        Validates: Requirements 1.1, 4.1, 4.2, 5.1
        """
        # Step 1: Get device state
        device_state = solar_device.get_state()
        assert device_state is not None
        assert device_state.device_id == "solar-001"
        
        # Step 2: Create VPP command
        vpp_command = VPPCommand(
            command_id="cmd-001",
            device_id="solar-001",
            command_type="set_power_output",
            parameters={"power": 50.0},
            timestamp=datetime.utcnow()
        )
        
        # Step 3: Map command to protocol
        protocol_message = vcc.map_command(vpp_command, "iec104")
        assert protocol_message is not None
        assert protocol_message.protocol == "iec104"
        assert protocol_message.destination == "solar-001"
        
        # Step 4: Process message through protocol simulator
        parsed_msg, comm_event = protocol_sim.process_message(
            protocol="iec104",
            data=b"test_iec104_message",
            source="vcc",
            destination="solar-001"
        )
        
        # Step 5: Verify message was processed
        assert comm_event is not None
        assert comm_event.protocol == "iec104"
        assert comm_event.source == "vcc"
        assert comm_event.destination == "solar-001"
    
    def test_wind_device_to_vcc_to_mqtt_flow(self, vcc, protocol_sim):
        """
        Test complete flow: Wind device → VCC → MQTT protocol
        
        Validates: Requirements 1.1, 4.1, 4.2, 5.2
        """
        wind_device = WindSimulator(
            device_id="wind-001",
            parameters={
                "capacity_kw": 200.0,
                "hub_height": 80.0,
                "location": "test-location"
            }
        )
        
        # Create VPP command
        vpp_command = VPPCommand(
            command_id="cmd-002",
            device_id="wind-001",
            command_type="get_status",
            parameters={},
            timestamp=datetime.utcnow()
        )
        
        # Map to MQTT protocol
        protocol_message = vcc.map_command(vpp_command, "mqtt")
        assert protocol_message.protocol == "mqtt"
        
        # Process through protocol simulator
        parsed_msg, comm_event = protocol_sim.process_message(
            protocol="mqtt",
            data=b"test_mqtt_message",
            source="vcc",
            destination="wind-001"
        )
        
        assert comm_event.protocol == "mqtt"
    
    def test_battery_device_to_vcc_flow(self, vcc):
        """
        Test battery device → VCC flow
        
        Validates: Requirements 2.1, 4.1, 4.2
        """
        battery_device = BatterySimulator(
            device_id="battery-001",
            parameters={
                "capacity_kwh": 50.0,
                "power_rating_kw": 25.0,
                "efficiency": 0.95
            }
        )
        
        # Get device state
        device_state = battery_device.get_state()
        assert device_state.device_id == "battery-001"
        
        # Create charge command
        vpp_command = VPPCommand(
            command_id="cmd-003",
            device_id="battery-001",
            command_type="charge",
            parameters={"power": 20.0, "duration": 60.0},
            timestamp=datetime.utcnow()
        )
        
        # Map to protocol
        protocol_message = vcc.map_command(vpp_command, "iec104")
        assert protocol_message is not None
        assert protocol_message.destination == "battery-001"
    
    def test_load_device_to_vcc_flow(self, vcc):
        """
        Test load device → VCC flow
        
        Validates: Requirements 3.1, 4.1, 4.2
        """
        load_device = LoadSimulator(
            device_id="load-001",
            parameters={
                "base_load_kw": 30.0,
                "flexibility_range": (0.8, 1.2)
            }
        )
        
        # Get device state
        device_state = load_device.get_state()
        assert device_state.device_id == "load-001"
        
        # Create demand response command
        vpp_command = VPPCommand(
            command_id="cmd-004",
            device_id="load-001",
            command_type="demand_response",
            parameters={"signal": 0.8},
            timestamp=datetime.utcnow()
        )
        
        # Map to protocol
        protocol_message = vcc.map_command(vpp_command, "mqtt")
        assert protocol_message is not None


class TestScenarioExecutionMetricsFlow:
    """Test scenario execution → metrics collection flow."""
    
    @pytest.fixture
    def scenario_engine(self):
        """Create scenario engine."""
        return ScenarioEngine()
    
    @pytest.fixture
    def metrics_collector(self):
        """Create metrics collector."""
        return MetricsCollector()
    
    def test_scenario_execution_with_metrics_collection(self, scenario_engine, metrics_collector, db_session):
        """
        Test scenario execution with metrics collection
        
        Validates: Requirements 7.1, 7.2, 7.3, 11.1
        """
        # Create scenario in memory
        scenario_id = scenario_engine.create_scenario(
            scenario_name="Test Scenario",
            description="Integration test scenario",
            duration=100.0
        )
        
        # Create scenario in database for metrics
        from models.scenario import Scenario, ScenarioStatus
        from datetime import datetime
        db_scenario = Scenario(
            id=scenario_id,
            name="Test Scenario",
            description="Integration test scenario",
            definition={},
            status=ScenarioStatus.RUNNING.value,
            start_time=datetime.utcnow()
        )
        db_session.add(db_scenario)
        db_session.commit()
        
        # Add events
        event1 = Event(
            event_id="evt-001",
            event_type=EventType.DEVICE_UPDATE,
            timestamp=10.0,
            device_id="device-001"
        )
        scenario_engine.add_event(scenario_id, event1)
        
        # Record metrics during scenario
        metrics_collector.record_metric(
            scenario_id=scenario_id,
            metric_name="power_output",
            value=50.0,
            tags={"device_id": "device-001"}
        )
        
        metrics_collector.record_metric(
            scenario_id=scenario_id,
            metric_name="latency_ms",
            value=25.5,
            tags={"protocol": "iec104"}
        )
        
        # Retrieve metrics
        metrics = metrics_collector.get_metrics(scenario_id)
        assert len(metrics) >= 2
        
        # Verify metrics have correct values
        power_metrics = [m for m in metrics if m.metric_name == "power_output"]
        assert len(power_metrics) > 0
        assert power_metrics[0].value == 50.0
    
    def test_scenario_metrics_aggregation(self, scenario_engine, metrics_collector, db_session):
        """
        Test metrics aggregation during scenario
        
        Validates: Requirements 11.2, 11.3
        """
        # Create scenario in memory
        scenario_id = scenario_engine.create_scenario(
            scenario_name="Aggregation Test",
            duration=60.0
        )
        
        # Create scenario in database for metrics
        from models.scenario import Scenario, ScenarioStatus
        from datetime import datetime
        db_scenario = Scenario(
            id=scenario_id,
            name="Aggregation Test",
            description="",
            definition={},
            status=ScenarioStatus.RUNNING.value,
            start_time=datetime.utcnow()
        )
        db_session.add(db_scenario)
        db_session.commit()
        
        # Record multiple metrics
        for i in range(10):
            metrics_collector.record_metric(
                scenario_id=scenario_id,
                metric_name="power_output",
                value=float(40 + i),
                tags={"device_id": "device-001"}
            )
        
        # Get metrics statistics
        stats = metrics_collector.get_metrics_statistics(
            scenario_id=scenario_id,
            metric_name="power_output"
        )
        
        assert stats["count"] == 10
        assert stats["min"] == 40.0
        assert stats["max"] == 49.0
        assert stats["avg"] == 44.5


class TestPowerFlowStabilityFlow:
    """Test power flow calculation → stability assessment flow."""
    
    @pytest.fixture
    def power_flow_engine(self):
        """Create power flow engine."""
        return PowerFlowEngine()
    
    def test_power_flow_calculation_with_stability_assessment(self, power_flow_engine):
        """
        Test power flow calculation with stability assessment
        
        Validates: Requirements 8.1, 8.2, 8.3, 8.4, 8.5
        """
        # Create network
        power_flow_engine.add_bus("bus-1", voltage_nominal=1.0, power_injection=100.0)
        power_flow_engine.add_bus("bus-2", voltage_nominal=1.0, power_injection=-50.0)
        power_flow_engine.add_bus("bus-3", voltage_nominal=1.0, power_injection=-50.0)
        
        # Add lines
        power_flow_engine.add_line("line-1", "bus-1", "bus-2", capacity=100.0)
        power_flow_engine.add_line("line-2", "bus-2", "bus-3", capacity=100.0)
        
        # Calculate power flow
        result = power_flow_engine.calculate_power_flow()
        
        # Verify result
        assert result is not None
        assert result.converged
        assert result.calculation_time < 500  # <500ms requirement
        assert len(result.buses) == 3
        assert len(result.lines) == 2
        
        # Verify stability assessment
        assert result.stability is not None
        assert result.stability.status is not None
    
    def test_violation_detection_in_power_flow(self, power_flow_engine):
        """
        Test violation detection during power flow
        
        Validates: Requirements 8.3
        """
        # Create network
        power_flow_engine.add_bus("bus-1", voltage_nominal=1.0)
        power_flow_engine.add_bus("bus-2", voltage_nominal=1.0)
        
        # Manually set voltage to trigger violation
        power_flow_engine.buses["bus-1"].voltage_actual = 1.15  # >10% violation
        
        # Calculate power flow
        result = power_flow_engine.calculate_power_flow()
        
        # Verify violations detected
        assert len(result.violations) > 0
        voltage_violations = [v for v in result.violations if "voltage" in str(v.violation_type).lower()]
        assert len(voltage_violations) > 0
    
    def test_congestion_detection_in_power_flow(self, power_flow_engine):
        """
        Test congestion detection during power flow
        
        Validates: Requirements 8.3
        """
        # Create network
        power_flow_engine.add_bus("bus-1", voltage_nominal=1.0)
        power_flow_engine.add_bus("bus-2", voltage_nominal=1.0)
        power_flow_engine.add_line("line-1", "bus-1", "bus-2", capacity=100.0)
        
        # Manually set line loading to trigger congestion
        power_flow_engine.lines["line-1"].loading_percent = 105.0  # >100% congestion
        
        # Calculate power flow
        result = power_flow_engine.calculate_power_flow()
        
        # Verify congestion detected
        assert len(result.violations) > 0
        congestion_violations = [v for v in result.violations if "congestion" in str(v.violation_type).lower()]
        assert len(congestion_violations) > 0


class TestErrorHandlingAcrossComponents:
    """Test error handling across all components."""
    
    def test_vcc_error_handling_invalid_protocol(self):
        """
        Test VCC error handling with invalid protocol
        
        Validates: Error handling across components
        """
        vcc = VCCCoordinator()
        
        vpp_command = VPPCommand(
            command_id="cmd-001",
            device_id="device-001",
            command_type="test",
            parameters={},
            timestamp=datetime.utcnow()
        )
        
        # Should raise error for invalid protocol
        with pytest.raises(ValidationError):
            vcc.map_command(vpp_command, "invalid_protocol")
    
    def test_protocol_simulator_error_handling_invalid_data(self):
        """
        Test protocol simulator error handling with invalid data
        
        Validates: Error handling across components
        """
        protocol_sim = ProtocolSimulator()
        
        # Should handle empty data gracefully
        with pytest.raises(ValidationError):
            protocol_sim.process_message(
                protocol="iec104",
                data=b"",
                source="vcc",
                destination="device-001"
            )
    
    def test_power_flow_error_handling_missing_bus(self):
        """
        Test power flow error handling with missing bus
        
        Validates: Error handling across components
        """
        power_flow_engine = PowerFlowEngine()
        
        # Try to add line without buses
        with pytest.raises(ValidationError):
            power_flow_engine.add_line(
                "line-1",
                "bus-1",
                "bus-2",
                capacity=100.0
            )
    
    def test_scenario_engine_error_handling_invalid_scenario(self):
        """
        Test scenario engine error handling with invalid scenario
        
        Validates: Error handling across components
        """
        scenario_engine = ScenarioEngine()
        
        # Try to execute non-existent scenario
        with pytest.raises(ValidationError):
            scenario_engine.execute_scenario("non-existent-scenario")
    
    def test_metrics_collector_error_handling_invalid_scenario(self):
        """
        Test metrics collector error handling with invalid scenario
        
        Validates: Error handling across components
        """
        metrics_collector = MetricsCollector()
        
        # Try to record metric with empty scenario ID
        with pytest.raises(ValueError):
            metrics_collector.record_metric(
                scenario_id="",
                metric_name="test_metric",
                value=10.0
            )


class TestNetworkConditionsIntegration:
    """Test network conditions integration with VCC and protocol simulator."""
    
    def test_vcc_with_network_latency(self):
        """
        Test VCC with network latency
        
        Validates: Requirements 4.3, 6.1
        """
        vcc = VCCCoordinator()
        network_sim = NetworkSimulator()
        
        vpp_command = VPPCommand(
            command_id="cmd-001",
            device_id="device-001",
            command_type="test",
            parameters={},
            timestamp=datetime.utcnow()
        )
        
        # Map command to protocol
        protocol_message = vcc.map_command(vpp_command, "iec104")
        
        # Apply network conditions
        latency_ms = 25.0
        protocol_message = vcc.apply_network_conditions(
            protocol_message,
            latency_ms=latency_ms,
            packet_loss_probability=0.0
        )
        
        assert protocol_message.latency_ms == latency_ms
    
    def test_vcc_with_packet_loss(self):
        """
        Test VCC with packet loss
        
        Validates: Requirements 4.4, 6.3
        """
        vcc = VCCCoordinator()
        
        vpp_command = VPPCommand(
            command_id="cmd-002",
            device_id="device-002",
            command_type="test",
            parameters={},
            timestamp=datetime.utcnow()
        )
        
        # Map command to protocol
        protocol_message = vcc.map_command(vpp_command, "mqtt")
        
        # Apply network conditions with packet loss
        protocol_message = vcc.apply_network_conditions(
            protocol_message,
            latency_ms=30.0,
            packet_loss_probability=0.5
        )
        
        # Packet loss is probabilistic, so we just verify the method works
        assert protocol_message is not None


class TestMultiDeviceIntegration:
    """Test integration with multiple devices."""
    
    def test_multiple_devices_with_vcc_and_protocol_simulator(self):
        """
        Test multiple devices through VCC and protocol simulator
        
        Validates: Requirements 1.5, 2.5, 3.5, 9.5
        """
        vcc = VCCCoordinator()
        protocol_sim = ProtocolSimulator()
        
        # Create multiple devices
        devices = []
        for i in range(10):
            if i % 3 == 0:
                device = SolarSimulator(
                    device_id=f"solar-{i:03d}",
                    parameters={
                        "capacity_kw": 100.0,
                        "efficiency": 0.18,
                        "location": "test-location"
                    }
                )
            elif i % 3 == 1:
                device = BatterySimulator(
                    device_id=f"battery-{i:03d}",
                    parameters={
                        "capacity_kwh": 50.0,
                        "power_rating_kw": 25.0,
                        "efficiency": 0.95
                    }
                )
            else:
                device = LoadSimulator(
                    device_id=f"load-{i:03d}",
                    parameters={
                        "base_load_kw": 30.0,
                        "flexibility_range": (0.8, 1.2)
                    }
                )
            devices.append(device)
        
        # Send commands to all devices through VCC
        for device in devices:
            vpp_command = VPPCommand(
                command_id=f"cmd-{device.device_id}",
                device_id=device.device_id,
                command_type="get_status",
                parameters={},
                timestamp=datetime.utcnow()
            )
            
            # Map to protocol
            protocol_message = vcc.map_command(vpp_command, "iec104")
            assert protocol_message is not None
            
            # Process through protocol simulator
            parsed_msg, comm_event = protocol_sim.process_message(
                protocol="iec104",
                data=b"test_message",
                source="vcc",
                destination=device.device_id
            )
            
            assert comm_event is not None
        
        # Verify all devices were processed
        assert protocol_sim.messages_processed == len(devices)


class TestMessageOrderingPreservation:
    """Test message ordering preservation across components."""
    
    def test_vcc_message_ordering_preservation(self):
        """
        Test VCC preserves message ordering
        
        Validates: Requirements 4.5
        """
        vcc = VCCCoordinator()
        
        # Send multiple commands from same device
        for i in range(5):
            vpp_command = VPPCommand(
                command_id=f"cmd-{i:03d}",
                device_id="device-001",
                command_type="test",
                parameters={"sequence": i},
                timestamp=datetime.utcnow()
            )
            
            # Map to protocol
            protocol_message = vcc.map_command(vpp_command, "iec104")
            
            # Check message ordering
            is_ordered = vcc.check_message_ordering(
                device_id="device-001",
                sequence_number=i
            )
            
            assert is_ordered
        
        # Verify no ordering violations
        assert vcc.message_ordering_violations == 0
@pytest.fixture
def db_session():
    """Create database session for tests."""
    session = get_session()
    yield session
    close_session(session)


# Property-based tests for integration scenarios

class TestIntegrationProperties:
    """Property-based tests for integration scenarios."""
    
    @given(
        num_devices=st.integers(min_value=1, max_value=50),
        num_events=st.integers(min_value=1, max_value=20)
    )
    @settings(max_examples=5, suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture])
    def test_property_multi_device_scenario_execution(self, num_devices, num_events, db_session):
        """
        Property: For any number of devices and events, scenario execution should complete
        without errors and collect metrics for all devices.
        
        Validates: Requirements 7.1, 7.2, 7.3, 9.5
        """
        scenario_engine = ScenarioEngine()
        metrics_collector = MetricsCollector()
        
        # Create scenario in memory
        scenario_id = scenario_engine.create_scenario(
            scenario_name=f"Property Test {num_devices} devices",
            duration=100.0
        )
        
        # Create scenario in database for metrics
        from models.scenario import Scenario, ScenarioStatus
        from datetime import datetime
        db_scenario = Scenario(
            id=scenario_id,
            name=f"Property Test {num_devices} devices",
            definition={},
            status=ScenarioStatus.RUNNING.value,
            start_time=datetime.utcnow()
        )
        db_session.add(db_scenario)
        db_session.commit()
        
        # Add events
        for i in range(num_events):
            event = Event(
                event_id=f"evt-{i:03d}",
                event_type=EventType.DEVICE_UPDATE,
                timestamp=float(i * 10),
                device_id=f"device-{i % num_devices:03d}"
            )
            scenario_engine.add_event(scenario_id, event)
        
        # Record metrics for each device
        for i in range(num_devices):
            metrics_collector.record_metric(
                scenario_id=scenario_id,
                metric_name="power_output",
                value=float(50 + i),
                tags={"device_id": f"device-{i:03d}"}
            )
        
        # Verify metrics were recorded
        metrics = metrics_collector.get_metrics(scenario_id)
        assert len(metrics) == num_devices
    
    @given(
        latency_ms=st.floats(min_value=0.0, max_value=100.0),
        packet_loss_prob=st.floats(min_value=0.0, max_value=0.1)
    )
    @settings(max_examples=20, suppress_health_check=[HealthCheck.too_slow])
    def test_property_vcc_network_conditions(self, latency_ms, packet_loss_prob):
        """
        Property: For any valid latency and packet loss probability, VCC should apply
        network conditions without errors.
        
        Validates: Requirements 4.3, 4.4, 6.1, 6.3
        """
        vcc = VCCCoordinator()
        
        vpp_command = VPPCommand(
            command_id="cmd-001",
            device_id="device-001",
            command_type="test",
            parameters={},
            timestamp=datetime.utcnow()
        )
        
        # Map command
        protocol_message = vcc.map_command(vpp_command, "iec104")
        
        # Apply network conditions
        protocol_message = vcc.apply_network_conditions(
            protocol_message,
            latency_ms=latency_ms,
            packet_loss_probability=packet_loss_prob
        )
        
        # Verify message was processed
        assert protocol_message is not None
        assert protocol_message.latency_ms == latency_ms
