"""
Analysis Result Data Model

Represents results from power system analysis operations.
"""

from sqlalchemy import Column, String, DateTime, JSON, Integer, Index
from datetime import datetime
from utils.database import Base


class AnalysisResult(Base):
    """
    Analysis result model for storing analysis execution results
    
    Attributes:
        id: Unique analysis result identifier (primary key)
        analysis_type: Type of analysis (power_flow, stability, metrics)
        system_state: JSON object containing system state at analysis time
        result_data: JSON object containing analysis results
        status: Analysis status (completed, failed)
        error_message: Error message if analysis failed
        execution_time_ms: Execution time in milliseconds
        created_at: Timestamp when analysis was created
    """
    
    __tablename__ = "analysis_results"
    
    # Primary key
    id = Column(String(255), primary_key=True, nullable=False)
    
    # Analysis information
    analysis_type = Column(String(50), nullable=False, index=True)  # power_flow, stability, metrics
    
    # Analysis data
    system_state = Column(JSON, nullable=False, default={})
    result_data = Column(JSON, nullable=False, default={})
    
    # Status tracking
    status = Column(String(20), default="completed", nullable=False)
    error_message = Column(String(500), nullable=True)
    
    # Performance metrics
    execution_time_ms = Column(Integer, nullable=False, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Indexes for query optimization
    __table_args__ = (
        Index('idx_analysis_type', 'analysis_type'),
        Index('idx_analysis_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f"<AnalysisResult(id={self.id}, type={self.analysis_type}, status={self.status})>"
    
    def to_dict(self):
        """Convert analysis result to dictionary"""
        return {
            "id": self.id,
            "analysis_type": self.analysis_type,
            "system_state": self.system_state,
            "result_data": self.result_data,
            "status": self.status,
            "error_message": self.error_message,
            "execution_time_ms": self.execution_time_ms,
            "created_at": self.created_at.isoformat()
        }
    
    def is_completed(self):
        """Check if analysis completed successfully"""
        return self.status == "completed"
    
    def is_failed(self):
        """Check if analysis failed"""
        return self.status == "failed"
    
    def mark_completed(self, result_data: dict, execution_time_ms: int):
        """Mark analysis as completed"""
        self.status = "completed"
        self.result_data = result_data
        self.execution_time_ms = execution_time_ms
    
    def mark_failed(self, error_message: str, execution_time_ms: int):
        """Mark analysis as failed"""
        self.status = "failed"
        self.error_message = error_message
        self.execution_time_ms = execution_time_ms
