"""
Unit tests for Storage Module.

Tests:
- Data collection service
- Data reporting service with retry logic
- Storage module integration
- Error handling
"""

import pytest
import time
import json
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
import requests

from models.realtime_data_models import StorageData
from services.storage_module import (
    DataCollectionService, DataReportingService, StorageModule
)


class TestDataCollectionService:
    """Test data collection service."""

    def test_initialization(self):
        """Test service initialization."""
        service = DataCollectionService()
        assert service.device_id == "vpp-storage"
        assert service.soc == 75.0
        assert service.soh == 98.0
        assert service.current_power == 50.0
        assert service.charge_status == "idle"
        assert service.temperature == 25.0

    def test_collect_data_returns_valid_data(self):
        """Test that collect_data returns valid StorageData."""
        service = DataCollectionService()
        data = service.collect_data()
        
        assert isinstance(data, StorageData)
        assert isinstance(data.timestamp, datetime)
        assert isinstance(data.soc, float)
        assert isinstance(data.soh, float)
        assert isinstance(data.current_power, float)
        assert isinstance(data.temperature, float)
        assert isinstance(data.charge_status, str)

    def test_collect_data_values_in_valid_range(self):
        """Test that collected data values are in valid ranges."""
        service = DataCollectionService()
        data = service.collect_data()
        
        assert 0 <= data.soc <= 100
        assert 0 <= data.soh <= 100
        assert data.current_power >= 0
        assert -50 <= data.temperature <= 80
        assert data.charge_status in ["charging", "discharging", "idle"]

    def test_collect_data_multiple_times(self):
        """Test collecting data multiple times."""
        service = DataCollectionService()
        data_list = [service.collect_data() for _ in range(5)]
        
        assert len(data_list) == 5
        # Values should vary slightly
        socs = [d.soc for d in data_list]
        assert len(set(socs)) > 1  # Not all the same

    def test_set_storage_level(self):
        """Test setting storage levels."""
        service = DataCollectionService()
        service.set_storage_level(80.0, 95.0, 60.0, "charging", 30.0)
        
        assert service.soc == 80.0
        assert service.soh == 95.0
        assert service.current_power == 60.0
        assert service.charge_status == "charging"
        assert service.temperature == 30.0

    def test_collect_data_after_set_storage_level(self):
        """Test collecting data after setting storage levels."""
        service = DataCollectionService()
        service.set_storage_level(80.0, 95.0, 60.0, "charging", 30.0)
        data = service.collect_data()
        
        # Values should be close to set values (with small variations)
        assert 78 < data.soc < 82
        assert 94.5 < data.soh < 95.5
        assert 55 < data.current_power < 65
        assert 29 < data.temperature < 31


class TestDataReportingService:
    """Test data reporting service."""

    def test_initialization(self):
        """Test service initialization."""
        service = DataReportingService()
        assert service.vcc_url == "http://localhost:8080"
        assert service.report_interval == 5
        assert service.max_retries == 3
        assert service.is_running is False
        assert service.report_count == 0
        assert service.failed_report_count == 0

    def test_initialization_with_custom_params(self):
        """Test service initialization with custom parameters."""
        service = DataReportingService(
            vcc_url="http://vcc-master:8080",
            report_interval=10,
            max_retries=5
        )
        assert service.vcc_url == "http://vcc-master:8080"
        assert service.report_interval == 10
        assert service.max_retries == 5

    @patch('requests.post')
    def test_send_report_success(self, mock_post):
        """Test successful data reporting."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        service = DataReportingService()
        data = StorageData(
            timestamp=datetime.now(),
            soc=75.0,
            soh=98.0,
            current_power=50.0,
            charge_status="charging",
            temperature=25.0
        )
        
        result = service._send_report(data)
        assert result is True
        mock_post.assert_called_once()

    @patch('requests.post')
    def test_send_report_failure(self, mock_post):
        """Test failed data reporting."""
        mock_post.side_effect = requests.exceptions.RequestException("Connection error")
        
        service = DataReportingService()
        data = StorageData(
            timestamp=datetime.now(),
            soc=75.0,
            soh=98.0,
            current_power=50.0,
            charge_status="charging",
            temperature=25.0
        )
        
        from tenacity import RetryError
        with pytest.raises(RetryError):
            service._send_report(data)

    @patch('requests.post')
    def test_report_data_success(self, mock_post):
        """Test report_data method with successful reporting."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        service = DataReportingService()
        result = service.report_data()
        
        assert result is True
        assert service.report_count == 1
        assert service.failed_report_count == 0
        assert service.last_report_time is not None

    @patch('requests.post')
    def test_report_data_failure(self, mock_post):
        """Test report_data method with failed reporting."""
        mock_post.side_effect = requests.exceptions.RequestException("Connection error")
        
        service = DataReportingService()
        result = service.report_data()
        
        assert result is False
        assert service.report_count == 0
        assert service.failed_report_count == 1

    @patch('requests.post')
    def test_report_data_multiple_times(self, mock_post):
        """Test reporting data multiple times."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        service = DataReportingService()
        for _ in range(3):
            result = service.report_data()
            assert result is True
        
        assert service.report_count == 3
        assert service.failed_report_count == 0

    def test_start_and_stop(self):
        """Test starting and stopping the reporting service."""
        with patch('requests.post'):
            service = DataReportingService(report_interval=1)
            
            service.start()
            assert service.is_running is True
            assert service.report_thread is not None
            
            time.sleep(0.5)
            service.stop()
            assert service.is_running is False

    def test_start_already_running(self):
        """Test starting service that's already running."""
        with patch('requests.post'):
            service = DataReportingService()
            service.is_running = True
            
            # Should not raise error
            service.start()
            assert service.is_running is True

    def test_get_stats(self):
        """Test getting service statistics."""
        service = DataReportingService()
        stats = service.get_stats()
        
        assert "is_running" in stats
        assert "report_count" in stats
        assert "failed_report_count" in stats
        assert "last_report_time" in stats
        assert "report_interval" in stats
        assert "vcc_url" in stats

    @patch('requests.post')
    def test_get_stats_after_reporting(self, mock_post):
        """Test getting stats after reporting data."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        service = DataReportingService()
        service.report_data()
        stats = service.get_stats()
        
        assert stats["report_count"] == 1
        assert stats["failed_report_count"] == 0
        assert stats["last_report_time"] is not None


class TestStorageModule:
    """Test storage module."""

    def test_initialization(self):
        """Test module initialization."""
        module = StorageModule()
        assert module.vcc_url == "http://localhost:8080"
        assert module.report_interval == 5
        assert module.collection_service is not None
        assert module.reporting_service is not None

    def test_initialization_with_custom_params(self):
        """Test module initialization with custom parameters."""
        module = StorageModule(
            vcc_url="http://vcc-master:8080",
            report_interval=10
        )
        assert module.vcc_url == "http://vcc-master:8080"
        assert module.report_interval == 10

    def test_collect_data(self):
        """Test collecting data through module."""
        module = StorageModule()
        data = module.collect_data()
        
        assert isinstance(data, StorageData)
        assert 0 <= data.soc <= 100
        assert 0 <= data.soh <= 100
        assert data.current_power >= 0

    @patch('requests.post')
    def test_report_data(self, mock_post):
        """Test reporting data through module."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        module = StorageModule()
        result = module.report_data()
        
        assert result is True

    @patch('requests.post')
    def test_start_and_stop(self, mock_post):
        """Test starting and stopping the module."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        module = StorageModule(report_interval=1)
        module.start()
        assert module.reporting_service.is_running is True
        
        time.sleep(0.5)
        module.stop()
        assert module.reporting_service.is_running is False

    def test_get_stats(self):
        """Test getting module statistics."""
        module = StorageModule()
        stats = module.get_stats()
        
        assert "module" in stats
        assert stats["module"] == "storage"
        assert "vcc_url" in stats
        assert "report_interval" in stats
        assert "reporting_stats" in stats

    def test_set_storage_level(self):
        """Test setting storage levels through module."""
        module = StorageModule()
        module.set_storage_level(80.0, 95.0, 60.0, "charging", 30.0)
        
        data = module.collect_data()
        assert 78 < data.soc < 82
        assert 94.5 < data.soh < 95.5


class TestDataReportingRetryLogic:
    """Test retry logic in data reporting."""

    @patch('requests.post')
    def test_retry_on_connection_error(self, mock_post):
        """Test retry on connection error."""
        # First call fails, second succeeds
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.side_effect = [
            requests.exceptions.ConnectionError("Connection failed"),
            mock_response
        ]
        
        service = DataReportingService()
        data = StorageData(
            timestamp=datetime.now(),
            soc=75.0,
            soh=98.0,
            current_power=50.0,
            charge_status="charging",
            temperature=25.0
        )
        
        result = service._send_report(data)
        assert result is True
        assert mock_post.call_count == 2

    @patch('requests.post')
    def test_retry_exhaustion(self, mock_post):
        """Test retry exhaustion after max attempts."""
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        service = DataReportingService(max_retries=3)
        data = StorageData(
            timestamp=datetime.now(),
            soc=75.0,
            soh=98.0,
            current_power=50.0,
            charge_status="charging",
            temperature=25.0
        )
        
        from tenacity import RetryError
        with pytest.raises(RetryError):
            service._send_report(data)
        
        # Should have tried 3 times
        assert mock_post.call_count == 3


class TestDataReportingIntegration:
    """Test integration scenarios."""

    @patch('requests.post')
    def test_continuous_reporting(self, mock_post):
        """Test continuous data reporting."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        module = StorageModule(report_interval=1)
        module.start()
        
        # Let it run for a bit
        time.sleep(2.5)
        module.stop()
        
        # Should have reported at least twice
        assert module.reporting_service.report_count >= 2

    @patch('requests.post')
    def test_reporting_with_varying_data(self, mock_post):
        """Test reporting with varying storage levels."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        module = StorageModule()
        
        # Report with different storage levels
        module.set_storage_level(70.0, 95.0, 40.0, "discharging", 20.0)
        module.report_data()
        
        module.set_storage_level(80.0, 98.0, 50.0, "charging", 25.0)
        module.report_data()
        
        module.set_storage_level(90.0, 99.0, 60.0, "idle", 30.0)
        module.report_data()
        
        assert module.reporting_service.report_count == 3

    def test_module_error_handling(self):
        """Test module error handling."""
        module = StorageModule(vcc_url="http://invalid-url:9999")
        
        # Should handle connection errors gracefully
        result = module.report_data()
        assert result is False
        assert module.reporting_service.failed_report_count == 1


class TestStorageDataValidation:
    """Test storage data validation."""

    def test_soc_boundary_values(self):
        """Test SOC boundary values."""
        service = DataCollectionService()
        service.set_storage_level(0.0, 98.0, 50.0, "idle", 25.0)
        data = service.collect_data()
        assert 0 <= data.soc <= 100
        
        service.set_storage_level(100.0, 98.0, 50.0, "idle", 25.0)
        data = service.collect_data()
        assert 0 <= data.soc <= 100

    def test_temperature_boundary_values(self):
        """Test temperature boundary values."""
        service = DataCollectionService()
        service.set_storage_level(75.0, 98.0, 50.0, "idle", -50.0)
        data = service.collect_data()
        assert -50 <= data.temperature <= 80
        
        service.set_storage_level(75.0, 98.0, 50.0, "idle", 80.0)
        data = service.collect_data()
        assert -50 <= data.temperature <= 80

    def test_charge_status_values(self):
        """Test charge status values."""
        service = DataCollectionService()
        for status in ["charging", "discharging", "idle"]:
            service.set_storage_level(75.0, 98.0, 50.0, status, 25.0)
            data = service.collect_data()
            assert data.charge_status in ["charging", "discharging", "idle"]
