"""
Dispatch Data Model

Represents a control command issued to a device in the VPP system.
"""

from sqlalchemy import Column, String, Float, Integer, DateTime, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from utils.database import Base


class Dispatch(Base):
    """
    Dispatch model representing a control command to a device
    
    Attributes:
        id: Unique dispatch identifier (primary key)
        device_id: Target device ID (foreign key)
        command_type: Type of command (power_adjust, mode_change, etc.)
        target_value: Target value for the command
        priority_level: Priority level (0-10)
        status: Current dispatch status (pending, executing, completed, failed)
        execution_time: Timestamp when dispatch was executed
        scheduled_time: Scheduled execution time (for future dispatches)
        retry_count: Number of retry attempts
        error_message: Error message if dispatch failed
        result_data: JSON object containing dispatch result
        created_at: Timestamp when dispatch was created
        updated_at: Timestamp of last update
        device: Relationship to device
    """
    
    __tablename__ = "dispatches"
    
    # Primary key
    id = Column(String(255), primary_key=True, nullable=False)
    
    # Foreign key
    device_id = Column(String(255), ForeignKey("devices.id"), nullable=False, index=True)
    
    # Command information
    command_type = Column(String(50), nullable=False)
    target_value = Column(Float, nullable=False)
    priority_level = Column(Integer, default=0, nullable=False)
    
    # Status tracking
    status = Column(String(20), default="pending", nullable=False, index=True)  # pending, executing, completed, failed
    execution_time = Column(DateTime, nullable=True)
    scheduled_time = Column(DateTime, nullable=True, index=True)
    
    # Retry information
    retry_count = Column(Integer, default=0, nullable=False)
    error_message = Column(String(500), nullable=True)
    
    # Result data
    result_data = Column(JSON, nullable=True, default={})
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    device = relationship("Device", back_populates="dispatches")
    
    # Indexes for query optimization
    __table_args__ = (
        Index('idx_dispatch_device_id', 'device_id'),
        Index('idx_dispatch_status', 'status'),
        Index('idx_dispatch_created_at', 'created_at'),
        Index('idx_dispatch_scheduled_time', 'scheduled_time'),
        Index('idx_dispatch_device_status', 'device_id', 'status'),
    )
    
    def __repr__(self):
        return f"<Dispatch(id={self.id}, device_id={self.device_id}, status={self.status})>"
    
    def to_dict(self):
        """Convert dispatch to dictionary"""
        return {
            "id": self.id,
            "device_id": self.device_id,
            "command_type": self.command_type,
            "target_value": self.target_value,
            "priority_level": self.priority_level,
            "status": self.status,
            "execution_time": self.execution_time.isoformat() if self.execution_time else None,
            "scheduled_time": self.scheduled_time.isoformat() if self.scheduled_time else None,
            "retry_count": self.retry_count,
            "error_message": self.error_message,
            "result_data": self.result_data,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    def is_pending(self):
        """Check if dispatch is pending"""
        return self.status == "pending"
    
    def is_executing(self):
        """Check if dispatch is executing"""
        return self.status == "executing"
    
    def is_completed(self):
        """Check if dispatch is completed"""
        return self.status == "completed"
    
    def is_failed(self):
        """Check if dispatch is failed"""
        return self.status == "failed"
    
    def mark_executing(self):
        """Mark dispatch as executing"""
        self.status = "executing"
        self.updated_at = datetime.utcnow()
    
    def mark_completed(self, result_data: dict = None):
        """Mark dispatch as completed"""
        self.status = "completed"
        self.execution_time = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        if result_data:
            self.result_data = result_data
    
    def mark_failed(self, error_message: str):
        """Mark dispatch as failed"""
        self.status = "failed"
        self.error_message = error_message
        self.execution_time = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def increment_retry(self):
        """Increment retry count"""
        self.retry_count += 1
        self.updated_at = datetime.utcnow()
    
    def can_retry(self, max_retries: int = 3):
        """Check if dispatch can be retried"""
        return self.retry_count < max_retries
