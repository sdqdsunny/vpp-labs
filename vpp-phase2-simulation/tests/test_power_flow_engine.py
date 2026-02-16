"""
Unit tests for Power Flow Engine

Tests PowerFlowEngine class with network model, power flow calculation,
violation detection, and stability assessment.

Requirements:
- 8.1: Real-time power flow calculation
- 8.2: Power flow recalculation on device changes
- 8.3: Violation detection (voltage and congestion)
- 8.4: Stability assessment
- 8.5: Network state management
"""

import pytest
import time
from datetime import datetime

from services.power_flow_engine import (
    PowerFlowEngine,
    Bus,
    Line,
    Violation,
    ViolationType,
    StabilityAssessment,
    StabilityStatus,
    PowerFlowResult,
)
from utils.errors import ValidationError


class TestBus:
    """Test Bus dataclass."""
    
    def test_bus_creation(self):
        """Test bus creation."""
        bus = Bus(
            bus_id="bus-001",
            voltage_nominal=1.0,
            power_injection=100.0,
        )
        
        assert bus.bus_id == "bus-001"
        assert bus.voltage_nominal == 1.0
        assert bus.voltage_actual == 1.0
        assert bus.power_injection == 100.0
    
    def test_bus_to_dict(self):
        """Test bus to dictionary conversion."""
        bus = Bus(
            bus_id="bus-001",
            voltage_nominal=1.0,
            power_injection=100.0,
        )
        
        bus_dict = bus.to_dict()
        
        assert bus_dict["bus_id"] == "bus-001"
        assert bus_dict["voltage_nominal"] == 1.0
        assert bus_dict["power_injection"] == 100.0


class TestLine:
    """Test Line dataclass."""
    
    def test_line_creation(self):
        """Test line creation."""
        line = Line(
            line_id="line-001",
            from_bus="bus-001",
            to_bus="bus-002",
            capacity=100.0,
        )
        
        assert line.line_id == "line-001"
        assert line.from_bus == "bus-001"
        assert line.to_bus == "bus-002"
        assert line.capacity == 100.0
    
    def test_line_to_dict(self):
        """Test line to dictionary conversion."""
        line = Line(
            line_id="line-001",
            from_bus="bus-001",
            to_bus="bus-002",
            capacity=100.0,
        )
        
        line_dict = line.to_dict()
        
        assert line_dict["line_id"] == "line-001"
        assert line_dict["from_bus"] == "bus-001"
        assert line_dict["capacity"] == 100.0


class TestViolation:
    """Test Violation dataclass."""
    
    def test_violation_creation(self):
        """Test violation creation."""
        violation = Violation(
            violation_id="viol-001",
            violation_type=ViolationType.VOLTAGE_HIGH,
            bus_id="bus-001",
            value=1.15,
            limit=1.1,
        )
        
        assert violation.violation_id == "viol-001"
        assert violation.violation_type == ViolationType.VOLTAGE_HIGH
        assert violation.bus_id == "bus-001"
    
    def test_violation_to_dict(self):
        """Test violation to dictionary conversion."""
        violation = Violation(
            violation_id="viol-001",
            violation_type=ViolationType.VOLTAGE_HIGH,
            bus_id="bus-001",
            value=1.15,
            limit=1.1,
        )
        
        viol_dict = violation.to_dict()
        
        assert viol_dict["violation_id"] == "viol-001"
        assert viol_dict["violation_type"] == "voltage_high"
        assert viol_dict["bus_id"] == "bus-001"


class TestPowerFlowEngine:
    """Test PowerFlowEngine class."""
    
    @pytest.fixture
    def engine(self):
        """Create power flow engine."""
        return PowerFlowEngine()
    
    def test_engine_initialization(self, engine):
        """Test engine initialization."""
        assert engine.engine_id is not None
        assert len(engine.buses) == 0
        assert len(engine.lines) == 0
        assert engine.calculation_count == 0
    
    def test_engine_initialization_with_id(self):
        """Test engine initialization with custom ID."""
        engine = PowerFlowEngine(engine_id="pf-custom")
        
        assert engine.engine_id == "pf-custom"
    
    def test_add_bus(self, engine):
        """Test adding bus to network."""
        engine.add_bus(
            bus_id="bus-001",
            voltage_nominal=1.0,
            power_injection=100.0,
        )
        
        assert "bus-001" in engine.buses
        assert engine.buses["bus-001"].voltage_nominal == 1.0
    
    def test_add_multiple_buses(self, engine):
        """Test adding multiple buses."""
        for i in range(1, 4):
            engine.add_bus(
                bus_id=f"bus-{i:03d}",
                voltage_nominal=1.0,
                power_injection=float(i * 100),
            )
        
        assert len(engine.buses) == 3
    
    def test_add_bus_duplicate_raises_error(self, engine):
        """Test adding duplicate bus raises error."""
        engine.add_bus("bus-001", voltage_nominal=1.0)
        
        with pytest.raises(ValidationError):
            engine.add_bus("bus-001", voltage_nominal=1.0)
    
    def test_add_line(self, engine):
        """Test adding line to network."""
        engine.add_bus("bus-001", voltage_nominal=1.0)
        engine.add_bus("bus-002", voltage_nominal=1.0)
        
        engine.add_line(
            line_id="line-001",
            from_bus="bus-001",
            to_bus="bus-002",
            capacity=100.0,
        )
        
        assert "line-001" in engine.lines
        assert engine.lines["line-001"].capacity == 100.0
    
    def test_add_line_duplicate_raises_error(self, engine):
        """Test adding duplicate line raises error."""
        engine.add_bus("bus-001", voltage_nominal=1.0)
        engine.add_bus("bus-002", voltage_nominal=1.0)
        
        engine.add_line("line-001", "bus-001", "bus-002")
        
        with pytest.raises(ValidationError):
            engine.add_line("line-001", "bus-001", "bus-002")
    
    def test_add_line_nonexistent_bus_raises_error(self, engine):
        """Test adding line with nonexistent bus raises error."""
        engine.add_bus("bus-001", voltage_nominal=1.0)
        
        with pytest.raises(ValidationError):
            engine.add_line("line-001", "bus-001", "bus-999")
    
    def test_update_bus_injection(self, engine):
        """Test updating bus power injection."""
        engine.add_bus("bus-001", voltage_nominal=1.0, power_injection=100.0)
        
        engine.update_bus_injection("bus-001", power_injection=150.0, reactive_injection=50.0)
        
        assert engine.buses["bus-001"].power_injection == 150.0
        assert engine.buses["bus-001"].reactive_injection == 50.0
    
    def test_update_bus_injection_nonexistent_raises_error(self, engine):
        """Test updating nonexistent bus raises error."""
        with pytest.raises(ValidationError):
            engine.update_bus_injection("bus-999", power_injection=100.0)
    
    def test_calculate_power_flow_simple_network(self, engine):
        """Test power flow calculation on simple network."""
        # Create simple 2-bus network
        engine.add_bus("bus-001", voltage_nominal=1.0, power_injection=100.0)
        engine.add_bus("bus-002", voltage_nominal=1.0, power_injection=-100.0)
        engine.add_line("line-001", "bus-001", "bus-002", capacity=150.0)
        
        result = engine.calculate_power_flow()
        
        assert result.converged
        assert result.calculation_time > 0
        assert len(result.buses) == 2
        assert len(result.lines) == 1
    
    def test_calculate_power_flow_empty_network(self, engine):
        """Test power flow calculation on empty network."""
        result = engine.calculate_power_flow()
        
        assert result.converged
        assert len(result.buses) == 0
        assert len(result.lines) == 0
    
    def test_calculate_power_flow_performance(self, engine):
        """Test power flow calculation performance (<500ms)."""
        # Create network with multiple buses and lines
        for i in range(1, 11):
            engine.add_bus(f"bus-{i:03d}", voltage_nominal=1.0)
        
        for i in range(1, 10):
            engine.add_line(
                f"line-{i:03d}",
                f"bus-{i:03d}",
                f"bus-{i+1:03d}",
                capacity=100.0,
            )
        
        result = engine.calculate_power_flow()
        
        assert result.calculation_time < 500  # ms
    
    def test_voltage_violation_detection_high(self, engine):
        """Test voltage violation detection (high)."""
        engine.add_bus("bus-001", voltage_nominal=1.0)
        
        # Manually set voltage after calculation to simulate violation
        result = engine.calculate_power_flow()
        engine.buses["bus-001"].voltage_actual = 1.15
        
        # Recalculate to detect violation
        result = engine.calculate_power_flow()
        
        assert len(result.violations) > 0
        assert any(v.violation_type == ViolationType.VOLTAGE_HIGH for v in result.violations)
    
    def test_voltage_violation_detection_low(self, engine):
        """Test voltage violation detection (low)."""
        engine.add_bus("bus-001", voltage_nominal=1.0)
        
        # Manually set voltage after calculation to simulate violation
        result = engine.calculate_power_flow()
        engine.buses["bus-001"].voltage_actual = 0.85
        
        # Recalculate to detect violation
        result = engine.calculate_power_flow()
        
        assert len(result.violations) > 0
        assert any(v.violation_type == ViolationType.VOLTAGE_LOW for v in result.violations)
    
    def test_congestion_detection(self, engine):
        """Test line congestion detection."""
        engine.add_bus("bus-001", voltage_nominal=1.0)
        engine.add_bus("bus-002", voltage_nominal=1.0)
        engine.add_line("line-001", "bus-001", "bus-002", capacity=100.0)
        
        # Calculate first
        result = engine.calculate_power_flow()
        
        # Set line loading above 100%
        engine.lines["line-001"].loading_percent = 110.0
        
        # Recalculate to detect violation
        result = engine.calculate_power_flow()
        
        assert len(result.violations) > 0
        assert any(v.violation_type == ViolationType.CONGESTION for v in result.violations)
    
    def test_stability_assessment_stable(self, engine):
        """Test stability assessment (stable)."""
        engine.add_bus("bus-001", voltage_nominal=1.0)
        engine.buses["bus-001"].frequency = 50.0
        engine.buses["bus-001"].voltage_actual = 1.0
        
        result = engine.calculate_power_flow()
        
        assert result.stability is not None
        assert result.stability.status == StabilityStatus.STABLE
    
    def test_stability_assessment_marginal(self, engine):
        """Test stability assessment (marginal)."""
        engine.add_bus("bus-001", voltage_nominal=1.0)
        engine.buses["bus-001"].frequency = 49.4  # 0.6 Hz deviation (>0.5)
        engine.buses["bus-001"].voltage_actual = 0.95
        
        result = engine.calculate_power_flow()
        
        assert result.stability is not None
        assert result.stability.status == StabilityStatus.MARGINAL
    
    def test_stability_assessment_unstable(self, engine):
        """Test stability assessment (unstable)."""
        engine.add_bus("bus-001", voltage_nominal=1.0)
        engine.buses["bus-001"].frequency = 48.5  # 1.5 Hz deviation
        engine.buses["bus-001"].voltage_actual = 0.85
        
        result = engine.calculate_power_flow()
        
        assert result.stability is not None
        assert result.stability.status == StabilityStatus.UNSTABLE
    
    def test_get_network_state(self, engine):
        """Test getting network state."""
        engine.add_bus("bus-001", voltage_nominal=1.0)
        engine.add_bus("bus-002", voltage_nominal=1.0)
        engine.add_line("line-001", "bus-001", "bus-002")
        
        state = engine.get_network_state()
        
        assert state["engine_id"] == engine.engine_id
        assert len(state["buses"]) == 2
        assert len(state["lines"]) == 1
    
    def test_get_violations(self, engine):
        """Test getting violations."""
        engine.add_bus("bus-001", voltage_nominal=1.0)
        engine.buses["bus-001"].voltage_actual = 1.15
        
        engine.calculate_power_flow()
        
        violations = engine.get_violations()
        
        assert len(violations) > 0
    
    def test_get_stability_history(self, engine):
        """Test getting stability history."""
        engine.add_bus("bus-001", voltage_nominal=1.0)
        
        engine.calculate_power_flow()
        engine.calculate_power_flow()
        
        history = engine.get_stability_history()
        
        assert len(history) >= 2
    
    def test_calculation_count_increment(self, engine):
        """Test calculation count increments."""
        engine.add_bus("bus-001", voltage_nominal=1.0)
        
        assert engine.calculation_count == 0
        
        engine.calculate_power_flow()
        assert engine.calculation_count == 1
        
        engine.calculate_power_flow()
        assert engine.calculation_count == 2
    
    def test_engine_reset(self, engine):
        """Test engine reset."""
        engine.add_bus("bus-001", voltage_nominal=1.0)
        engine.add_bus("bus-002", voltage_nominal=1.0)
        engine.add_line("line-001", "bus-001", "bus-002")
        
        engine.calculate_power_flow()
        
        engine.reset()
        
        assert len(engine.buses) == 0
        assert len(engine.lines) == 0
        assert engine.calculation_count == 0
        assert len(engine.violation_history) == 0


class TestPowerFlowIntegration:
    """Integration tests for Power Flow Engine."""
    
    def test_complete_network_analysis(self):
        """Test complete network analysis workflow."""
        engine = PowerFlowEngine()
        
        # Create 3-bus network
        engine.add_bus("bus-001", voltage_nominal=1.0, power_injection=100.0)
        engine.add_bus("bus-002", voltage_nominal=1.0, power_injection=0.0)
        engine.add_bus("bus-003", voltage_nominal=1.0, power_injection=-100.0)
        
        # Add transmission lines
        engine.add_line("line-001", "bus-001", "bus-002", capacity=150.0)
        engine.add_line("line-002", "bus-002", "bus-003", capacity=150.0)
        
        # Calculate power flow
        result = engine.calculate_power_flow()
        
        # Verify results
        assert result.converged
        assert len(result.buses) == 3
        assert len(result.lines) == 2
        assert result.stability is not None
        
        # Get network state
        state = engine.get_network_state()
        assert state["calculation_count"] == 1
    
    def test_dynamic_network_update(self):
        """Test dynamic network updates."""
        engine = PowerFlowEngine()
        
        # Create initial network
        engine.add_bus("bus-001", voltage_nominal=1.0, power_injection=100.0)
        engine.add_bus("bus-002", voltage_nominal=1.0, power_injection=-100.0)
        engine.add_line("line-001", "bus-001", "bus-002", capacity=100.0)
        
        # Calculate initial power flow
        result1 = engine.calculate_power_flow()
        assert result1.converged
        
        # Update bus injection
        engine.update_bus_injection("bus-001", power_injection=150.0)
        
        # Recalculate power flow
        result2 = engine.calculate_power_flow()
        assert result2.converged
        
        # Verify calculation count increased
        assert engine.calculation_count == 2
    
    def test_violation_tracking(self):
        """Test violation tracking over multiple calculations."""
        engine = PowerFlowEngine()
        
        engine.add_bus("bus-001", voltage_nominal=1.0)
        
        # First calculation - no violation
        engine.buses["bus-001"].voltage_actual = 1.0
        result1 = engine.calculate_power_flow()
        assert len(result1.violations) == 0
        
        # Second calculation - voltage violation
        engine.buses["bus-001"].voltage_actual = 1.15
        result2 = engine.calculate_power_flow()
        assert len(result2.violations) > 0
        
        # Verify violation history
        all_violations = engine.get_violations()
        assert len(all_violations) > 0
    
    def test_stability_monitoring(self):
        """Test stability monitoring over time."""
        engine = PowerFlowEngine()
        
        engine.add_bus("bus-001", voltage_nominal=1.0)
        
        # Stable condition
        engine.buses["bus-001"].frequency = 50.0
        engine.buses["bus-001"].voltage_actual = 1.0
        result1 = engine.calculate_power_flow()
        assert result1.stability.status == StabilityStatus.STABLE
        
        # Marginal condition
        engine.buses["bus-001"].frequency = 49.4  # 0.6 Hz deviation
        result2 = engine.calculate_power_flow()
        assert result2.stability.status == StabilityStatus.MARGINAL
        
        # Unstable condition
        engine.buses["bus-001"].frequency = 48.0
        result3 = engine.calculate_power_flow()
        assert result3.stability.status == StabilityStatus.UNSTABLE
        
        # Verify history
        history = engine.get_stability_history()
        assert len(history) == 3
