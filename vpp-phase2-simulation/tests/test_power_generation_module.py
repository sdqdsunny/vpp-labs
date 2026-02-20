"""
Unit tests for Power Generation Module.

Tests:
- Data collection service
- Data reporting service with retry logic
- Power generation module integration
- Error handling
"""

import pytest
import time
import json
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
import requests

from models.realtime_data_models import PowerGenerationData
from services.power_generation_module import (
    DataCollectionService, DataReportingService, PowerGenerationModule
)


class TestDataCollectionService:
    """Test data collection service."""

    def test_initialization(self):
        """Test service initialization."""
        service = DataCollectionService()
        assert service.device_id == "vpp-power-generation"
        assert service.current_power == 100.0
        assert service.solar_power == 50.0
        assert service.wind_power == 50.0
        assert service.efficiency == 95.0
        assert service.device_status == "running"

    def test_collect_data_returns_valid_data(self):
        """Test that collect_data returns valid PowerGenerationData."""
        service = DataCollectionService()
        data = service.collect_data()
        
        assert isinstance(data, PowerGenerationData)
        assert isinstance(data.timestamp, datetime)
        assert isinstance(data.current_power, float)
        assert isinstance(data.solar_power, float)
        assert isinstance(data.wind_power, float)
        assert isinstance(data.efficiency, float)
        assert isinstance(data.device_status, str)

    def test_collect_data_values_in_valid_range(self):
        """Test that collected data values are in valid ranges."""
        service = DataCollectionService()
        data = service.collect_data()
        
        assert data.current_power >= 0
        assert data.solar_power >= 0
        assert data.wind_power >= 0
        assert 0 <= data.efficiency <= 100
        assert data.device_status in ["running", "idle", "error"]

    def test_collect_data_multiple_times(self):
        """Test collecting data multiple times."""
        service = DataCollectionService()
        data_list = [service.collect_data() for _ in range(5)]
        
        assert len(data_list) == 5
        # Values should vary slightly
        powers = [d.current_power for d in data_list]
        assert len(set(powers)) > 1  # Not all the same

    def test_set_power_level(self):
        """Test setting power levels."""
        service = DataCollectionService()
        service.set_power_level(200.0, 100.0, 100.0, 98.0)
        
        assert service.current_power == 200.0
        assert service.solar_power == 100.0
        assert service.wind_power == 100.0
        assert service.efficiency == 98.0

    def test_collect_data_after_set_power_level(self):
        """Test collecting data after setting power levels."""
        service = DataCollectionService()
        service.set_power_level(200.0, 100.0, 100.0, 98.0)
        data = service.collect_data()
        
        # Values should be close to set values (with small variations)
        assert 195 < data.current_power < 205
        assert 97 < data.solar_power < 103
        assert 97 < data.wind_power < 103
        assert 97 < data.efficiency < 99


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
        data = PowerGenerationData(
            timestamp=datetime.now(),
            current_power=150.0,
            solar_power=100.0,
            wind_power=50.0,
            efficiency=95.0,
            device_status="running"
        )
        
        result = service._send_report(data)
        assert result is True
        mock_post.assert_called_once()

    @patch('requests.post')
    def test_send_report_failure(self, mock_post):
        """Test failed data reporting."""
        mock_post.side_effect = requests.exceptions.RequestException("Connection error")
        
        service = DataReportingService()
        data = PowerGenerationData(
            timestamp=datetime.now(),
            current_power=150.0,
            solar_power=100.0,
            wind_power=50.0,
            efficiency=95.0,
            device_status="running"
        )
        
        # tenacity wraps the exception in RetryError
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


class TestPowerGenerationModule:
    """Test power generation module."""

    def test_initialization(self):
        """Test module initialization."""
        module = PowerGenerationModule()
        assert module.vcc_url == "http://localhost:8080"
        assert module.report_interval == 5
        assert module.collection_service is not None
        assert module.reporting_service is not None

    def test_initialization_with_custom_params(self):
        """Test module initialization with custom parameters."""
        module = PowerGenerationModule(
            vcc_url="http://vcc-master:8080",
            report_interval=10
        )
        assert module.vcc_url == "http://vcc-master:8080"
        assert module.report_interval == 10

    def test_collect_data(self):
        """Test collecting data through module."""
        module = PowerGenerationModule()
        data = module.collect_data()
        
        assert isinstance(data, PowerGenerationData)
        assert data.current_power >= 0
        assert data.solar_power >= 0
        assert data.wind_power >= 0

    @patch('requests.post')
    def test_report_data(self, mock_post):
        """Test reporting data through module."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        module = PowerGenerationModule()
        result = module.report_data()
        
        assert result is True

    @patch('requests.post')
    def test_start_and_stop(self, mock_post):
        """Test starting and stopping the module."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        module = PowerGenerationModule(report_interval=1)
        module.start()
        assert module.reporting_service.is_running is True
        
        time.sleep(0.5)
        module.stop()
        assert module.reporting_service.is_running is False

    def test_get_stats(self):
        """Test getting module statistics."""
        module = PowerGenerationModule()
        stats = module.get_stats()
        
        assert "module" in stats
        assert stats["module"] == "power_generation"
        assert "vcc_url" in stats
        assert "report_interval" in stats
        assert "reporting_stats" in stats

    def test_set_power_level(self):
        """Test setting power levels through module."""
        module = PowerGenerationModule()
        module.set_power_level(200.0, 100.0, 100.0, 98.0)
        
        data = module.collect_data()
        assert 195 < data.current_power < 205
        assert 97 < data.solar_power < 103


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
        data = PowerGenerationData(
            timestamp=datetime.now(),
            current_power=150.0,
            solar_power=100.0,
            wind_power=50.0,
            efficiency=95.0,
            device_status="running"
        )
        
        result = service._send_report(data)
        assert result is True
        assert mock_post.call_count == 2

    @patch('requests.post')
    def test_retry_exhaustion(self, mock_post):
        """Test retry exhaustion after max attempts."""
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        service = DataReportingService(max_retries=3)
        data = PowerGenerationData(
            timestamp=datetime.now(),
            current_power=150.0,
            solar_power=100.0,
            wind_power=50.0,
            efficiency=95.0,
            device_status="running"
        )
        
        # tenacity wraps the exception in RetryError
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
        
        module = PowerGenerationModule(report_interval=1)
        module.start()
        
        # Let it run for a bit
        time.sleep(2.5)
        module.stop()
        
        # Should have reported at least twice
        assert module.reporting_service.report_count >= 2

    @patch('requests.post')
    def test_reporting_with_varying_data(self, mock_post):
        """Test reporting with varying power levels."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        module = PowerGenerationModule()
        
        # Report with different power levels
        module.set_power_level(100.0, 50.0, 50.0, 95.0)
        module.report_data()
        
        module.set_power_level(200.0, 100.0, 100.0, 98.0)
        module.report_data()
        
        module.set_power_level(150.0, 75.0, 75.0, 96.0)
        module.report_data()
        
        assert module.reporting_service.report_count == 3

    def test_module_error_handling(self):
        """Test module error handling."""
        module = PowerGenerationModule(vcc_url="http://invalid-url:9999")
        
        # Should handle connection errors gracefully
        result = module.report_data()
        assert result is False
        assert module.reporting_service.failed_report_count == 1
