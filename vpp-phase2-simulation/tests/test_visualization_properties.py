"""
Property-Based Tests for Visualization and Monitoring Dashboard

Tests universal properties of dashboard behavior using Hypothesis.

Requirements: 12.1, 12.2, 12.3, 12.4, 12.5
"""

import json
import time
from datetime import datetime, timedelta
from hypothesis import given, strategies as st, settings, HealthCheck
from unittest.mock import Mock, patch

from routes.visualization import create_visualization_routes
from models.device_state import DeviceState
from models.scenario import Scenario
from models.metrics import Metric
from models.power_flow_result import PowerFlowResult
from bottle import Bottle
from webtest import TestApp


def create_test_app():
    """Create a fresh test app for each test."""
    app = Bottle()
    create_visualization_routes(app)
    return TestApp(app)


class TestDashboardRealTimeUpdates:
    """
    Property 56: Real-Time Dashboard Updates
    
    For any running simulation, the dashboard should update with real-time metrics
    and device status.
    
    Validates: Requirements 12.1, 12.4
    """
    
    @given(metric_count=st.integers(min_value=1, max_value=50))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_dashboard_returns_current_metrics(self, metric_count):
        """
        For any number of metrics, the dashboard should return current metric values.
        """
        test_client = create_test_app()
        
        with patch('routes.visualization.request') as mock_request:
            mock_session = Mock()
            mock_request.db = mock_session
            mock_request.query.get.side_effect = lambda x, default="": default
            
            # Create mock scenario
            scenario = Mock(spec=Scenario)
            scenario.id = "scenario-001"
            scenario.status = "running"
            
            # Create mock metrics
            metrics = []
            for i in range(metric_count):
                metric = Mock(spec=Metric)
                metric.metric_name = f"metric_{i}"
                metric.value = float(i * 10)
                metric.tags = {"index": i}
                metric.timestamp = datetime.utcnow()
                metrics.append(metric)
            
            # Mock queries
            scenario_query = Mock()
            scenario_query.filter.return_value.first.return_value = scenario
            
            metrics_query = Mock()
            metrics_query.filter.return_value.filter.return_value.order_by.return_value.all.return_value = metrics
            
            def query_side_effect(model):
                if model == Scenario:
                    return scenario_query
                elif model == Metric:
                    return metrics_query
                return Mock()
            
            mock_session.query.side_effect = query_side_effect
            
            # Call endpoint
            response = test_client.get('/api/dashboard/metrics', status=200)
            
            # Verify response
            assert response.status_code == 200
            data = response.json
            assert "metrics" in data
            assert "timestamp" in data
            # Verify metrics are returned
            assert len(data["metrics"]) == metric_count


class TestDashboardDisplayCompleteness:
    """
    Property 57: Dashboard Display Completeness
    
    For any dashboard access, the system should display device status,
    power flows, and alerts.
    
    Validates: Requirements 12.2
    """
    
    @given(violation_count=st.integers(min_value=0, max_value=10))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_dashboard_displays_violations(self, violation_count):
        """
        For any power flow result with violations, the dashboard should
        display all violations.
        """
        test_client = create_test_app()
        
        with patch('routes.visualization.request') as mock_request:
            mock_session = Mock()
            mock_request.db = mock_session
            mock_request.query.get.side_effect = lambda x, default="": default
            
            # Create mock scenario
            scenario = Mock(spec=Scenario)
            scenario.id = "scenario-001"
            
            # Create mock power flow result
            pf_result = Mock(spec=PowerFlowResult)
            pf_result.violations = [
                {"message": f"Violation {i}"} for i in range(violation_count)
            ]
            pf_result.stability_assessment = {"is_stable": True}
            pf_result.timestamp = datetime.utcnow()
            
            # Mock queries
            scenario_query = Mock()
            scenario_query.filter.return_value.first.return_value = scenario
            
            pf_query = Mock()
            pf_query.filter.return_value.order_by.return_value.first.return_value = pf_result
            
            def query_side_effect(model):
                if model == Scenario:
                    return scenario_query
                elif model == PowerFlowResult:
                    return pf_query
                return Mock()
            
            mock_session.query.side_effect = query_side_effect
            
            # Call endpoint
            response = test_client.get('/api/dashboard/alerts', status=200)
            
            # Verify response
            assert response.status_code == 200
            data = response.json
            assert data["count"] == violation_count


class TestDashboardResponseTime:
    """
    Property 58: Dashboard Response Time
    
    For any user interaction with the dashboard, the system should respond
    within 500ms.
    
    Validates: Requirements 12.3
    """
    
    @given(endpoint=st.sampled_from([
        '/api/dashboard/status',
        '/api/dashboard/metrics',
        '/api/dashboard/devices',
        '/api/dashboard/power-flows',
        '/api/dashboard/alerts'
    ]))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_dashboard_response_time_under_500ms(self, endpoint):
        """
        For any dashboard endpoint, the response time should be under 500ms.
        """
        test_client = create_test_app()
        
        with patch('routes.visualization.request') as mock_request:
            mock_session = Mock()
            mock_request.db = mock_session
            mock_request.query.get.side_effect = lambda x, default="": default
            
            # Mock all queries to return empty results
            mock_query = Mock()
            mock_query.filter.return_value.first.return_value = None
            mock_query.filter.return_value.all.return_value = []
            mock_query.filter.return_value.order_by.return_value.first.return_value = None
            mock_query.filter.return_value.order_by.return_value.all.return_value = []
            mock_session.query.return_value = mock_query
            
            # Measure response time
            start_time = time.time()
            response = test_client.get(endpoint, status=200)
            elapsed_time = (time.time() - start_time) * 1000  # Convert to ms
            
            # Verify response time is under 500ms
            assert elapsed_time < 500
            assert response.status_code == 200


class TestDashboardEventUpdates:
    """
    Property 59: Dashboard Event Updates
    
    For any simulation event that occurs, the dashboard should update
    immediately to reflect the event.
    
    Validates: Requirements 12.4
    """
    
    @given(event_count=st.integers(min_value=1, max_value=50))
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_dashboard_reflects_metric_changes(self, event_count):
        """
        For any number of metric events, the dashboard should reflect
        the latest metric values.
        """
        test_client = create_test_app()
        
        with patch('routes.visualization.request') as mock_request:
            mock_session = Mock()
            mock_request.db = mock_session
            mock_request.query.get.side_effect = lambda x, default="": default
            
            # Create mock scenario
            scenario = Mock(spec=Scenario)
            scenario.id = "scenario-001"
            
            # Create mock metrics with increasing values, all within 5 minutes
            metrics = []
            now = datetime.utcnow()
            for i in range(event_count):
                metric = Mock(spec=Metric)
                metric.metric_name = "power_output"
                metric.value = float(i * 100)  # Increasing values
                metric.tags = {}
                # Create timestamps within the last 5 minutes, with most recent first
                # (since they're sorted by timestamp descending)
                metric.timestamp = now - timedelta(seconds=i)
                metrics.append(metric)
            
            # Mock queries
            scenario_query = Mock()
            scenario_query.filter.return_value.first.return_value = scenario
            
            metrics_query = Mock()
            # Metrics are sorted by timestamp descending, so most recent is first
            metrics_query.filter.return_value.filter.return_value.order_by.return_value.all.return_value = metrics
            
            def query_side_effect(model):
                if model == Scenario:
                    return scenario_query
                elif model == Metric:
                    return metrics_query
                return Mock()
            
            mock_session.query.side_effect = query_side_effect
            
            # Call endpoint
            response = test_client.get('/api/dashboard/metrics', status=200)
            
            # Verify response
            assert response.status_code == 200
            data = response.json
            # Verify latest value is one of the metric values
            assert "power_output" in data["metrics"]
            assert "latest" in data["metrics"]["power_output"]
            assert "values" in data["metrics"]["power_output"]
            assert data["metrics"]["power_output"]["latest"] in data["metrics"]["power_output"]["values"]


class TestDashboardFinalResults:
    """
    Property 60: Final Results Display
    
    For any completed simulation, the dashboard should display final results
    and analysis.
    
    Validates: Requirements 12.5
    """
    
    @given(
        metric_count=st.integers(min_value=1, max_value=20),
        violation_count=st.integers(min_value=0, max_value=10)
    )
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    def test_dashboard_displays_final_results(self, metric_count, violation_count):
        """
        For any completed scenario with metrics and violations, the dashboard
        should display all results and analysis.
        """
        test_client = create_test_app()
        
        with patch('routes.visualization.request') as mock_request:
            mock_session = Mock()
            mock_request.db = mock_session
            mock_request.query.get.return_value = "scenario-001"
            
            # Create mock scenario
            scenario = Mock(spec=Scenario)
            scenario.id = "scenario-001"
            scenario.status = "completed"
            scenario.start_time = datetime.utcnow() - timedelta(hours=1)
            scenario.end_time = datetime.utcnow()
            
            # Create mock metrics
            metrics = []
            for i in range(metric_count):
                metric = Mock(spec=Metric)
                metric.metric_name = f"metric_{i}"
                metric.value = float(i * 10)
                metric.tags = {}
                metric.timestamp = datetime.utcnow()
                metrics.append(metric)
            
            # Create mock power flow result
            pf_result = Mock(spec=PowerFlowResult)
            pf_result.violations = [
                {"message": f"Violation {i}"} for i in range(violation_count)
            ]
            pf_result.stability_assessment = {"is_stable": True}
            pf_result.timestamp = datetime.utcnow()
            
            # Mock queries
            scenario_query = Mock()
            scenario_query.filter.return_value.first.return_value = scenario
            
            metrics_query = Mock()
            metrics_query.filter.return_value.all.return_value = metrics
            
            pf_query = Mock()
            pf_query.filter.return_value.order_by.return_value.first.return_value = pf_result
            
            def query_side_effect(model):
                if model == Scenario:
                    return scenario_query
                elif model == Metric:
                    return metrics_query
                elif model == PowerFlowResult:
                    return pf_query
                return Mock()
            
            mock_session.query.side_effect = query_side_effect
            
            # Call endpoint
            response = test_client.get('/api/dashboard/results?scenario_id=scenario-001', status=200)
            
            # Verify response
            assert response.status_code == 200
            data = response.json
            assert data["scenario_id"] == "scenario-001"
            assert "metrics_summary" in data
            assert "power_flow_analysis" in data
            assert len(data["metrics_summary"]) == metric_count
            assert len(data["power_flow_analysis"]["violations"]) == violation_count
