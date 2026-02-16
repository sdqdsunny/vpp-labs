"""
Demand-Side Simulator for controllable loads.

Implements realistic load profiles with demand response capabilities.
"""

import logging
import math
from typing import Dict, Any, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

from services.device_emulator import DeviceEmulator, DeviceCommand, CommandResult, DeviceState
from utils.errors import SimulatorError

logger = logging.getLogger(__name__)


class LoadSimulator(DeviceEmulator):
    """
    Demand-side load simulator.

    Models controllable loads with realistic profiles and demand response.
    """

    def __init__(self, device_id: str, parameters: Dict[str, Any]):
        """
        Initialize load simulator.

        Args:
            device_id: Unique device identifier
            parameters: Must include:
                - base_load_kw: Base load in kW
                - min_load_kw: Minimum load (flexibility lower bound)
                - max_load_kw: Maximum load (flexibility upper bound)
                - flexibility_range: (min_factor, max_factor) relative to base
        """
        super().__init__(device_id, "load", parameters)

        if not self.validate_parameters(["base_load_kw"]):
            raise SimulatorError(
                "Missing required load parameters",
                simulator_id=device_id
            )

        self.initialize()

    def initialize(self) -> None:
        """Initialize load simulator state."""
        base_load = self.parameters["base_load_kw"]
        
        # Calculate flexibility range
        flexibility = self.parameters.get("flexibility_range", (0.8, 1.2))
        min_load = self.parameters.get("min_load_kw", base_load * flexibility[0])
        max_load = self.parameters.get("max_load_kw", base_load * flexibility[1])

        self.state = {
            "current_load_kw": base_load,
            "base_load_kw": base_load,
            "min_load_kw": min_load,
            "max_load_kw": max_load,
            "demand_response_signal": 1.0,  # 1.0 = normal, <1.0 = reduce, >1.0 = increase
            "status": "normal",
            "daily_pattern": self._generate_daily_pattern(),
            "seasonal_factor": 1.0,
            "hour_of_day": 0,
        }
        self._update_timestamp()

    def update(self, time_delta: float) -> None:
        """
        Update load state for time step.

        Args:
            time_delta: Time elapsed since last update (seconds)
        """
        # Update hour of day for pattern tracking
        self.state["hour_of_day"] = (self.state["hour_of_day"] + time_delta / 3600.0) % 24.0
        
        # Recalculate current load based on patterns
        self._update_current_load()
        self._update_timestamp()

    def get_state(self) -> DeviceState:
        """Get current load simulator state."""
        return DeviceState(
            device_id=self.device_id,
            device_type=self.device_type,
            state_data=self.state.copy()
        )

    def set_command(self, command: DeviceCommand) -> CommandResult:
        """
        Process command for load simulator.

        Supported commands:
        - "set_demand_response": Set demand response signal
        - "get_current_load": Get current load
        - "get_load_forecast": Get load forecast for next N hours
        - "get_flexibility_range": Get flexibility bounds
        """
        try:
            if command.command_type == "set_demand_response":
                return self._handle_set_demand_response(command)
            elif command.command_type == "get_current_load":
                return self._handle_get_current_load(command)
            elif command.command_type == "get_load_forecast":
                return self._handle_get_load_forecast(command)
            elif command.command_type == "get_flexibility_range":
                return self._handle_get_flexibility_range(command)
            else:
                return CommandResult(
                    success=False,
                    message=f"Unknown command: {command.command_type}"
                )
        except Exception as e:
            logger.error(
                f"Error processing load command: {str(e)}",
                extra={"device_id": self.device_id}
            )
            return CommandResult(success=False, message=str(e))

    def _handle_set_demand_response(self, command: DeviceCommand) -> CommandResult:
        """Handle demand response signal."""
        try:
            signal = command.parameters.get("signal", 1.0)

            # Validate signal (typically 0.5 to 1.5)
            if signal < 0.5 or signal > 1.5:
                return CommandResult(
                    success=False,
                    message=f"Invalid demand response signal: {signal}"
                )

            self.state["demand_response_signal"] = signal
            
            # Update status based on signal
            if signal < 0.9:
                self.state["status"] = "reduced"
            elif signal > 1.1:
                self.state["status"] = "increased"
            else:
                self.state["status"] = "normal"

            # Recalculate load
            self._update_current_load()
            self._update_timestamp()

            return CommandResult(
                success=True,
                message="Demand response signal updated",
                data={
                    "current_load_kw": self.state["current_load_kw"],
                    "status": self.state["status"]
                }
            )
        except Exception as e:
            return CommandResult(success=False, message=str(e))

    def _handle_get_current_load(self, command: DeviceCommand) -> CommandResult:
        """Get current load."""
        return CommandResult(
            success=True,
            message="Current load retrieved",
            data={"current_load_kw": self.state["current_load_kw"]}
        )

    def _handle_get_load_forecast(self, command: DeviceCommand) -> CommandResult:
        """Get load forecast for next N hours."""
        hours = command.parameters.get("hours", 24)
        forecast = self._generate_load_forecast(hours)
        
        return CommandResult(
            success=True,
            message="Load forecast generated",
            data={"forecast_kw": forecast}
        )

    def _handle_get_flexibility_range(self, command: DeviceCommand) -> CommandResult:
        """Get flexibility range."""
        return CommandResult(
            success=True,
            message="Flexibility range retrieved",
            data={
                "min_load_kw": self.state["min_load_kw"],
                "max_load_kw": self.state["max_load_kw"],
                "current_load_kw": self.state["current_load_kw"]
            }
        )

    def _update_current_load(self) -> None:
        """Update current load based on patterns and demand response."""
        base_load = self.state["base_load_kw"]
        hour = int(self.state["hour_of_day"])
        
        # Apply daily pattern
        daily_factor = self.state["daily_pattern"].get(hour, 1.0)
        
        # Apply seasonal factor
        seasonal_factor = self.state["seasonal_factor"]
        
        # Apply demand response signal
        dr_signal = self.state["demand_response_signal"]
        
        # Calculate load
        load = base_load * daily_factor * seasonal_factor * dr_signal
        
        # Clamp to flexibility range
        load = max(self.state["min_load_kw"], min(load, self.state["max_load_kw"]))
        
        self.state["current_load_kw"] = round(load, 3)

    def _generate_daily_pattern(self) -> Dict[int, float]:
        """
        Generate realistic daily load pattern.

        Returns:
            Dictionary mapping hour (0-23) to load factor
        """
        # Typical daily pattern: low at night, peak during day
        pattern = {}
        for hour in range(24):
            if hour < 6:  # Night (0-6)
                factor = 0.6 + 0.2 * (hour / 6.0)
            elif hour < 9:  # Morning ramp (6-9)
                factor = 0.8 + 0.2 * ((hour - 6) / 3.0)
            elif hour < 17:  # Day (9-17)
                factor = 1.0 + 0.1 * math.sin((hour - 9) * math.pi / 8.0)
            elif hour < 21:  # Evening ramp (17-21)
                factor = 1.0 - 0.2 * ((hour - 17) / 4.0)
            else:  # Night (21-24)
                factor = 0.8 - 0.2 * ((hour - 21) / 3.0)
            
            pattern[hour] = max(0.5, min(1.5, factor))
        
        return pattern

    def _generate_load_forecast(self, hours: int) -> List[float]:
        """
        Generate load forecast for next N hours.

        Args:
            hours: Number of hours to forecast

        Returns:
            List of forecasted loads in kW
        """
        forecast = []
        current_hour = self.state["hour_of_day"]
        
        for i in range(hours):
            hour = int((current_hour + i) % 24)
            daily_factor = self.state["daily_pattern"].get(hour, 1.0)
            seasonal_factor = self.state["seasonal_factor"]
            dr_signal = self.state["demand_response_signal"]
            
            load = self.state["base_load_kw"] * daily_factor * seasonal_factor * dr_signal
            load = max(self.state["min_load_kw"], min(load, self.state["max_load_kw"]))
            forecast.append(round(load, 3))
        
        return forecast

    def get_current_load(self) -> float:
        """Get current load in kW."""
        return self.state["current_load_kw"]

    def get_load_forecast(self, hours: int) -> List[float]:
        """Get load forecast for next N hours."""
        return self._generate_load_forecast(hours)

    def get_flexibility_range(self) -> Tuple[float, float]:
        """Get flexibility range (min, max) in kW."""
        return (self.state["min_load_kw"], self.state["max_load_kw"])

    def set_seasonal_factor(self, factor: float) -> None:
        """
        Set seasonal factor (e.g., 1.2 for summer, 0.8 for winter).

        Args:
            factor: Seasonal adjustment factor
        """
        self.state["seasonal_factor"] = max(0.5, min(1.5, factor))
        self._update_current_load()

    def get_capabilities(self) -> Dict[str, Any]:
        """Get load simulator capabilities."""
        return {
            "device_type": "load",
            "base_load_kw": self.parameters["base_load_kw"],
            "min_load_kw": self.state["min_load_kw"],
            "max_load_kw": self.state["max_load_kw"],
            "flexibility_range": self.parameters.get("flexibility_range", (0.8, 1.2)),
            "supported_commands": [
                "set_demand_response",
                "get_current_load",
                "get_load_forecast",
                "get_flexibility_range"
            ],
        }

    def reset(self) -> None:
        """Reset load simulator to initial state."""
        self.initialize()
