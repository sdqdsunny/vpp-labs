"""
Property-based tests for Scenario Engine.

Feature: vpp-phase2-simulation
Properties: 30-34
"""

import pytest
from hypothesis import given, strategies as st, settings
import json
import csv
import io

from services.scenario_engine import (
    ScenarioEngine,
    Event,
    EventType,
    ScenarioStatus,
)


class TestScenarioEngineProperties:
    """Property-based tests for Scenario Engine."""

    @given(
        event_times=st.lists(
            st.floats(min_value=0, max_value=1000, allow_nan=False, allow_infinity=False),
            min_size=1,
            max_size=20,
            unique=True,
        ),
    )
    @settings(max_examples=100)
    def test_property_30_event_scheduling_accuracy(self, event_times):
        """
        Property 30: Event Scheduling Accuracy
        
        For any scenario with events scheduled at specific times, the events should 
        execute at the specified times (within ±100ms tolerance).
        
        **Validates: Requirements 7.1**
        """
        engine = ScenarioEngine()
        scenario_id = engine.create_scenario("Test Scenario")

        # Sort event times
        sorted_times = sorted(event_times)
        num_events = len(sorted_times)

        # Track execution times
        execution_times = []

        def event_handler(event: Event, eng: ScenarioEngine):
            """Handler to track event execution time."""
            execution_times.append(eng.scheduler.current_time)

        # Register handler
        engine.register_event_handler(EventType.DEVICE_UPDATE, event_handler)

        # Add events
        for i, event_time in enumerate(sorted_times):
            event = Event(
                event_id=f"event_{i}",
                timestamp=event_time,
                event_type=EventType.DEVICE_UPDATE,
                device_id=f"device_{i}",
                parameters={"value": i},
            )
            engine.add_event(scenario_id, event)

        # Execute scenario
        result = engine.execute_scenario(scenario_id)

        # Verify execution
        assert result.status == ScenarioStatus.COMPLETED
        assert result.events_executed == num_events
        assert len(execution_times) == num_events

        # Verify timing accuracy (within ±100ms = 0.1s)
        tolerance = 0.1
        for i, (expected_time, actual_time) in enumerate(zip(sorted_times, execution_times)):
            time_diff = abs(actual_time - expected_time)
            assert (
                time_diff <= tolerance
            ), f"Event {i}: expected {expected_time}, got {actual_time}, diff {time_diff}"

    @given(
        event_times=st.lists(
            st.floats(min_value=0, max_value=500, allow_nan=False, allow_infinity=False),
            min_size=1,
            max_size=15,
            unique=True,
        ),
    )
    @settings(max_examples=100)
    def test_property_31_event_triggering(self, event_times):
        """
        Property 31: Event Triggering
        
        For any scenario event that occurs, the event should trigger appropriate 
        simulator updates and state changes.
        
        **Validates: Requirements 7.2**
        """
        engine = ScenarioEngine()
        scenario_id = engine.create_scenario("Test Scenario")

        # Sort event times
        sorted_times = sorted(event_times)
        num_events = len(sorted_times)

        # Track triggered events
        triggered_events = []

        def event_handler(event: Event, eng: ScenarioEngine):
            """Handler to track triggered events."""
            triggered_events.append(
                {
                    "event_id": event.event_id,
                    "timestamp": event.timestamp,
                    "event_type": event.event_type,
                    "parameters": event.parameters,
                }
            )

        # Register handler
        engine.register_event_handler(EventType.DEVICE_UPDATE, event_handler)

        # Add events
        for i, event_time in enumerate(sorted_times):
            event = Event(
                event_id=f"event_{i}",
                timestamp=event_time,
                event_type=EventType.DEVICE_UPDATE,
                device_id=f"device_{i}",
                parameters={"value": i * 10},
            )
            engine.add_event(scenario_id, event)

        # Execute scenario
        result = engine.execute_scenario(scenario_id)

        # Verify all events were triggered
        assert result.status == ScenarioStatus.COMPLETED
        assert result.events_executed == num_events
        assert len(triggered_events) == num_events

        # Verify event data integrity
        for i, triggered_event in enumerate(triggered_events):
            assert triggered_event["event_id"] == f"event_{i}"
            assert triggered_event["event_type"] == EventType.DEVICE_UPDATE
            assert triggered_event["parameters"]["value"] == i * 10

    @given(
        event_times=st.lists(
            st.floats(min_value=0, max_value=500, allow_nan=False, allow_infinity=False),
            min_size=1,
            max_size=15,
            unique=True,
        ),
    )
    @settings(max_examples=100)
    def test_property_32_metrics_collection_during_scenario(self, event_times):
        """
        Property 32: Metrics Collection During Scenario
        
        For any scenario execution, the system should collect metrics and results 
        throughout the scenario execution.
        
        **Validates: Requirements 7.3**
        """
        engine = ScenarioEngine()
        scenario_id = engine.create_scenario("Test Scenario")

        # Sort event times
        sorted_times = sorted(event_times)
        num_events = len(sorted_times)

        def event_handler(event: Event, eng: ScenarioEngine):
            """Handler to record metrics."""
            eng.metrics_collector.record_metric(
                metric_name="event_executed",
                value=1,
                device_id=event.device_id,
                timestamp=eng.scheduler.current_time,
                tags={"event_type": event.event_type.value},
            )

        # Register handler
        engine.register_event_handler(EventType.DEVICE_UPDATE, event_handler)

        # Add events
        for i, event_time in enumerate(sorted_times):
            event = Event(
                event_id=f"event_{i}",
                timestamp=event_time,
                event_type=EventType.DEVICE_UPDATE,
                device_id=f"device_{i}",
                parameters={"value": i},
            )
            engine.add_event(scenario_id, event)

        # Execute scenario
        result = engine.execute_scenario(scenario_id)

        # Verify execution
        assert result.status == ScenarioStatus.COMPLETED
        assert result.events_executed == num_events

        # Verify metrics were collected
        assert result.metrics_collected == num_events
        assert len(result.metrics) == num_events

        # Verify metric data
        for i, metric in enumerate(result.metrics):
            assert metric.metric_name == "event_executed"
            assert metric.value == 1
            assert metric.device_id == f"device_{i}"

    @given(
        event_times=st.lists(
            st.floats(min_value=0, max_value=300, allow_nan=False, allow_infinity=False),
            min_size=1,
            max_size=10,
            unique=True,
        ),
    )
    @settings(max_examples=50)
    def test_property_33_scenario_report_generation(self, event_times):
        """
        Property 33: Scenario Report Generation
        
        For any completed scenario, the system should generate a comprehensive report 
        with all results, metrics, and analysis.
        
        **Validates: Requirements 7.4**
        """
        engine = ScenarioEngine()
        scenario_id = engine.create_scenario("Test Scenario")

        # Sort event times
        sorted_times = sorted(event_times)
        num_events = len(sorted_times)

        # Add events
        for i, event_time in enumerate(sorted_times):
            event = Event(
                event_id=f"event_{i}",
                timestamp=event_time,
                event_type=EventType.DEVICE_UPDATE,
                device_id=f"device_{i}",
                parameters={"value": i * 5},
            )
            engine.add_event(scenario_id, event)

        # Execute scenario
        result = engine.execute_scenario(scenario_id)
        assert result.status == ScenarioStatus.COMPLETED

        # Generate report
        report = engine.generate_report(scenario_id)

        # Verify report structure
        assert "scenario_id" in report
        assert "scenario_name" in report
        assert "scenario_description" in report
        assert "execution_result" in report
        assert "aggregated_metrics" in report
        assert "generated_at" in report

        # Verify report content
        assert report["scenario_id"] == scenario_id
        assert report["execution_result"]["status"] == ScenarioStatus.COMPLETED.value
        assert report["execution_result"]["events_executed"] == num_events

        # Test JSON export
        json_export = engine.export_report(scenario_id, format="json")
        assert isinstance(json_export, str)
        json_data = json.loads(json_export)
        assert json_data["scenario_id"] == scenario_id
        assert json_data["execution_result"]["events_executed"] == num_events

        # Test CSV export (may be empty if no metrics collected)
        csv_export = engine.export_report(scenario_id, format="csv")
        assert isinstance(csv_export, str)

    @given(
        num_scenarios=st.integers(min_value=2, max_value=5),
        events_per_scenario=st.integers(min_value=1, max_value=8),
    )
    @settings(max_examples=50)
    def test_property_34_parallel_scenario_execution(
        self, num_scenarios, events_per_scenario
    ):
        """
        Property 34: Parallel Scenario Execution
        
        For any set of multiple scenarios, the system should support parallel execution 
        without interference between scenarios.
        
        **Validates: Requirements 7.5**
        """
        engine = ScenarioEngine()
        # Create multiple scenarios
        scenario_ids = []
        for s in range(num_scenarios):
            scenario_id = engine.create_scenario(f"Test Scenario {s}")
            scenario_ids.append(scenario_id)

            # Add events to each scenario
            for e in range(events_per_scenario):
                event = Event(
                    event_id=f"event_{s}_{e}",
                    timestamp=float(e * 10),
                    event_type=EventType.DEVICE_UPDATE,
                    device_id=f"device_{s}_{e}",
                    parameters={"value": s * 100 + e},
                )
                engine.add_event(scenario_id, event)

        # Execute scenarios in parallel
        futures = []
        for scenario_id in scenario_ids:
            future = engine.execute_scenario_async(scenario_id)
            futures.append(future)

        # Wait for all scenarios to complete
        results = []
        for future in futures:
            result = future.result(timeout=10)
            results.append(result)

        # Verify all scenarios completed
        assert len(results) == num_scenarios
        for result in results:
            assert result.status == ScenarioStatus.COMPLETED
            assert result.events_executed == events_per_scenario

        # Verify no interference between scenarios
        for i, result in enumerate(results):
            assert result.scenario_id == scenario_ids[i]

        # Verify each scenario has independent execution
        for i, scenario_id in enumerate(scenario_ids):
            report = engine.generate_report(scenario_id)
            assert report["execution_result"]["events_executed"] == events_per_scenario


class TestScenarioEngineBehavior:
    """Behavior tests for Scenario Engine."""

    def test_event_ordering_preserved(self):
        """Test that events execute in chronological order."""
        engine = ScenarioEngine()
        scenario_id = engine.create_scenario("Test Scenario")

        execution_order = []

        def event_handler(event: Event, eng: ScenarioEngine):
            """Handler to track execution order."""
            execution_order.append(event.event_id)

        engine.register_event_handler(EventType.DEVICE_UPDATE, event_handler)

        # Add events in random order
        event_times = [50, 10, 30, 20, 40]
        for i, event_time in enumerate(event_times):
            event = Event(
                event_id=f"event_{event_time}",
                timestamp=float(event_time),
                event_type=EventType.DEVICE_UPDATE,
                parameters={"value": event_time},
            )
            engine.add_event(scenario_id, event)

        # Execute scenario
        result = engine.execute_scenario(scenario_id)

        # Verify events executed in chronological order
        assert result.status == ScenarioStatus.COMPLETED
        assert execution_order == ["event_10", "event_20", "event_30", "event_40", "event_50"]

    def test_scenario_isolation(self):
        """Test that multiple scenarios don't interfere with each other."""
        engine = ScenarioEngine()
        # Create two scenarios
        scenario_1_id = engine.create_scenario("Scenario 1")
        scenario_2_id = engine.create_scenario("Scenario 2")

        # Add different events to each scenario
        for i in range(3):
            event_1 = Event(
                event_id=f"s1_event_{i}",
                timestamp=float(i * 10),
                event_type=EventType.DEVICE_UPDATE,
                device_id=f"device_1_{i}",
                parameters={"value": 100 + i},
            )
            engine.add_event(scenario_1_id, event_1)

            event_2 = Event(
                event_id=f"s2_event_{i}",
                timestamp=float(i * 20),
                event_type=EventType.DEVICE_UPDATE,
                device_id=f"device_2_{i}",
                parameters={"value": 200 + i},
            )
            engine.add_event(scenario_2_id, event_2)

        # Execute scenarios
        result_1 = engine.execute_scenario(scenario_1_id)
        result_2 = engine.execute_scenario(scenario_2_id)

        # Verify both completed successfully
        assert result_1.status == ScenarioStatus.COMPLETED
        assert result_2.status == ScenarioStatus.COMPLETED
        assert result_1.events_executed == 3
        assert result_2.events_executed == 3

        # Verify reports are independent
        report_1 = engine.generate_report(scenario_1_id)
        report_2 = engine.generate_report(scenario_2_id)

        assert report_1["scenario_id"] == scenario_1_id
        assert report_2["scenario_id"] == scenario_2_id
        assert report_1["execution_result"]["events_executed"] == 3
        assert report_2["execution_result"]["events_executed"] == 3
