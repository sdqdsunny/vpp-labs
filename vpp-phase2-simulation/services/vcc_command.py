"""
VCC Master Command Service.

Implements:
- CommandService: Sends control commands to all sides
- Command validation and sending logic
- Command tracking and statistics
"""

import uuid
import logging
from datetime import datetime
from typing import Optional, Dict, List
from enum import Enum

from models.realtime_data_models import (
    PowerCommand, StorageCommand, DemandCommand,
    CommandResult, CommandStatus
)

logger = logging.getLogger(__name__)


class CommandService:
    """VCC Master command service for sending control commands to sides."""

    def __init__(self):
        """Initialize command service."""
        self.sent_commands: Dict[str, CommandResult] = {}
        self.command_count = 0
        self.failed_commands = 0
        self.last_command_time: Optional[datetime] = None

    def send_power_command(self, command: PowerCommand) -> bool:
        """
        Send power generation control command to power side.
        
        Args:
            command: PowerCommand to send
            
        Returns:
            bool: True if command was successfully sent, False otherwise
        """
        try:
            # Validate command
            if not command.validate():
                logger.error(f"Invalid power command: {command}")
                self.failed_commands += 1
                return False
            
            # Create command result
            result = CommandResult(
                command_id=command.command_id,
                status=CommandStatus.PENDING.value,
                executed_at=None
            )
            
            # Store command
            self.sent_commands[command.command_id] = result
            self.command_count += 1
            self.last_command_time = datetime.now()
            
            logger.info(f"Power command sent: {command.command_id}, "
                       f"target_power={command.target_power}kW, "
                       f"duration={command.duration}s")
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending power command: {str(e)}")
            self.failed_commands += 1
            return False

    def send_storage_command(self, command: StorageCommand) -> bool:
        """
        Send storage control command to storage side.
        
        Args:
            command: StorageCommand to send
            
        Returns:
            bool: True if command was successfully sent, False otherwise
        """
        try:
            # Validate command
            if not command.validate():
                logger.error(f"Invalid storage command: {command}")
                self.failed_commands += 1
                return False
            
            # Create command result
            result = CommandResult(
                command_id=command.command_id,
                status=CommandStatus.PENDING.value,
                executed_at=None
            )
            
            # Store command
            self.sent_commands[command.command_id] = result
            self.command_count += 1
            self.last_command_time = datetime.now()
            
            logger.info(f"Storage command sent: {command.command_id}, "
                       f"action={command.action}, "
                       f"target_power={command.target_power}kW, "
                       f"duration={command.duration}s")
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending storage command: {str(e)}")
            self.failed_commands += 1
            return False

    def send_demand_command(self, command: DemandCommand) -> bool:
        """
        Send demand response control command to demand side.
        
        Args:
            command: DemandCommand to send
            
        Returns:
            bool: True if command was successfully sent, False otherwise
        """
        try:
            # Validate command
            if not command.validate():
                logger.error(f"Invalid demand command: {command}")
                self.failed_commands += 1
                return False
            
            # Create command result
            result = CommandResult(
                command_id=command.command_id,
                status=CommandStatus.PENDING.value,
                executed_at=None
            )
            
            # Store command
            self.sent_commands[command.command_id] = result
            self.command_count += 1
            self.last_command_time = datetime.now()
            
            logger.info(f"Demand command sent: {command.command_id}, "
                       f"action={command.action}, "
                       f"target_load={command.target_load}kW, "
                       f"duration={command.duration}s")
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending demand command: {str(e)}")
            self.failed_commands += 1
            return False

    def update_command_status(self, command_id: str, status: str,
                             result: Optional[dict] = None,
                             error_message: Optional[str] = None) -> bool:
        """
        Update command execution status.
        
        Args:
            command_id: Command ID to update
            status: New status
            result: Execution result data
            error_message: Error message if failed
            
        Returns:
            bool: True if status was updated, False if command not found
        """
        if command_id not in self.sent_commands:
            logger.warning(f"Command not found: {command_id}")
            return False
        
        try:
            cmd_result = self.sent_commands[command_id]
            cmd_result.status = status
            cmd_result.result = result
            cmd_result.error_message = error_message
            cmd_result.executed_at = datetime.now()
            
            logger.info(f"Command status updated: {command_id}, status={status}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating command status: {str(e)}")
            return False

    def get_command_status(self, command_id: str) -> Optional[CommandResult]:
        """
        Get command execution status.
        
        Args:
            command_id: Command ID to query
            
        Returns:
            CommandResult if found, None otherwise
        """
        return self.sent_commands.get(command_id)

    def get_all_commands(self) -> List[CommandResult]:
        """
        Get all sent commands.
        
        Returns:
            List of all CommandResult objects
        """
        return list(self.sent_commands.values())

    def get_pending_commands(self) -> List[CommandResult]:
        """
        Get all pending commands.
        
        Returns:
            List of pending CommandResult objects
        """
        return [cmd for cmd in self.sent_commands.values()
                if cmd.status == CommandStatus.PENDING.value]

    def get_failed_commands(self) -> List[CommandResult]:
        """
        Get all failed commands.
        
        Returns:
            List of failed CommandResult objects
        """
        return [cmd for cmd in self.sent_commands.values()
                if cmd.status == CommandStatus.FAILED.value]

    def get_stats(self) -> dict:
        """
        Get command service statistics.
        
        Returns:
            dict: Statistics including command count, failed count, etc.
        """
        total_commands = len(self.sent_commands)
        completed_commands = len([cmd for cmd in self.sent_commands.values()
                                 if cmd.status == CommandStatus.COMPLETED.value])
        failed_commands = len([cmd for cmd in self.sent_commands.values()
                              if cmd.status == CommandStatus.FAILED.value])
        pending_commands = len([cmd for cmd in self.sent_commands.values()
                               if cmd.status == CommandStatus.PENDING.value])
        
        return {
            "total_commands_sent": self.command_count,
            "total_commands_tracked": total_commands,
            "completed_commands": completed_commands,
            "failed_commands": failed_commands,
            "pending_commands": pending_commands,
            "last_command_time": self.last_command_time.isoformat() if self.last_command_time else None,
        }

    def clear_old_commands(self, max_age_seconds: int = 3600) -> int:
        """
        Clear old command records to prevent memory bloat.
        
        Args:
            max_age_seconds: Maximum age of commands to keep (default 1 hour)
            
        Returns:
            int: Number of commands cleared
        """
        now = datetime.now()
        commands_to_remove = []
        
        for cmd_id, cmd_result in self.sent_commands.items():
            if cmd_result.executed_at:
                age = (now - cmd_result.executed_at).total_seconds()
                if age > max_age_seconds:
                    commands_to_remove.append(cmd_id)
        
        for cmd_id in commands_to_remove:
            del self.sent_commands[cmd_id]
        
        if commands_to_remove:
            logger.info(f"Cleared {len(commands_to_remove)} old commands")
        
        return len(commands_to_remove)
