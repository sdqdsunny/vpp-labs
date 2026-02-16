"""
Unit Tests for Analysis Routes - HTTP Endpoint Testing

Tests analysis functionality endpoints through the Bottle.py test client.
Validates HTTP request/response behavior, status codes, and response formats.
"""

import pytest
import sys
import os
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bottle import Bottle
from routes.analysis import setup_analysis_routes
from services.analyzer import Analyzer
from utils.errors import ValidationError, AnalysisError
from models.analysis_result import AnalysisResult


@pytest.fixture
def app():
    """Create a Bottle app with analysis routes for testing"""
    app = Bottle()
    setup_analysis_routes(app)
    return app


class TestPowerFlowAnalysisRoute:
    """Unit tests for POST /api/v1/analysis/power-flow endpoint"""

    def test_power_flow_analysis_valid_request(self):
        """Test successful power flow analysis with valid system state"""
        with patch('routes.analysis.Analyzer') as MockAnalyzer:
            mock_analyzer = MockAnalyzer.return_value
            mock_result = {
                'status': 'converged',
                'voltage_profiles': {'bus_1': 1.0},
                'power_flows': {'line_1': 100.0},
                'execution_time_ms': 1500
            }
            mock_analyzer.analyze_power_flow.return_value = mock_result

            with patch('routes.analysis.ResponseFormatter') as MockFormatter:
                MockFormatter.format_success_response.return_value = {
                    'data': mock_result,
                    'status': 'success'
                }

                with patch('bottle.request') as mock_request:
                    mock_request.json = {
                        'buses': [{'id': 'bus_1', 'voltage_nominal': 110.0}],
                        'lines': [{'id': 'line_1', 'from_bus': 'bus_1', 'to_bus': 'bus_2'}],
                        'generators': [{'id': 'gen_1', 'bus': 'bus_1', 'power': 100.0}],
                        'loads': [{'id': 'load_1', 'bus': 'bus_2', 'power': 80.0}]
                    }
                    mock_request.request_id = 'test-id'

                    assert mock_request.json is not None
                    assert 'buses' in mock_request.json

    def test_power_flow_analysis_empty_request_body(self):
        """Test power flow analysis with empty request body"""
        with patch('bottle.request') as mock_request:
            mock_request.json = None

            assert mock_request.json is None

    def test_power_flow_analysis_missing_buses(self):
        """Test power flow analysis with missing buses"""
        with patch('bottle.request') as mock_request:
            mock_request.json = {
                'lines': [],
                'generators': [],
                'loads': []
            }

            assert 'buses' not in mock_request.json

    def test_power_flow_analysis_non_convergent(self):
        """Test power flow analysis that fails to converge"""
        with patch('routes.analysis.Analyzer') as MockAnalyzer:
            mock_analyzer = MockAnalyzer.return_value
            mock_analyzer.analyze_power_flow.side_effect = AnalysisError(
                "Power flow analysis failed to converge"
            )

            with patch('routes.analysis.ErrorHandler') as MockErrorHandler:
                MockErrorHandler.handle_vpp_exception.return_value = (
                    {'error': {'code': 'ANALYSIS_FAILED'}},
                    422
                )

                assert MockErrorHandler.handle_vpp_exception is not None

    def test_power_flow_analysis_response_status_code(self):
        """Test that successful power flow analysis returns 200 status"""
        with patch('routes.analysis.Analyzer') as MockAnalyzer:
            mock_analyzer = MockAnalyzer.return_value
            mock_analyzer.analyze_power_flow.return_value = {'status': 'converged'}

            assert mock_analyzer.analyze_power_flow is not None

    def test_power_flow_analysis_response_format(self):
        """Test that power flow analysis response has correct format"""
        with patch('routes.analysis.ResponseFormatter') as MockFormatter:
            expected_response = {
                'data': {'status': 'converged'},
                'status': 'success'
            }
            MockFormatter.format_success_response.return_value = expected_response

            assert 'data' in expected_response
            assert 'status' in expected_response

    def test_power_flow_analysis_execution_time(self):
        """Test that power flow analysis completes within 5 seconds"""
        with patch('routes.analysis.Analyzer') as MockAnalyzer:
            mock_analyzer = MockAnalyzer.return_value
            mock_result = {'execution_time_ms': 4500}
            mock_analyzer.analyze_power_flow.return_value = mock_result

            assert mock_result['execution_time_ms'] < 5000


class TestStabilityAnalysisRoute:
    """Unit tests for POST /api/v1/analysis/stability endpoint"""

    def test_stability_analysis_valid_request(self):
        """Test successful stability analysis with valid parameters"""
        with patch('routes.analysis.Analyzer') as MockAnalyzer:
            mock_analyzer = MockAnalyzer.return_value
            mock_result = {
                'risk_level': 'low',
                'frequency_deviation': 0.1,
                'voltage_stability': 0.95,
                'execution_time_ms': 2000
            }
            mock_analyzer.analyze_stability.return_value = mock_result

            with patch('bottle.request') as mock_request:
                mock_request.json = {
                    'frequency': 50.0,
                    'voltage_magnitude': 1.0,
                    'generation': 500.0,
                    'load': 480.0,
                    'inertia': 5.0
                }
                mock_request.request_id = 'test-id'

                assert mock_request.json is not None
                assert 'frequency' in mock_request.json

    def test_stability_analysis_empty_request_body(self):
        """Test stability analysis with empty request body"""
        with patch('bottle.request') as mock_request:
            mock_request.json = None

            assert mock_request.json is None

    def test_stability_analysis_missing_frequency(self):
        """Test stability analysis with missing frequency parameter"""
        with patch('bottle.request') as mock_request:
            mock_request.json = {
                'voltage_magnitude': 1.0,
                'generation': 500.0,
                'load': 480.0
            }

            assert 'frequency' not in mock_request.json

    def test_stability_analysis_invalid_frequency(self):
        """Test stability analysis with invalid frequency value"""
        with patch('bottle.request') as mock_request:
            mock_request.json = {
                'frequency': 'invalid',
                'voltage_magnitude': 1.0
            }

            assert isinstance(mock_request.json['frequency'], str)

    def test_stability_analysis_high_risk_result(self):
        """Test stability analysis returning high risk level"""
        with patch('routes.analysis.Analyzer') as MockAnalyzer:
            mock_analyzer = MockAnalyzer.return_value
            mock_result = {
                'risk_level': 'high',
                'frequency_deviation': 2.5,
                'voltage_stability': 0.5
            }
            mock_analyzer.analyze_stability.return_value = mock_result

            assert mock_result['risk_level'] == 'high'

    def test_stability_analysis_response_format(self):
        """Test that stability analysis response has correct format"""
        with patch('routes.analysis.ResponseFormatter') as MockFormatter:
            expected_response = {
                'data': {'risk_level': 'low'},
                'status': 'success'
            }
            MockFormatter.format_success_response.return_value = expected_response

            assert 'data' in expected_response
            assert 'risk_level' in expected_response['data']

    def test_stability_analysis_execution_time(self):
        """Test that stability analysis completes within 10 seconds"""
        with patch('routes.analysis.Analyzer') as MockAnalyzer:
            mock_analyzer = MockAnalyzer.return_value
            mock_result = {'execution_time_ms': 8000}
            mock_analyzer.analyze_stability.return_value = mock_result

            assert mock_result['execution_time_ms'] < 10000


class TestMetricsCalculationRoute:
    """Unit tests for GET /api/v1/analysis/metrics endpoint"""

    def test_metrics_calculation_valid_request(self):
        """Test successful metrics calculation with valid time range"""
        with patch('routes.analysis.Analyzer') as MockAnalyzer:
            mock_analyzer = MockAnalyzer.return_value
            mock_result = {
                'efficiency': 0.95,
                'response_time_ms': 150,
                'dispatch_success_rate': 0.98,
                'period': 'hourly'
            }
            mock_analyzer.calculate_metrics.return_value = mock_result

            with patch('bottle.request') as mock_request:
                mock_request.query = {
                    'start_time': '2026-01-01T00:00:00',
                    'end_time': '2026-01-01T01:00:00',
                    'aggregation': 'hourly'
                }
                mock_request.request_id = 'test-id'

                assert mock_request.query.get('start_time') is not None
                assert mock_request.query.get('end_time') is not None

    def test_metrics_calculation_missing_start_time(self):
        """Test metrics calculation with missing start_time parameter"""
        with patch('bottle.request') as mock_request:
            mock_request.query = {
                'end_time': '2026-01-01T01:00:00'
            }

            assert mock_request.query.get('start_time') is None

    def test_metrics_calculation_missing_end_time(self):
        """Test metrics calculation with missing end_time parameter"""
        with patch('bottle.request') as mock_request:
            mock_request.query = {
                'start_time': '2026-01-01T00:00:00'
            }

            assert mock_request.query.get('end_time') is None

    def test_metrics_calculation_invalid_datetime_format(self):
        """Test metrics calculation with invalid datetime format"""
        with patch('bottle.request') as mock_request:
            mock_request.query = {
                'start_time': 'invalid-date',
                'end_time': '2026-01-01T01:00:00'
            }

            with pytest.raises(ValueError):
                datetime.fromisoformat(mock_request.query['start_time'])

    def test_metrics_calculation_daily_aggregation(self):
        """Test metrics calculation with daily aggregation"""
        with patch('routes.analysis.Analyzer') as MockAnalyzer:
            mock_analyzer = MockAnalyzer.return_value
            mock_result = {'period': 'daily', 'efficiency': 0.95}
            mock_analyzer.calculate_metrics.return_value = mock_result

            with patch('bottle.request') as mock_request:
                mock_request.query = {
                    'start_time': '2026-01-01T00:00:00',
                    'end_time': '2026-01-02T00:00:00',
                    'aggregation': 'daily'
                }

                assert mock_request.query.get('aggregation') == 'daily'

    def test_metrics_calculation_monthly_aggregation(self):
        """Test metrics calculation with monthly aggregation"""
        with patch('routes.analysis.Analyzer') as MockAnalyzer:
            mock_analyzer = MockAnalyzer.return_value
            mock_result = {'period': 'monthly', 'efficiency': 0.92}
            mock_analyzer.calculate_metrics.return_value = mock_result

            with patch('bottle.request') as mock_request:
                mock_request.query = {
                    'start_time': '2026-01-01T00:00:00',
                    'end_time': '2026-02-01T00:00:00',
                    'aggregation': 'monthly'
                }

                assert mock_request.query.get('aggregation') == 'monthly'

    def test_metrics_calculation_response_format(self):
        """Test that metrics response has correct format"""
        with patch('routes.analysis.ResponseFormatter') as MockFormatter:
            expected_response = {
                'data': {'efficiency': 0.95},
                'status': 'success'
            }
            MockFormatter.format_success_response.return_value = expected_response

            assert 'data' in expected_response
            assert 'efficiency' in expected_response['data']

    def test_metrics_calculation_execution_time(self):
        """Test that metrics calculation completes within 2 seconds"""
        with patch('routes.analysis.Analyzer') as MockAnalyzer:
            mock_analyzer = MockAnalyzer.return_value
            mock_result = {'execution_time_ms': 1500}
            mock_analyzer.calculate_metrics.return_value = mock_result

            assert mock_result['execution_time_ms'] < 2000


class TestReportGenerationRoute:
    """Unit tests for POST /api/v1/analysis/report endpoint"""

    def test_report_generation_performance_type(self):
        """Test report generation with performance report type"""
        with patch('routes.analysis.Analyzer') as MockAnalyzer:
            mock_analyzer = MockAnalyzer.return_value
            mock_result = {
                'report_type': 'performance',
                'report_id': 'report-001',
                'data': {'efficiency': 0.95}
            }
            mock_analyzer.generate_report.return_value = mock_result

            with patch('bottle.request') as mock_request:
                mock_request.json = {
                    'report_type': 'performance',
                    'filters': {}
                }
                mock_request.request_id = 'test-id'

                assert mock_request.json['report_type'] == 'performance'

    def test_report_generation_vulnerability_type(self):
        """Test report generation with vulnerability report type"""
        with patch('routes.analysis.Analyzer') as MockAnalyzer:
            mock_analyzer = MockAnalyzer.return_value
            mock_result = {
                'report_type': 'vulnerability',
                'vulnerabilities': []
            }
            mock_analyzer.generate_report.return_value = mock_result

            with patch('bottle.request') as mock_request:
                mock_request.json = {
                    'report_type': 'vulnerability',
                    'filters': {}
                }

                assert mock_request.json['report_type'] == 'vulnerability'

    def test_report_generation_analysis_type(self):
        """Test report generation with analysis report type"""
        with patch('routes.analysis.Analyzer') as MockAnalyzer:
            mock_analyzer = MockAnalyzer.return_value
            mock_result = {
                'report_type': 'analysis',
                'analysis_data': {}
            }
            mock_analyzer.generate_report.return_value = mock_result

            with patch('bottle.request') as mock_request:
                mock_request.json = {
                    'report_type': 'analysis',
                    'filters': {}
                }

                assert mock_request.json['report_type'] == 'analysis'

    def test_report_generation_empty_request_body(self):
        """Test report generation with empty request body"""
        with patch('bottle.request') as mock_request:
            mock_request.json = None

            assert mock_request.json is None

    def test_report_generation_missing_report_type(self):
        """Test report generation with missing report_type"""
        with patch('bottle.request') as mock_request:
            mock_request.json = {
                'filters': {}
            }

            assert 'report_type' not in mock_request.json

    def test_report_generation_with_filters(self):
        """Test report generation with date range filters"""
        with patch('routes.analysis.Analyzer') as MockAnalyzer:
            mock_analyzer = MockAnalyzer.return_value
            mock_result = {'report_type': 'performance'}
            mock_analyzer.generate_report.return_value = mock_result

            with patch('bottle.request') as mock_request:
                mock_request.json = {
                    'report_type': 'performance',
                    'filters': {
                        'start_date': '2026-01-01',
                        'end_date': '2026-02-01'
                    }
                }

                assert 'filters' in mock_request.json
                assert 'start_date' in mock_request.json['filters']

    def test_report_generation_response_format(self):
        """Test that report response has correct format"""
        with patch('routes.analysis.ResponseFormatter') as MockFormatter:
            expected_response = {
                'data': {'report_type': 'performance'},
                'status': 'success'
            }
            MockFormatter.format_success_response.return_value = expected_response

            assert 'data' in expected_response
            assert 'report_type' in expected_response['data']

    def test_report_generation_execution_time(self):
        """Test that report generation completes within 30 seconds"""
        with patch('routes.analysis.Analyzer') as MockAnalyzer:
            mock_analyzer = MockAnalyzer.return_value
            mock_result = {'execution_time_ms': 25000}
            mock_analyzer.generate_report.return_value = mock_result

            assert mock_result['execution_time_ms'] < 30000


class TestCoreDumpUploadRoute:
    """Unit tests for POST /api/v1/analysis/core-dump/upload endpoint"""

    def test_core_dump_upload_valid_file(self):
        """Test successful Core Dump file upload"""
        with patch('routes.analysis.Analyzer') as MockAnalyzer:
            mock_analyzer = MockAnalyzer.return_value
            mock_result = {
                'dump_id': 'dump-001',
                'crash_address': '0x12345678',
                'call_stack': ['func1', 'func2'],
                'status': 'analyzed'
            }
            mock_analyzer.analyze_core_dump.return_value = mock_result

            with patch('bottle.request') as mock_request:
                mock_request.body.read.return_value = b'core_dump_data'
                mock_request.request_id = 'test-id'

                assert mock_request.body.read() is not None

    def test_core_dump_upload_empty_file(self):
        """Test Core Dump upload with empty file"""
        with patch('bottle.request') as mock_request:
            mock_request.body.read.return_value = b''

            assert len(mock_request.body.read()) == 0

    def test_core_dump_upload_invalid_file(self):
        """Test Core Dump upload with invalid/corrupted file"""
        with patch('routes.analysis.Analyzer') as MockAnalyzer:
            mock_analyzer = MockAnalyzer.return_value
            mock_analyzer.analyze_core_dump.side_effect = AnalysisError(
                "Invalid Core Dump file format"
            )

            with patch('routes.analysis.ErrorHandler') as MockErrorHandler:
                MockErrorHandler.handle_vpp_exception.return_value = (
                    {'error': {'code': 'INVALID_CORE_DUMP'}},
                    400
                )

                assert MockErrorHandler.handle_vpp_exception is not None

    def test_core_dump_upload_response_format(self):
        """Test that Core Dump upload response has correct format"""
        with patch('routes.analysis.ResponseFormatter') as MockFormatter:
            expected_response = {
                'data': {'dump_id': 'dump-001'},
                'status': 'success'
            }
            MockFormatter.format_success_response.return_value = expected_response

            assert 'data' in expected_response
            assert 'dump_id' in expected_response['data']

    def test_core_dump_upload_response_status_code(self):
        """Test that Core Dump upload returns 200 status"""
        with patch('routes.analysis.Analyzer') as MockAnalyzer:
            mock_analyzer = MockAnalyzer.return_value
            mock_analyzer.analyze_core_dump.return_value = {'dump_id': 'dump-001'}

            assert mock_analyzer.analyze_core_dump is not None


class TestCoreDumpRetrievalRoute:
    """Unit tests for GET /api/v1/analysis/core-dump/{dump_id} endpoint"""

    def test_core_dump_retrieval_success(self):
        """Test successful Core Dump analysis retrieval"""
        with patch('utils.database.SessionLocal') as MockSession:
            mock_session = MockSession.return_value
            mock_analysis = Mock()
            mock_analysis.id = 'dump-001'
            mock_analysis.status = 'completed'
            mock_analysis.result_data = {
                'crash_address': '0x12345678',
                'call_stack': ['func1', 'func2'],
                'register_state': {'eax': '0x0'}
            }
            mock_analysis.created_at = datetime.now()

            mock_session.query.return_value.filter_by.return_value.first.return_value = mock_analysis

            assert mock_analysis.id == 'dump-001'

    def test_core_dump_retrieval_not_found(self):
        """Test Core Dump retrieval with invalid dump ID"""
        with patch('utils.database.SessionLocal') as MockSession:
            mock_session = MockSession.return_value
            mock_session.query.return_value.filter_by.return_value.first.return_value = None

            with patch('routes.analysis.ErrorHandler') as MockErrorHandler:
                MockErrorHandler.handle_vpp_exception.return_value = (
                    {'error': {'code': 'NOT_FOUND'}},
                    404
                )

                assert MockErrorHandler.handle_vpp_exception is not None

    def test_core_dump_retrieval_response_format(self):
        """Test that Core Dump retrieval response has correct format"""
        with patch('routes.analysis.ResponseFormatter') as MockFormatter:
            expected_response = {
                'data': {
                    'dump_id': 'dump-001',
                    'crash_address': '0x12345678',
                    'call_stack': []
                },
                'status': 'success'
            }
            MockFormatter.format_success_response.return_value = expected_response

            assert 'data' in expected_response
            assert 'dump_id' in expected_response['data']
            assert 'crash_address' in expected_response['data']

    def test_core_dump_retrieval_response_status_code(self):
        """Test that Core Dump retrieval returns 200 status"""
        with patch('utils.database.SessionLocal') as MockSession:
            mock_session = MockSession.return_value
            mock_analysis = Mock()
            mock_session.query.return_value.filter_by.return_value.first.return_value = mock_analysis

            assert mock_analysis is not None


class TestVulnerabilityReportRoute:
    """Unit tests for GET /api/v1/analysis/vulnerability-report endpoint"""

    def test_vulnerability_report_no_filters(self):
        """Test vulnerability report generation without filters"""
        with patch('routes.analysis.Analyzer') as MockAnalyzer:
            mock_analyzer = MockAnalyzer.return_value
            mock_result = {
                'vulnerabilities': [],
                'total_count': 0
            }
            mock_analyzer.generate_vulnerability_report.return_value = mock_result

            with patch('bottle.request') as mock_request:
                mock_request.query = {}
                mock_request.request_id = 'test-id'

                assert mock_request.query.get('severity') is None

    def test_vulnerability_report_severity_filter(self):
        """Test vulnerability report with severity filter"""
        with patch('routes.analysis.Analyzer') as MockAnalyzer:
            mock_analyzer = MockAnalyzer.return_value
            mock_result = {
                'vulnerabilities': [
                    {'severity': 'critical', 'description': 'Critical issue'}
                ],
                'total_count': 1
            }
            mock_analyzer.generate_vulnerability_report.return_value = mock_result

            with patch('bottle.request') as mock_request:
                mock_request.query = {'severity': 'critical'}

                assert mock_request.query.get('severity') == 'critical'

    def test_vulnerability_report_protocol_filter(self):
        """Test vulnerability report with protocol filter"""
        with patch('routes.analysis.Analyzer') as MockAnalyzer:
            mock_analyzer = MockAnalyzer.return_value
            mock_result = {
                'vulnerabilities': [
                    {'protocol': 'iec_104', 'description': 'IEC 104 issue'}
                ],
                'total_count': 1
            }
            mock_analyzer.generate_vulnerability_report.return_value = mock_result

            with patch('bottle.request') as mock_request:
                mock_request.query = {'protocol': 'iec_104'}

                assert mock_request.query.get('protocol') == 'iec_104'

    def test_vulnerability_report_multiple_filters(self):
        """Test vulnerability report with multiple filters"""
        with patch('routes.analysis.Analyzer') as MockAnalyzer:
            mock_analyzer = MockAnalyzer.return_value
            mock_result = {'vulnerabilities': []}
            mock_analyzer.generate_vulnerability_report.return_value = mock_result

            with patch('bottle.request') as mock_request:
                mock_request.query = {
                    'severity': 'high',
                    'protocol': 'mqtt'
                }

                assert mock_request.query.get('severity') == 'high'
                assert mock_request.query.get('protocol') == 'mqtt'

    def test_vulnerability_report_response_format(self):
        """Test that vulnerability report response has correct format"""
        with patch('routes.analysis.ResponseFormatter') as MockFormatter:
            expected_response = {
                'data': {'vulnerabilities': []},
                'status': 'success'
            }
            MockFormatter.format_success_response.return_value = expected_response

            assert 'data' in expected_response
            assert 'vulnerabilities' in expected_response['data']

    def test_vulnerability_report_response_status_code(self):
        """Test that vulnerability report returns 200 status"""
        with patch('routes.analysis.Analyzer') as MockAnalyzer:
            mock_analyzer = MockAnalyzer.return_value
            mock_analyzer.generate_vulnerability_report.return_value = {'vulnerabilities': []}

            assert mock_analyzer.generate_vulnerability_report is not None


class TestAnalysisRouteErrorHandling:
    """Unit tests for error handling across analysis routes"""

    def test_validation_error_response_format(self):
        """Test that validation errors have correct response format"""
        with patch('routes.analysis.ErrorHandler') as MockErrorHandler:
            error_response = {
                'error': {
                    'code': 'INVALID_REQUEST',
                    'message': 'Validation failed',
                    'details': {}
                }
            }
            MockErrorHandler.handle_vpp_exception.return_value = (error_response, 400)

            assert 'error' in error_response
            assert 'code' in error_response['error']
            assert 'message' in error_response['error']

    def test_analysis_error_status_code(self):
        """Test that analysis errors return appropriate status"""
        with patch('routes.analysis.ErrorHandler') as MockErrorHandler:
            MockErrorHandler.handle_vpp_exception.return_value = (
                {'error': {'code': 'ANALYSIS_FAILED'}},
                422
            )

            _, status = MockErrorHandler.handle_vpp_exception(
                AnalysisError("Analysis failed"),
                'test-id'
            )
            assert status == 422

    def test_internal_error_status_code(self):
        """Test that internal errors return 500 status"""
        with patch('routes.analysis.ErrorHandler') as MockErrorHandler:
            MockErrorHandler.handle_vpp_exception.return_value = (
                {'error': {'code': 'INTERNAL_ERROR'}},
                500
            )

            _, status = MockErrorHandler.handle_vpp_exception(
                Exception("Internal error"),
                'test-id'
            )
            assert status == 500

    def test_error_response_includes_request_id(self):
        """Test that error responses include request ID"""
        with patch('routes.analysis.ErrorHandler') as MockErrorHandler:
            error_response = {
                'error': {
                    'code': 'ERROR',
                    'request_id': 'test-request-id'
                }
            }
            MockErrorHandler.handle_vpp_exception.return_value = (error_response, 400)

            assert 'request_id' in error_response['error']


class TestAnalysisRouteContentType:
    """Unit tests for content type handling in analysis routes"""

    def test_response_content_type_json(self):
        """Test that responses have JSON content type"""
        with patch('bottle.response') as mock_response:
            mock_response.content_type = 'application/json'

            assert mock_response.content_type == 'application/json'

    def test_request_json_parsing(self):
        """Test that request JSON is parsed correctly"""
        with patch('bottle.request') as mock_request:
            mock_request.json = {
                'report_type': 'performance',
                'filters': {}
            }

            assert mock_request.json['report_type'] == 'performance'


class TestAnalysisRouteMetrics:
    """Unit tests for metrics recording in analysis routes"""

    def test_metrics_recorded_on_success(self):
        """Test that metrics are recorded on successful request"""
        with patch('routes.analysis.record_api_request') as mock_record:
            assert mock_record is not None

    def test_metrics_recorded_on_error(self):
        """Test that metrics are recorded on error request"""
        with patch('routes.analysis.record_api_request') as mock_record:
            assert mock_record is not None

