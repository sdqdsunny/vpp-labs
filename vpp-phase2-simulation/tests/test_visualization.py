"""
Unit tests for Visualization and Monitoring Dashboard

Tests dashboard endpoints, real-time data aggregation, and response optimization.

Requirements: 12.1, 12.2, 12.3, 12.4, 12.5
"""

import json
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from bottle import Bottle
from webtest import TestApp

from routes.visualization import create_visualization_routes
from models.device_state import DeviceState
from models.scenario import Scenario
from models.metrics import Metric
from models.power_flow_result import PowerFlowResult


@pytest.fixture
def app():
    """Create test Bottle app with visualization routes."""
    app = Bottle()
    create_visualization_routes(app)
    return app


@pytest.fixture
def test_client(app):
    """Create test client for Bottle app."""
    return TestApp(app)


@pytest.fixture
def mock_session():
    """Create mock database session."""
    return Mock()


class TestDashboardStatus:
    """Tests for dashboard status endpoint."""
    
    def test_get_dashboard_status_idle(self, test_client, mock_session):
        """Test dashboard status when no scenarios are running."""
        with patch('routes.visualization.request') as mock_request:
            mock_request.db = mock_session
            mock_session.query.return_value.filter.return_value.all.return_value = []
            
            response = test_client.get('/api/dashboard/status')
            
            assert response.status_code == 200
            data = response.json
            assert data["status"] == "idle"
            assert data["device_count"] == 0
            assert "timestamp" in data


class TestDashboardMetrics:
    """Tests for dashboard metrics endpoint."""
    
    def test_get_dashboard_metrics_no_scenario(self, test_client, mock_session):
        """Test metrics endpoint when no scenarios are running."""
        with patch('routes.visualization.request') as mock_request:
            mock_request.db = mock_session
            mock_request.query.get.side_effect = lambda x, default="": default
            
            scenario_query = Mock()
            scenario_query.filter.return_value.first.return_value = None
            mock_session.query.return_value = scenario_query
            
            response = test_client.get('/api/dashboard/metrics', status=200)
            
            assert response.status_code == 200
            data = response.json
            assert "metrics" in data
            assert "timestamp" in data


class TestDashboardDevices:
    """Tests for dashboard devices endpoint."""
    
    def test_get_dashboard_devices_empty(self, test_client, mock_session):
        """Test devices endpoint with no devices."""
        with patch('routes.visualization.request') as mock_request:
            mock_request.db = mock_session
            mock_request.query.get.side_effect = lambda x, default="": default
            
            scenario_query = Mock()
            scenario_query.filter.return_value.first.return_value = None
            
            device_query = Mock()
            device_query.filter.return_value.all.return_value = []
            
            def query_side_effect(model):
                if model == Scenario:
                    return scenario_query
                elif model == DeviceState:
                    return device_query
                return Mock()
            
            mock_session.query.side_effect = query_side_effect
            
            response = test_client.get('/api/dashboard/devices', status=200)
            
            assert response.status_code == 200
            data = response.json
            assert data["devices"] == []


class TestDashboardPowerFlows:
    """Tests for dashboard power flows endpoint."""
    
    def test_get_dashboard_power_flows_no_data(self, test_client, mock_session):
        """Test power flows endpoint with no data."""
        with patch('routes.visualization.request') as mock_request:
            mock_request.db = mock_session
            mock_request.query.get.side_effect = lambda x, default="": default
            
            scenario_query = Mock()
            scenario_query.filter.return_value.first.return_value = None
            
            pf_query = Mock()
            pf_query.filter.return_value.order_by.return_value.first.return_value = None
            
            def query_side_effect(model):
                if model == Scenario:
                    return scenario_query
                elif model == PowerFlowResult:
                    return pf_query
                return Mock()
            
            mock_session.query.side_effect = query_side_effect
            
            response = test_client.get('/api/dashboard/power-flows')
            
            assert response.status_code == 200
            data = response.json
            assert data["power_flows"] == []
            assert data["violations"] == []


class TestDashboardAlerts:
    """Tests for dashboard alerts endpoint."""
    
    def test_get_dashboard_alerts_no_violations(self, test_client, mock_session):
        """Test alerts endpoint with no violations."""
        with patch('routes.visualization.request') as mock_request:
            mock_request.db = mock_session
            mock_request.query.get.side_effect = lambda x, default="": default
            
            scenario_query = Mock()
            scenario_query.filter.return_value.first.return_value = None
            
            pf_query = Mock()
            pf_query.filter.return_value.order_by.return_value.first.return_value = None
            
            def query_side_effect(model):
                if model == Scenario:
                    return scenario_query
                elif model == PowerFlowResult:
                    return pf_query
                return Mock()
            
            mock_session.query.side_effect = query_side_effect
            
            response = test_client.get('/api/dashboard/alerts', status=200)
            
            assert response.status_code == 200
            data = response.json
            assert "alerts" in data


class TestDashboardResults:
    """Tests for dashboard results endpoint."""
    
    def test_get_dashboard_results_missing_scenario_id(self, test_client, mock_session):
        """Test results endpoint without scenario_id."""
        with patch('routes.visualization.request') as mock_request:
            mock_request.db = mock_session
            mock_request.query.get.return_value = None
            
            response = test_client.get('/api/dashboard/results', status=400)
            
            assert response.status_code == 400
    
    def test_get_dashboard_results_scenario_not_found(self, test_client, mock_session):
        """Test results endpoint with non-existent scenario."""
        with patch('routes.visualization.request') as mock_request:
            mock_request.db = mock_session
            mock_request.query.get.return_value = "scenario-999"
            
            scenario_query = Mock()
            scenario_query.filter.return_value.first.return_value = None
            mock_session.query.return_value = scenario_query
            
            response = test_client.get('/api/dashboard/results?scenario_id=scenario-999', status=404)
            
            assert response.status_code == 404


class TestDashboardResponseTime:
    """Tests for dashboard response time optimization."""
    
    def test_dashboard_status_response_time(self, test_client, mock_session):
        """Test dashboard status response time is under 500ms."""
        import time
        
        with patch('routes.visualization.request') as mock_request:
            mock_request.db = mock_session
            mock_session.query.return_value.filter.return_value.all.return_value = []
            
            start_time = time.time()
            response = test_client.get('/api/dashboard/status')
            elapsed_time = (time.time() - start_time) * 1000
            
            assert elapsed_time < 500
            assert response.status_code == 200
    
    def test_dashboard_metrics_response_time(self, test_client, mock_session):
        """Test dashboard metrics response time is under 500ms."""
        import time
        
        with patch('routes.visualization.request') as mock_request:
            mock_request.db = mock_session
            mock_request.query.get.side_effect = lambda x, default="": default
            
            scenario_query = Mock()
            scenario_query.filter.return_value.first.return_value = None
            mock_session.query.return_value = scenario_query
            
            start_time = time.time()
            response = test_client.get('/api/dashboard/metrics')
            elapsed_time = (time.time() - start_time) * 1000
            
            assert elapsed_time < 500
            assert response.status_code == 200


class TestDashboardDataCompleteness:
    """Tests for dashboard data completeness."""
    
    def test_dashboard_status_includes_all_fields(self, test_client, mock_session):
        """Test dashboard status includes all required fields."""
        with patch('routes.visualization.request') as mock_request:
            mock_request.db = mock_session
            mock_session.query.return_value.filter.return_value.all.return_value = []
            
            response = test_client.get('/api/dashboard/status')
            data = response.json
            
            assert "status" in data
            assert "device_count" in data
            assert "devices" in data
            assert "power_flows" in data
            assert "alerts" in data
            assert "timestamp" in data
    
    def test_dashboard_devices_includes_all_fields(self, test_client, mock_session):
        """Test dashboard devices includes all required fields."""
        with patch('routes.visualization.request') as mock_request:
            mock_request.db = mock_session
            mock_request.query.get.side_effect = lambda x, default="": default
            
            scenario_query = Mock()
            scenario_query.filter.return_value.first.return_value = None
            
            device_query = Mock()
            device_query.filter.return_value.all.return_value = []
            
            def query_side_effect(model):
                if model == Scenario:
                    return scenario_query
                elif model == DeviceState:
                    return device_query
                return Mock()
            
            mock_session.query.side_effect = query_side_effect
            
            response = test_client.get('/api/dashboard/devices')
            data = response.json
            
            assert "devices" in data
            assert "timestamp" in data
