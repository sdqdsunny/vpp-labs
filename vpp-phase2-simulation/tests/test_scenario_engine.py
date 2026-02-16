"""
Unit tests for Scenario Engine

Tests EventScheduler, MetricsCollector, and ScenarioEngine classes.

Requirements:
- 7.1: Event scheduling and execution
- 7.2: Event triggering and simulator updates
- 7.3: Metrics collection during scenario execution
- 7.4: Scenario report generation
- 7.5: Parallel scenario execution
"""

import pytest
import json
import time
from datetime import datetime
from concurrent.futures import Future

from services.scenario_engine import (
    EventScheduler,
    MetricsCollector,
    ScenarioEngine,
    Event,
    EventType,
    ScenarioStatus,
    ScenarioMetric,
    ScenarioResult,
)
from utils.errors import ValidationError


class TestEventScheduler:
    """Test EventScheduler class."""
    
    @pytest.fixture
    def scheduler(self):
        """Create event scheduler."""
        return EventScheduler()
    
    def test_scheduler_initialization(self, scheduler):
        """Test scheduler initialization."""
        assert scheduler.current_time == 0.0
        assert len(scheduler.events) == 0
        assert len(scheduler.executed_events) == 0
    
    def test_schedule_event(self, scheduler):
        """Test scheduling an event."""
        event = Event(
            event_id="evt-001",
            event_type=EventType.DEVICE_UPDATE,
            timestamp=10.0,
            device_id="device-001",
        )
        
        scheduler.schedule_event(event)
        
        assert len(scheduler.events) == 1
    
    def test_schedule_multiple_events(self, scheduler):
        """Test scheduling multiple events."""
        events = [
            Event(
                event_id=f"evt-{i:03d}",
                event_type=EventType.DEVICE_UPDATE,
                timestamp=float(i * 10),
                device_id=f"device-{i:03d}",
            )
            for i in range(1, 6)
        ]
        
        for event in events:
            scheduler.schedule_event(event)
        
        assert len(scheduler.events) == 5
    
    def test_schedule_event_in_past_raises_error(self, scheduler):
        """Test scheduling event in past raises error."""
        scheduler.current_time = 100.0
        
        event = Event(
            event_id="evt-001",
            event_type=EventType.DEVICE_UPDATE,
            timestamp=50.0,
        )
        
        with pytest.raises(ValidationError):
            scheduler.schedule_event(event)
    
    def test_get_next_event(self, scheduler):
        """Test getting next event."""
        event1 = Event(
            event_id="evt-001",
            event_type=EventType.DEVICE_UPDATE,
            timestamp=10.0,
        )
        event2 = Event(
            event_id="evt-002",
            event_type=EventType.DEVICE_COMMAND,
            timestamp=20.0,
        )
        
        scheduler.schedule_event(event2)
        scheduler.schedule_event(event1)
        
        next_event = scheduler.get_next_event()
        
        assert next_event.event_id == "evt-001"
        assert next_event.timestamp == 10.0
    
    def test_get_next_event_empty_returns_none(self, scheduler):
        """Test getting next event when empty returns None."""
        next_event = scheduler.get_next_event()
        
        assert next_event is None
    
    def test_advance_time(self, scheduler):
        """Test advancing time."""
        scheduler.advance_time(10.0)
        
        assert scheduler.current_time == 10.0
    
    def test_advance_time_multiple(self, scheduler):
        """Test advancing time multiple times."""
        scheduler.advance_time(10.0)
        scheduler.advance_time(5.0)
        scheduler.advance_time(15.0)
        
        assert scheduler.current_time == 30.0
    
    def test_advance_time_negative_raises_error(self, scheduler):
        """Test advancing time with negative delta raises error."""
        with pytest.raises(ValidationError):
            scheduler.advance_time(-5.0)
    
    def test_get_pending_events_at_time(self, scheduler):
        """Test getting pending events at specific time."""
        events = [
            Event(
                event_id=f"evt-{i:03d}",
                event_type=EventType.DEVICE_UPDATE,
                timestamp=10.0,
            )
            for i in range(1, 4)
        ]
        
        for event in events:
            scheduler.schedule_event(event)
        
        pending = scheduler.get_pending_events_at_time(10.0)
        
        assert len(pending) == 3
    
    def test_get_pending_events_at_time_partial(self, scheduler):
        """Test getting pending events at specific time (partial)."""
        events = [
            Event(
                event_id=f"evt-{i:03d}",
                event_type=EventType.DEVICE_UPDATE,
                timestamp=float(i * 10),
            )
            for i in range(1, 4)
        ]
        
        for event in events:
            scheduler.schedule_event(event)
        
        pending = scheduler.get_pending_events_at_time(15.0)
        
        # Events at time <= 15.0: evt-001 (10.0) only
        assert len(pending) == 1
        assert pending[0].event_id == "evt-001"
    
    def test_event_priority_ordering(self, scheduler):
        """Test events are ordered by priority when timestamps equal."""
        event1 = Event(
            event_id="evt-001",
            event_type=EventType.DEVICE_UPDATE,
            timestamp=10.0,
            priority=1,
        )
        event2 = Event(
            event_id="evt-002",
            event_type=EventType.DEVICE_COMMAND,
            timestamp=10.0,
            priority=5,
        )
        
        scheduler.schedule_event(event1)
        scheduler.schedule_event(event2)
        
        next_event = scheduler.get_next_event()
        
        assert next_event.event_id == "evt-002"  # Higher priority
    
    def test_scheduler_reset(self, scheduler):
        """Test scheduler reset."""
        event = Event(
            event_id="evt-001",
            event_type=EventType.DEVICE_UPDATE,
            timestamp=10.0,
        )
        
        scheduler.schedule_event(event)
        scheduler.advance_time(5.0)
        scheduler.reset()
        
        assert scheduler.current_time == 0.0
        assert len(scheduler.events) == 0
        assert len(scheduler.executed_events) == 0


class TestMetricsCollector:
    """Test MetricsCollector class."""
    
    @pytest.fixture
    def collector(self):
        """Create metrics collector."""
        return MetricsCollector()
    
    def test_collector_initialization(self, collector):
        """Test collector initialization."""
        assert len(collector.metrics) == 0
        assert len(collector.aggregated_metrics) == 0
    
    def test_record_metric(self, collector):
        """Test recording a metric."""
        collector.record_metric(
            metric_name="power_output",
            value=100.0,
            timestamp=1.0,
            device_id="device-001",
        )
        
        assert len(collector.metrics) == 1
        assert collector.metrics[0].metric_name == "power_output"
        assert collector.metrics[0].value == 100.0
    
    def test_record_multiple_metrics(self, collector):
        """Test recording multiple metrics."""
        for i in range(1, 6):
            collector.record_metric(
                metric_name="power_output",
                value=float(i * 10),
                timestamp=float(i),
                device_id="device-001",
            )
        
        assert len(collector.metrics) == 5
    
    def test_record_metric_without_device_id(self, collector):
        """Test recording metric without device ID."""
        collector.record_metric(
            metric_name="system_load",
            value=500.0,
            timestamp=1.0,
        )
        
        assert len(collector.metrics) == 1
        assert collector.metrics[0].device_id is None
    
    def test_record_metric_with_tags(self, collector):
        """Test recording metric with tags."""
        collector.record_metric(
            metric_name="power_output",
            value=100.0,
            timestamp=1.0,
            device_id="device-001",
            tags={"type": "solar", "location": "north"},
        )
        
        assert len(collector.metrics) == 1
        assert collector.metrics[0].tags["type"] == "solar"
    
    def test_get_metrics(self, collector):
        """Test getting all metrics."""
        for i in range(1, 4):
            collector.record_metric(
                metric_name="power_output",
                value=float(i * 10),
                timestamp=float(i),
            )
        
        metrics = collector.get_metrics()
        
        assert len(metrics) == 3
    
    def test_get_aggregated_metrics(self, collector):
        """Test getting aggregated metrics."""
        values = [100.0, 150.0, 200.0, 250.0, 300.0]
        
        for i, value in enumerate(values):
            collector.record_metric(
                metric_name="power_output",
                value=value,
                timestamp=float(i),
                device_id="device-001",
            )
        
        aggregated = collector.get_aggregated_metrics()
        
        assert "power_output:device-001" in aggregated
        assert aggregated["power_output:device-001"]["min"] == 100.0
        assert aggregated["power_output:device-001"]["max"] == 300.0
        assert aggregated["power_output:device-001"]["avg"] == 200.0
        assert aggregated["power_output:device-001"]["count"] == 5
    
    def test_get_aggregated_metrics_multiple_devices(self, collector):
        """Test aggregated metrics for multiple devices."""
        for device_id in ["device-001", "device-002"]:
            for i in range(1, 4):
                collector.record_metric(
                    metric_name="power_output",
                    value=float(i * 10),
                    timestamp=float(i),
                    device_id=device_id,
                )
        
        aggregated = collector.get_aggregated_metrics()
        
        assert len(aggregated) == 2
        assert "power_output:device-001" in aggregated
        assert "power_output:device-002" in aggregated
    
    def test_collector_reset(self, collector):
        """Test collector reset."""
        collector.record_metric(
            metric_name="power_output",
            value=100.0,
            timestamp=1.0,
        )
        
        collector.reset()
        
        assert len(collector.metrics) == 0
        assert len(collector.aggregated_metrics) == 0


class TestScenarioEngine:
    """Test ScenarioEngine class."""
    
    @pytest.fixture
    def engine(self):
        """Create scenario engine."""
        return ScenarioEngine()
    
    def test_engine_initialization(self, engine):
        """Test engine initialization."""
        assert engine.engine_id is not None
        assert len(engine.scenarios) == 0
        assert len(engine.devices) == 0
        assert len(engine.execution_results) == 0
    
    def test_engine_initialization_with_id(self):
        """Test engine initialization with custom ID."""
        engine = ScenarioEngine(engine_id="engine-custom")
        
        assert engine.engine_id == "engine-custom"
    
    def test_create_scenario(self, engine):
        """Test creating a scenario."""
        scenario_id = engine.create_scenario(
            scenario_name="Test Scenario",
            description="Test scenario description",
            duration=3600.0,
        )
        
        assert scenario_id is not None
        assert scenario_id in engine.scenarios
        assert engine.scenarios[scenario_id]["name"] == "Test Scenario"
    
    def test_create_multiple_scenarios(self, engine):
        """Test creating multiple scenarios."""
        scenario_ids = []
        for i in range(1, 4):
            scenario_id = engine.create_scenario(
                scenario_name=f"Scenario {i}",
                duration=3600.0,
            )
            scenario_ids.append(scenario_id)
        
        assert len(engine.scenarios) == 3
        assert all(sid in engine.scenarios for sid in scenario_ids)
    
    def test_add_event_to_scenario(self, engine):
        """Test adding event to scenario."""
        scenario_id = engine.create_scenario("Test Scenario")
        
        event = Event(
            event_id="evt-001",
            event_type=EventType.DEVICE_UPDATE,
            timestamp=10.0,
            device_id="device-001",
        )
        
        engine.add_event(scenario_id, event)
        
        assert len(engine.scenarios[scenario_id]["events"]) == 1
    
    def test_add_event_to_nonexistent_scenario_raises_error(self, engine):
        """Test adding event to nonexistent scenario raises error."""
        event = Event(
            event_id="evt-001",
            event_type=EventType.DEVICE_UPDATE,
            timestamp=10.0,
        )
        
        with pytest.raises(ValidationError):
            engine.add_event("nonexistent-scenario", event)
    
    def test_register_device(self, engine):
        """Test registering a device."""
        class MockDevice:
            def __init__(self, device_id):
                self.device_id = device_id
        
        device = MockDevice("device-001")
        engine.register_device("device-001", device)
        
        assert "device-001" in engine.devices
        assert engine.devices["device-001"] == device
    
    def test_register_multiple_devices(self, engine):
        """Test registering multiple devices."""
        class MockDevice:
            def __init__(self, device_id):
                self.device_id = device_id
        
        for i in range(1, 4):
            device = MockDevice(f"device-{i:03d}")
            engine.register_device(f"device-{i:03d}", device)
        
        assert len(engine.devices) == 3
    
    def test_register_event_handler(self, engine):
        """Test registering event handler."""
        def handler(event, engine):
            pass
        
        engine.register_event_handler(EventType.DEVICE_UPDATE, handler)
        
        assert EventType.DEVICE_UPDATE in engine.event_handlers
        assert len(engine.event_handlers[EventType.DEVICE_UPDATE]) == 1
    
    def test_register_multiple_event_handlers(self, engine):
        """Test registering multiple event handlers."""
        def handler1(event, engine):
            pass
        
        def handler2(event, engine):
            pass
        
        engine.register_event_handler(EventType.DEVICE_UPDATE, handler1)
        engine.register_event_handler(EventType.DEVICE_UPDATE, handler2)
        
        assert len(engine.event_handlers[EventType.DEVICE_UPDATE]) == 2
    
    def test_execute_scenario_empty(self, engine):
        """Test executing empty scenario."""
        scenario_id = engine.create_scenario("Empty Scenario")
        
        result = engine.execute_scenario(scenario_id)
        
        assert result.scenario_id == scenario_id
        assert result.status == ScenarioStatus.COMPLETED
        assert result.events_executed == 0
    
    def test_execute_scenario_with_events(self, engine):
        """Test executing scenario with events."""
        scenario_id = engine.create_scenario("Test Scenario")
        
        # Add events
        for i in range(1, 4):
            event = Event(
                event_id=f"evt-{i:03d}",
                event_type=EventType.DEVICE_UPDATE,
                timestamp=float(i * 10),
                device_id=f"device-{i:03d}",
            )
            engine.add_event(scenario_id, event)
        
        # Register handler
        executed_events = []
        
        def handler(event, engine):
            executed_events.append(event.event_id)
        
        engine.register_event_handler(EventType.DEVICE_UPDATE, handler)
        
        result = engine.execute_scenario(scenario_id)
        
        assert result.status == ScenarioStatus.COMPLETED
        assert result.events_executed == 3
        assert len(executed_events) == 3
    
    def test_execute_scenario_nonexistent_raises_error(self, engine):
        """Test executing nonexistent scenario raises error."""
        with pytest.raises(ValidationError):
            engine.execute_scenario("nonexistent-scenario")
    
    def test_execute_scenario_with_metrics(self, engine):
        """Test executing scenario with metrics collection."""
        scenario_id = engine.create_scenario("Test Scenario")
        
        # Add event
        event = Event(
            event_id="evt-001",
            event_type=EventType.DEVICE_UPDATE,
            timestamp=10.0,
        )
        engine.add_event(scenario_id, event)
        
        # Register handler that records metrics
        def handler(event, engine):
            engine.metrics_collector.record_metric(
                metric_name="power_output",
                value=100.0,
                timestamp=event.timestamp,
            )
        
        engine.register_event_handler(EventType.DEVICE_UPDATE, handler)
        
        result = engine.execute_scenario(scenario_id)
        
        assert result.metrics_collected == 1
    
    def test_execute_scenario_async(self, engine):
        """Test executing scenario asynchronously."""
        scenario_id = engine.create_scenario("Test Scenario")
        
        future = engine.execute_scenario_async(scenario_id)
        
        assert isinstance(future, Future)
        assert scenario_id in engine.running_scenarios
        
        # Wait for completion
        result = future.result(timeout=5)
        assert result.scenario_id == scenario_id
    
    def test_get_scenario_status(self, engine):
        """Test getting scenario status."""
        scenario_id = engine.create_scenario("Test Scenario")
        
        status = engine.get_scenario_status(scenario_id)
        
        assert status["scenario_id"] == scenario_id
        assert status["name"] == "Test Scenario"
    
    def test_get_scenario_status_nonexistent_raises_error(self, engine):
        """Test getting status of nonexistent scenario raises error."""
        with pytest.raises(ValidationError):
            engine.get_scenario_status("nonexistent-scenario")
    
    def test_generate_report(self, engine):
        """Test generating scenario report."""
        scenario_id = engine.create_scenario("Test Scenario")
        
        # Add event
        event = Event(
            event_id="evt-001",
            event_type=EventType.DEVICE_UPDATE,
            timestamp=10.0,
        )
        engine.add_event(scenario_id, event)
        
        # Execute scenario
        engine.execute_scenario(scenario_id)
        
        report = engine.generate_report(scenario_id)
        
        assert report["scenario_id"] == scenario_id
        assert "execution_result" in report
        assert "aggregated_metrics" in report
    
    def test_generate_report_nonexistent_scenario_raises_error(self, engine):
        """Test generating report for nonexistent scenario raises error."""
        with pytest.raises(ValidationError):
            engine.generate_report("nonexistent-scenario")
    
    def test_generate_report_not_executed_raises_error(self, engine):
        """Test generating report for non-executed scenario raises error."""
        scenario_id = engine.create_scenario("Test Scenario")
        
        with pytest.raises(ValidationError):
            engine.generate_report(scenario_id)
    
    def test_export_report_json(self, engine):
        """Test exporting report as JSON."""
        scenario_id = engine.create_scenario("Test Scenario")
        
        # Add event
        event = Event(
            event_id="evt-001",
            event_type=EventType.DEVICE_UPDATE,
            timestamp=10.0,
        )
        engine.add_event(scenario_id, event)
        
        # Execute scenario
        engine.execute_scenario(scenario_id)
        
        report_json = engine.export_report(scenario_id, format="json")
        
        assert isinstance(report_json, str)
        report_dict = json.loads(report_json)
        assert report_dict["scenario_id"] == scenario_id
    
    def test_export_report_csv(self, engine):
        """Test exporting report as CSV."""
        scenario_id = engine.create_scenario("Test Scenario")
        
        # Add event
        event = Event(
            event_id="evt-001",
            event_type=EventType.DEVICE_UPDATE,
            timestamp=10.0,
        )
        engine.add_event(scenario_id, event)
        
        # Register handler that records metrics
        def handler(event, engine):
            engine.metrics_collector.record_metric(
                metric_name="power_output",
                value=100.0,
                timestamp=event.timestamp,
                device_id="device-001",
            )
        
        engine.register_event_handler(EventType.DEVICE_UPDATE, handler)
        
        # Execute scenario
        engine.execute_scenario(scenario_id)
        
        report_csv = engine.export_report(scenario_id, format="csv")
        
        assert isinstance(report_csv, str)
        assert "metric_name" in report_csv
        # CSV header should be present
        lines = report_csv.strip().split("\n")
        assert len(lines) >= 1  # At least header
    
    def test_export_report_invalid_format_raises_error(self, engine):
        """Test exporting report with invalid format raises error."""
        scenario_id = engine.create_scenario("Test Scenario")
        engine.execute_scenario(scenario_id)
        
        with pytest.raises(ValidationError):
            engine.export_report(scenario_id, format="invalid")
    
    def test_get_engine_status(self, engine):
        """Test getting engine status."""
        # Create scenarios
        for i in range(1, 3):
            engine.create_scenario(f"Scenario {i}")
        
        # Register devices
        class MockDevice:
            pass
        
        for i in range(1, 3):
            engine.register_device(f"device-{i:03d}", MockDevice())
        
        status = engine.get_engine_status()
        
        assert status["engine_id"] == engine.engine_id
        assert status["total_scenarios"] == 2
        assert status["registered_devices"] == 2
    
    def test_engine_reset(self, engine):
        """Test engine reset."""
        # Create scenario
        scenario_id = engine.create_scenario("Test Scenario")
        
        # Register device
        class MockDevice:
            pass
        
        engine.register_device("device-001", MockDevice())
        
        # Execute scenario
        engine.execute_scenario(scenario_id)
        
        # Reset
        engine.reset()
        
        assert len(engine.scenarios) == 0
        assert len(engine.devices) == 0
        assert len(engine.execution_results) == 0
    
    def test_engine_shutdown(self, engine):
        """Test engine shutdown."""
        engine.shutdown()
        
        # Executor should be shutdown
        assert engine.executor._shutdown


class TestScenarioIntegration:
    """Integration tests for Scenario Engine."""
    
    def test_complete_scenario_workflow(self):
        """Test complete scenario workflow."""
        engine = ScenarioEngine()
        
        # Create scenario
        scenario_id = engine.create_scenario(
            scenario_name="Complete Workflow",
            description="Test complete workflow",
            duration=100.0,
        )
        
        # Register devices
        class MockDevice:
            def __init__(self, device_id):
                self.device_id = device_id
                self.power = 0.0
        
        devices = {}
        for i in range(1, 4):
            device = MockDevice(f"device-{i:03d}")
            devices[f"device-{i:03d}"] = device
            engine.register_device(f"device-{i:03d}", device)
        
        # Add events
        for i in range(1, 4):
            event = Event(
                event_id=f"evt-{i:03d}",
                event_type=EventType.DEVICE_UPDATE,
                timestamp=float(i * 10),
                device_id=f"device-{i:03d}",
                parameters={"power": float(i * 100)},
            )
            engine.add_event(scenario_id, event)
        
        # Register handler
        def device_update_handler(event, engine):
            if event.device_id in engine.devices:
                device = engine.devices[event.device_id]
                device.power = event.parameters.get("power", 0.0)
                engine.metrics_collector.record_metric(
                    metric_name="device_power",
                    value=device.power,
                    timestamp=event.timestamp,
                    device_id=event.device_id,
                )
        
        engine.register_event_handler(EventType.DEVICE_UPDATE, device_update_handler)
        
        # Execute scenario
        result = engine.execute_scenario(scenario_id)
        
        # Verify results
        assert result.status == ScenarioStatus.COMPLETED
        assert result.events_executed == 3
        assert result.metrics_collected == 3
        
        # Verify devices were updated
        assert devices["device-001"].power == 100.0
        assert devices["device-002"].power == 200.0
        assert devices["device-003"].power == 300.0
        
        # Generate report
        report = engine.generate_report(scenario_id)
        assert report["scenario_id"] == scenario_id
        assert report["execution_result"]["events_executed"] == 3
        
        engine.shutdown()
    
    def test_parallel_scenario_execution(self):
        """Test parallel scenario execution."""
        engine = ScenarioEngine()
        
        # Create multiple scenarios
        scenario_ids = []
        for i in range(1, 4):
            scenario_id = engine.create_scenario(f"Scenario {i}")
            
            # Add events
            for j in range(1, 3):
                event = Event(
                    event_id=f"evt-{i:03d}-{j:03d}",
                    event_type=EventType.DEVICE_UPDATE,
                    timestamp=float(j * 10),
                )
                engine.add_event(scenario_id, event)
            
            scenario_ids.append(scenario_id)
        
        # Register handler
        def handler(event, engine):
            engine.metrics_collector.record_metric(
                metric_name="event_executed",
                value=1.0,
                timestamp=event.timestamp,
            )
        
        engine.register_event_handler(EventType.DEVICE_UPDATE, handler)
        
        # Execute scenarios asynchronously
        futures = []
        for scenario_id in scenario_ids:
            future = engine.execute_scenario_async(scenario_id)
            futures.append(future)
        
        # Wait for all to complete
        results = [f.result(timeout=5) for f in futures]
        
        # Verify all completed
        assert len(results) == 3
        assert all(r.status == ScenarioStatus.COMPLETED for r in results)
        assert all(r.events_executed == 2 for r in results)
        
        engine.shutdown()
    
    def test_scenario_with_event_ordering(self):
        """Test scenario with event ordering."""
        engine = ScenarioEngine()
        
        scenario_id = engine.create_scenario("Event Ordering Test")
        
        # Add events with same timestamp but different priorities
        for i in range(1, 4):
            event = Event(
                event_id=f"evt-{i:03d}",
                event_type=EventType.DEVICE_UPDATE,
                timestamp=10.0,
                priority=i,
            )
            engine.add_event(scenario_id, event)
        
        # Track execution order
        execution_order = []
        
        def handler(event, engine):
            execution_order.append(event.event_id)
        
        engine.register_event_handler(EventType.DEVICE_UPDATE, handler)
        
        # Execute scenario
        result = engine.execute_scenario(scenario_id)
        
        # Verify events executed in priority order (higher priority first)
        assert result.events_executed == 3
        assert execution_order == ["evt-003", "evt-002", "evt-001"]
        
        engine.shutdown()
