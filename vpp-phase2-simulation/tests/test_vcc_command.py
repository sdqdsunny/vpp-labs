"""
Unit tests for VCC Master Command Service.

Tests:
- Command service initialization
- Power command sending
- Storage command sending
- Demand command sending
- Command validation
- Error handling
- Command statistics
"""

import pytest
from datetime import datetime
from uuid import uuid4

from services.vcc_command import CommandService
from models.realtime_data_models import (
    PowerCommand, StorageCommand, DemandCommand,
    CommandStatus
)


class TestCommandServiceInitialization:
    """Test command service initialization."""

    def test_service_initialization(self):
        """Test that service initializes correctly."""
        service = CommandService()
        
        assert service.command_count == 0
        assert service.failed_commands == 0
        assert service.last_command_time is None
        assert len(service.sent_commands) == 0

    def test_service_stats_on_init(self):
        """Test that stats are correct on initialization."""
        service = CommandService()
        stats = service.get_stats()
        
        assert stats['total_commands_sent'] == 0
        assert stats['total_commands_tracked'] == 0
        assert stats['completed_commands'] == 0
        assert stats['failed_commands'] == 0
        assert stats['pending_commands'] == 0
        assert stats['last_command_time'] is None


class TestPowerCommandSending:
    """Test power command sending."""

    def test_send_valid_power_command(self):
        """Test sending a valid power command."""
        service = CommandService()
        
        command = PowerCommand(
            command_id="power_001",
            target_power=150.0,
            duration=300,
            priority=1
        )
        
        result = service.send_power_command(command)
        
        assert result is True
        assert service.command_count == 1
        assert service.failed_commands == 0
        assert command.command_id in service.sent_commands
        assert service.last_command_time is not None

    def test_send_power_command_with_zero_power(self):
        """Test sending power command with zero target power."""
        service = CommandService()
        
        command = PowerCommand(
            command_id="power_002",
            target_power=0.0,
            duration=300,
            priority=1
        )
        
        result = service.send_power_command(command)
        
        assert result is True
        assert service.command_count == 1

    def test_send_power_command_with_high_power(self):
        """Test sending power command with high target power."""
        service = CommandService()
        
        command = PowerCommand(
            command_id="power_003",
            target_power=500.0,
            duration=600,
            priority=5
        )
        
        result = service.send_power_command(command)
        
        assert result is True
        assert service.command_count == 1

    def test_send_invalid_power_command_negative_power(self):
        """Test sending invalid power command with negative power."""
        service = CommandService()
        
        command = PowerCommand(
            command_id="power_004",
            target_power=-10.0,
            duration=300,
            priority=1
        )
        
        result = service.send_power_command(command)
        
        assert result is False
        assert service.failed_commands == 1
        assert service.command_count == 0

    def test_send_invalid_power_command_invalid_priority(self):
        """Test sending invalid power command with invalid priority."""
        service = CommandService()
        
        command = PowerCommand(
            command_id="power_005",
            target_power=150.0,
            duration=300,
            priority=15  # Invalid priority > 10
        )
        
        result = service.send_power_command(command)
        
        assert result is False
        assert service.failed_commands == 1

    def test_send_invalid_power_command_invalid_duration(self):
        """Test sending invalid power command with invalid duration."""
        service = CommandService()
        
        command = PowerCommand(
            command_id="power_006",
            target_power=150.0,
            duration=0,  # Invalid duration
            priority=1
        )
        
        result = service.send_power_command(command)
        
        assert result is False
        assert service.failed_commands == 1

    def test_send_multiple_power_commands(self):
        """Test sending multiple power commands."""
        service = CommandService()
        
        for i in range(5):
            command = PowerCommand(
                command_id=f"power_{i:03d}",
                target_power=100.0 + i * 10,
                duration=300,
                priority=1
            )
            result = service.send_power_command(command)
            assert result is True
        
        assert service.command_count == 5
        assert len(service.sent_commands) == 5


class TestStorageCommandSending:
    """Test storage command sending."""

    def test_send_valid_storage_command_charging(self):
        """Test sending a valid storage charging command."""
        service = CommandService()
        
        command = StorageCommand(
            command_id="storage_001",
            action="charging",
            target_power=80.0,
            duration=300
        )
        
        result = service.send_storage_command(command)
        
        assert result is True
        assert service.command_count == 1
        assert service.failed_commands == 0

    def test_send_valid_storage_command_discharging(self):
        """Test sending a valid storage discharging command."""
        service = CommandService()
        
        command = StorageCommand(
            command_id="storage_002",
            action="discharging",
            target_power=60.0,
            duration=300
        )
        
        result = service.send_storage_command(command)
        
        assert result is True
        assert service.command_count == 1

    def test_send_valid_storage_command_idle(self):
        """Test sending a valid storage idle command."""
        service = CommandService()
        
        command = StorageCommand(
            command_id="storage_003",
            action="idle",
            target_power=0.0,
            duration=300
        )
        
        result = service.send_storage_command(command)
        
        assert result is True
        assert service.command_count == 1

    def test_send_invalid_storage_command_invalid_action(self):
        """Test sending invalid storage command with invalid action."""
        service = CommandService()
        
        command = StorageCommand(
            command_id="storage_004",
            action="invalid_action",
            target_power=50.0,
            duration=300
        )
        
        result = service.send_storage_command(command)
        
        assert result is False
        assert service.failed_commands == 1

    def test_send_invalid_storage_command_negative_power(self):
        """Test sending invalid storage command with negative power."""
        service = CommandService()
        
        command = StorageCommand(
            command_id="storage_005",
            action="charging",
            target_power=-50.0,
            duration=300
        )
        
        result = service.send_storage_command(command)
        
        assert result is False
        assert service.failed_commands == 1

    def test_send_multiple_storage_commands(self):
        """Test sending multiple storage commands."""
        service = CommandService()
        
        actions = ["charging", "discharging", "idle"]
        for i in range(6):
            command = StorageCommand(
                command_id=f"storage_{i:03d}",
                action=actions[i % 3],
                target_power=50.0 + i * 10,
                duration=300
            )
            result = service.send_storage_command(command)
            assert result is True
        
        assert service.command_count == 6


class TestDemandCommandSending:
    """Test demand command sending."""

    def test_send_valid_demand_command_increase(self):
        """Test sending a valid demand increase command."""
        service = CommandService()
        
        command = DemandCommand(
            command_id="demand_001",
            action="increase",
            target_load=220.0,
            duration=300
        )
        
        result = service.send_demand_command(command)
        
        assert result is True
        assert service.command_count == 1
        assert service.failed_commands == 0

    def test_send_valid_demand_command_decrease(self):
        """Test sending a valid demand decrease command."""
        service = CommandService()
        
        command = DemandCommand(
            command_id="demand_002",
            action="decrease",
            target_load=180.0,
            duration=300
        )
        
        result = service.send_demand_command(command)
        
        assert result is True
        assert service.command_count == 1

    def test_send_valid_demand_command_maintain(self):
        """Test sending a valid demand maintain command."""
        service = CommandService()
        
        command = DemandCommand(
            command_id="demand_003",
            action="maintain",
            target_load=200.0,
            duration=300
        )
        
        result = service.send_demand_command(command)
        
        assert result is True
        assert service.command_count == 1

    def test_send_invalid_demand_command_invalid_action(self):
        """Test sending invalid demand command with invalid action."""
        service = CommandService()
        
        command = DemandCommand(
            command_id="demand_004",
            action="invalid_action",
            target_load=200.0,
            duration=300
        )
        
        result = service.send_demand_command(command)
        
        assert result is False
        assert service.failed_commands == 1

    def test_send_invalid_demand_command_negative_load(self):
        """Test sending invalid demand command with negative load."""
        service = CommandService()
        
        command = DemandCommand(
            command_id="demand_005",
            action="increase",
            target_load=-50.0,
            duration=300
        )
        
        result = service.send_demand_command(command)
        
        assert result is False
        assert service.failed_commands == 1

    def test_send_multiple_demand_commands(self):
        """Test sending multiple demand commands."""
        service = CommandService()
        
        actions = ["increase", "decrease", "maintain"]
        for i in range(6):
            command = DemandCommand(
                command_id=f"demand_{i:03d}",
                action=actions[i % 3],
                target_load=200.0 + i * 5,
                duration=300
            )
            result = service.send_demand_command(command)
            assert result is True
        
        assert service.command_count == 6


class TestCommandValidation:
    """Test command validation."""

    def test_validate_power_command_all_fields(self):
        """Test power command validation with all fields."""
        command = PowerCommand(
            command_id="power_test",
            target_power=150.0,
            duration=300,
            priority=5
        )
        
        assert command.validate() is True

    def test_validate_storage_command_all_fields(self):
        """Test storage command validation with all fields."""
        command = StorageCommand(
            command_id="storage_test",
            action="charging",
            target_power=80.0,
            duration=300
        )
        
        assert command.validate() is True

    def test_validate_demand_command_all_fields(self):
        """Test demand command validation with all fields."""
        command = DemandCommand(
            command_id="demand_test",
            action="increase",
            target_load=220.0,
            duration=300
        )
        
        assert command.validate() is True


class TestCommandStatusUpdate:
    """Test command status updates."""

    def test_update_command_status_to_accepted(self):
        """Test updating command status to accepted."""
        service = CommandService()
        
        command = PowerCommand(
            command_id="power_001",
            target_power=150.0,
            duration=300,
            priority=1
        )
        
        service.send_power_command(command)
        result = service.update_command_status(
            "power_001",
            CommandStatus.ACCEPTED.value
        )
        
        assert result is True
        cmd_result = service.get_command_status("power_001")
        assert cmd_result.status == CommandStatus.ACCEPTED.value

    def test_update_command_status_to_completed(self):
        """Test updating command status to completed."""
        service = CommandService()
        
        command = PowerCommand(
            command_id="power_002",
            target_power=150.0,
            duration=300,
            priority=1
        )
        
        service.send_power_command(command)
        result = service.update_command_status(
            "power_002",
            CommandStatus.COMPLETED.value,
            result={"actual_power": 150.0}
        )
        
        assert result is True
        cmd_result = service.get_command_status("power_002")
        assert cmd_result.status == CommandStatus.COMPLETED.value
        assert cmd_result.result == {"actual_power": 150.0}

    def test_update_command_status_to_failed(self):
        """Test updating command status to failed."""
        service = CommandService()
        
        command = PowerCommand(
            command_id="power_003",
            target_power=150.0,
            duration=300,
            priority=1
        )
        
        service.send_power_command(command)
        result = service.update_command_status(
            "power_003",
            CommandStatus.FAILED.value,
            error_message="Device not responding"
        )
        
        assert result is True
        cmd_result = service.get_command_status("power_003")
        assert cmd_result.status == CommandStatus.FAILED.value
        assert cmd_result.error_message == "Device not responding"

    def test_update_nonexistent_command_status(self):
        """Test updating status of nonexistent command."""
        service = CommandService()
        
        result = service.update_command_status(
            "nonexistent_001",
            CommandStatus.COMPLETED.value
        )
        
        assert result is False


class TestCommandRetrieval:
    """Test command retrieval methods."""

    def test_get_command_status(self):
        """Test getting command status."""
        service = CommandService()
        
        command = PowerCommand(
            command_id="power_001",
            target_power=150.0,
            duration=300,
            priority=1
        )
        
        service.send_power_command(command)
        cmd_result = service.get_command_status("power_001")
        
        assert cmd_result is not None
        assert cmd_result.command_id == "power_001"
        assert cmd_result.status == CommandStatus.PENDING.value

    def test_get_nonexistent_command_status(self):
        """Test getting status of nonexistent command."""
        service = CommandService()
        
        cmd_result = service.get_command_status("nonexistent_001")
        
        assert cmd_result is None

    def test_get_all_commands(self):
        """Test getting all commands."""
        service = CommandService()
        
        for i in range(3):
            command = PowerCommand(
                command_id=f"power_{i:03d}",
                target_power=100.0 + i * 10,
                duration=300,
                priority=1
            )
            service.send_power_command(command)
        
        all_commands = service.get_all_commands()
        
        assert len(all_commands) == 3

    def test_get_pending_commands(self):
        """Test getting pending commands."""
        service = CommandService()
        
        # Send 3 commands
        for i in range(3):
            command = PowerCommand(
                command_id=f"power_{i:03d}",
                target_power=100.0 + i * 10,
                duration=300,
                priority=1
            )
            service.send_power_command(command)
        
        # Update one to completed
        service.update_command_status("power_001", CommandStatus.COMPLETED.value)
        
        pending = service.get_pending_commands()
        
        assert len(pending) == 2

    def test_get_failed_commands(self):
        """Test getting failed commands."""
        service = CommandService()
        
        # Send 3 commands
        for i in range(3):
            command = PowerCommand(
                command_id=f"power_{i:03d}",
                target_power=100.0 + i * 10,
                duration=300,
                priority=1
            )
            service.send_power_command(command)
        
        # Update two to failed
        service.update_command_status("power_001", CommandStatus.FAILED.value)
        service.update_command_status("power_002", CommandStatus.FAILED.value)
        
        failed = service.get_failed_commands()
        
        assert len(failed) == 2


class TestCommandStatistics:
    """Test command statistics."""

    def test_stats_after_sending_commands(self):
        """Test statistics after sending commands."""
        service = CommandService()
        
        # Send 5 commands
        for i in range(5):
            command = PowerCommand(
                command_id=f"power_{i:03d}",
                target_power=100.0 + i * 10,
                duration=300,
                priority=1
            )
            service.send_power_command(command)
        
        stats = service.get_stats()
        
        assert stats['total_commands_sent'] == 5
        assert stats['total_commands_tracked'] == 5
        assert stats['pending_commands'] == 5
        assert stats['completed_commands'] == 0
        assert stats['failed_commands'] == 0

    def test_stats_with_mixed_statuses(self):
        """Test statistics with mixed command statuses."""
        service = CommandService()
        
        # Send 5 commands
        for i in range(5):
            command = PowerCommand(
                command_id=f"power_{i:03d}",
                target_power=100.0 + i * 10,
                duration=300,
                priority=1
            )
            service.send_power_command(command)
        
        # Update statuses
        service.update_command_status("power_000", CommandStatus.COMPLETED.value)
        service.update_command_status("power_001", CommandStatus.COMPLETED.value)
        service.update_command_status("power_002", CommandStatus.FAILED.value)
        
        stats = service.get_stats()
        
        assert stats['total_commands_sent'] == 5
        assert stats['completed_commands'] == 2
        assert stats['failed_commands'] == 1
        assert stats['pending_commands'] == 2


class TestErrorHandling:
    """Test error handling."""

    def test_send_command_with_exception(self):
        """Test handling of exceptions during command sending."""
        service = CommandService()
        
        # Create a command with invalid type to trigger exception
        try:
            # This should not raise, but return False
            result = service.send_power_command(None)
            assert result is False
        except:
            pytest.fail("send_power_command should not raise exception")

    def test_multiple_failed_commands(self):
        """Test tracking of multiple failed commands."""
        service = CommandService()
        
        # Try to send invalid commands
        for i in range(3):
            command = PowerCommand(
                command_id=f"power_{i:03d}",
                target_power=-10.0,  # Invalid
                duration=300,
                priority=1
            )
            service.send_power_command(command)
        
        assert service.failed_commands == 3
        assert service.command_count == 0


class TestCommandCleanup:
    """Test command cleanup."""

    def test_clear_old_commands(self):
        """Test clearing old commands."""
        service = CommandService()
        
        # Send 5 commands
        for i in range(5):
            command = PowerCommand(
                command_id=f"power_{i:03d}",
                target_power=100.0 + i * 10,
                duration=300,
                priority=1
            )
            service.send_power_command(command)
        
        # Mark all as completed (with old timestamps)
        for i in range(5):
            service.update_command_status(
                f"power_{i:03d}",
                CommandStatus.COMPLETED.value
            )
            # Manually set old timestamp
            cmd = service.get_command_status(f"power_{i:03d}")
            cmd.executed_at = datetime(2020, 1, 1)
        
        # Clear old commands
        cleared = service.clear_old_commands(max_age_seconds=1)
        
        assert cleared == 5
        assert len(service.sent_commands) == 0

    def test_clear_old_commands_keeps_recent(self):
        """Test that clearing old commands keeps recent ones."""
        service = CommandService()
        
        # Send 5 commands
        for i in range(5):
            command = PowerCommand(
                command_id=f"power_{i:03d}",
                target_power=100.0 + i * 10,
                duration=300,
                priority=1
            )
            service.send_power_command(command)
        
        # Mark all as completed
        for i in range(5):
            service.update_command_status(
                f"power_{i:03d}",
                CommandStatus.COMPLETED.value
            )
        
        # Clear old commands (with large max_age)
        cleared = service.clear_old_commands(max_age_seconds=3600)
        
        assert cleared == 0
        assert len(service.sent_commands) == 5
