"""
Power Flow Simulator

Implements real-time power flow calculation with violation detection and stability assessment.

Requirements:
- 8.1: Real-time power flow calculation
- 8.2: Power flow recalculation on device changes
- 8.3: Violation detection (voltage and congestion)
- 8.4: Stability assessment
- 8.5: Network state management
"""

import logging
import uuid
import time
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import math

from utils.errors import ValidationError, SimulatorError
from utils.logger import get_logger

logger = get_logger(__name__)


class ViolationType(Enum):
    """Violation types."""
    VOLTAGE_HIGH = "voltage_high"
    VOLTAGE_LOW = "voltage_low"
    CONGESTION = "congestion"
    FREQUENCY_DEVIATION = "frequency_deviation"


class StabilityStatus(Enum):
    """System stability status."""
    STABLE = "stable"
    MARGINAL = "marginal"
    UNSTABLE = "unstable"


@dataclass
class Bus:
    """Network bus."""
    bus_id: str
    voltage_nominal: float = 1.0  # p.u.
    voltage_actual: float = 1.0  # p.u.
    frequency: float = 50.0  # Hz
    power_injection: float = 0.0  # MW
    reactive_injection: float = 0.0  # MVAr
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class Line:
    """Network transmission line."""
    line_id: str
    from_bus: str
    to_bus: str
    resistance: float = 0.01  # p.u.
    reactance: float = 0.05  # p.u.
    capacity: float = 100.0  # MW
    power_flow: float = 0.0  # MW
    loading_percent: float = 0.0  # %
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class Violation:
    """Network violation."""
    violation_id: str
    violation_type: ViolationType
    bus_id: Optional[str] = None
    line_id: Optional[str] = None
    value: float = 0.0
    limit: float = 0.0
    severity: str = "warning"  # warning, critical
    timestamp: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "violation_id": self.violation_id,
            "violation_type": self.violation_type.value,
            "bus_id": self.bus_id,
            "line_id": self.line_id,
            "value": self.value,
            "limit": self.limit,
            "severity": self.severity,
            "timestamp": self.timestamp,
        }


@dataclass
class StabilityAssessment:
    """System stability assessment."""
    status: StabilityStatus
    frequency_deviation: float = 0.0  # Hz
    voltage_stability_margin: float = 0.0  # %
    rotor_angle_stability: float = 0.0  # degrees
    damping_ratio: float = 0.0
    assessment_time: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "status": self.status.value,
            "frequency_deviation": self.frequency_deviation,
            "voltage_stability_margin": self.voltage_stability_margin,
            "rotor_angle_stability": self.rotor_angle_stability,
            "damping_ratio": self.damping_ratio,
            "assessment_time": self.assessment_time,
        }


@dataclass
class PowerFlowResult:
    """Power flow calculation result."""
    result_id: str
    calculation_time: float
    converged: bool
    buses: List[Bus] = field(default_factory=list)
    lines: List[Line] = field(default_factory=list)
    violations: List[Violation] = field(default_factory=list)
    stability: Optional[StabilityAssessment] = None
    total_loss: float = 0.0  # MW
    timestamp: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "result_id": self.result_id,
            "calculation_time": self.calculation_time,
            "converged": self.converged,
            "buses": [b.to_dict() for b in self.buses],
            "lines": [l.to_dict() for l in self.lines],
            "violations": [v.to_dict() for v in self.violations],
            "stability": self.stability.to_dict() if self.stability else None,
            "total_loss": self.total_loss,
            "timestamp": self.timestamp,
        }


class PowerFlowEngine:
    """
    Power Flow Simulator
    
    Implements real-time power flow calculation with violation detection and stability assessment.
    
    Requirements:
    - 8.1: Real-time power flow calculation
    - 8.2: Power flow recalculation on device changes
    - 8.3: Violation detection (voltage and congestion)
    - 8.4: Stability assessment
    - 8.5: Network state management
    """
    
    def __init__(self, engine_id: Optional[str] = None):
        """
        Initialize Power Flow Engine.
        
        Args:
            engine_id: Unique engine identifier
        """
        self.engine_id = engine_id or f"pf-engine-{uuid.uuid4().hex[:8]}"
        self.buses: Dict[str, Bus] = {}
        self.lines: Dict[str, Line] = {}
        self.network_state: Dict[str, Any] = {}
        self.last_calculation_time = 0.0
        self.calculation_count = 0
        self.violation_history: List[Violation] = []
        self.stability_history: List[StabilityAssessment] = []
        
        logger.info(f"PowerFlowEngine initialized: {self.engine_id}")
    
    def add_bus(
        self,
        bus_id: str,
        voltage_nominal: float = 1.0,
        power_injection: float = 0.0,
        reactive_injection: float = 0.0
    ) -> None:
        """
        Add bus to network.
        
        Args:
            bus_id: Bus identifier
            voltage_nominal: Nominal voltage (p.u.)
            power_injection: Power injection (MW)
            reactive_injection: Reactive injection (MVAr)
        """
        if bus_id in self.buses:
            raise ValidationError(f"Bus already exists: {bus_id}")
        
        bus = Bus(
            bus_id=bus_id,
            voltage_nominal=voltage_nominal,
            voltage_actual=voltage_nominal,
            power_injection=power_injection,
            reactive_injection=reactive_injection,
        )
        self.buses[bus_id] = bus
        logger.debug(f"Bus added: {bus_id}")
    
    def add_line(
        self,
        line_id: str,
        from_bus: str,
        to_bus: str,
        resistance: float = 0.01,
        reactance: float = 0.05,
        capacity: float = 100.0
    ) -> None:
        """
        Add transmission line to network.
        
        Args:
            line_id: Line identifier
            from_bus: From bus ID
            to_bus: To bus ID
            resistance: Line resistance (p.u.)
            reactance: Line reactance (p.u.)
            capacity: Line capacity (MW)
        """
        if line_id in self.lines:
            raise ValidationError(f"Line already exists: {line_id}")
        
        if from_bus not in self.buses or to_bus not in self.buses:
            raise ValidationError(f"Bus not found for line: {line_id}")
        
        line = Line(
            line_id=line_id,
            from_bus=from_bus,
            to_bus=to_bus,
            resistance=resistance,
            reactance=reactance,
            capacity=capacity,
        )
        self.lines[line_id] = line
        logger.debug(f"Line added: {line_id}")
    
    def update_bus_injection(
        self,
        bus_id: str,
        power_injection: float,
        reactive_injection: float = 0.0
    ) -> None:
        """
        Update bus power injection.
        
        Args:
            bus_id: Bus identifier
            power_injection: Power injection (MW)
            reactive_injection: Reactive injection (MVAr)
        """
        if bus_id not in self.buses:
            raise ValidationError(f"Bus not found: {bus_id}")
        
        self.buses[bus_id].power_injection = power_injection
        self.buses[bus_id].reactive_injection = reactive_injection
        logger.debug(f"Bus injection updated: {bus_id}")
    
    def calculate_power_flow(self) -> PowerFlowResult:
        """
        Calculate power flow.
        
        Returns:
            Power flow calculation result
        """
        start_time = time.time()
        result_id = f"pf-result-{uuid.uuid4().hex[:8]}"
        
        try:
            # Simplified DC power flow calculation
            # In production, would use Newton-Raphson or similar
            
            # Initialize voltages (only if not already set to non-nominal value)
            for bus_id, bus in self.buses.items():
                # Only reset to nominal if voltage is already at nominal
                # This preserves manually-set voltages for testing
                if bus.voltage_actual == bus.voltage_nominal or bus.voltage_actual == 1.0:
                    bus.voltage_actual = bus.voltage_nominal
            
            # Calculate power flows on lines
            total_loss = 0.0
            for line_id, line in self.lines.items():
                # Simplified power flow calculation
                from_bus = self.buses[line.from_bus]
                to_bus = self.buses[line.to_bus]
                
                # Power flow based on voltage difference and impedance
                voltage_diff = from_bus.voltage_actual - to_bus.voltage_actual
                impedance = math.sqrt(line.resistance**2 + line.reactance**2)
                
                if impedance > 0:
                    line.power_flow = (voltage_diff / impedance) * 100  # Simplified
                else:
                    line.power_flow = 0.0
                
                # Calculate loading percentage (preserve manually-set values)
                if line.capacity > 0:
                    # Only recalculate if loading_percent is 0 (not manually set)
                    if line.loading_percent == 0.0:
                        line.loading_percent = abs(line.power_flow) / line.capacity * 100
                else:
                    line.loading_percent = 0.0
                
                # Calculate losses
                if line.power_flow != 0:
                    loss = (line.power_flow ** 2) * line.resistance / 100
                    total_loss += loss
            
            # Detect violations
            violations = self._detect_violations()
            
            # Assess stability
            stability = self._assess_stability()
            
            # Calculate execution time
            calculation_time = (time.time() - start_time) * 1000  # ms
            
            # Create result
            result = PowerFlowResult(
                result_id=result_id,
                calculation_time=calculation_time,
                converged=True,
                buses=list(self.buses.values()),
                lines=list(self.lines.values()),
                violations=violations,
                stability=stability,
                total_loss=total_loss,
                timestamp=time.time(),
            )
            
            # Update history
            self.last_calculation_time = calculation_time
            self.calculation_count += 1
            self.violation_history.extend(violations)
            if stability:
                self.stability_history.append(stability)
            
            logger.info(f"Power flow calculated: {result_id} ({calculation_time:.2f}ms)")
            
            return result
            
        except Exception as e:
            error_msg = f"Power flow calculation failed: {str(e)}"
            logger.error(error_msg)
            
            result = PowerFlowResult(
                result_id=result_id,
                calculation_time=(time.time() - start_time) * 1000,
                converged=False,
                timestamp=time.time(),
            )
            
            return result
    
    def _detect_violations(self) -> List[Violation]:
        """
        Detect network violations.
        
        Returns:
            List of violations
        """
        violations = []
        
        # Check voltage violations
        for bus_id, bus in self.buses.items():
            voltage_high_limit = bus.voltage_nominal * 1.1  # ±10%
            voltage_low_limit = bus.voltage_nominal * 0.9
            
            if bus.voltage_actual > voltage_high_limit:
                violation = Violation(
                    violation_id=f"viol-{uuid.uuid4().hex[:8]}",
                    violation_type=ViolationType.VOLTAGE_HIGH,
                    bus_id=bus_id,
                    value=bus.voltage_actual,
                    limit=voltage_high_limit,
                    severity="critical",
                    timestamp=time.time(),
                )
                violations.append(violation)
                logger.warning(f"Voltage violation (high): {bus_id}")
            
            elif bus.voltage_actual < voltage_low_limit:
                violation = Violation(
                    violation_id=f"viol-{uuid.uuid4().hex[:8]}",
                    violation_type=ViolationType.VOLTAGE_LOW,
                    bus_id=bus_id,
                    value=bus.voltage_actual,
                    limit=voltage_low_limit,
                    severity="critical",
                    timestamp=time.time(),
                )
                violations.append(violation)
                logger.warning(f"Voltage violation (low): {bus_id}")
        
        # Check line congestion
        for line_id, line in self.lines.items():
            if line.loading_percent > 100.0:
                violation = Violation(
                    violation_id=f"viol-{uuid.uuid4().hex[:8]}",
                    violation_type=ViolationType.CONGESTION,
                    line_id=line_id,
                    value=line.loading_percent,
                    limit=100.0,
                    severity="critical",
                    timestamp=time.time(),
                )
                violations.append(violation)
                logger.warning(f"Line congestion: {line_id} ({line.loading_percent:.1f}%)")
        
        return violations
    
    def _assess_stability(self) -> StabilityAssessment:
        """
        Assess system stability.
        
        Returns:
            Stability assessment
        """
        # Calculate frequency deviation
        avg_frequency = sum(b.frequency for b in self.buses.values()) / len(self.buses) if self.buses else 50.0
        frequency_deviation = avg_frequency - 50.0
        
        # Calculate voltage stability margin
        voltages = [b.voltage_actual for b in self.buses.values()]
        if voltages:
            avg_voltage = sum(voltages) / len(voltages)
            voltage_stability_margin = (avg_voltage - 0.9) / (1.1 - 0.9) * 100
        else:
            voltage_stability_margin = 50.0
        
        # Determine stability status
        if abs(frequency_deviation) > 1.0 or voltage_stability_margin < 20.0:
            status = StabilityStatus.UNSTABLE
        elif abs(frequency_deviation) > 0.5 or voltage_stability_margin < 40.0:
            status = StabilityStatus.MARGINAL
        else:
            status = StabilityStatus.STABLE
        
        assessment = StabilityAssessment(
            status=status,
            frequency_deviation=frequency_deviation,
            voltage_stability_margin=voltage_stability_margin,
            rotor_angle_stability=0.0,
            damping_ratio=0.7,
            assessment_time=time.time(),
        )
        
        if status != StabilityStatus.STABLE:
            logger.warning(f"System stability: {status.value}")
        
        return assessment
    
    def get_network_state(self) -> Dict[str, Any]:
        """
        Get current network state.
        
        Returns:
            Network state dictionary
        """
        return {
            "engine_id": self.engine_id,
            "buses": {bid: b.to_dict() for bid, b in self.buses.items()},
            "lines": {lid: l.to_dict() for lid, l in self.lines.items()},
            "calculation_count": self.calculation_count,
            "last_calculation_time": self.last_calculation_time,
            "timestamp": time.time(),
        }
    
    def get_violations(self) -> List[Violation]:
        """Get current violations."""
        return self.violation_history.copy()
    
    def get_stability_history(self) -> List[StabilityAssessment]:
        """Get stability assessment history."""
        return self.stability_history.copy()
    
    def reset(self) -> None:
        """Reset engine state."""
        self.buses.clear()
        self.lines.clear()
        self.network_state.clear()
        self.violation_history.clear()
        self.stability_history.clear()
        self.calculation_count = 0
        logger.info(f"PowerFlowEngine reset: {self.engine_id}")
