"""
Energy Storage Simulator for battery systems.

Implements realistic battery charging/discharging with SOC and SOH tracking.
"""

import logging
from typing import Dict, Any, List, Tuple
from datetime import datetime
from dataclasses import dataclass

from services.device_emulator import DeviceEmulator, DeviceCommand, CommandResult, DeviceState
from utils.errors import SimulatorError

logger = logging.getLogger(__name__)


@dataclass
class BatteryState:
    """Battery state information."""

    soc: float  # State of Charge (0-100%)
    soh: float  # State of Health (0-100%)
    power_kw: float  # Current power (positive=charging, negative=discharging)
    voltage: float  # Terminal voltage
    temperature: float  # Battery temperature


class BatterySimulator(DeviceEmulator):
    """
    Battery energy storage simulator.

    Models battery charging/discharging with SOC/SOH tracking and efficiency losses.
    """

    def __init__(self, device_id: str, parameters: Dict[str, Any]):
        """
        Initialize battery simulator.

        Args:
            device_id: Unique device identifier
            parameters: Must include:
                - capacity_kwh: Battery capacity in kWh
                - power_rating_kw: Max charge/discharge power in kW
                - efficiency: Round-trip efficiency (0-1)
                - min_soc: Minimum SOC limit (%)
                - max_soc: Maximum SOC limit (%)
        """
        super().__init__(device_id, "battery", parameters)

        if not self.validate_parameters(["capacity_kwh", "power_rating_kw", "efficiency"]):
            raise SimulatorError(
                "Missing required battery parameters",
                simulator_id=device_id
            )

        self.initialize()

    def initialize(self) -> None:
        """Initialize battery simulator state."""
        initial_soc = self.parameters.get("initial_soc", 50.0)
        
        self.state = {
            "soc": initial_soc,  # State of Charge (%)
            "soh": 100.0,  # State of Health (%)
            "power_kw": 0.0,  # Current power
            "voltage": self._calculate_voltage(initial_soc),
            "temperature": 25.0,
            "status": "idle",
            "charge_cycles": 0,
            "energy_charged_kwh": 0.0,
            "energy_discharged_kwh": 0.0,
        }
        self._update_timestamp()

    def update(self, time_delta: float) -> None:
        """
        Update battery state for time step.

        Args:
            time_delta: Time elapsed since last update (seconds)
        """
        # Battery state is updated via commands
        # This method is called periodically for passive updates
        self._update_timestamp()

    def get_state(self) -> DeviceState:
        """Get current battery simulator state."""
        return DeviceState(
            device_id=self.device_id,
            device_type=self.device_type,
            state_data=self.state.copy()
        )

    def set_command(self, command: DeviceCommand) -> CommandResult:
        """
        Process command for battery simulator.

        Supported commands:
        - "charge": Charge battery with specified power
        - "discharge": Discharge battery with specified power
        - "set_power": Set power (positive=charge, negative=discharge)
        - "get_available_power": Get available power for charge/discharge
        """
        try:
            if command.command_type == "charge":
                return self._handle_charge(command)
            elif command.command_type == "discharge":
                return self._handle_discharge(command)
            elif command.command_type == "set_power":
                return self._handle_set_power(command)
            elif command.command_type == "get_available_power":
                return self._handle_get_available_power(command)
            else:
                return CommandResult(
                    success=False,
                    message=f"Unknown command: {command.command_type}"
                )
        except Exception as e:
            logger.error(
                f"Error processing battery command: {str(e)}",
                extra={"device_id": self.device_id}
            )
            return CommandResult(success=False, message=str(e))

    def _handle_charge(self, command: DeviceCommand) -> CommandResult:
        """Handle charging command."""
        try:
            power_kw = command.parameters.get("power_kw", 0.0)
            duration_hours = command.parameters.get("duration_hours", 1.0)

            # Validate inputs
            if power_kw < 0:
                return CommandResult(
                    success=False,
                    message=f"Invalid charge power: {power_kw}"
                )

            # Check if already at max SOC
            if self.state["soc"] >= self.parameters.get("max_soc", 100.0):
                return CommandResult(
                    success=False,
                    message="Battery already at maximum SOC"
                )

            # Calculate energy to charge
            energy_kwh = power_kw * duration_hours
            
            # Apply efficiency loss
            efficiency = self.parameters.get("efficiency", 0.95)
            energy_loss = energy_kwh * (1 - efficiency)
            
            # Update SOC
            capacity = self.parameters["capacity_kwh"]
            soc_increase = (energy_kwh / capacity) * 100
            new_soc = min(
                self.state["soc"] + soc_increase,
                self.parameters.get("max_soc", 100.0)
            )

            # Update state
            self.state["soc"] = new_soc
            self.state["power_kw"] = power_kw
            self.state["status"] = "charging"
            self.state["energy_charged_kwh"] += energy_kwh
            self.state["voltage"] = self._calculate_voltage(new_soc)

            # Track cycle (half cycle for charging)
            self.state["charge_cycles"] += 0.5

            self._update_timestamp()

            return CommandResult(
                success=True,
                message="Charging command executed",
                data={
                    "soc": new_soc,
                    "energy_charged_kwh": energy_kwh,
                    "energy_loss_kwh": energy_loss
                }
            )
        except Exception as e:
            return CommandResult(success=False, message=str(e))

    def _handle_discharge(self, command: DeviceCommand) -> CommandResult:
        """Handle discharging command."""
        try:
            power_kw = command.parameters.get("power_kw", 0.0)
            duration_hours = command.parameters.get("duration_hours", 1.0)

            # Validate inputs
            if power_kw < 0:
                return CommandResult(
                    success=False,
                    message=f"Invalid discharge power: {power_kw}"
                )

            # Check if already at min SOC
            if self.state["soc"] <= self.parameters.get("min_soc", 0.0):
                return CommandResult(
                    success=False,
                    message="Battery already at minimum SOC"
                )

            # Calculate energy to discharge
            energy_kwh = power_kw * duration_hours
            
            # Apply efficiency loss
            efficiency = self.parameters.get("efficiency", 0.95)
            energy_loss = energy_kwh * (1 - efficiency)
            
            # Update SOC
            capacity = self.parameters["capacity_kwh"]
            soc_decrease = (energy_kwh / capacity) * 100
            new_soc = max(
                self.state["soc"] - soc_decrease,
                self.parameters.get("min_soc", 0.0)
            )

            # Update state
            self.state["soc"] = new_soc
            self.state["power_kw"] = -power_kw  # Negative for discharge
            self.state["status"] = "discharging"
            self.state["energy_discharged_kwh"] += energy_kwh
            self.state["voltage"] = self._calculate_voltage(new_soc)

            # Track cycle (half cycle for discharging)
            self.state["charge_cycles"] += 0.5

            self._update_timestamp()

            return CommandResult(
                success=True,
                message="Discharging command executed",
                data={
                    "soc": new_soc,
                    "energy_discharged_kwh": energy_kwh,
                    "energy_loss_kwh": energy_loss
                }
            )
        except Exception as e:
            return CommandResult(success=False, message=str(e))

    def _handle_set_power(self, command: DeviceCommand) -> CommandResult:
        """Handle set power command (positive=charge, negative=discharge)."""
        power_kw = command.parameters.get("power_kw", 0.0)
        duration_hours = command.parameters.get("duration_hours", 1.0)

        if power_kw > 0:
            return self._handle_charge(DeviceCommand(
                command_type="charge",
                parameters={
                    "power_kw": power_kw,
                    "duration_hours": duration_hours
                }
            ))
        elif power_kw < 0:
            return self._handle_discharge(DeviceCommand(
                command_type="discharge",
                parameters={
                    "power_kw": abs(power_kw),
                    "duration_hours": duration_hours
                }
            ))
        else:
            self.state["power_kw"] = 0.0
            self.state["status"] = "idle"
            return CommandResult(
                success=True,
                message="Battery idle",
                data={"soc": self.state["soc"]}
            )

    def _handle_get_available_power(self, command: DeviceCommand) -> CommandResult:
        """Get available power for charging/discharging."""
        capacity = self.parameters["capacity_kwh"]
        power_rating = self.parameters["power_rating_kw"]
        soc = self.state["soc"]
        min_soc = self.parameters.get("min_soc", 0.0)
        max_soc = self.parameters.get("max_soc", 100.0)

        # Available power for charging
        charge_available = power_rating if soc < max_soc else 0.0
        
        # Available power for discharging
        discharge_available = power_rating if soc > min_soc else 0.0

        return CommandResult(
            success=True,
            message="Available power calculated",
            data={
                "charge_power_kw": charge_available,
                "discharge_power_kw": discharge_available,
                "soc": soc
            }
        )

    def _calculate_voltage(self, soc: float) -> float:
        """
        Calculate terminal voltage based on SOC.

        Uses simplified linear model.
        """
        # Typical Li-ion: 2.5V (empty) to 4.2V (full) per cell
        # Assuming 48V system (typical for storage)
        min_voltage = 40.0  # 2.5V × 16 cells
        max_voltage = 67.2  # 4.2V × 16 cells
        
        voltage = min_voltage + (max_voltage - min_voltage) * (soc / 100.0)
        return round(voltage, 2)

    def get_soc(self) -> float:
        """Get state of charge (%)."""
        return self.state["soc"]

    def get_soh(self) -> float:
        """Get state of health (%)."""
        # Simplified SOH model: degrades with cycles
        cycles = self.state["charge_cycles"]
        # Assume 5000 cycles to 80% SOH
        soh = max(80.0, 100.0 - (cycles / 5000.0) * 20.0)
        return round(soh, 2)

    def get_available_power(self) -> Tuple[float, float]:
        """
        Get available power for charge and discharge.

        Returns:
            Tuple of (charge_power_kw, discharge_power_kw)
        """
        cmd = DeviceCommand(command_type="get_available_power", parameters={})
        result = self.set_command(cmd)
        
        if result.success:
            return (
                result.data["charge_power_kw"],
                result.data["discharge_power_kw"]
            )
        return (0.0, 0.0)

    def get_capabilities(self) -> Dict[str, Any]:
        """Get battery simulator capabilities."""
        return {
            "device_type": "battery",
            "capacity_kwh": self.parameters["capacity_kwh"],
            "power_rating_kw": self.parameters["power_rating_kw"],
            "efficiency": self.parameters.get("efficiency", 0.95),
            "min_soc": self.parameters.get("min_soc", 0.0),
            "max_soc": self.parameters.get("max_soc", 100.0),
            "supported_commands": ["charge", "discharge", "set_power", "get_available_power"],
        }

    def reset(self) -> None:
        """Reset battery simulator to initial state."""
        self.initialize()
