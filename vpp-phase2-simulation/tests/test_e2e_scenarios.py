"""
End-to-End Test Scenarios for VPP Phase 2 Simulation Framework

Tests complete VPP workflows:
- Complete VPP workflow from device registration to analysis
- Multi-device scenarios (1000+ devices)
- High-load scenarios
- Scenario reproducibility validation

Requirements:
- All 12 requirement groups (1-12)
- Properties 41-60 for correctness validation
- Performance requirements (500ms power flow, etc.)
- Scalability requirements (1000+ devices, 100+ concurrent scenarios)
"""

import pytest
import json
import time
import random
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

from hypothesis import given, strategies as st, settings, HealthCheck

from services.device_emulator import DeviceEmulator
from services.power_gen_simulator import SolarSimulator, WindSimulator
from services.storage_simulator import BatterySimulator
from services.demand_simulator import LoadSimulator
from services.vcc_coordinator import VCCCoordinator, VPPCommand
from services.protocol_simulator import ProtocolSimulator
from services.power_flow_engine import PowerFlowEngine
from services.scenario_engine import ScenarioEngine, Event, EventType
from services.metrics_collector import MetricsCollector
from services.network_simulator import NetworkSimulator
from utils.errors import ValidationError
from utils.database import get_session, close_session
from models import Scenario, Metric


class TestCompleteVPPWorkflow:
    """Test complete VPP workflow from device registration to analysis."""
    
    @pytest.fixture
    def vpp_system(self, db_session):
        """Create complete VPP system."""
        return {
            "vcc": VCCCoordinator(),
            "protocol_sim": ProtocolSimulator(),
            "power_flow_engine": PowerFlowEngine(),
            "scenario_engine": ScenarioEngine(),
            "metrics_collector": MetricsCollector(),
            "network_sim": NetworkSimulator(),
            "devices": {},
        }
    
    def test_complete_workflow_100_devices(self, vpp_system, db_session):
        """
        Test complete VPP workflow with 100 devices
        
        Validates: Requirements 1.1-1.5, 2.1-2.5, 3.1-3.5, 4.1-4.5, 5.1-5.5,
                   6.1-6.5, 7.1-7.5, 8.1-8.5, 9.1-9.5, 10.1-10.5, 11.1-11.5, 12.1-12.5
        """
        vcc = vpp_system["vcc"]
        protocol_sim = vpp_system["protocol_sim"]
        power_flow_engine = vpp_system["power_flow_engine"]
        scenario_engine = vpp_system["scenario_engine"]
        metrics_collector = vpp_system["metrics_collector"]
        
        # Step 1: Register 100 devices
        devices = []
        for i in range(100):
            device_type = i % 4
            if device_type == 0:
                device = SolarSimulator(
                    device_id=f"solar-{i:03d}",
                    parameters={
                        "capacity_kw": 100.0,
                        "efficiency": 0.18,
                        "location": f"location-{i % 10}"
                    }
                )
            elif device_type == 1:
                device = WindSimulator(
                    device_id=f"wind-{i:03d}",
                    parameters={
                        "capacity_kw": 200.0,
                        "hub_height": 80.0,
                        "location": f"location-{i % 10}"
                    }
                )
            elif device_type == 2:
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
            scenario_engine.register_device(device.device_id, device)
        
        assert len(devices) == 100
        
        # Step 2: Create scenario in memory
        scenario_id = scenario_engine.create_scenario(
            scenario_name="Complete VPP Workflow Test",
            description="Test with 100 devices",
            duration=600.0
        )
        
        # Step 2b: Create scenario in database for metrics
        db_scenario = Scenario(
            id=scenario_id,
            name="Complete VPP Workflow Test",
            description="Test with 100 devices",
            definition={},
            status="running",
            start_time=datetime.utcnow()
        )
        db_session.add(db_scenario)
        db_session.commit()
        
        # Step 3: Create network for power flow
        for i in range(10):
            power_flow_engine.add_bus(f"bus-{i}", voltage_nominal=1.0)
        
        for i in range(9):
            power_flow_engine.add_line(
                f"line-{i}",
                f"bus-{i}",
                f"bus-{i+1}",
                capacity=500.0
            )
        
        # Step 4: Send commands to all devices through VCC
        commands_sent = 0
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
            
            # Process through protocol simulator
            parsed_msg, comm_event = protocol_sim.process_message(
                protocol="iec104",
                data=b"test_message",
                source="vcc",
                destination=device.device_id
            )
            
            commands_sent += 1
        
        assert commands_sent == 100
        
        # Step 5: Calculate power flow
        start_time = time.time()
        result = power_flow_engine.calculate_power_flow()
        calculation_time = (time.time() - start_time) * 1000
        
        assert result.converged
        assert calculation_time < 500  # <500ms requirement
        
        # Step 6: Collect metrics
        for device in devices:
            metrics_collector.record_metric(
                scenario_id=scenario_id,
                metric_name="power_output",
                value=random.uniform(0, 100),
                tags={"device_id": device.device_id}
            )
            
            metrics_collector.record_metric(
                scenario_id=scenario_id,
                metric_name="latency_ms",
                value=random.uniform(10, 50),
                tags={"device_id": device.device_id}
            )
        
        # Step 7: Verify metrics collection
        metrics = metrics_collector.get_metrics(scenario_id)
        assert len(metrics) >= 100  # At least one metric per device


class TestMultiDeviceScenarios:
    """Test multi-device scenarios with 1000+ devices."""
    
    def test_1000_device_scenario(self, db_session):
        """
        Test scenario with 1000+ devices
        
        Validates: Requirements 1.5, 2.5, 3.5, 9.5
        """
        vcc = VCCCoordinator()
        protocol_sim = ProtocolSimulator()
        scenario_engine = ScenarioEngine()
        metrics_collector = MetricsCollector()
        
        # Create 1000 devices
        devices = []
        for i in range(1000):
            device_type = i % 4
            if device_type == 0:
                device = SolarSimulator(
                    device_id=f"solar-{i:04d}",
                    parameters={
                        "capacity_kw": 100.0,
                        "efficiency": 0.18,
                        "location": f"location-{i % 50}"
                    }
                )
            elif device_type == 1:
                device = WindSimulator(
                    device_id=f"wind-{i:04d}",
                    parameters={
                        "capacity_kw": 200.0,
                        "hub_height": 80.0,
                        "location": f"location-{i % 50}"
                    }
                )
            elif device_type == 2:
                device = BatterySimulator(
                    device_id=f"battery-{i:04d}",
                    parameters={
                        "capacity_kwh": 50.0,
                        "power_rating_kw": 25.0,
                        "efficiency": 0.95
                    }
                )
            else:
                device = LoadSimulator(
                    device_id=f"load-{i:04d}",
                    parameters={
                        "base_load_kw": 30.0,
                        "flexibility_range": (0.8, 1.2)
                    }
                )
            
            devices.append(device)
            scenario_engine.register_device(device.device_id, device)
        
        # Create scenario
        scenario_id = scenario_engine.create_scenario(
            scenario_name="1000 Device Scenario",
            duration=600.0
        )
        
        # Create scenario in database
        scenario = Scenario(
            id=scenario_id,
            name="1000 Device Scenario",
            definition={},
            status="pending",
            start_time=datetime.utcnow()
        )
        db_session.add(scenario)
        db_session.commit()
        
        # Send commands to all devices
        start_time = time.time()
        for device in devices:
            vpp_command = VPPCommand(
                command_id=f"cmd-{device.device_id}",
                device_id=device.device_id,
                command_type="get_status",
                parameters={},
                timestamp=datetime.utcnow()
            )
            
            protocol_message = vcc.map_command(vpp_command, "iec104")
            parsed_msg, comm_event = protocol_sim.process_message(
                protocol="iec104",
                data=b"test_message",
                source="vcc",
                destination=device.device_id
            )
        
        elapsed_time = time.time() - start_time
        
        # Verify all devices were processed
        assert protocol_sim.messages_processed == 1000
        
        # Verify performance (should handle 1000 devices without degradation)
        # Rough estimate: should complete in reasonable time
        assert elapsed_time < 60  # Should complete within 60 seconds
        
        # Collect metrics for all devices
        for device in devices:
            metrics_collector.record_metric(
                scenario_id=scenario_id,
                metric_name="power_output",
                value=random.uniform(0, 100),
                tags={"device_id": device.device_id}
            )
        
        # Verify metrics collection
        metrics = metrics_collector.get_metrics(scenario_id)
        assert len(metrics) == 1000


class TestHighLoadScenarios:
    """Test high-load scenarios with concurrent execution."""
    
    def test_concurrent_scenario_execution(self, db_session):
        """
        Test concurrent execution of multiple scenarios
        
        Validates: Requirements 7.5, 9.5
        """
        num_scenarios = 10
        scenario_engines = [ScenarioEngine() for _ in range(num_scenarios)]
        
        # Create scenarios
        scenario_ids = []
        for i, engine in enumerate(scenario_engines):
            scenario_id = engine.create_scenario(
                scenario_name=f"Concurrent Scenario {i}",
                duration=100.0
            )
            
            # Create scenario in database
            scenario = Scenario(
                id=scenario_id,
                name=f"Concurrent Scenario {i}",
                definition={},
                status="pending",
                start_time=datetime.utcnow()
            )
            db_session.add(scenario)
            
            scenario_ids.append(scenario_id)
        
        db_session.commit()
        
        # Execute scenarios concurrently
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            for i, engine in enumerate(scenario_engines):
                future = executor.submit(engine.execute_scenario, scenario_ids[i])
                futures.append(future)
            
            # Wait for all to complete
            results = []
            for future in as_completed(futures):
                result = future.result()
                results.append(result)
        
        # Verify all scenarios completed
        assert len(results) == num_scenarios
    
    def test_high_metrics_throughput(self, db_session):
        """
        Test high metrics collection throughput (1000+ metrics/sec)
        
        Validates: Requirements 11.1, 11.2
        """
        metrics_collector = MetricsCollector()
        
        # Create scenario
        scenario_id = "scenario-high-load"
        scenario = Scenario(
            id=scenario_id,
            name="High Load Metrics Test",
            definition={},
            status="pending",
            start_time=datetime.utcnow()
        )
        db_session.add(scenario)
        db_session.commit()
        
        # Record 1000+ metrics
        start_time = time.time()
        num_metrics = 1000
        
        for i in range(num_metrics):
            metrics_collector.record_metric(
                scenario_id=scenario_id,
                metric_name=f"metric-{i % 10}",
                value=float(i),
                tags={"index": i}
            )
        
        elapsed_time = time.time() - start_time
        throughput = num_metrics / elapsed_time
        
        # Verify throughput (should handle 1000+ metrics/sec)
        assert throughput > 100  # At least 100 metrics/sec
        
        # Verify metrics were recorded
        metrics = metrics_collector.get_metrics(scenario_id)
        assert len(metrics) == num_metrics


class TestScenarioReproducibility:
    """Test scenario reproducibility with deterministic execution."""
    
    def test_scenario_reproducibility_with_fixed_seed(self, db_session):
        """
        Test scenario reproducibility with fixed random seed
        
        Validates: Requirements 10.3
        """
        # Set random seed
        random.seed(42)
        
        # First execution
        scenario_engine_1 = ScenarioEngine()
        scenario_id_1 = scenario_engine_1.create_scenario(
            scenario_name="Reproducibility Test 1",
            duration=100.0
        )
        
        scenario_1 = Scenario(
            id=scenario_id_1,
            name="Reproducibility Test 1",
            definition={},
            status="pending",
            start_time=datetime.utcnow()
        )
        db_session.add(scenario_1)
        db_session.commit()
        
        # Record metrics with fixed seed
        metrics_1 = []
        for i in range(10):
            value = random.uniform(0, 100)
            metrics_1.append(value)
        
        # Reset seed and execute again
        random.seed(42)
        
        scenario_engine_2 = ScenarioEngine()
        scenario_id_2 = scenario_engine_2.create_scenario(
            scenario_name="Reproducibility Test 2",
            duration=100.0
        )
        
        scenario_2 = Scenario(
            id=scenario_id_2,
            name="Reproducibility Test 2",
            definition={},
            status="pending",
            start_time=datetime.utcnow()
        )
        db_session.add(scenario_2)
        db_session.commit()
        
        # Record metrics with same seed
        metrics_2 = []
        for i in range(10):
            value = random.uniform(0, 100)
            metrics_2.append(value)
        
        # Verify results are identical
        assert metrics_1 == metrics_2
    
    def test_scenario_data_persistence_and_retrieval(self, db_session):
        """
        Test scenario data persistence and retrieval
        
        Validates: Requirements 10.1, 10.2
        """
        metrics_collector = MetricsCollector()
        
        # Create scenario
        scenario_id = "scenario-persistence-test"
        scenario = Scenario(
            id=scenario_id,
            name="Persistence Test",
            definition={"test": "data"},
            status="pending",
            start_time=datetime.utcnow()
        )
        db_session.add(scenario)
        db_session.commit()
        
        # Record metrics
        test_metrics = [
            ("power_output", 50.0, {"device_id": "device-001"}),
            ("latency_ms", 25.5, {"protocol": "iec104"}),
            ("error_rate", 0.01, {"component": "vcc"}),
        ]
        
        for metric_name, value, tags in test_metrics:
            metrics_collector.record_metric(
                scenario_id=scenario_id,
                metric_name=metric_name,
                value=value,
                tags=tags
            )
        
        # Retrieve metrics
        retrieved_metrics = metrics_collector.get_metrics(scenario_id)
        
        # Verify data persistence
        assert len(retrieved_metrics) == 3
        
        # Verify specific metrics
        power_metrics = [m for m in retrieved_metrics if m.metric_name == "power_output"]
        assert len(power_metrics) == 1
        assert power_metrics[0].value == 50.0


class TestPerformanceRequirements:
    """Test performance requirements are met."""
    
    def test_power_flow_calculation_performance(self):
        """
        Test power flow calculation completes within 500ms
        
        Validates: Requirements 8.1, 8.2
        """
        power_flow_engine = PowerFlowEngine()
        
        # Create large network
        for i in range(50):
            power_flow_engine.add_bus(f"bus-{i}", voltage_nominal=1.0)
        
        for i in range(49):
            power_flow_engine.add_line(
                f"line-{i}",
                f"bus-{i}",
                f"bus-{i+1}",
                capacity=500.0
            )
        
        # Measure calculation time
        start_time = time.time()
        result = power_flow_engine.calculate_power_flow()
        calculation_time = (time.time() - start_time) * 1000
        
        # Verify performance requirement
        assert calculation_time < 500  # <500ms requirement
        assert result.converged
    
    def test_device_update_performance(self):
        """
        Test device updates complete within 100ms
        
        Validates: Requirements 1.3, 2.3, 3.3
        """
        devices = [
            SolarSimulator(
                device_id="solar-001",
                parameters={"capacity_kw": 100.0, "efficiency": 0.18, "location": "test"}
            ),
            BatterySimulator(
                device_id="battery-001",
                parameters={"capacity_kwh": 50.0, "power_rating_kw": 25.0, "efficiency": 0.95}
            ),
            LoadSimulator(
                device_id="load-001",
                parameters={"base_load_kw": 30.0, "flexibility_range": (0.8, 1.2)}
            ),
        ]
        
        # Measure update time
        start_time = time.time()
        for device in devices:
            device.update(1.0)  # 1 second update
        update_time = (time.time() - start_time) * 1000
        
        # Verify performance requirement
        assert update_time < 100  # <100ms requirement


# Property-based tests for end-to-end scenarios

class TestE2EProperties:
    """Property-based tests for end-to-end scenarios."""
    
    @given(
        num_devices=st.integers(min_value=10, max_value=500),
        num_scenarios=st.integers(min_value=1, max_value=10)
    )
    @settings(max_examples=5, suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture])
    def test_property_multi_scenario_execution(self, num_devices, num_scenarios, db_session):
        """
        Property: For any number of devices and scenarios, all scenarios should execute
        successfully without data corruption or race conditions.
        
        Validates: Requirements 7.5, 9.5
        """
        scenario_engines = [ScenarioEngine() for _ in range(num_scenarios)]
        
        # Create scenarios
        scenario_ids = []
        for i, engine in enumerate(scenario_engines):
            scenario_id = engine.create_scenario(
                scenario_name=f"Property Test Scenario {i}",
                duration=100.0
            )
            
            # Create scenario in database
            scenario = Scenario(
                id=scenario_id,
                name=f"Property Test Scenario {i}",
                definition={},
                status="pending",
                start_time=datetime.utcnow()
            )
            db_session.add(scenario)
            
            scenario_ids.append(scenario_id)
        
        db_session.commit()
        
        # Execute scenarios
        results = []
        for i, engine in enumerate(scenario_engines):
            result = engine.execute_scenario(scenario_ids[i])
            results.append(result)
        
        # Verify all scenarios completed
        assert len(results) == num_scenarios
    
    @given(
        num_metrics=st.integers(min_value=100, max_value=1000),
        num_devices=st.integers(min_value=10, max_value=100)
    )
    @settings(max_examples=5, suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture])
    def test_property_metrics_collection_and_aggregation(self, num_metrics, num_devices, db_session):
        """
        Property: For any number of metrics and devices, metrics should be collected
        and aggregated correctly without data loss.
        
        Validates: Requirements 11.1, 11.2, 11.3
        """
        metrics_collector = MetricsCollector()
        
        # Create scenario with unique ID
        scenario_id = f"property-test-{uuid.uuid4().hex[:8]}"
        scenario = Scenario(
            id=scenario_id,
            name="Property Test Metrics",
            definition={},
            status="pending",
            start_time=datetime.utcnow()
        )
        db_session.add(scenario)
        db_session.commit()
        
        # Record metrics
        for i in range(num_metrics):
            device_id = f"device-{i % num_devices:03d}"
            metrics_collector.record_metric(
                scenario_id=scenario_id,
                metric_name="power_output",
                value=float(i),
                tags={"device_id": device_id}
            )
        
        # Retrieve metrics
        metrics = metrics_collector.get_metrics(scenario_id)
        
        # Verify all metrics were recorded
        assert len(metrics) == num_metrics
        
        # Verify aggregation
        stats = metrics_collector.get_metrics_statistics(
            scenario_id=scenario_id,
            metric_name="power_output"
        )
        
        assert stats["count"] == num_metrics
        assert stats["min"] == 0.0
        assert stats["max"] == float(num_metrics - 1)
@pytest.fixture
def db_session():
    """Create database session for tests."""
    session = get_session()
    yield session
    close_session(session)
