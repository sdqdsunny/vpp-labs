"""
Unit tests for Demand Module.

Tests:
- Data collection service
- Data reporting service with retry logic
- Demand module integration
- Error handling
"""

import pytest
import time
import json
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
import requests

from models.realtime_data_models import DemandData
from services.demand_module import (
    DataCollectionService, DataReportingService, DemandModule
)


class TestDataCollectionService:
    """Test data collection service."""

    def test_initialization(self):
        """Test service initialization."""
        service = DataCollectionService()
        assert service.device_id == "vpp-demand"
        assert service.current_load == 100.0
        assert service.forecast_load == 110.0
        assert service.adjustable_range == (80.0, 120.0)
        assert service.dr_status == "inactive"

    def test_collect_data_returns_valid_data(self):
        """Test that collect_data returns valid DemandData."""
        service = DataCollectionService()
        data = service.collect_data()
        
        assert isinstance(data, DemandData)
        assert isinstance(data.timestamp, datetime)
        assert isinstance(data.current_load, float)
        assert isinstance(data.forecast_load, float)
        assert isinstance(data.adjustable_range, tuple)
        assert isinstance(data.dr_status, str)

    def test_collect_data_values_in_valid_range(self):
        """Test that collected data values are in valid ranges."""
        service = DataCollectionService()
        data = service.collect_data()
        
        assert data.current_load >= 0
        assert data.forecast_load >= 0
        assert data.adjustable_range[0] <= data.adjustable_range[1]
        assert data.dr_status in ["active", "inactive"]

    def test_collect_data_multiple_times(self):
        """Test collecting data multiple times."""
        service = DataCollectionService()
        data_list = [service.collect_data() for _ in range(5)]
        
        assert len(data_list) == 5
        # Values should vary slightly
        loads = [d.current_load for d in data_list]
        assert len(set(loads)) > 1  # Not all the same

    def test_set_demand_level(self):
        """Test setting demand levels."""
        service = DataCollectionService()
        service.set_demand_level(120.0, 130.0, 100.0, 150.0, "active")
        
        assert service.current_load == 120.0
        assert service.forecast_load == 130.0
        assert service.adjustable_range == (100.0, 150.0)
        assert service.dr_status == "active"

    def test_collect_data_after_set_demand_level(self):
        """Test collecting data after setting demand levels."""
        service = DataCollectionService()
        service.set_demand_level(120.0, 130.0, 100.0, 150.0, "active")
        data = service.collect_data()
        
        # Values should be close to set values (with small variations)
        assert 115 < data.current_load < 125
        assert 120 < data.forecast_load < 140
        assert data.dr_status == "active"


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
        data = DemandData(
            timestamp=datetime.now(),
            current_load=100.0,
            forecast_load=110.0,
            adjustable_range=(80.0, 120.0),
            dr_status="inactive"
        )
        
        result = service._send_report(data)
        assert result is True
        mock_post.assert_called_once()

    @patch('requests.post')
    def test_send_report_failure(self, mock_post):
        """Test failed data reporting."""
        mock_post.side_effect = requests.exceptions.RequestException("Connection error")
        
        service = DataReportingService()
        data = DemandData(
            timestamp=datetime.now(),
            current_load=100.0,
            forecast_load=110.0,
            adjustable_range=(80.0, 120.0),
            dr_status="inactive"
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


class TestDemandModule:
    """Test demand module."""

    def test_initialization(self):
        """Test module initialization."""
        module = DemandModule()
        assert module.vcc_url == "http://localhost:8080"
        assert module.report_interval == 5
        assert module.collection_service is not None
        assert module.reporting_service is not None

    def test_initialization_with_custom_params(self):
        """Test module initialization with custom parameters."""
        module = DemandModule(
            vcc_url="http://vcc-master:8080",
            report_interval=10
        )
        assert module.vcc_url == "http://vcc-master:8080"
        assert module.report_interval == 10

    def test_collect_data(self):
        """Test collecting data through module."""
        module = DemandModule()
        data = module.collect_data()
        
        assert isinstance(data, DemandData)
        assert data.current_load >= 0
        assert data.forecast_load >= 0
        assert data.adjustable_range[0] <= data.adjustable_range[1]

    @patch('requests.post')
    def test_report_data(self, mock_post):
        """Test reporting data through module."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        module = DemandModule()
        result = module.report_data()
        
        assert result is True

    @patch('requests.post')
    def test_start_and_stop(self, mock_post):
        """Test starting and stopping the module."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        module = DemandModule(report_interval=1)
        module.start()
        assert module.reporting_service.is_running is True
        
        time.sleep(0.5)
        module.stop()
        assert module.reporting_service.is_running is False

    def test_get_stats(self):
        """Test getting module statistics."""
        module = DemandModule()
        stats = module.get_stats()
        
        assert "module" in stats
        assert stats["module"] == "demand"
        assert "vcc_url" in stats
        assert "report_interval" in stats
        assert "reporting_stats" in stats

    def test_set_demand_level(self):
        """Test setting demand levels through module."""
        module = DemandModule()
        module.set_demand_level(120.0, 130.0, 100.0, 150.0, "active")
        
        data = module.collect_data()
        assert 115 < data.current_load < 125
        assert 120 < data.forecast_load < 140


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
        data = DemandData(
            timestamp=datetime.now(),
            current_load=100.0,
            forecast_load=110.0,
            adjustable_range=(80.0, 120.0),
            dr_status="inactive"
        )
        
        result = service._send_report(data)
        assert result is True
        assert mock_post.call_count == 2

    @patch('requests.post')
    def test_retry_exhaustion(self, mock_post):
        """Test retry exhaustion after max attempts."""
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        service = DataReportingService(max_retries=3)
        data = DemandData(
            timestamp=datetime.now(),
            current_load=100.0,
            forecast_load=110.0,
            adjustable_range=(80.0, 120.0),
            dr_status="inactive"
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
        
        module = DemandModule(report_interval=1)
        module.start()
        
        # Let it run for a bit
        time.sleep(2.5)
        module.stop()
        
        # Should have reported at least twice
        assert module.reporting_service.report_count >= 2

    @patch('requests.post')
    def test_reporting_with_varying_data(self, mock_post):
        """Test reporting with varying demand levels."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        module = DemandModule()
        
        # Report with different demand levels
        module.set_demand_level(80.0, 90.0, 70.0, 100.0, "inactive")
        module.report_data()
        
        module.set_demand_level(100.0, 110.0, 80.0, 120.0, "active")
        module.report_data()
        
        module.set_demand_level(120.0, 130.0, 100.0, 150.0, "active")
        module.report_data()
        
        assert module.reporting_service.report_count == 3

    def test_module_error_handling(self):
        """Test module error handling."""
        module = DemandModule(vcc_url="http://invalid-url:9999")
        
        # Should handle connection errors gracefully
        result = module.report_data()
        assert result is False
        assert module.reporting_service.failed_report_count == 1


class TestDemandDataValidation:
    """Test demand data validation."""

    def test_current_load_boundary_values(self):
        """Test current load boundary values."""
        service = DataCollectionService()
        service.set_demand_level(0.0, 110.0, 80.0, 120.0, "inactive")
        data = service.collect_data()
        assert data.current_load >= 0
        
        service.set_demand_level(200.0, 110.0, 80.0, 120.0, "inactive")
        data = service.collect_data()
        assert data.current_load >= 0

    def test_forecast_load_boundary_values(self):
        """Test forecast load boundary values."""
        service = DataCollectionService()
        service.set_demand_level(100.0, 0.0, 80.0, 120.0, "inactive")
        data = service.collect_data()
        assert data.forecast_load >= 0
        
        service.set_demand_level(100.0, 200.0, 80.0, 120.0, "inactive")
        data = service.collect_data()
        assert data.forecast_load >= 0

    def test_adjustable_range_values(self):
        """Test adjustable range values."""
        service = DataCollectionService()
        service.set_demand_level(100.0, 110.0, 50.0, 150.0, "inactive")
        data = service.collect_data()
        assert data.adjustable_range[0] <= data.adjustable_range[1]

    def test_dr_status_values(self):
        """Test DR status values."""
        service = DataCollectionService()
        for status in ["active", "inactive"]:
            service.set_demand_level(100.0, 110.0, 80.0, 120.0, status)
            data = service.collect_data()
            assert data.dr_status in ["active", "inactive"]
