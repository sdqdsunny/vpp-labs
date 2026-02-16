"""
Scenario Engine

Implements scenario execution framework with event scheduling, device management,
metrics collection, and report generation.

Requirements:
- 7.1: Event scheduling and execution
- 7.2: Event triggering and simulator updates
- 7.3: Metrics collection during scenario execution
- 7.4: Scenario report generation
- 7.5: Parallel scenario execution
"""

import logging
import json
import uuid
import threading
import queue
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from abc import ABC, abstractmethod
import heapq
from concurrent.futures import ThreadPoolExecutor, Future

from utils.errors import ValidationError, SimulatorError
from utils.logger import get_logger

logger = get_logger(__name__)


class EventType(Enum):
    """Scenario event types."""
    DEVICE_UPDATE = "device_update"
    DEVICE_COMMAND = "device_command"
    SCENARIO_START = "scenario_start"
    SCENARIO_END = "scenario_end"
    CHECKPOINT = "checkpoint"
    CUSTOM = "custom"


class ScenarioStatus(Enum):
    """Scenario execution status."""
    CREATED = "created"
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class Event:
    """Scenario event."""
    event_id: str
    event_type: EventType
    timestamp: float
    device_id: Optional[str] = None
    command: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    priority: int = 0
    
    def __lt__(self, other):
        """Compare events by timestamp for priority queue."""
        if self.timestamp != other.timestamp:
            return self.timestamp < other.timestamp
        return self.priority > other.priority  # Higher priority first


@dataclass
class ScenarioMetric:
    """Scenario metric data point."""
    metric_name: str
    value: float
    timestamp: float
    device_id: Optional[str] = None
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class ScenarioResult:
    """Scenario execution result."""
    scenario_id: str
    status: ScenarioStatus
    start_time: float
    end_time: float
    duration: float
    events_executed: int
    metrics_collected: int
    errors: List[str] = field(default_factory=list)
    metrics: List[ScenarioMetric] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "scenario_id": self.scenario_id,
            "status": self.status.value,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "events_executed": self.events_executed,
            "metrics_collected": self.metrics_collected,
            "errors": self.errors,
            "metrics_count": len(self.metrics),
        }


class EventScheduler:
    """
    Event scheduler for scenario execution.
    
    Manages event scheduling, execution, and time advancement.
    """
    
    def __init__(self):
        """Initialize event scheduler."""
        self.events: List[Event] = []
        self.current_time = 0.0
        self.executed_events: List[Event] = []
        logger.info("EventScheduler initialized")
    
    def schedule_event(self, event: Event) -> None:
        """
        Schedule an event for execution.
        
        Args:
            event: Event to schedule
        """
        if event.timestamp < self.current_time:
            raise ValidationError(
                f"Cannot schedule event in the past: {event.timestamp} < {self.current_time}"
            )
        heapq.heappush(self.events, event)
        logger.debug(f"Event scheduled: {event.event_id} at {event.timestamp}")
    
    def get_next_event(self) -> Optional[Event]:
        """
        Get the next event to execute.
        
        Returns:
            Next event or None if no events scheduled
        """
        if not self.events:
            return None
        return heapq.heappop(self.events)
    
    def advance_time(self, delta: float) -> None:
        """
        Advance scenario time.
        
        Args:
            delta: Time delta in seconds
        """
        if delta < 0:
            raise ValidationError("Time delta must be non-negative")
        self.current_time += delta
        logger.debug(f"Time advanced to {self.current_time}")
    
    def get_pending_events_at_time(self, target_time: float) -> List[Event]:
        """
        Get all events scheduled at a specific time.
        
        Args:
            target_time: Target time
            
        Returns:
            List of events at target time
        """
        pending = []
        while self.events and self.events[0].timestamp <= target_time:
            pending.append(heapq.heappop(self.events))
        # Put them back if we're not at that time yet
        for event in pending:
            heapq.heappush(self.events, event)
        return pending
    
    def reset(self) -> None:
        """Reset scheduler state."""
        self.events.clear()
        self.current_time = 0.0
        self.executed_events.clear()
        logger.info("EventScheduler reset")


class MetricsCollector:
    """
    Metrics collector for scenario execution.
    
    Collects and aggregates metrics during scenario execution.
    """
    
    def __init__(self):
        """Initialize metrics collector."""
        self.metrics: List[ScenarioMetric] = []
        self.aggregated_metrics: Dict[str, List[float]] = {}
        logger.info("MetricsCollector initialized")
    
    def record_metric(
        self,
        metric_name: str,
        value: float,
        timestamp: float,
        device_id: Optional[str] = None,
        tags: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Record a metric.
        
        Args:
            metric_name: Metric name
            value: Metric value
            timestamp: Timestamp
            device_id: Optional device ID
            tags: Optional tags
        """
        metric = ScenarioMetric(
            metric_name=metric_name,
            value=value,
            timestamp=timestamp,
            device_id=device_id,
            tags=tags or {}
        )
        self.metrics.append(metric)
        
        # Aggregate
        key = f"{metric_name}:{device_id or 'global'}"
        if key not in self.aggregated_metrics:
            self.aggregated_metrics[key] = []
        self.aggregated_metrics[key].append(value)
        
        logger.debug(f"Metric recorded: {metric_name}={value}")
    
    def get_metrics(self) -> List[ScenarioMetric]:
        """Get all collected metrics."""
        return self.metrics.copy()
    
    def get_aggregated_metrics(self) -> Dict[str, Dict[str, float]]:
        """
        Get aggregated metrics (min, max, avg).
        
        Returns:
            Dictionary of aggregated metrics
        """
        result = {}
        for key, values in self.aggregated_metrics.items():
            if values:
                result[key] = {
                    "min": min(values),
                    "max": max(values),
                    "avg": sum(values) / len(values),
                    "count": len(values),
                }
        return result
    
    def reset(self) -> None:
        """Reset collector state."""
        self.metrics.clear()
        self.aggregated_metrics.clear()
        logger.info("MetricsCollector reset")


class ScenarioEngine:
    """
    Scenario Engine
    
    Manages scenario execution with event scheduling, device management,
    metrics collection, and report generation.
    
    Requirements:
    - 7.1: Event scheduling and execution
    - 7.2: Event triggering and simulator updates
    - 7.3: Metrics collection during scenario execution
    - 7.4: Scenario report generation
    - 7.5: Parallel scenario execution
    """
    
    def __init__(self, engine_id: Optional[str] = None):
        """
        Initialize Scenario Engine.
        
        Args:
            engine_id: Unique engine identifier
        """
        self.engine_id = engine_id or f"scenario-engine-{uuid.uuid4().hex[:8]}"
        self.scenarios: Dict[str, Dict[str, Any]] = {}
        self.scheduler = EventScheduler()
        self.metrics_collector = MetricsCollector()
        self.devices: Dict[str, Any] = {}
        self.event_handlers: Dict[EventType, List[Callable]] = {}
        self.execution_results: Dict[str, ScenarioResult] = {}
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.running_scenarios: Dict[str, Future] = {}
        
        logger.info(f"ScenarioEngine initialized: {self.engine_id}")
    
    def create_scenario(
        self,
        scenario_name: str,
        description: str = "",
        duration: float = 3600.0
    ) -> str:
        """
        Create a new scenario.
        
        Args:
            scenario_name: Scenario name
            description: Scenario description
            duration: Scenario duration in seconds
            
        Returns:
            Scenario ID
        """
        scenario_id = f"scenario-{uuid.uuid4().hex[:8]}"
        
        self.scenarios[scenario_id] = {
            "id": scenario_id,
            "name": scenario_name,
            "description": description,
            "duration": duration,
            "events": [],
            "devices": {},
            "created_at": datetime.utcnow().isoformat(),
            "status": ScenarioStatus.CREATED.value,
        }
        
        logger.info(f"Scenario created: {scenario_id} ({scenario_name})")
        return scenario_id
    
    def add_event(self, scenario_id: str, event: Event) -> None:
        """
        Add event to scenario.
        
        Args:
            scenario_id: Scenario ID
            event: Event to add
            
        Raises:
            ValidationError: If scenario not found
        """
        if scenario_id not in self.scenarios:
            raise ValidationError(f"Scenario not found: {scenario_id}")
        
        self.scenarios[scenario_id]["events"].append(asdict(event))
        logger.debug(f"Event added to scenario {scenario_id}: {event.event_id}")
    
    def register_device(self, device_id: str, device: Any) -> None:
        """
        Register a device for scenario execution.
        
        Args:
            device_id: Device ID
            device: Device instance
        """
        self.devices[device_id] = device
        logger.debug(f"Device registered: {device_id}")
    
    def register_event_handler(
        self,
        event_type: EventType,
        handler: Callable
    ) -> None:
        """
        Register event handler.
        
        Args:
            event_type: Event type
            handler: Handler function
        """
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
        logger.debug(f"Event handler registered for {event_type.value}")
    
    def execute_scenario(self, scenario_id: str) -> ScenarioResult:
        """
        Execute scenario.
        
        Args:
            scenario_id: Scenario ID
            
        Returns:
            Scenario execution result
            
        Raises:
            ValidationError: If scenario not found
        """
        if scenario_id not in self.scenarios:
            raise ValidationError(f"Scenario not found: {scenario_id}")
        
        scenario = self.scenarios[scenario_id]
        start_time = datetime.utcnow().timestamp()
        
        logger.info(f"Starting scenario execution: {scenario_id}")
        
        try:
            # Reset scheduler and metrics
            self.scheduler.reset()
            self.metrics_collector.reset()
            
            # Schedule events
            events_data = scenario.get("events", [])
            for event_data in events_data:
                event = Event(**event_data)
                self.scheduler.schedule_event(event)
            
            # Execute events
            events_executed = 0
            errors = []
            
            while True:
                event = self.scheduler.get_next_event()
                if not event:
                    break
                
                # Advance time
                self.scheduler.advance_time(event.timestamp - self.scheduler.current_time)
                
                try:
                    # Execute event handlers
                    handlers = self.event_handlers.get(event.event_type, [])
                    for handler in handlers:
                        handler(event, self)
                    
                    events_executed += 1
                    logger.debug(f"Event executed: {event.event_id}")
                    
                except Exception as e:
                    error_msg = f"Error executing event {event.event_id}: {str(e)}"
                    errors.append(error_msg)
                    logger.error(error_msg)
            
            end_time = datetime.utcnow().timestamp()
            duration = end_time - start_time
            
            # Create result
            result = ScenarioResult(
                scenario_id=scenario_id,
                status=ScenarioStatus.COMPLETED if not errors else ScenarioStatus.FAILED,
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                events_executed=events_executed,
                metrics_collected=len(self.metrics_collector.metrics),
                errors=errors,
                metrics=self.metrics_collector.get_metrics(),
            )
            
            self.execution_results[scenario_id] = result
            logger.info(f"Scenario execution completed: {scenario_id}")
            
            return result
            
        except Exception as e:
            end_time = datetime.utcnow().timestamp()
            error_msg = f"Scenario execution failed: {str(e)}"
            logger.error(error_msg)
            
            result = ScenarioResult(
                scenario_id=scenario_id,
                status=ScenarioStatus.FAILED,
                start_time=start_time,
                end_time=end_time,
                duration=end_time - start_time,
                events_executed=0,
                metrics_collected=0,
                errors=[error_msg],
            )
            
            self.execution_results[scenario_id] = result
            return result
    
    def execute_scenario_async(self, scenario_id: str) -> Future:
        """
        Execute scenario asynchronously.
        
        Args:
            scenario_id: Scenario ID
            
        Returns:
            Future for scenario execution
        """
        future = self.executor.submit(self.execute_scenario, scenario_id)
        self.running_scenarios[scenario_id] = future
        logger.info(f"Scenario queued for async execution: {scenario_id}")
        return future
    
    def get_scenario_status(self, scenario_id: str) -> Dict[str, Any]:
        """
        Get scenario status.
        
        Args:
            scenario_id: Scenario ID
            
        Returns:
            Scenario status dictionary
        """
        if scenario_id not in self.scenarios:
            raise ValidationError(f"Scenario not found: {scenario_id}")
        
        scenario = self.scenarios[scenario_id]
        result = self.execution_results.get(scenario_id)
        
        return {
            "scenario_id": scenario_id,
            "name": scenario["name"],
            "status": scenario["status"],
            "created_at": scenario["created_at"],
            "result": result.to_dict() if result else None,
        }
    
    def generate_report(self, scenario_id: str) -> Dict[str, Any]:
        """
        Generate scenario execution report.
        
        Args:
            scenario_id: Scenario ID
            
        Returns:
            Report dictionary
            
        Raises:
            ValidationError: If scenario not found or not executed
        """
        if scenario_id not in self.scenarios:
            raise ValidationError(f"Scenario not found: {scenario_id}")
        
        if scenario_id not in self.execution_results:
            raise ValidationError(f"Scenario not executed: {scenario_id}")
        
        scenario = self.scenarios[scenario_id]
        result = self.execution_results[scenario_id]
        
        report = {
            "scenario_id": scenario_id,
            "scenario_name": scenario["name"],
            "scenario_description": scenario["description"],
            "execution_result": result.to_dict(),
            "aggregated_metrics": self.metrics_collector.get_aggregated_metrics(),
            "generated_at": datetime.utcnow().isoformat(),
        }
        
        logger.info(f"Report generated for scenario: {scenario_id}")
        return report
    
    def export_report(self, scenario_id: str, format: str = "json") -> str:
        """
        Export scenario report.
        
        Args:
            scenario_id: Scenario ID
            format: Export format (json, csv)
            
        Returns:
            Exported report as string
        """
        report = self.generate_report(scenario_id)
        
        if format == "json":
            return json.dumps(report, indent=2)
        elif format == "csv":
            # Simple CSV export of metrics
            lines = ["metric_name,value,timestamp,device_id"]
            for metric in report["execution_result"].get("metrics", []):
                lines.append(
                    f"{metric['metric_name']},{metric['value']},"
                    f"{metric['timestamp']},{metric.get('device_id', '')}"
                )
            return "\n".join(lines)
        else:
            raise ValidationError(f"Unsupported export format: {format}")
    
    def get_engine_status(self) -> Dict[str, Any]:
        """Get engine status."""
        return {
            "engine_id": self.engine_id,
            "total_scenarios": len(self.scenarios),
            "executed_scenarios": len(self.execution_results),
            "running_scenarios": len(self.running_scenarios),
            "registered_devices": len(self.devices),
            "pending_events": len(self.scheduler.events),
        }
    
    def reset(self) -> None:
        """Reset engine state."""
        self.scenarios.clear()
        self.scheduler.reset()
        self.metrics_collector.reset()
        self.devices.clear()
        self.execution_results.clear()
        logger.info(f"ScenarioEngine reset: {self.engine_id}")
    
    def shutdown(self) -> None:
        """Shutdown engine."""
        self.executor.shutdown(wait=True)
        logger.info(f"ScenarioEngine shutdown: {self.engine_id}")
