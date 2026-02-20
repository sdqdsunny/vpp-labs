"""
Test Result Persistence Service

Integrates test result storage and retrieval with SecurityTestManager.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from models.security_test_result import SecurityTestResultModel, TestResultRepository

logger = logging.getLogger(__name__)


class TestResultPersistenceService:
    """Service for persisting and retrieving test results"""
    
    def __init__(self, session: Session):
        """Initialize persistence service
        
        Args:
            session: SQLAlchemy database session
        """
        self.session = session
        self.repository = TestResultRepository(session)
    
    def store_result(self, test_result: Any) -> Optional[SecurityTestResultModel]:
        """Store a test result in the database
        
        Args:
            test_result: TestResult object to store
            
        Returns:
            SecurityTestResultModel instance or None if storage failed
        """
        try:
            model = self.repository.create(test_result)
            logger.info(f"Stored test result: {test_result.test_id}")
            return model
        except Exception as e:
            logger.error(f"Failed to store test result: {e}", exc_info=True)
            return None
    
    def retrieve_result(self, test_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a test result by ID
        
        Args:
            test_id: The test ID to retrieve
            
        Returns:
            Dictionary representation of the result or None if not found
        """
        try:
            model = self.repository.get_by_id(test_id)
            if model:
                return model.to_dict()
            return None
        except Exception as e:
            logger.error(f"Failed to retrieve test result: {e}", exc_info=True)
            return None
    
    def get_results_by_adapter(self, adapter_name: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get test results by adapter name
        
        Args:
            adapter_name: Name of the adapter
            limit: Maximum number of results to return
            
        Returns:
            List of result dictionaries
        """
        try:
            models = self.repository.get_by_adapter(adapter_name, limit)
            return [model.to_dict() for model in models]
        except Exception as e:
            logger.error(f"Failed to retrieve results by adapter: {e}", exc_info=True)
            return []
    
    def get_results_by_host(self, target_host: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get test results by target host
        
        Args:
            target_host: Target host to filter by
            limit: Maximum number of results to return
            
        Returns:
            List of result dictionaries
        """
        try:
            models = self.repository.get_by_target_host(target_host, limit)
            return [model.to_dict() for model in models]
        except Exception as e:
            logger.error(f"Failed to retrieve results by host: {e}", exc_info=True)
            return []
    
    def get_results_by_type(self, test_type: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get test results by test type
        
        Args:
            test_type: Test type to filter by
            limit: Maximum number of results to return
            
        Returns:
            List of result dictionaries
        """
        try:
            models = self.repository.get_by_test_type(test_type, limit)
            return [model.to_dict() for model in models]
        except Exception as e:
            logger.error(f"Failed to retrieve results by type: {e}", exc_info=True)
            return []
    
    def get_results_by_status(self, status: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get test results by status
        
        Args:
            status: Status to filter by ("success", "failed", "error")
            limit: Maximum number of results to return
            
        Returns:
            List of result dictionaries
        """
        try:
            models = self.repository.get_by_status(status, limit)
            return [model.to_dict() for model in models]
        except Exception as e:
            logger.error(f"Failed to retrieve results by status: {e}", exc_info=True)
            return []
    
    def get_recent_results(self, days: int = 30, limit: int = 100) -> List[Dict[str, Any]]:
        """Get test results from the past N days
        
        Args:
            days: Number of days to look back
            limit: Maximum number of results to return
            
        Returns:
            List of result dictionaries
        """
        try:
            models = self.repository.get_recent(days, limit)
            return [model.to_dict() for model in models]
        except Exception as e:
            logger.error(f"Failed to retrieve recent results: {e}", exc_info=True)
            return []
    
    def filter_results(self, adapter_name: Optional[str] = None,
                      target_host: Optional[str] = None,
                      test_type: Optional[str] = None,
                      status: Optional[str] = None,
                      days: int = 30,
                      limit: int = 100) -> List[Dict[str, Any]]:
        """Filter test results by multiple criteria
        
        Args:
            adapter_name: Filter by adapter name
            target_host: Filter by target host
            test_type: Filter by test type
            status: Filter by status
            days: Look back N days
            limit: Maximum number of results to return
            
        Returns:
            List of result dictionaries
        """
        try:
            models = self.repository.filter(
                adapter_name=adapter_name,
                target_host=target_host,
                test_type=test_type,
                status=status,
                days=days,
                limit=limit
            )
            return [model.to_dict() for model in models]
        except Exception as e:
            logger.error(f"Failed to filter results: {e}", exc_info=True)
            return []
    
    def get_statistics(self, days: int = 30) -> Dict[str, Any]:
        """Get statistics about test results
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dictionary with statistics
        """
        try:
            return self.repository.get_statistics(days)
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}", exc_info=True)
            return {}
    
    def export_results(self, format: str = "json", 
                      adapter_name: Optional[str] = None,
                      target_host: Optional[str] = None,
                      test_type: Optional[str] = None,
                      days: int = 30) -> Optional[str]:
        """Export test results in specified format
        
        Args:
            format: Export format ("json" or "csv")
            adapter_name: Filter by adapter name
            target_host: Filter by target host
            test_type: Filter by test type
            days: Look back N days
            
        Returns:
            Exported data as string or None if export failed
        """
        try:
            # Get filtered results
            models = self.repository.filter(
                adapter_name=adapter_name,
                target_host=target_host,
                test_type=test_type,
                days=days,
                limit=10000  # Allow large exports
            )
            
            if format.lower() == "json":
                return self.repository.export_to_json(models)
            elif format.lower() == "csv":
                return self.repository.export_to_csv(models)
            else:
                logger.error(f"Unsupported export format: {format}")
                return None
        except Exception as e:
            logger.error(f"Failed to export results: {e}", exc_info=True)
            return None
    
    def cleanup_old_results(self, days: int = 90) -> int:
        """Delete test results older than N days
        
        Args:
            days: Delete results older than this many days
            
        Returns:
            Number of deleted records
        """
        try:
            count = self.repository.delete_old_results(days)
            logger.info(f"Deleted {count} old test results (older than {days} days)")
            return count
        except Exception as e:
            logger.error(f"Failed to cleanup old results: {e}", exc_info=True)
            return 0


# Global persistence service instance
_persistence_service: Optional[TestResultPersistenceService] = None


def get_persistence_service(session: Optional[Session] = None) -> Optional[TestResultPersistenceService]:
    """Get or create the global persistence service
    
    Args:
        session: SQLAlchemy database session (required for first call)
        
    Returns:
        TestResultPersistenceService instance or None
    """
    global _persistence_service
    
    if _persistence_service is None:
        if session is None:
            logger.warning("Cannot create persistence service without database session")
            return None
        _persistence_service = TestResultPersistenceService(session)
    
    return _persistence_service


def set_persistence_service(service: TestResultPersistenceService) -> None:
    """Set the global persistence service
    
    Args:
        service: TestResultPersistenceService instance
    """
    global _persistence_service
    _persistence_service = service
