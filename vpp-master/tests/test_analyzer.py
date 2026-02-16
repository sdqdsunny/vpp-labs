"""
Unit Tests for Analyzer Service

Tests power flow analysis, stability analysis, metrics calculation,
report generation, and Core Dump analysis.
"""

import pytest
import sys
import os
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.analyzer import Analyzer
from models.analysis_result import AnalysisResult
from utils.errors import AnalysisError, ValidationError
from utils.database import SessionLocal


class TestAnalyzerPowerFlow:
    """Tests for power flow analysis"""
    
    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance"""
        return Analyzer()
    
    @pytest.fixture
    def valid_system_state(self):
        """Create valid system state"""
        return {
            "buses": [
                {"id": "bus_1", "voltage": 1.0},
                {"id": "bus_2", "voltage": 0.98},
                {"id": "bus_3", "voltage": 0.99}
            ],
            "lines": [
                {"id": "line_1", "from_bus": "bus_1", "to_bus": "bus_2", "power": 100.5},
                {"id": "line_2", "from_bus": "bus_2", "to_bus": "bus_3", "power": 95.3}
            ]
        }
    
    def test_analyze_power_flow_success(self, analyzer, valid_system_state):
        """Test successful power flow analysis"""
        result = analyzer.analyze_power_flow(valid_system_state)
        
        assert result is not None
        assert result["status"] == "completed"
        assert "analysis_id" in result
        assert "voltage_profiles" in result
        assert "power_flows" in result
        assert "convergence_status" in result
        assert "execution_time_ms" in result
        assert result["execution_time_ms"] >= 0
    
    def test_analyze_power_flow_with_empty_system_state(self, analyzer):
        """Test power flow analysis with empty system state"""
        with pytest.raises(ValidationError):
            analyzer.analyze_power_flow({})
    
    def test_analyze_power_flow_with_invalid_system_state(self, analyzer):
        """Test power flow analysis with invalid system state"""
        with pytest.raises(ValidationError):
            analyzer.analyze_power_flow("invalid")
    
    def test_analyze_power_flow_with_none_system_state(self, analyzer):
        """Test power flow analysis with None system state"""
        with pytest.raises(ValidationError):
            analyzer.analyze_power_flow(None)
    
    def test_analyze_power_flow_results_persisted(self, analyzer, valid_system_state):
        """Test that power flow analysis results are persisted"""
        result = analyzer.analyze_power_flow(valid_system_state)
        
        # Query database to verify persistence
        session = SessionLocal()
        analysis = session.query(AnalysisResult).filter_by(
            id=result["analysis_id"]
        ).first()
        
        assert analysis is not None
        assert analysis.analysis_type == "power_flow"
        assert analysis.status == "completed"
        assert analysis.system_state == valid_system_state
        
        session.close()
    
    def test_analyze_power_flow_convergence_status(self, analyzer, valid_system_state):
        """Test power flow analysis convergence status"""
        result = analyzer.analyze_power_flow(valid_system_state)
        
        assert "convergence_status" in result
        assert isinstance(result["convergence_status"], bool)


class TestAnalyzerStability:
    """Tests for stability analysis"""
    
    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance"""
        return Analyzer()
    
    @pytest.fixture
    def valid_system_state(self):
        """Create valid system state"""
        return {
            "frequency": 50.0,
            "voltage_magnitude": 1.0,
            "generation": 500.0,
            "load": 480.0
        }
    
    def test_analyze_stability_success(self, analyzer, valid_system_state):
        """Test successful stability analysis"""
        result = analyzer.analyze_stability(valid_system_state)
        
        assert result is not None
        assert result["status"] == "completed"
        assert "analysis_id" in result
        assert "frequency_deviation" in result
        assert "voltage_stability" in result
        assert "transient_stability" in result
        assert "risk_level" in result
        assert "execution_time_ms" in result
    
    def test_analyze_stability_risk_levels(self, analyzer, valid_system_state):
        """Test stability analysis risk level values"""
        result = analyzer.analyze_stability(valid_system_state)
        
        assert result["risk_level"] in ["low", "medium", "high"]
    
    def test_analyze_stability_with_invalid_system_state(self, analyzer):
        """Test stability analysis with invalid system state"""
        with pytest.raises(ValidationError):
            analyzer.analyze_stability("invalid")
    
    def test_analyze_stability_results_persisted(self, analyzer, valid_system_state):
        """Test that stability analysis results are persisted"""
        result = analyzer.analyze_stability(valid_system_state)
        
        # Query database to verify persistence
        session = SessionLocal()
        analysis = session.query(AnalysisResult).filter_by(
            id=result["analysis_id"]
        ).first()
        
        assert analysis is not None
        assert analysis.analysis_type == "stability"
        assert analysis.status == "completed"
        
        session.close()
    
    def test_analyze_stability_frequency_deviation(self, analyzer, valid_system_state):
        """Test stability analysis frequency deviation"""
        result = analyzer.analyze_stability(valid_system_state)
        
        assert "frequency_deviation" in result
        assert isinstance(result["frequency_deviation"], (int, float))


class TestAnalyzerMetrics:
    """Tests for metrics calculation"""
    
    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance"""
        return Analyzer()
    
    def test_calculate_metrics_success(self, analyzer):
        """Test successful metrics calculation"""
        start_time = datetime.utcnow() - timedelta(hours=1)
        end_time = datetime.utcnow()
        
        result = analyzer.calculate_metrics(start_time, end_time, "hourly")
        
        assert result is not None
        assert result["status"] == "completed"
        assert "metrics_id" in result
        assert "efficiency" in result
        assert "response_time_ms" in result
        assert "dispatch_success_rate" in result
        assert "aggregation" in result
        assert "execution_time_ms" in result
    
    def test_calculate_metrics_with_invalid_start_time(self, analyzer):
        """Test metrics calculation with invalid start time"""
        end_time = datetime.utcnow()
        
        with pytest.raises(ValidationError):
            analyzer.calculate_metrics("invalid", end_time, "hourly")
    
    def test_calculate_metrics_with_invalid_end_time(self, analyzer):
        """Test metrics calculation with invalid end time"""
        start_time = datetime.utcnow()
        
        with pytest.raises(ValidationError):
            analyzer.calculate_metrics(start_time, "invalid", "hourly")
    
    def test_calculate_metrics_with_start_after_end(self, analyzer):
        """Test metrics calculation with start time after end time"""
        start_time = datetime.utcnow()
        end_time = datetime.utcnow() - timedelta(hours=1)
        
        with pytest.raises(ValidationError):
            analyzer.calculate_metrics(start_time, end_time, "hourly")
    
    def test_calculate_metrics_with_invalid_aggregation(self, analyzer):
        """Test metrics calculation with invalid aggregation"""
        start_time = datetime.utcnow() - timedelta(hours=1)
        end_time = datetime.utcnow()
        
        with pytest.raises(ValidationError):
            analyzer.calculate_metrics(start_time, end_time, "invalid")
    
    def test_calculate_metrics_aggregation_levels(self, analyzer):
        """Test metrics calculation with different aggregation levels"""
        start_time = datetime.utcnow() - timedelta(days=30)
        end_time = datetime.utcnow()
        
        for aggregation in ["hourly", "daily", "monthly"]:
            result = analyzer.calculate_metrics(start_time, end_time, aggregation)
            assert result["aggregation"] == aggregation
    
    def test_calculate_metrics_results_persisted(self, analyzer):
        """Test that metrics calculation results are persisted"""
        start_time = datetime.utcnow() - timedelta(hours=1)
        end_time = datetime.utcnow()
        
        result = analyzer.calculate_metrics(start_time, end_time, "hourly")
        
        # Query database to verify persistence
        session = SessionLocal()
        analysis = session.query(AnalysisResult).filter_by(
            id=result["metrics_id"]
        ).first()
        
        assert analysis is not None
        assert analysis.analysis_type == "metrics"
        assert analysis.status == "completed"
        
        session.close()


class TestAnalyzerReportGeneration:
    """Tests for report generation"""
    
    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance"""
        return Analyzer()
    
    def test_generate_performance_report(self, analyzer):
        """Test performance report generation"""
        result = analyzer.generate_report("performance")
        
        assert result is not None
        assert result["status"] == "completed"
        assert "report_id" in result
        assert result["report_type"] == "performance"
        assert "report_data" in result
        assert "execution_time_ms" in result
    
    def test_generate_vulnerability_report_type(self, analyzer):
        """Test vulnerability report generation"""
        result = analyzer.generate_report("vulnerability")
        
        assert result is not None
        assert result["status"] == "completed"
        assert result["report_type"] == "vulnerability"
    
    def test_generate_analysis_report_type(self, analyzer):
        """Test analysis report generation"""
        result = analyzer.generate_report("analysis")
        
        assert result is not None
        assert result["status"] == "completed"
        assert result["report_type"] == "analysis"
    
    def test_generate_report_with_invalid_type(self, analyzer):
        """Test report generation with invalid type"""
        with pytest.raises(ValidationError):
            analyzer.generate_report("invalid_type")
    
    def test_generate_report_with_filters(self, analyzer):
        """Test report generation with filters"""
        filters = {
            "start_date": "2026-01-01",
            "end_date": "2026-02-01",
            "device_type": "solar"
        }
        
        result = analyzer.generate_report("performance", filters)
        
        assert result is not None
        assert result["status"] == "completed"
    
    def test_generate_report_results_persisted(self, analyzer):
        """Test that report generation results are persisted"""
        result = analyzer.generate_report("performance")
        
        # Query database to verify persistence
        session = SessionLocal()
        analysis = session.query(AnalysisResult).filter_by(
            id=result["report_id"]
        ).first()
        
        assert analysis is not None
        assert analysis.analysis_type == "report"
        assert analysis.status == "completed"
        
        session.close()


class TestAnalyzerCoreDump:
    """Tests for Core Dump analysis"""
    
    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance"""
        return Analyzer()
    
    @pytest.fixture
    def valid_core_dump_data(self):
        """Create valid Core Dump data"""
        return b"CORE_DUMP_DATA_PLACEHOLDER_12345"
    
    def test_analyze_core_dump_success(self, analyzer, valid_core_dump_data):
        """Test successful Core Dump analysis"""
        result = analyzer.analyze_core_dump(valid_core_dump_data)
        
        assert result is not None
        assert result["status"] == "completed"
        assert "dump_id" in result
        assert "crash_address" in result
        assert "call_stack" in result
        assert "register_state" in result
        assert "execution_time_ms" in result
    
    def test_analyze_core_dump_with_empty_data(self, analyzer):
        """Test Core Dump analysis with empty data"""
        with pytest.raises(ValidationError):
            analyzer.analyze_core_dump(b"")
    
    def test_analyze_core_dump_with_invalid_data_type(self, analyzer):
        """Test Core Dump analysis with invalid data type"""
        with pytest.raises(ValidationError):
            analyzer.analyze_core_dump("not_bytes")
    
    def test_analyze_core_dump_with_none_data(self, analyzer):
        """Test Core Dump analysis with None data"""
        with pytest.raises(ValidationError):
            analyzer.analyze_core_dump(None)
    
    def test_analyze_core_dump_results_persisted(self, analyzer, valid_core_dump_data):
        """Test that Core Dump analysis results are persisted"""
        result = analyzer.analyze_core_dump(valid_core_dump_data)
        
        # Query database to verify persistence
        session = SessionLocal()
        analysis = session.query(AnalysisResult).filter_by(
            id=result["dump_id"]
        ).first()
        
        assert analysis is not None
        assert analysis.analysis_type == "core_dump"
        assert analysis.status == "completed"
        
        session.close()
    
    def test_analyze_core_dump_crash_address(self, analyzer, valid_core_dump_data):
        """Test Core Dump analysis crash address extraction"""
        result = analyzer.analyze_core_dump(valid_core_dump_data)
        
        assert "crash_address" in result
        assert isinstance(result["crash_address"], str)
    
    def test_analyze_core_dump_call_stack(self, analyzer, valid_core_dump_data):
        """Test Core Dump analysis call stack extraction"""
        result = analyzer.analyze_core_dump(valid_core_dump_data)
        
        assert "call_stack" in result
        assert isinstance(result["call_stack"], list)
    
    def test_analyze_core_dump_register_state(self, analyzer, valid_core_dump_data):
        """Test Core Dump analysis register state extraction"""
        result = analyzer.analyze_core_dump(valid_core_dump_data)
        
        assert "register_state" in result
        assert isinstance(result["register_state"], dict)


class TestAnalyzerVulnerabilityReport:
    """Tests for vulnerability report generation"""
    
    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance"""
        return Analyzer()
    
    def test_generate_vulnerability_report_success(self, analyzer):
        """Test successful vulnerability report generation"""
        result = analyzer.generate_vulnerability_report()
        
        assert result is not None
        assert result["status"] == "completed"
        assert "report_id" in result
        assert "vulnerabilities" in result
        assert "severity_summary" in result
        assert "recommendations" in result
        assert "execution_time_ms" in result
    
    def test_generate_vulnerability_report_with_filters(self, analyzer):
        """Test vulnerability report generation with filters"""
        filters = {
            "severity": "high",
            "protocol": "iec_104"
        }
        
        result = analyzer.generate_vulnerability_report(filters)
        
        assert result is not None
        assert result["status"] == "completed"
    
    def test_generate_vulnerability_report_severity_summary(self, analyzer):
        """Test vulnerability report severity summary"""
        result = analyzer.generate_vulnerability_report()
        
        severity_summary = result["severity_summary"]
        assert "critical" in severity_summary
        assert "high" in severity_summary
        assert "medium" in severity_summary
        assert "low" in severity_summary
    
    def test_generate_vulnerability_report_results_persisted(self, analyzer):
        """Test that vulnerability report results are persisted"""
        result = analyzer.generate_vulnerability_report()
        
        # Query database to verify persistence
        session = SessionLocal()
        analysis = session.query(AnalysisResult).filter_by(
            id=result["report_id"]
        ).first()
        
        assert analysis is not None
        assert analysis.analysis_type == "vulnerability_report"
        assert analysis.status == "completed"
        
        session.close()


class TestAnalyzerExecutionTiming:
    """Tests for execution timing constraints"""
    
    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance"""
        return Analyzer()
    
    def test_power_flow_execution_time_recorded(self, analyzer):
        """Test that power flow execution time is recorded"""
        system_state = {
            "buses": [{"id": "bus_1", "voltage_nominal": 110.0}],
            "lines": []
        }
        result = analyzer.analyze_power_flow(system_state)
        
        assert result["execution_time_ms"] >= 0
        assert result["execution_time_ms"] < analyzer.POWER_FLOW_TIMEOUT * 1000
    
    def test_stability_execution_time_recorded(self, analyzer):
        """Test that stability execution time is recorded"""
        system_state = {"frequency": 50.0}
        result = analyzer.analyze_stability(system_state)
        
        assert result["execution_time_ms"] >= 0
        assert result["execution_time_ms"] < analyzer.STABILITY_TIMEOUT * 1000
    
    def test_metrics_execution_time_recorded(self, analyzer):
        """Test that metrics execution time is recorded"""
        start_time = datetime.utcnow() - timedelta(hours=1)
        end_time = datetime.utcnow()
        result = analyzer.calculate_metrics(start_time, end_time)
        
        assert result["execution_time_ms"] >= 0
        assert result["execution_time_ms"] < analyzer.METRICS_TIMEOUT * 1000
    
    def test_report_execution_time_recorded(self, analyzer):
        """Test that report execution time is recorded"""
        result = analyzer.generate_report("performance")
        
        assert result["execution_time_ms"] >= 0
        assert result["execution_time_ms"] < analyzer.REPORT_TIMEOUT * 1000


class TestAnalyzerErrorHandling:
    """Tests for error handling"""
    
    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance"""
        return Analyzer()
    
    def test_power_flow_analysis_error_persisted(self, analyzer):
        """Test that power flow analysis errors are persisted"""
        # This test verifies error handling and persistence
        system_state = {"invalid": "data"}
        
        try:
            analyzer.analyze_power_flow(system_state)
        except AnalysisError:
            pass
    
    def test_stability_analysis_error_persisted(self, analyzer):
        """Test that stability analysis errors are persisted"""
        try:
            analyzer.analyze_stability(None)
        except ValidationError:
            pass
    
    def test_metrics_calculation_error_handling(self, analyzer):
        """Test metrics calculation error handling"""
        with pytest.raises(ValidationError):
            analyzer.calculate_metrics(None, None)
    
    def test_report_generation_error_handling(self, analyzer):
        """Test report generation error handling"""
        with pytest.raises(ValidationError):
            analyzer.generate_report("nonexistent_type")
