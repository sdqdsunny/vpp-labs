"""
Real-time data exchange service interfaces.

Defines abstract base classes for:
- Data reception service
- Data collection service
- Data reporting service
- Command execution service
- Coordination service
- Command service
"""

from abc import ABC, abstractmethod
from typing import Optional, List
from datetime import datetime
from models.realtime_data_models import (
    PowerGenerationData, StorageData, DemandData,
    PowerCommand, StorageCommand, DemandCommand,
    CommandResult, CoordinationResult
)


class DataReceptionService(ABC):
    """Abstract base class for data reception service."""

    @abstractmethod
    def receive_power_generation_data(self, data: PowerGenerationData) -> bool:
        """
        Receive power generation data.
        
        Args:
            data: Power generation data
            
        Returns:
            True if data was successfully received and stored, False otherwise
        """
        pass

    @abstractmethod
    def receive_storage_data(self, data: StorageData) -> bool:
        """
        Receive storage data.
        
        Args:
            data: Storage data
            
        Returns:
            True if data was successfully received and stored, False otherwise
        """
        pass

    @abstractmethod
    def receive_demand_data(self, data: DemandData) -> bool:
        """
        Receive demand data.
        
        Args:
            data: Demand data
            
        Returns:
            True if data was successfully received and stored, False otherwise
        """
        pass


class DataCollectionService(ABC):
    """Abstract base class for data collection service."""

    @abstractmethod
    def collect_power_data(self) -> PowerGenerationData:
        """
        Collect power generation data.
        
        Returns:
            Power generation data
        """
        pass

    @abstractmethod
    def collect_storage_data(self) -> StorageData:
        """
        Collect storage data.
        
        Returns:
            Storage data
        """
        pass

    @abstractmethod
    def collect_demand_data(self) -> DemandData:
        """
        Collect demand data.
        
        Returns:
            Demand data
        """
        pass


class DataReportingService(ABC):
    """Abstract base class for data reporting service."""

    @abstractmethod
    def start_reporting(self, interval: int = 5) -> None:
        """
        Start periodic data reporting.
        
        Args:
            interval: Reporting interval in seconds (default: 5)
        """
        pass

    @abstractmethod
    def stop_reporting(self) -> None:
        """Stop periodic data reporting."""
        pass

    @abstractmethod
    def report_data(self, data, endpoint: str, max_retries: int = 3) -> bool:
        """
        Report data to VCC with retry mechanism.
        
        Args:
            data: Data to report
            endpoint: VCC endpoint URL
            max_retries: Maximum number of retries (default: 3)
            
        Returns:
            True if data was successfully reported, False otherwise
        """
        pass


class CommandExecutionService(ABC):
    """Abstract base class for command execution service."""

    @abstractmethod
    def execute_power_command(self, command: PowerCommand) -> CommandResult:
        """
        Execute power generation command.
        
        Args:
            command: Power command
            
        Returns:
            Command execution result
        """
        pass

    @abstractmethod
    def execute_storage_command(self, command: StorageCommand) -> CommandResult:
        """
        Execute storage command.
        
        Args:
            command: Storage command
            
        Returns:
            Command execution result
        """
        pass

    @abstractmethod
    def execute_demand_command(self, command: DemandCommand) -> CommandResult:
        """
        Execute demand command.
        
        Args:
            command: Demand command
            
        Returns:
            Command execution result
        """
        pass


class CoordinationService(ABC):
    """Abstract base class for coordination service."""

    @abstractmethod
    def start_coordination(self, interval: int = 10) -> None:
        """
        Start periodic coordination.
        
        Args:
            interval: Coordination interval in seconds (default: 10)
        """
        pass

    @abstractmethod
    def stop_coordination(self) -> None:
        """Stop periodic coordination."""
        pass

    @abstractmethod
    def coordinate(self) -> Optional[CoordinationResult]:
        """
        Execute one coordination cycle.
        
        Returns:
            Coordination result if successful, None otherwise
        """
        pass

    @abstractmethod
    def calculate_optimal_schedule(
        self,
        power_data: PowerGenerationData,
        storage_data: StorageData,
        demand_data: DemandData
    ) -> tuple:
        """
        Calculate optimal schedule for all sides.
        
        Args:
            power_data: Latest power generation data
            storage_data: Latest storage data
            demand_data: Latest demand data
            
        Returns:
            Tuple of (PowerCommand, StorageCommand, DemandCommand)
        """
        pass


class CommandService(ABC):
    """Abstract base class for command service."""

    @abstractmethod
    def send_power_command(self, command: PowerCommand) -> bool:
        """
        Send command to power generation side.
        
        Args:
            command: Power command
            
        Returns:
            True if command was successfully sent, False otherwise
        """
        pass

    @abstractmethod
    def send_storage_command(self, command: StorageCommand) -> bool:
        """
        Send command to storage side.
        
        Args:
            command: Storage command
            
        Returns:
            True if command was successfully sent, False otherwise
        """
        pass

    @abstractmethod
    def send_demand_command(self, command: DemandCommand) -> bool:
        """
        Send command to demand side.
        
        Args:
            command: Demand command
            
        Returns:
            True if command was successfully sent, False otherwise
        """
        pass


class BackgroundTaskService(ABC):
    """Abstract base class for background task service."""

    @abstractmethod
    def start_coordination_task(self, interval: int = 10) -> None:
        """
        Start background coordination task.
        
        Args:
            interval: Coordination interval in seconds (default: 10)
        """
        pass

    @abstractmethod
    def stop_coordination_task(self) -> None:
        """Stop background coordination task."""
        pass

    @abstractmethod
    def start_data_cleanup_task(self, interval: int = 3600) -> None:
        """
        Start background data cleanup task.
        
        Args:
            interval: Cleanup interval in seconds (default: 3600 = 1 hour)
        """
        pass

    @abstractmethod
    def stop_data_cleanup_task(self) -> None:
        """Stop background data cleanup task."""
        pass
