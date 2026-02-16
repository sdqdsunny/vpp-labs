"""
Power Generation Simulator for solar and wind resources.

Implements realistic power generation models based on weather data.
"""

import math
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass

from services.device_emulator import DeviceEmulator, DeviceCommand, CommandResult, DeviceState
from utils.errors import SimulatorError

logger = logging.getLogger(__name__)


@dataclass
class WeatherData:
    """Weather data for power generation calculation."""

    solar_irradiance: float  # W/m²
    temperature: float  # °C
    wind_speed: float  # m/s
    wind_direction: float  # degrees (0-360)
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class SolarSimulator(DeviceEmulator):
    """
    Solar power generation simulator.

    Models solar PV output based on irradiance, temperature, and efficiency.
    """

    def __init__(self, device_id: str, parameters: Dict[str, Any]):
        """
        Initialize solar simulator.

        Args:
            device_id: Unique device identifier
            parameters: Must include:
                - capacity_kw: Installed capacity in kW
                - efficiency: Panel efficiency (0-1)
                - temperature_coefficient: Efficiency change per °C
                - location: Geographic location
        """
        super().__init__(device_id, "solar", parameters)

        # Validate required parameters
        if not self.validate_parameters(["capacity_kw", "efficiency"]):
            raise SimulatorError(
                "Missing required solar parameters",
                simulator_id=device_id
            )

        self.initialize()

    def initialize(self) -> None:
        """Initialize solar simulator state."""
        self.state = {
            "power_output_kw": 0.0,
            "efficiency": self.parameters.get("efficiency", 0.18),
            "temperature": 25.0,
            "solar_irradiance": 0.0,
            "status": "idle",
        }
        self._update_timestamp()

    def update(self, time_delta: float) -> None:
        """
        Update solar output for time step.

        Args:
            time_delta: Time elapsed since last update (seconds)
        """
        # Solar output is determined by weather data
        # This is typically set via set_command with weather data
        self._update_timestamp()

    def get_state(self) -> DeviceState:
        """Get current solar simulator state."""
        return DeviceState(
            device_id=self.device_id,
            device_type=self.device_type,
            state_data=self.state.copy()
        )

    def set_command(self, command: DeviceCommand) -> CommandResult:
        """
        Process command for solar simulator.

        Supported commands:
        - "set_weather": Set weather data and recalculate output
        - "get_forecast": Get power forecast for next N hours
        """
        try:
            if command.command_type == "set_weather":
                return self._handle_set_weather(command)
            elif command.command_type == "get_forecast":
                return self._handle_get_forecast(command)
            else:
                return CommandResult(
                    success=False,
                    message=f"Unknown command: {command.command_type}"
                )
        except Exception as e:
            logger.error(
                f"Error processing solar command: {str(e)}",
                extra={"device_id": self.device_id}
            )
            return CommandResult(success=False, message=str(e))

    def _handle_set_weather(self, command: DeviceCommand) -> CommandResult:
        """Handle weather data update."""
        try:
            irradiance = command.parameters.get("solar_irradiance", 0.0)
            temperature = command.parameters.get("temperature", 25.0)

            # Validate inputs
            if irradiance < 0:
                return CommandResult(
                    success=False,
                    message=f"Invalid irradiance: {irradiance}"
                )

            # Calculate power output
            power_kw = self._calculate_power_output(irradiance, temperature)

            self.state["solar_irradiance"] = irradiance
            self.state["temperature"] = temperature
            self.state["power_output_kw"] = power_kw
            self.state["status"] = "generating" if power_kw > 0 else "idle"

            self._update_timestamp()

            return CommandResult(
                success=True,
                message="Weather data updated",
                data={"power_output_kw": power_kw}
            )
        except Exception as e:
            return CommandResult(success=False, message=str(e))

    def _handle_get_forecast(self, command: DeviceCommand) -> CommandResult:
        """Handle forecast request."""
        hours = command.parameters.get("hours", 24)
        # Placeholder forecast - would use weather forecast data
        forecast = [self.state["power_output_kw"] * 0.9 for _ in range(hours)]
        return CommandResult(
            success=True,
            message="Forecast generated",
            data={"forecast_kw": forecast}
        )

    def _calculate_power_output(self, irradiance: float, temperature: float) -> float:
        """
        Calculate solar power output.

        Args:
            irradiance: Solar irradiance in W/m²
            temperature: Ambient temperature in °C

        Returns:
            Power output in kW
        """
        capacity_kw = self.parameters["capacity_kw"]
        base_efficiency = self.parameters.get("efficiency", 0.18)
        temp_coefficient = self.parameters.get("temperature_coefficient", -0.004)

        # Reference conditions: 1000 W/m², 25°C
        reference_irradiance = 1000.0
        reference_temp = 25.0

        # Adjust efficiency for temperature
        temp_delta = temperature - reference_temp
        efficiency = base_efficiency * (1 + temp_coefficient * temp_delta)
        efficiency = max(0, min(efficiency, base_efficiency))  # Clamp to valid range

        # Calculate power output
        # Power = Capacity × (Irradiance / Reference) × Efficiency
        power_kw = capacity_kw * (irradiance / reference_irradiance) * efficiency

        # Clamp to capacity
        power_kw = max(0, min(power_kw, capacity_kw))

        return round(power_kw, 3)

    def get_efficiency(self) -> float:
        """Get current efficiency."""
        return self.state["efficiency"]

    def get_generation_forecast(self, hours: int) -> List[float]:
        """Get generation forecast for next N hours."""
        # Placeholder - would use weather forecast
        return [self.state["power_output_kw"] * 0.9 for _ in range(hours)]

    def get_capabilities(self) -> Dict[str, Any]:
        """Get solar simulator capabilities."""
        return {
            "device_type": "solar",
            "capacity_kw": self.parameters["capacity_kw"],
            "efficiency": self.parameters.get("efficiency", 0.18),
            "supported_commands": ["set_weather", "get_forecast"],
            "max_irradiance": 1500,  # W/m²
            "temp_range": (-20, 60),  # °C
        }

    def reset(self) -> None:
        """Reset solar simulator to initial state."""
        self.initialize()


class WindSimulator(DeviceEmulator):
    """
    Wind power generation simulator.

    Models wind turbine output based on wind speed and direction.
    """

    def __init__(self, device_id: str, parameters: Dict[str, Any]):
        """
        Initialize wind simulator.

        Args:
            device_id: Unique device identifier
            parameters: Must include:
                - capacity_kw: Installed capacity in kW
                - hub_height: Hub height in meters
                - cut_in_speed: Cut-in wind speed (m/s)
                - rated_speed: Rated wind speed (m/s)
                - cut_out_speed: Cut-out wind speed (m/s)
        """
        super().__init__(device_id, "wind", parameters)

        if not self.validate_parameters(["capacity_kw", "hub_height"]):
            raise SimulatorError(
                "Missing required wind parameters",
                simulator_id=device_id
            )

        self.initialize()

    def initialize(self) -> None:
        """Initialize wind simulator state."""
        self.state = {
            "power_output_kw": 0.0,
            "wind_speed": 0.0,
            "wind_direction": 0.0,
            "status": "idle",
        }
        self._update_timestamp()

    def update(self, time_delta: float) -> None:
        """Update wind output for time step."""
        self._update_timestamp()

    def get_state(self) -> DeviceState:
        """Get current wind simulator state."""
        return DeviceState(
            device_id=self.device_id,
            device_type=self.device_type,
            state_data=self.state.copy()
        )

    def set_command(self, command: DeviceCommand) -> CommandResult:
        """
        Process command for wind simulator.

        Supported commands:
        - "set_weather": Set wind speed and direction
        - "get_forecast": Get power forecast
        """
        try:
            if command.command_type == "set_weather":
                return self._handle_set_weather(command)
            elif command.command_type == "get_forecast":
                return self._handle_get_forecast(command)
            else:
                return CommandResult(
                    success=False,
                    message=f"Unknown command: {command.command_type}"
                )
        except Exception as e:
            logger.error(
                f"Error processing wind command: {str(e)}",
                extra={"device_id": self.device_id}
            )
            return CommandResult(success=False, message=str(e))

    def _handle_set_weather(self, command: DeviceCommand) -> CommandResult:
        """Handle weather data update."""
        try:
            wind_speed = command.parameters.get("wind_speed", 0.0)
            wind_direction = command.parameters.get("wind_direction", 0.0)

            # Validate inputs
            if wind_speed < 0 or wind_speed > 50:
                return CommandResult(
                    success=False,
                    message=f"Invalid wind speed: {wind_speed}"
                )

            # Calculate power output
            power_kw = self._calculate_power_output(wind_speed)

            self.state["wind_speed"] = wind_speed
            self.state["wind_direction"] = wind_direction
            self.state["power_output_kw"] = power_kw
            self.state["status"] = "generating" if power_kw > 0 else "idle"

            self._update_timestamp()

            return CommandResult(
                success=True,
                message="Weather data updated",
                data={"power_output_kw": power_kw}
            )
        except Exception as e:
            return CommandResult(success=False, message=str(e))

    def _handle_get_forecast(self, command: DeviceCommand) -> CommandResult:
        """Handle forecast request."""
        hours = command.parameters.get("hours", 24)
        forecast = [self.state["power_output_kw"] * 0.85 for _ in range(hours)]
        return CommandResult(
            success=True,
            message="Forecast generated",
            data={"forecast_kw": forecast}
        )

    def _calculate_power_output(self, wind_speed: float) -> float:
        """
        Calculate wind power output using power curve.

        Args:
            wind_speed: Wind speed at hub height in m/s

        Returns:
            Power output in kW
        """
        capacity_kw = self.parameters["capacity_kw"]
        cut_in = self.parameters.get("cut_in_speed", 3.0)
        rated = self.parameters.get("rated_speed", 12.0)
        cut_out = self.parameters.get("cut_out_speed", 25.0)

        # Simple power curve model
        if wind_speed < cut_in or wind_speed > cut_out:
            return 0.0
        elif wind_speed >= rated:
            return capacity_kw
        else:
            # Cubic relationship between cut-in and rated
            normalized = (wind_speed - cut_in) / (rated - cut_in)
            power_kw = capacity_kw * (normalized ** 3)
            return round(power_kw, 3)

    def get_generation_forecast(self, hours: int) -> List[float]:
        """Get generation forecast for next N hours."""
        return [self.state["power_output_kw"] * 0.85 for _ in range(hours)]

    def get_capabilities(self) -> Dict[str, Any]:
        """Get wind simulator capabilities."""
        return {
            "device_type": "wind",
            "capacity_kw": self.parameters["capacity_kw"],
            "hub_height": self.parameters.get("hub_height", 80),
            "cut_in_speed": self.parameters.get("cut_in_speed", 3.0),
            "rated_speed": self.parameters.get("rated_speed", 12.0),
            "cut_out_speed": self.parameters.get("cut_out_speed", 25.0),
            "supported_commands": ["set_weather", "get_forecast"],
            "max_wind_speed": 50,  # m/s
        }

    def reset(self) -> None:
        """Reset wind simulator to initial state."""
        self.initialize()
