"""
Command Execution Service for side modules.

Implements:
- CommandExecutionService: Executes commands from VCC
- Command execution for power, storage, and demand sides
- Command result reporting
"""

import logging
from datetime import datetime
from typing import Optional

from models.realtime_data_models import (
    PowerCommand, StorageCommand, DemandCommand,
    CommandResult, CommandStatus
)

logger = logging.getLogger(__name__)


class CommandExecutionService:
    """Service for executing commands from VCC on side modules."""

    def __init__(self, module_id: str = "unknown"):
        """
        Initialize command execution service.
        
        Args:
            module_id: ID of the module (e.g., 'vpp-power-generation')
        """
        self.module_id = module_id
        self.executed_commands = {}
        self.execution_count = 0
        self.failed_executions = 0
        self.last_execution_time: Optional[datetime] = None

    def execute_power_command(self, command: PowerCommand) -> CommandResult:
        """
        Execute power generation control command.
        
        Args:
            command: PowerCommand to execute
            
        Returns:
            CommandResult with execution status and result
        """
        try:
            # Check if command is None
            if command is None:
                logger.error("Power command is None")
                result = CommandResult(
                    command_id="unknown",
                    status=CommandStatus.FAILED.value,
                    error_message="Command is None"
                )
                self.failed_executions += 1
                return result
            
            # Validate command
            if not command.validate():
                logger.error(f"Invalid power command: {command}")
                result = CommandResult(
                    command_id=command.command_id,
                    status=CommandStatus.FAILED.value,
                    error_message="Invalid command format"
                )
                self.failed_executions += 1
                return result
            
            # Simulate command execution
            logger.info(f"Executing power command: {command.command_id}, "
                       f"target_power={command.target_power}kW, "
                       f"duration={command.duration}s")
            
            # In a real scenario, this would interact with actual hardware
            # For simulation, we just accept the command
            execution_result = {
                "command_id": command.command_id,
                "target_power": command.target_power,
                "actual_power": command.target_power * 0.95,  # Simulate 95% efficiency
                "duration": command.duration,
                "executed_at": datetime.now().isoformat()
            }
            
            result = CommandResult(
                command_id=command.command_id,
                status=CommandStatus.COMPLETED.value,
                result=execution_result,
                executed_at=datetime.now()
            )
            
            self.executed_commands[command.command_id] = result
            self.execution_count += 1
            self.last_execution_time = datetime.now()
            
            logger.info(f"Power command executed successfully: {command.command_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error executing power command: {str(e)}")
            result = CommandResult(
                command_id="unknown",
                status=CommandStatus.FAILED.value,
                error_message=str(e),
                executed_at=datetime.now()
            )
            self.failed_executions += 1
            return result

    def execute_storage_command(self, command: StorageCommand) -> CommandResult:
        """
        Execute storage control command.
        
        Args:
            command: StorageCommand to execute
            
        Returns:
            CommandResult with execution status and result
        """
        try:
            # Check if command is None
            if command is None:
                logger.error("Storage command is None")
                result = CommandResult(
                    command_id="unknown",
                    status=CommandStatus.FAILED.value,
                    error_message="Command is None"
                )
                self.failed_executions += 1
                return result
            
            # Validate command
            if not command.validate():
                logger.error(f"Invalid storage command: {command}")
                result = CommandResult(
                    command_id=command.command_id,
                    status=CommandStatus.FAILED.value,
                    error_message="Invalid command format"
                )
                self.failed_executions += 1
                return result
            
            # Simulate command execution
            logger.info(f"Executing storage command: {command.command_id}, "
                       f"action={command.action}, "
                       f"target_power={command.target_power}kW, "
                       f"duration={command.duration}s")
            
            # In a real scenario, this would interact with actual battery system
            # For simulation, we just accept the command
            execution_result = {
                "command_id": command.command_id,
                "action": command.action,
                "target_power": command.target_power,
                "actual_power": command.target_power * 0.98,  # Simulate 98% efficiency
                "duration": command.duration,
                "executed_at": datetime.now().isoformat()
            }
            
            result = CommandResult(
                command_id=command.command_id,
                status=CommandStatus.COMPLETED.value,
                result=execution_result,
                executed_at=datetime.now()
            )
            
            self.executed_commands[command.command_id] = result
            self.execution_count += 1
            self.last_execution_time = datetime.now()
            
            logger.info(f"Storage command executed successfully: {command.command_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error executing storage command: {str(e)}")
            result = CommandResult(
                command_id="unknown",
                status=CommandStatus.FAILED.value,
                error_message=str(e),
                executed_at=datetime.now()
            )
            self.failed_executions += 1
            return result

    def execute_demand_command(self, command: DemandCommand) -> CommandResult:
        """
        Execute demand response control command.
        
        Args:
            command: DemandCommand to execute
            
        Returns:
            CommandResult with execution status and result
        """
        try:
            # Check if command is None
            if command is None:
                logger.error("Demand command is None")
                result = CommandResult(
                    command_id="unknown",
                    status=CommandStatus.FAILED.value,
                    error_message="Command is None"
                )
                self.failed_executions += 1
                return result
            
            # Validate command
            if not command.validate():
                logger.error(f"Invalid demand command: {command}")
                result = CommandResult(
                    command_id=command.command_id,
                    status=CommandStatus.FAILED.value,
                    error_message="Invalid command format"
                )
                self.failed_executions += 1
                return result
            
            # Simulate command execution
            logger.info(f"Executing demand command: {command.command_id}, "
                       f"action={command.action}, "
                       f"target_load={command.target_load}kW, "
                       f"duration={command.duration}s")
            
            # In a real scenario, this would interact with actual load control system
            # For simulation, we just accept the command
            execution_result = {
                "command_id": command.command_id,
                "action": command.action,
                "target_load": command.target_load,
                "actual_load": command.target_load * 0.97,  # Simulate 97% compliance
                "duration": command.duration,
                "executed_at": datetime.now().isoformat()
            }
            
            result = CommandResult(
                command_id=command.command_id,
                status=CommandStatus.COMPLETED.value,
                result=execution_result,
                executed_at=datetime.now()
            )
            
            self.executed_commands[command.command_id] = result
            self.execution_count += 1
            self.last_execution_time = datetime.now()
            
            logger.info(f"Demand command executed successfully: {command.command_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error executing demand command: {str(e)}")
            result = CommandResult(
                command_id="unknown",
                status=CommandStatus.FAILED.value,
                error_message=str(e),
                executed_at=datetime.now()
            )
            self.failed_executions += 1
            return result

    def get_execution_result(self, command_id: str) -> Optional[CommandResult]:
        """
        Get execution result for a command.
        
        Args:
            command_id: Command ID to query
            
        Returns:
            CommandResult if found, None otherwise
        """
        return self.executed_commands.get(command_id)

    def get_all_executions(self) -> dict:
        """
        Get all executed commands.
        
        Returns:
            Dictionary of all executed commands
        """
        return dict(self.executed_commands)

    def get_stats(self) -> dict:
        """
        Get execution statistics.
        
        Returns:
            dict: Statistics including execution count, failures, etc.
        """
        successful_executions = len([cmd for cmd in self.executed_commands.values()
                                    if cmd.status == CommandStatus.COMPLETED.value])
        
        return {
            "module_id": self.module_id,
            "total_executions": self.execution_count,
            "successful_executions": successful_executions,
            "failed_executions": self.failed_executions,
            "last_execution_time": self.last_execution_time.isoformat() if self.last_execution_time else None,
        }

    def clear_old_executions(self, max_age_seconds: int = 3600) -> int:
        """
        Clear old execution records.
        
        Args:
            max_age_seconds: Maximum age of records to keep
            
        Returns:
            int: Number of records cleared
        """
        now = datetime.now()
        commands_to_remove = []
        
        for cmd_id, cmd_result in self.executed_commands.items():
            if cmd_result.executed_at:
                age = (now - cmd_result.executed_at).total_seconds()
                if age > max_age_seconds:
                    commands_to_remove.append(cmd_id)
        
        for cmd_id in commands_to_remove:
            del self.executed_commands[cmd_id]
        
        if commands_to_remove:
            logger.info(f"Cleared {len(commands_to_remove)} old execution records")
        
        return len(commands_to_remove)
