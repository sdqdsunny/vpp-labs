"""
Security Test Result Database Model

Defines the SQLAlchemy model for persisting security test results.
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import uuid
import json

from sqlalchemy import Column, String, Integer, Float, DateTime, JSON, Text, Index
from sqlalchemy.orm import Session

from models.base import Base


class SecurityTestResultModel(Base):
    """SQLAlchemy model for security test results"""
    
    __tablename__ = "security_test_results"
    
    # Primary key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Test identification
    test_id = Column(String(36), unique=True, nullable=False, index=True)
    test_type = Column(String(50), nullable=False, index=True)
    adapter_name = Column(String(50), nullable=False, index=True)
    
    # Test status
    status = Column(String(20), nullable=False)  # "success", "failed", "error"
    
    # Timing information
    start_time = Column(DateTime, nullable=False, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    duration = Column(Float, nullable=False, default=0.0)
    
    # Target information
    target_host = Column(String(255), nullable=False, index=True)
    target_port = Column(Integer, nullable=False)
    target_url = Column(String(255), nullable=True)
    
    # Results
    result_data = Column(JSON, nullable=False, default=dict)
    error_message = Column(Text, nullable=True)
    vulnerabilities_found = Column(JSON, nullable=False, default=list)
    
    # Metadata
    test_metadata = Column(JSON, nullable=False, default=dict)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_adapter_name_created_at', 'adapter_name', 'created_at'),
        Index('idx_target_host_created_at', 'target_host', 'created_at'),
        Index('idx_test_type_created_at', 'test_type', 'created_at'),
        Index('idx_status_created_at', 'status', 'created_at'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            'id': self.id,
            'test_id': self.test_id,
            'test_type': self.test_type,
            'adapter_name': self.adapter_name,
            'status': self.status,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration': self.duration,
            'target_host': self.target_host,
            'target_port': self.target_port,
            'target_url': self.target_url,
            'result_data': self.result_data,
            'error_message': self.error_message,
            'vulnerabilities_found': self.vulnerabilities_found,
            'test_metadata': self.test_metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @staticmethod
    def from_test_result(test_result: Any) -> 'SecurityTestResultModel':
        """Create a model instance from a TestResult object"""
        return SecurityTestResultModel(
            test_id=test_result.test_id,
            test_type=test_result.test_type,
            adapter_name=test_result.adapter_name,
            status=test_result.status,
            start_time=test_result.start_time,
            end_time=test_result.end_time,
            duration=test_result.duration,
            target_host=test_result.target_host,
            target_port=test_result.target_port,
            target_url=test_result.target_url,
            result_data=test_result.result_data,
            error_message=test_result.error_message,
            vulnerabilities_found=test_result.vulnerabilities_found,
            test_metadata=test_result.metadata,
        )


class TestResultRepository:
    """Repository for test result persistence operations"""
    
    def __init__(self, session: Session):
        """Initialize repository with database session"""
        self.session = session
    
    def create(self, test_result: Any) -> SecurityTestResultModel:
        """Create and store a test result
        
        Args:
            test_result: TestResult object to store
            
        Returns:
            SecurityTestResultModel instance
        """
        model = SecurityTestResultModel.from_test_result(test_result)
        self.session.add(model)
        self.session.commit()
        return model
    
    def get_by_id(self, test_id: str) -> Optional[SecurityTestResultModel]:
        """Retrieve a test result by ID
        
        Args:
            test_id: The test ID to retrieve
            
        Returns:
            SecurityTestResultModel or None if not found
        """
        return self.session.query(SecurityTestResultModel).filter(
            SecurityTestResultModel.test_id == test_id
        ).first()
    
    def get_by_adapter(self, adapter_name: str, limit: int = 100) -> List[SecurityTestResultModel]:
        """Get test results by adapter name
        
        Args:
            adapter_name: Name of the adapter
            limit: Maximum number of results to return
            
        Returns:
            List of SecurityTestResultModel instances
        """
        return self.session.query(SecurityTestResultModel).filter(
            SecurityTestResultModel.adapter_name == adapter_name
        ).order_by(SecurityTestResultModel.created_at.desc()).limit(limit).all()
    
    def get_by_target_host(self, target_host: str, limit: int = 100) -> List[SecurityTestResultModel]:
        """Get test results by target host
        
        Args:
            target_host: Target host to filter by
            limit: Maximum number of results to return
            
        Returns:
            List of SecurityTestResultModel instances
        """
        return self.session.query(SecurityTestResultModel).filter(
            SecurityTestResultModel.target_host == target_host
        ).order_by(SecurityTestResultModel.created_at.desc()).limit(limit).all()
    
    def get_by_test_type(self, test_type: str, limit: int = 100) -> List[SecurityTestResultModel]:
        """Get test results by test type
        
        Args:
            test_type: Test type to filter by
            limit: Maximum number of results to return
            
        Returns:
            List of SecurityTestResultModel instances
        """
        return self.session.query(SecurityTestResultModel).filter(
            SecurityTestResultModel.test_type == test_type
        ).order_by(SecurityTestResultModel.created_at.desc()).limit(limit).all()
    
    def get_by_status(self, status: str, limit: int = 100) -> List[SecurityTestResultModel]:
        """Get test results by status
        
        Args:
            status: Status to filter by ("success", "failed", "error")
            limit: Maximum number of results to return
            
        Returns:
            List of SecurityTestResultModel instances
        """
        return self.session.query(SecurityTestResultModel).filter(
            SecurityTestResultModel.status == status
        ).order_by(SecurityTestResultModel.created_at.desc()).limit(limit).all()
    
    def get_recent(self, days: int = 30, limit: int = 100) -> List[SecurityTestResultModel]:
        """Get test results from the past N days
        
        Args:
            days: Number of days to look back
            limit: Maximum number of results to return
            
        Returns:
            List of SecurityTestResultModel instances
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        return self.session.query(SecurityTestResultModel).filter(
            SecurityTestResultModel.created_at >= cutoff_date
        ).order_by(SecurityTestResultModel.created_at.desc()).limit(limit).all()
    
    def filter(self, adapter_name: Optional[str] = None, 
               target_host: Optional[str] = None,
               test_type: Optional[str] = None,
               status: Optional[str] = None,
               days: int = 30,
               limit: int = 100) -> List[SecurityTestResultModel]:
        """Filter test results by multiple criteria
        
        Args:
            adapter_name: Filter by adapter name
            target_host: Filter by target host
            test_type: Filter by test type
            status: Filter by status
            days: Look back N days
            limit: Maximum number of results to return
            
        Returns:
            List of SecurityTestResultModel instances
        """
        query = self.session.query(SecurityTestResultModel)
        
        # Apply filters
        if adapter_name:
            query = query.filter(SecurityTestResultModel.adapter_name == adapter_name)
        
        if target_host:
            query = query.filter(SecurityTestResultModel.target_host == target_host)
        
        if test_type:
            query = query.filter(SecurityTestResultModel.test_type == test_type)
        
        if status:
            query = query.filter(SecurityTestResultModel.status == status)
        
        # Apply date filter
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        query = query.filter(SecurityTestResultModel.created_at >= cutoff_date)
        
        # Order and limit
        return query.order_by(SecurityTestResultModel.created_at.desc()).limit(limit).all()
    
    def get_statistics(self, days: int = 30) -> Dict[str, Any]:
        """Get statistics about test results
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dictionary with statistics
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        query = self.session.query(SecurityTestResultModel).filter(
            SecurityTestResultModel.created_at >= cutoff_date
        )
        
        total_tests = query.count()
        successful_tests = query.filter(SecurityTestResultModel.status == "success").count()
        failed_tests = query.filter(SecurityTestResultModel.status == "failed").count()
        error_tests = query.filter(SecurityTestResultModel.status == "error").count()
        
        # Get unique adapters and hosts
        adapters = self.session.query(SecurityTestResultModel.adapter_name.distinct()).filter(
            SecurityTestResultModel.created_at >= cutoff_date
        ).all()
        
        hosts = self.session.query(SecurityTestResultModel.target_host.distinct()).filter(
            SecurityTestResultModel.created_at >= cutoff_date
        ).all()
        
        return {
            'total_tests': total_tests,
            'successful_tests': successful_tests,
            'failed_tests': failed_tests,
            'error_tests': error_tests,
            'success_rate': (successful_tests / total_tests * 100) if total_tests > 0 else 0,
            'unique_adapters': len(adapters),
            'unique_hosts': len(hosts),
            'period_days': days,
        }
    
    def delete_old_results(self, days: int = 90) -> int:
        """Delete test results older than N days
        
        Args:
            days: Delete results older than this many days
            
        Returns:
            Number of deleted records
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        count = self.session.query(SecurityTestResultModel).filter(
            SecurityTestResultModel.created_at < cutoff_date
        ).delete()
        self.session.commit()
        return count
    
    def export_to_json(self, results: List[SecurityTestResultModel]) -> str:
        """Export test results to JSON format
        
        Args:
            results: List of SecurityTestResultModel instances
            
        Returns:
            JSON string representation
        """
        data = [result.to_dict() for result in results]
        return json.dumps(data, indent=2)
    
    def export_to_csv(self, results: List[SecurityTestResultModel]) -> str:
        """Export test results to CSV format
        
        Args:
            results: List of SecurityTestResultModel instances
            
        Returns:
            CSV string representation
        """
        import csv
        from io import StringIO
        
        output = StringIO()
        if not results:
            return ""
        
        # Get all keys from first result
        fieldnames = list(results[0].to_dict().keys())
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for result in results:
            writer.writerow(result.to_dict())
        
        return output.getvalue()
