"""
Test Result Persistence Tests

Tests for database storage, retrieval, filtering, and export of test results.
"""

import pytest
import json
import csv
from io import StringIO
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models.base import Base
from models.security_test_result import SecurityTestResultModel, TestResultRepository
from services.test_result_persistence import TestResultPersistenceService
from services.security_adapters.base_adapter import TestResult


@pytest.fixture
def db_session():
    """Create an in-memory SQLite database for testing"""
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def sample_test_result():
    """Create a sample test result"""
    result = TestResult(
        test_type="connection",
        adapter_name="dnp3",
        target_host="localhost",
        target_port=20000,
    )
    result.mark_success()
    result.result_data = {"connection_status": "success"}
    result.vulnerabilities_found = []
    return result


class TestSecurityTestResultModel:
    """Test SecurityTestResultModel"""
    
    def test_model_creation(self, sample_test_result):
        """Test creating a model from test result"""
        model = SecurityTestResultModel.from_test_result(sample_test_result)
        
        assert model.test_id == sample_test_result.test_id
        assert model.test_type == "connection"
        assert model.adapter_name == "dnp3"
        assert model.target_host == "localhost"
        assert model.target_port == 20000
        assert model.status == "success"
    
    def test_model_to_dict(self, sample_test_result):
        """Test converting model to dictionary"""
        model = SecurityTestResultModel.from_test_result(sample_test_result)
        data = model.to_dict()
        
        assert data['test_type'] == "connection"
        assert data['adapter_name'] == "dnp3"
        assert data['target_host'] == "localhost"
        assert data['target_port'] == 20000
        assert data['status'] == "success"
        assert isinstance(data['start_time'], str)


class TestTestResultRepository:
    """Test TestResultRepository"""
    
    def test_create_result(self, db_session, sample_test_result):
        """Test creating and storing a result"""
        repo = TestResultRepository(db_session)
        
        model = repo.create(sample_test_result)
        
        assert model is not None
        assert model.test_id == sample_test_result.test_id
        assert model.status == "success"
    
    def test_get_by_id(self, db_session, sample_test_result):
        """Test retrieving a result by ID"""
        repo = TestResultRepository(db_session)
        repo.create(sample_test_result)
        
        retrieved = repo.get_by_id(sample_test_result.test_id)
        
        assert retrieved is not None
        assert retrieved.test_id == sample_test_result.test_id
    
    def test_get_by_id_not_found(self, db_session):
        """Test retrieving non-existent result"""
        repo = TestResultRepository(db_session)
        
        retrieved = repo.get_by_id("nonexistent_id")
        
        assert retrieved is None
    
    def test_get_by_adapter(self, db_session):
        """Test retrieving results by adapter"""
        repo = TestResultRepository(db_session)
        
        # Create multiple results
        for i in range(3):
            result = TestResult(
                test_type="connection",
                adapter_name="dnp3",
                target_host=f"host{i}",
                target_port=20000 + i,
            )
            result.mark_success()
            repo.create(result)
        
        results = repo.get_by_adapter("dnp3")
        
        assert len(results) == 3
        assert all(r.adapter_name == "dnp3" for r in results)
    
    def test_get_by_target_host(self, db_session):
        """Test retrieving results by target host"""
        repo = TestResultRepository(db_session)
        
        # Create results for different hosts
        for i in range(2):
            result = TestResult(
                test_type="connection",
                adapter_name=f"adapter{i}",
                target_host="localhost",
                target_port=20000 + i,
            )
            result.mark_success()
            repo.create(result)
        
        results = repo.get_by_target_host("localhost")
        
        assert len(results) == 2
        assert all(r.target_host == "localhost" for r in results)
    
    def test_get_by_test_type(self, db_session):
        """Test retrieving results by test type"""
        repo = TestResultRepository(db_session)
        
        # Create results with different test types
        for test_type in ["connection", "scan", "fuzz"]:
            result = TestResult(
                test_type=test_type,
                adapter_name="dnp3",
                target_host="localhost",
                target_port=20000,
            )
            result.mark_success()
            repo.create(result)
        
        results = repo.get_by_test_type("connection")
        
        assert len(results) == 1
        assert results[0].test_type == "connection"
    
    def test_get_by_status(self, db_session):
        """Test retrieving results by status"""
        repo = TestResultRepository(db_session)
        
        # Create results with different statuses
        for status in ["success", "failed", "error"]:
            result = TestResult(
                test_type="connection",
                adapter_name="dnp3",
                target_host="localhost",
                target_port=20000,
            )
            if status == "success":
                result.mark_success()
            elif status == "failed":
                result.mark_failed("Test failed")
            else:
                result.mark_error("Test error")
            repo.create(result)
        
        results = repo.get_by_status("success")
        
        assert len(results) == 1
        assert results[0].status == "success"
    
    def test_get_recent(self, db_session, sample_test_result):
        """Test retrieving recent results"""
        repo = TestResultRepository(db_session)
        repo.create(sample_test_result)
        
        results = repo.get_recent(days=30)
        
        assert len(results) == 1
        assert results[0].test_id == sample_test_result.test_id
    
    def test_filter_multiple_criteria(self, db_session):
        """Test filtering with multiple criteria"""
        repo = TestResultRepository(db_session)
        
        # Create results with different combinations
        result1 = TestResult(
            test_type="connection",
            adapter_name="dnp3",
            target_host="localhost",
            target_port=20000,
        )
        result1.mark_success()
        repo.create(result1)
        
        result2 = TestResult(
            test_type="scan",
            adapter_name="opcua",
            target_host="localhost",
            target_port=4840,
        )
        result2.mark_failed("Scan failed")
        repo.create(result2)
        
        # Filter by adapter and status
        results = repo.filter(adapter_name="dnp3", status="success")
        
        assert len(results) == 1
        assert results[0].adapter_name == "dnp3"
        assert results[0].status == "success"
    
    def test_get_statistics(self, db_session):
        """Test getting statistics"""
        repo = TestResultRepository(db_session)
        
        # Create results with different statuses
        for i in range(3):
            result = TestResult(
                test_type="connection",
                adapter_name="dnp3",
                target_host="localhost",
                target_port=20000,
            )
            if i < 2:
                result.mark_success()
            else:
                result.mark_failed("Test failed")
            repo.create(result)
        
        stats = repo.get_statistics(days=30)
        
        assert stats['total_tests'] == 3
        assert stats['successful_tests'] == 2
        assert stats['failed_tests'] == 1
        assert stats['error_tests'] == 0
        assert stats['success_rate'] == pytest.approx(66.67, rel=0.01)
    
    def test_delete_old_results(self, db_session):
        """Test deleting old results"""
        repo = TestResultRepository(db_session)
        
        # Create a result
        result = TestResult(
            test_type="connection",
            adapter_name="dnp3",
            target_host="localhost",
            target_port=20000,
        )
        result.mark_success()
        model = repo.create(result)
        
        # Manually set created_at to old date
        model.created_at = datetime.utcnow() - timedelta(days=100)
        db_session.commit()
        
        # Delete old results
        count = repo.delete_old_results(days=90)
        
        assert count == 1
        assert repo.get_by_id(result.test_id) is None
    
    def test_export_to_json(self, db_session, sample_test_result):
        """Test exporting results to JSON"""
        repo = TestResultRepository(db_session)
        model = repo.create(sample_test_result)
        
        json_str = repo.export_to_json([model])
        data = json.loads(json_str)
        
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]['test_id'] == sample_test_result.test_id
    
    def test_export_to_csv(self, db_session, sample_test_result):
        """Test exporting results to CSV"""
        repo = TestResultRepository(db_session)
        model = repo.create(sample_test_result)
        
        csv_str = repo.export_to_csv([model])
        
        # Parse CSV
        reader = csv.DictReader(StringIO(csv_str))
        rows = list(reader)
        
        assert len(rows) == 1
        assert rows[0]['test_id'] == sample_test_result.test_id


class TestTestResultPersistenceService:
    """Test TestResultPersistenceService"""
    
    def test_store_result(self, db_session, sample_test_result):
        """Test storing a result"""
        service = TestResultPersistenceService(db_session)
        
        model = service.store_result(sample_test_result)
        
        assert model is not None
        assert model.test_id == sample_test_result.test_id
    
    def test_retrieve_result(self, db_session, sample_test_result):
        """Test retrieving a result"""
        service = TestResultPersistenceService(db_session)
        service.store_result(sample_test_result)
        
        data = service.retrieve_result(sample_test_result.test_id)
        
        assert data is not None
        assert data['test_id'] == sample_test_result.test_id
        assert data['status'] == "success"
    
    def test_get_results_by_adapter(self, db_session):
        """Test getting results by adapter"""
        service = TestResultPersistenceService(db_session)
        
        # Store multiple results
        for i in range(2):
            result = TestResult(
                test_type="connection",
                adapter_name="dnp3",
                target_host=f"host{i}",
                target_port=20000 + i,
            )
            result.mark_success()
            service.store_result(result)
        
        results = service.get_results_by_adapter("dnp3")
        
        assert len(results) == 2
        assert all(r['adapter_name'] == "dnp3" for r in results)
    
    def test_filter_results(self, db_session):
        """Test filtering results"""
        service = TestResultPersistenceService(db_session)
        
        # Store results
        result1 = TestResult(
            test_type="connection",
            adapter_name="dnp3",
            target_host="localhost",
            target_port=20000,
        )
        result1.mark_success()
        service.store_result(result1)
        
        result2 = TestResult(
            test_type="scan",
            adapter_name="opcua",
            target_host="localhost",
            target_port=4840,
        )
        result2.mark_failed("Scan failed")
        service.store_result(result2)
        
        # Filter
        results = service.filter_results(adapter_name="dnp3", status="success")
        
        assert len(results) == 1
        assert results[0]['adapter_name'] == "dnp3"
    
    def test_get_statistics(self, db_session):
        """Test getting statistics"""
        service = TestResultPersistenceService(db_session)
        
        # Store results
        for i in range(3):
            result = TestResult(
                test_type="connection",
                adapter_name="dnp3",
                target_host="localhost",
                target_port=20000,
            )
            if i < 2:
                result.mark_success()
            else:
                result.mark_failed("Test failed")
            service.store_result(result)
        
        stats = service.get_statistics(days=30)
        
        assert stats['total_tests'] == 3
        assert stats['successful_tests'] == 2
        assert stats['failed_tests'] == 1
    
    def test_export_results_json(self, db_session, sample_test_result):
        """Test exporting results as JSON"""
        service = TestResultPersistenceService(db_session)
        service.store_result(sample_test_result)
        
        json_str = service.export_results(format="json")
        data = json.loads(json_str)
        
        assert isinstance(data, list)
        assert len(data) == 1
    
    def test_export_results_csv(self, db_session, sample_test_result):
        """Test exporting results as CSV"""
        service = TestResultPersistenceService(db_session)
        service.store_result(sample_test_result)
        
        csv_str = service.export_results(format="csv")
        
        reader = csv.DictReader(StringIO(csv_str))
        rows = list(reader)
        
        assert len(rows) == 1
    
    def test_cleanup_old_results(self, db_session, sample_test_result):
        """Test cleaning up old results"""
        service = TestResultPersistenceService(db_session)
        model = service.repository.create(sample_test_result)
        
        # Set old date
        model.created_at = datetime.utcnow() - timedelta(days=100)
        db_session.commit()
        
        count = service.cleanup_old_results(days=90)
        
        assert count == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
