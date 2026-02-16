"""
Analysis Functionality API Routes

HTTP endpoints for power flow analysis, stability analysis, metrics calculation,
report generation, and Core Dump analysis.
"""

from bottle import request, response
from datetime import datetime
from utils.logger import setup_logger
from utils.validators import (
    PowerFlowAnalysisRequest, StabilityAnalysisRequest,
    MetricsRequest, ReportRequest
)
from utils.errors import ValidationError, AnalysisError
from middleware.error_handler import ErrorHandler
from middleware.response_formatter import ResponseFormatter
from services.analyzer import Analyzer
from utils.metrics import time_api_request, record_api_request

logger = setup_logger(__name__)


def setup_analysis_routes(app):
    """
    Setup analysis functionality routes
    
    Args:
        app: Bottle application instance
    """
    
    analyzer = Analyzer()
    
    @app.post('/api/v1/analysis/power-flow')
    @time_api_request('/api/v1/analysis/power-flow', 'POST')
    def execute_power_flow_analysis():
        """
        Execute power flow analysis
        
        Request body:
        {
            "buses": [
                {"id": "bus_1", "voltage_nominal": 110.0},
                {"id": "bus_2", "voltage_nominal": 110.0}
            ],
            "lines": [
                {
                    "id": "line_1",
                    "from_bus": "bus_1",
                    "to_bus": "bus_2",
                    "resistance": 0.05,
                    "reactance": 0.1,
                    "length": 1.0
                }
            ],
            "generators": [
                {"id": "gen_1", "bus": "bus_1", "power": 100.0}
            ],
            "loads": [
                {"id": "load_1", "bus": "bus_2", "power": 80.0}
            ]
        }
        
        Returns:
            200 OK with power flow analysis results
        """
        try:
            request_id = getattr(request, 'request_id', 'unknown')
            
            # Validate request body
            data = request.json
            if not data:
                raise ValidationError("Request body is required")
            
            # Execute power flow analysis
            result = analyzer.analyze_power_flow(data)
            
            # Format response
            response_data = ResponseFormatter.format_success_response(
                data=result,
                request_id=request_id
            )
            
            response.status = 200
            response.content_type = 'application/json'
            record_api_request('/api/v1/analysis/power-flow', 'POST', 200)
            
            return response_data
        
        except ValidationError as e:
            error_response, status = ErrorHandler.handle_vpp_exception(
                e,
                getattr(request, 'request_id', 'unknown')
            )
            response.status = status
            record_api_request('/api/v1/analysis/power-flow', 'POST', status)
            return error_response
        
        except AnalysisError as e:
            error_response, status = ErrorHandler.handle_vpp_exception(
                e,
                getattr(request, 'request_id', 'unknown')
            )
            response.status = status
            record_api_request('/api/v1/analysis/power-flow', 'POST', status)
            return error_response
        
        except Exception as e:
            logger.error(f"Failed to execute power flow analysis: {str(e)}", exc_info=True)
            error_response, status = ErrorHandler.handle_vpp_exception(
                e,
                getattr(request, 'request_id', 'unknown')
            )
            response.status = status
            record_api_request('/api/v1/analysis/power-flow', 'POST', status)
            return error_response
    
    @app.post('/api/v1/analysis/stability')
    @time_api_request('/api/v1/analysis/stability', 'POST')
    def execute_stability_analysis():
        """
        Execute stability analysis
        
        Request body:
        {
            "frequency": 50.0,
            "voltage_magnitude": 1.0,
            "generation": 500.0,
            "load": 480.0,
            "inertia": 5.0
        }
        
        Returns:
            200 OK with stability analysis results
        """
        try:
            request_id = getattr(request, 'request_id', 'unknown')
            
            # Validate request body
            data = request.json
            if not data:
                raise ValidationError("Request body is required")
            
            # Execute stability analysis
            result = analyzer.analyze_stability(data)
            
            # Format response
            response_data = ResponseFormatter.format_success_response(
                data=result,
                request_id=request_id
            )
            
            response.status = 200
            response.content_type = 'application/json'
            record_api_request('/api/v1/analysis/stability', 'POST', 200)
            
            return response_data
        
        except ValidationError as e:
            error_response, status = ErrorHandler.handle_vpp_exception(
                e,
                getattr(request, 'request_id', 'unknown')
            )
            response.status = status
            record_api_request('/api/v1/analysis/stability', 'POST', status)
            return error_response
        
        except AnalysisError as e:
            error_response, status = ErrorHandler.handle_vpp_exception(
                e,
                getattr(request, 'request_id', 'unknown')
            )
            response.status = status
            record_api_request('/api/v1/analysis/stability', 'POST', status)
            return error_response
        
        except Exception as e:
            logger.error(f"Failed to execute stability analysis: {str(e)}", exc_info=True)
            error_response, status = ErrorHandler.handle_vpp_exception(
                e,
                getattr(request, 'request_id', 'unknown')
            )
            response.status = status
            record_api_request('/api/v1/analysis/stability', 'POST', status)
            return error_response
    
    @app.get('/api/v1/analysis/metrics')
    @time_api_request('/api/v1/analysis/metrics', 'GET')
    def get_metrics():
        """
        Get performance metrics
        
        Query parameters:
        - start_time: Start time (ISO format)
        - end_time: End time (ISO format)
        - aggregation: Aggregation level (hourly/daily/monthly)
        
        Returns:
            200 OK with metrics data
        """
        try:
            request_id = getattr(request, 'request_id', 'unknown')
            
            # Get query parameters
            start_time_str = request.query.get('start_time')
            end_time_str = request.query.get('end_time')
            aggregation = request.query.get('aggregation', 'hourly')
            
            # Validate parameters
            if not start_time_str or not end_time_str:
                raise ValidationError(
                    "start_time and end_time query parameters are required"
                )
            
            # Parse datetime strings
            try:
                start_time = datetime.fromisoformat(start_time_str)
                end_time = datetime.fromisoformat(end_time_str)
            except ValueError as e:
                raise ValidationError(
                    f"Invalid datetime format: {str(e)}"
                )
            
            # Calculate metrics
            result = analyzer.calculate_metrics(start_time, end_time, aggregation)
            
            # Format response
            response_data = ResponseFormatter.format_success_response(
                data=result,
                request_id=request_id
            )
            
            response.status = 200
            response.content_type = 'application/json'
            record_api_request('/api/v1/analysis/metrics', 'GET', 200)
            
            return response_data
        
        except ValidationError as e:
            error_response, status = ErrorHandler.handle_vpp_exception(
                e,
                getattr(request, 'request_id', 'unknown')
            )
            response.status = status
            record_api_request('/api/v1/analysis/metrics', 'GET', status)
            return error_response
        
        except AnalysisError as e:
            error_response, status = ErrorHandler.handle_vpp_exception(
                e,
                getattr(request, 'request_id', 'unknown')
            )
            response.status = status
            record_api_request('/api/v1/analysis/metrics', 'GET', status)
            return error_response
        
        except Exception as e:
            logger.error(f"Failed to get metrics: {str(e)}", exc_info=True)
            error_response, status = ErrorHandler.handle_vpp_exception(
                e,
                getattr(request, 'request_id', 'unknown')
            )
            response.status = status
            record_api_request('/api/v1/analysis/metrics', 'GET', status)
            return error_response
    
    @app.post('/api/v1/analysis/report')
    @time_api_request('/api/v1/analysis/report', 'POST')
    def generate_report():
        """
        Generate analysis report
        
        Request body:
        {
            "report_type": "performance",
            "filters": {
                "start_date": "2026-01-01",
                "end_date": "2026-02-01"
            }
        }
        
        Returns:
            200 OK with report data
        """
        try:
            request_id = getattr(request, 'request_id', 'unknown')
            
            # Validate request body
            data = request.json
            if not data:
                raise ValidationError("Request body is required")
            
            report_type = data.get('report_type')
            if not report_type:
                raise ValidationError("report_type is required")
            
            filters = data.get('filters', {})
            
            # Generate report
            result = analyzer.generate_report(report_type, filters)
            
            # Format response
            response_data = ResponseFormatter.format_success_response(
                data=result,
                request_id=request_id
            )
            
            response.status = 200
            response.content_type = 'application/json'
            record_api_request('/api/v1/analysis/report', 'POST', 200)
            
            return response_data
        
        except ValidationError as e:
            error_response, status = ErrorHandler.handle_vpp_exception(
                e,
                getattr(request, 'request_id', 'unknown')
            )
            response.status = status
            record_api_request('/api/v1/analysis/report', 'POST', status)
            return error_response
        
        except AnalysisError as e:
            error_response, status = ErrorHandler.handle_vpp_exception(
                e,
                getattr(request, 'request_id', 'unknown')
            )
            response.status = status
            record_api_request('/api/v1/analysis/report', 'POST', status)
            return error_response
        
        except Exception as e:
            logger.error(f"Failed to generate report: {str(e)}", exc_info=True)
            error_response, status = ErrorHandler.handle_vpp_exception(
                e,
                getattr(request, 'request_id', 'unknown')
            )
            response.status = status
            record_api_request('/api/v1/analysis/report', 'POST', status)
            return error_response
    
    @app.post('/api/v1/analysis/core-dump/upload')
    @time_api_request('/api/v1/analysis/core-dump/upload', 'POST')
    def upload_core_dump():
        """
        Upload and analyze Core Dump file
        
        Request: Binary Core Dump file in request body
        
        Returns:
            200 OK with Core Dump analysis results
        """
        try:
            request_id = getattr(request, 'request_id', 'unknown')
            
            # Get binary data from request body
            core_dump_data = request.body.read()
            
            if not core_dump_data:
                raise ValidationError("Core Dump file data is required")
            
            # Analyze Core Dump
            result = analyzer.analyze_core_dump(core_dump_data)
            
            # Format response
            response_data = ResponseFormatter.format_success_response(
                data=result,
                request_id=request_id
            )
            
            response.status = 200
            response.content_type = 'application/json'
            record_api_request('/api/v1/analysis/core-dump/upload', 'POST', 200)
            
            return response_data
        
        except ValidationError as e:
            error_response, status = ErrorHandler.handle_vpp_exception(
                e,
                getattr(request, 'request_id', 'unknown')
            )
            response.status = status
            record_api_request('/api/v1/analysis/core-dump/upload', 'POST', status)
            return error_response
        
        except AnalysisError as e:
            error_response, status = ErrorHandler.handle_vpp_exception(
                e,
                getattr(request, 'request_id', 'unknown')
            )
            response.status = status
            record_api_request('/api/v1/analysis/core-dump/upload', 'POST', status)
            return error_response
        
        except Exception as e:
            logger.error(f"Failed to upload Core Dump: {str(e)}", exc_info=True)
            error_response, status = ErrorHandler.handle_vpp_exception(
                e,
                getattr(request, 'request_id', 'unknown')
            )
            response.status = status
            record_api_request('/api/v1/analysis/core-dump/upload', 'POST', status)
            return error_response
    
    @app.get('/api/v1/analysis/core-dump/<dump_id>')
    @time_api_request('/api/v1/analysis/core-dump/<dump_id>', 'GET')
    def get_core_dump_analysis(dump_id):
        """
        Get Core Dump analysis results
        
        Path parameters:
        - dump_id: Core Dump analysis ID
        
        Returns:
            200 OK with Core Dump analysis results
        """
        try:
            request_id = getattr(request, 'request_id', 'unknown')
            
            from models.analysis_result import AnalysisResult
            from utils.database import SessionLocal
            
            session = SessionLocal()
            
            # Query Core Dump analysis
            analysis = session.query(AnalysisResult).filter_by(
                id=dump_id,
                analysis_type="core_dump"
            ).first()
            
            session.close()
            
            if not analysis:
                raise ValidationError(
                    f"Core Dump analysis with ID '{dump_id}' not found"
                )
            
            # Format response
            result_data = analysis.result_data or {}
            response_data = ResponseFormatter.format_success_response(
                data={
                    "dump_id": analysis.id,
                    "status": analysis.status,
                    "crash_address": result_data.get("crash_address", "0x0"),
                    "call_stack": result_data.get("call_stack", []),
                    "register_state": result_data.get("register_state", {}),
                    "created_at": analysis.created_at.isoformat()
                },
                request_id=request_id
            )
            
            response.status = 200
            response.content_type = 'application/json'
            record_api_request('/api/v1/analysis/core-dump/<dump_id>', 'GET', 200)
            
            return response_data
        
        except ValidationError as e:
            error_response, status = ErrorHandler.handle_vpp_exception(
                e,
                getattr(request, 'request_id', 'unknown')
            )
            response.status = status
            record_api_request('/api/v1/analysis/core-dump/<dump_id>', 'GET', status)
            return error_response
        
        except Exception as e:
            logger.error(f"Failed to get Core Dump analysis: {str(e)}", exc_info=True)
            error_response, status = ErrorHandler.handle_vpp_exception(
                e,
                getattr(request, 'request_id', 'unknown')
            )
            response.status = status
            record_api_request('/api/v1/analysis/core-dump/<dump_id>', 'GET', status)
            return error_response
    
    @app.get('/api/v1/analysis/vulnerability-report')
    @time_api_request('/api/v1/analysis/vulnerability-report', 'GET')
    def get_vulnerability_report():
        """
        Get vulnerability report
        
        Query parameters:
        - severity: Filter by severity (critical/high/medium/low)
        - protocol: Filter by protocol (iec_104/mqtt/etc)
        
        Returns:
            200 OK with vulnerability report
        """
        try:
            request_id = getattr(request, 'request_id', 'unknown')
            
            # Get query parameters for filters
            filters = {}
            severity = request.query.get('severity')
            protocol = request.query.get('protocol')
            
            if severity:
                filters['severity'] = severity
            if protocol:
                filters['protocol'] = protocol
            
            # Generate vulnerability report
            result = analyzer.generate_vulnerability_report(filters)
            
            # Format response
            response_data = ResponseFormatter.format_success_response(
                data=result,
                request_id=request_id
            )
            
            response.status = 200
            response.content_type = 'application/json'
            record_api_request('/api/v1/analysis/vulnerability-report', 'GET', 200)
            
            return response_data
        
        except AnalysisError as e:
            error_response, status = ErrorHandler.handle_vpp_exception(
                e,
                getattr(request, 'request_id', 'unknown')
            )
            response.status = status
            record_api_request('/api/v1/analysis/vulnerability-report', 'GET', status)
            return error_response
        
        except Exception as e:
            logger.error(f"Failed to get vulnerability report: {str(e)}", exc_info=True)
            error_response, status = ErrorHandler.handle_vpp_exception(
                e,
                getattr(request, 'request_id', 'unknown')
            )
            response.status = status
            record_api_request('/api/v1/analysis/vulnerability-report', 'GET', status)
            return error_response
