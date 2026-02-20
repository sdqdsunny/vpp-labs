"""
Unit tests for command execution routes and service.

Tests:
- Command execution service initialization
- Power command execution
- Storage command execution
- Demand command execution
- Command execution result tracking
- Error handling
"""

import pytest
import json
from datetime import datetime

from services.command_execution import CommandExecutionService
from models.realtime_data_models import (
    PowerCommand, StorageCommand, DemandCommand,
    CommandStatus
)


class TestCommandExecutionServiceInitialization:
    """Test command execution service initialization."""

    def test_service_initialization(self):
        """Test that service initializes correctly."""
        service = CommandExecutionService(module_id="test-module")
        
        assert service.module_id == "test-module"
        assert service.execution_count == 0
        assert service.failed_executions == 0
        assert service.last_execution_time is None
        assert len(service.executed_commands) == 0

    def test_service_stats_on_init(self):
        """Test that stats are correct on initialization."""
        service = CommandExecutionService(module_id="test-module")
        stats = service.get_stats()
        
        assert stats['module_id'] == "test-module"
        assert stats['total_executions'] == 0
        assert stats['successful_executions'] == 0
        assert stats['failed_executions'] == 0
        assert stats['last_execution_time'] is None


class TestPowerCommandExecution:
    """Test power command execution."""

    def test_execute_valid_power_command(self):
        """Test executing a valid power command."""
        service = CommandExecutionService(module_id="vpp-power-generation")
        
        command = PowerCommand(
            command_id="power_001",
            target_power=150.0,
            duration=300,
            priority=1
        )
        
        result = service.execute_power_command(command)
        
        assert result.command_id == "power_001"
        assert result.status == CommandStatus.COMPLETED.value
        assert result.result is not None
        assert result.error_message is None
        assert service.execution_count == 1
        assert service.failed_executions == 0

    def test_execute_power_command_result_contains_data(self):
        """Test that power command result contains execution data."""
        service = CommandExecutionService(module_id="vpp-power-generation")
        
        command = PowerCommand(
            command_id="power_002",
            target_power=200.0,
            duration=600,
            priority=2
        )
        
        result = service.execute_power_command(command)
        
        assert result.result['command_id'] == "power_002"
        assert result.result['target_power'] == 200.0
        assert result.result['duration'] == 600
        assert 'actual_power' in result.result
        assert 'executed_at' in result.result

    def test_execute_invalid_power_command(self):
        """Test executing invalid power command."""
        service = CommandExecutionService(module_id="vpp-power-generation")
        
        command = PowerCommand(
            command_id="power_003",
            target_power=-10.0,  # Invalid
            duration=300,
            priority=1
        )
        
        result = service.execute_power_command(command)
        
        assert result.status == CommandStatus.FAILED.value
        assert result.error_message is not None
        assert service.failed_executions == 1

    def test_execute_multiple_power_commands(self):
        """Test executing multiple power commands."""
        service = CommandExecutionService(module_id="vpp-power-generation")
        
        for i in range(5):
            command = PowerCommand(
                command_id=f"power_{i:03d}",
                target_power=100.0 + i * 10,
                duration=300,
                priority=1
            )
            result = service.execute_power_command(command)
            assert result.status == CommandStatus.COMPLETED.value
        
        assert service.execution_count == 5
        assert len(service.executed_commands) == 5


class TestStorageCommandExecution:
    """Test storage command execution."""

    def test_execute_valid_storage_command_charging(self):
        """Test executing a valid storage charging command."""
        service = CommandExecutionService(module_id="vpp-storage")
        
        command = StorageCommand(
            command_id="storage_001",
            action="charging",
            target_power=80.0,
            duration=300
        )
        
        result = service.execute_storage_command(command)
        
        assert result.command_id == "storage_001"
        assert result.status == CommandStatus.COMPLETED.value
        assert result.result is not None
        assert result.error_message is None
        assert service.execution_count == 1

    def test_execute_valid_storage_command_discharging(self):
        """Test executing a valid storage discharging command."""
        service = CommandExecutionService(module_id="vpp-storage")
        
        command = StorageCommand(
            command_id="storage_002",
            action="discharging",
            target_power=60.0,
            duration=300
        )
        
        result = service.execute_storage_command(command)
        
        assert result.status == CommandStatus.COMPLETED.value
        assert result.result['action'] == "discharging"

    def test_execute_valid_storage_command_idle(self):
        """Test executing a valid storage idle command."""
        service = CommandExecutionService(module_id="vpp-storage")
        
        command = StorageCommand(
            command_id="storage_003",
            action="idle",
            target_power=0.0,
            duration=300
        )
        
        result = service.execute_storage_command(command)
        
        assert result.status == CommandStatus.COMPLETED.value
        assert result.result['action'] == "idle"

    def test_execute_invalid_storage_command(self):
        """Test executing invalid storage command."""
        service = CommandExecutionService(module_id="vpp-storage")
        
        command = StorageCommand(
            command_id="storage_004",
            action="invalid_action",
            target_power=50.0,
            duration=300
        )
        
        result = service.execute_storage_command(command)
        
        assert result.status == CommandStatus.FAILED.value
        assert service.failed_executions == 1

    def test_execute_multiple_storage_commands(self):
        """Test executing multiple storage commands."""
        service = CommandExecutionService(module_id="vpp-storage")
        
        actions = ["charging", "discharging", "idle"]
        for i in range(6):
            command = StorageCommand(
                command_id=f"storage_{i:03d}",
                action=actions[i % 3],
                target_power=50.0 + i * 10,
                duration=300
            )
            result = service.execute_storage_command(command)
            assert result.status == CommandStatus.COMPLETED.value
        
        assert service.execution_count == 6


class TestDemandCommandExecution:
    """Test demand command execution."""

    def test_execute_valid_demand_command_increase(self):
        """Test executing a valid demand increase command."""
        service = CommandExecutionService(module_id="vpp-demand")
        
        command = DemandCommand(
            command_id="demand_001",
            action="increase",
            target_load=220.0,
            duration=300
        )
        
        result = service.execute_demand_command(command)
        
        assert result.command_id == "demand_001"
        assert result.status == CommandStatus.COMPLETED.value
        assert result.result is not None
        assert result.error_message is None
        assert service.execution_count == 1

    def test_execute_valid_demand_command_decrease(self):
        """Test executing a valid demand decrease command."""
        service = CommandExecutionService(module_id="vpp-demand")
        
        command = DemandCommand(
            command_id="demand_002",
            action="decrease",
            target_load=180.0,
            duration=300
        )
        
        result = service.execute_demand_command(command)
        
        assert result.status == CommandStatus.COMPLETED.value
        assert result.result['action'] == "decrease"

    def test_execute_valid_demand_command_maintain(self):
        """Test executing a valid demand maintain command."""
        service = CommandExecutionService(module_id="vpp-demand")
        
        command = DemandCommand(
            command_id="demand_003",
            action="maintain",
            target_load=200.0,
            duration=300
        )
        
        result = service.execute_demand_command(command)
        
        assert result.status == CommandStatus.COMPLETED.value
        assert result.result['action'] == "maintain"

    def test_execute_invalid_demand_command(self):
        """Test executing invalid demand command."""
        service = CommandExecutionService(module_id="vpp-demand")
        
        command = DemandCommand(
            command_id="demand_004",
            action="invalid_action",
            target_load=200.0,
            duration=300
        )
        
        result = service.execute_demand_command(command)
        
        assert result.status == CommandStatus.FAILED.value
        assert service.failed_executions == 1

    def test_execute_multiple_demand_commands(self):
        """Test executing multiple demand commands."""
        service = CommandExecutionService(module_id="vpp-demand")
        
        actions = ["increase", "decrease", "maintain"]
        for i in range(6):
            command = DemandCommand(
                command_id=f"demand_{i:03d}",
                action=actions[i % 3],
                target_load=200.0 + i * 5,
                duration=300
            )
            result = service.execute_demand_command(command)
            assert result.status == CommandStatus.COMPLETED.value
        
        assert service.execution_count == 6


class TestExecutionResultRetrieval:
    """Test execution result retrieval."""

    def test_get_execution_result(self):
        """Test getting execution result."""
        service = CommandExecutionService(module_id="vpp-power-generation")
        
        command = PowerCommand(
            command_id="power_001",
            target_power=150.0,
            duration=300,
            priority=1
        )
        
        service.execute_power_command(command)
        result = service.get_execution_result("power_001")
        
        assert result is not None
        assert result.command_id == "power_001"
        assert result.status == CommandStatus.COMPLETED.value

    def test_get_nonexistent_execution_result(self):
        """Test getting nonexistent execution result."""
        service = CommandExecutionService(module_id="vpp-power-generation")
        
        result = service.get_execution_result("nonexistent_001")
        
        assert result is None

    def test_get_all_executions(self):
        """Test getting all executions."""
        service = CommandExecutionService(module_id="vpp-power-generation")
        
        for i in range(3):
            command = PowerCommand(
                command_id=f"power_{i:03d}",
                target_power=100.0 + i * 10,
                duration=300,
                priority=1
            )
            service.execute_power_command(command)
        
        all_executions = service.get_all_executions()
        
        assert len(all_executions) == 3


class TestExecutionStatistics:
    """Test execution statistics."""

    def test_stats_after_executions(self):
        """Test statistics after executions."""
        service = CommandExecutionService(module_id="vpp-power-generation")
        
        # Execute 5 commands
        for i in range(5):
            command = PowerCommand(
                command_id=f"power_{i:03d}",
                target_power=100.0 + i * 10,
                duration=300,
                priority=1
            )
            service.execute_power_command(command)
        
        stats = service.get_stats()
        
        assert stats['module_id'] == "vpp-power-generation"
        assert stats['total_executions'] == 5
        assert stats['successful_executions'] == 5
        assert stats['failed_executions'] == 0

    def test_stats_with_failures(self):
        """Test statistics with failed executions."""
        service = CommandExecutionService(module_id="vpp-power-generation")
        
        # Execute 3 valid commands
        for i in range(3):
            command = PowerCommand(
                command_id=f"power_{i:03d}",
                target_power=100.0 + i * 10,
                duration=300,
                priority=1
            )
            service.execute_power_command(command)
        
        # Execute 2 invalid commands
        for i in range(2):
            command = PowerCommand(
                command_id=f"power_invalid_{i:03d}",
                target_power=-10.0,
                duration=300,
                priority=1
            )
            service.execute_power_command(command)
        
        stats = service.get_stats()
        
        assert stats['total_executions'] == 3
        assert stats['successful_executions'] == 3
        assert stats['failed_executions'] == 2


class TestExecutionCleanup:
    """Test execution cleanup."""

    def test_clear_old_executions(self):
        """Test clearing old executions."""
        service = CommandExecutionService(module_id="vpp-power-generation")
        
        # Execute 5 commands
        for i in range(5):
            command = PowerCommand(
                command_id=f"power_{i:03d}",
                target_power=100.0 + i * 10,
                duration=300,
                priority=1
            )
            service.execute_power_command(command)
        
        # Manually set old timestamps
        for i in range(5):
            result = service.get_execution_result(f"power_{i:03d}")
            result.executed_at = datetime(2020, 1, 1)
        
        # Clear old executions
        cleared = service.clear_old_executions(max_age_seconds=1)
        
        assert cleared == 5
        assert len(service.executed_commands) == 0

    def test_clear_old_executions_keeps_recent(self):
        """Test that clearing old executions keeps recent ones."""
        service = CommandExecutionService(module_id="vpp-power-generation")
        
        # Execute 5 commands
        for i in range(5):
            command = PowerCommand(
                command_id=f"power_{i:03d}",
                target_power=100.0 + i * 10,
                duration=300,
                priority=1
            )
            service.execute_power_command(command)
        
        # Clear old executions (with large max_age)
        cleared = service.clear_old_executions(max_age_seconds=3600)
        
        assert cleared == 0
        assert len(service.executed_commands) == 5


class TestErrorHandling:
    """Test error handling in command execution."""

    def test_execute_command_with_exception(self):
        """Test handling of exceptions during command execution."""
        service = CommandExecutionService(module_id="vpp-power-generation")
        
        # This should not raise, but return failed result
        try:
            result = service.execute_power_command(None)
            assert result.status == CommandStatus.FAILED.value
        except:
            pytest.fail("execute_power_command should not raise exception")

    def test_multiple_failed_executions(self):
        """Test tracking of multiple failed executions."""
        service = CommandExecutionService(module_id="vpp-power-generation")
        
        # Try to execute invalid commands
        for i in range(3):
            command = PowerCommand(
                command_id=f"power_{i:03d}",
                target_power=-10.0,  # Invalid
                duration=300,
                priority=1
            )
            service.execute_power_command(command)
        
        assert service.failed_executions == 3
        assert service.execution_count == 0


class TestCrossModuleExecution:
    """Test execution across different modules."""

    def test_power_module_execution(self):
        """Test power module command execution."""
        service = CommandExecutionService(module_id="vpp-power-generation")
        
        command = PowerCommand(
            command_id="power_001",
            target_power=150.0,
            duration=300,
            priority=1
        )
        
        result = service.execute_power_command(command)
        
        assert result.status == CommandStatus.COMPLETED.value
        assert service.module_id == "vpp-power-generation"

    def test_storage_module_execution(self):
        """Test storage module command execution."""
        service = CommandExecutionService(module_id="vpp-storage")
        
        command = StorageCommand(
            command_id="storage_001",
            action="charging",
            target_power=80.0,
            duration=300
        )
        
        result = service.execute_storage_command(command)
        
        assert result.status == CommandStatus.COMPLETED.value
        assert service.module_id == "vpp-storage"

    def test_demand_module_execution(self):
        """Test demand module command execution."""
        service = CommandExecutionService(module_id="vpp-demand")
        
        command = DemandCommand(
            command_id="demand_001",
            action="increase",
            target_load=220.0,
            duration=300
        )
        
        result = service.execute_demand_command(command)
        
        assert result.status == CommandStatus.COMPLETED.value
        assert service.module_id == "vpp-demand"
