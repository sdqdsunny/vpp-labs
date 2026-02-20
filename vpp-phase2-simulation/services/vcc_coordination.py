"""
VCC Master Coordination Service.

Implements:
- CoordinationService: Executes VCC coordination decisions
- Collects data from all sides
- Calculates optimal schedule
- Generates control commands
"""

import uuid
from datetime import datetime
from typing import Optional, Tuple
import logging

from models.realtime_data_models import (
    PowerGenerationData, StorageData, DemandData,
    PowerCommand, StorageCommand, DemandCommand,
    CoordinationResult
)

logger = logging.getLogger(__name__)


class CoordinationService:
    """VCC Master coordination service."""

    def __init__(self):
        """Initialize coordination service."""
        self.last_power_data: Optional[PowerGenerationData] = None
        self.last_storage_data: Optional[StorageData] = None
        self.last_demand_data: Optional[DemandData] = None
        self.coordination_count = 0
        self.last_coordination_time: Optional[datetime] = None

    def set_latest_data(self, power_data: PowerGenerationData = None,
                       storage_data: StorageData = None,
                       demand_data: DemandData = None):
        """Set latest data from sides.
        
        Args:
            power_data: Latest power generation data
            storage_data: Latest storage data
            demand_data: Latest demand data
        """
        if power_data:
            self.last_power_data = power_data
        if storage_data:
            self.last_storage_data = storage_data
        if demand_data:
            self.last_demand_data = demand_data

    def coordinate(self) -> Optional[CoordinationResult]:
        """Execute coordination decision.
        
        Returns:
            CoordinationResult: Coordination result with commands, or None if data incomplete
        """
        # Check if all data is available
        if not self._has_all_data():
            logger.warning("Coordination skipped: incomplete data from sides")
            return None

        try:
            # Calculate optimal schedule
            power_cmd, storage_cmd, demand_cmd, score = self.calculate_optimal_schedule(
                self.last_power_data,
                self.last_storage_data,
                self.last_demand_data
            )

            # Create coordination result
            result = CoordinationResult(
                timestamp=datetime.now(),
                power_command=power_cmd,
                storage_command=storage_cmd,
                demand_command=demand_cmd,
                optimization_score=score,
                status="success"
            )

            self.coordination_count += 1
            self.last_coordination_time = datetime.now()

            logger.info(f"Coordination executed: score={score:.1f}, count={self.coordination_count}")
            return result

        except Exception as e:
            logger.error(f"Coordination failed: {str(e)}")
            return None

    def calculate_optimal_schedule(self,
                                   power_data: PowerGenerationData,
                                   storage_data: StorageData,
                                   demand_data: DemandData) -> Tuple[PowerCommand, StorageCommand, DemandCommand, float]:
        """Calculate optimal schedule based on current data.
        
        Implements a simple load balancing algorithm:
        1. Calculate total available power (generation + storage discharge)
        2. Calculate total demand
        3. Balance power and storage to meet demand
        4. Adjust demand if necessary
        
        Args:
            power_data: Current power generation data
            storage_data: Current storage data
            demand_data: Current demand data
            
        Returns:
            Tuple of (PowerCommand, StorageCommand, DemandCommand, optimization_score)
        """
        # Generate command IDs
        cmd_id = str(uuid.uuid4())[:8]

        # Extract current values
        current_power = power_data.current_power
        soc = storage_data.soc
        current_load = demand_data.current_load

        # Calculate total available power (assuming storage can discharge if needed)
        # For calculation purposes, assume storage can provide up to 100kW if SOC > 30%
        if soc > 30:
            available_storage_power = 100.0  # Can discharge
        else:
            available_storage_power = 0.0  # Cannot discharge when SOC is very low

        # Calculate total available power
        total_available = current_power + available_storage_power

        # Calculate optimization score (0-100)
        # Score based on how well we can meet demand
        if total_available >= current_load:
            # Can meet demand
            optimization_score = min(100.0, 80.0 + (total_available - current_load) / 10.0)
        else:
            # Cannot fully meet demand
            shortage = current_load - total_available
            optimization_score = max(0.0, 80.0 - (shortage / current_load) * 20.0)

        # Generate power command
        # Target power should be current power adjusted for demand
        if total_available < current_load:
            # Need more power, increase generation
            target_power = min(current_power * 1.1, 200.0)
        else:
            # Have excess power, can reduce generation
            target_power = max(current_power * 0.9, 50.0)

        power_cmd = PowerCommand(
            command_id=f"power_{cmd_id}",
            target_power=target_power,
            duration=300,  # 5 minutes
            priority=1
        )

        # Generate storage command
        # Adjust storage action based on SOC and demand
        if soc < 20:
            # Low SOC, should charge (priority)
            storage_action = "charging"
            target_storage_power = 80.0
        elif total_available < current_load:
            # Shortage, discharge storage (priority)
            storage_action = "discharging"
            target_storage_power = 60.0
        elif soc > 80:
            # High SOC, should discharge to help with demand
            storage_action = "discharging"
            target_storage_power = 50.0
        else:
            # Balanced, idle or light charge
            storage_action = "idle"
            target_storage_power = 0.0

        storage_cmd = StorageCommand(
            command_id=f"storage_{cmd_id}",
            action=storage_action,
            target_power=target_storage_power,
            duration=300
        )

        # Generate demand command
        # Adjust demand based on available power
        if total_available < current_load:
            # Shortage, request demand reduction
            demand_action = "decrease"
            target_load = current_load * 0.9
        elif total_available > current_load * 1.2:
            # Excess power, can increase demand (e.g., EV charging)
            demand_action = "increase"
            target_load = min(current_load * 1.1, demand_data.adjustable_range[1])
        else:
            # Balanced
            demand_action = "maintain"
            target_load = current_load

        # Ensure target load is within adjustable range
        target_load = max(demand_data.adjustable_range[0],
                         min(target_load, demand_data.adjustable_range[1]))

        demand_cmd = DemandCommand(
            command_id=f"demand_{cmd_id}",
            action=demand_action,
            target_load=target_load,
            duration=300
        )

        return power_cmd, storage_cmd, demand_cmd, optimization_score

    def get_stats(self) -> dict:
        """Get coordination statistics.
        
        Returns:
            dict: Statistics including coordination count, last time, etc.
        """
        return {
            "coordination_count": self.coordination_count,
            "last_coordination_time": self.last_coordination_time.isoformat() if self.last_coordination_time else None,
            "has_power_data": self.last_power_data is not None,
            "has_storage_data": self.last_storage_data is not None,
            "has_demand_data": self.last_demand_data is not None,
        }

    def _has_all_data(self) -> bool:
        """Check if all required data is available.
        
        Returns:
            bool: True if all data is available
        """
        return (self.last_power_data is not None and
                self.last_storage_data is not None and
                self.last_demand_data is not None)
