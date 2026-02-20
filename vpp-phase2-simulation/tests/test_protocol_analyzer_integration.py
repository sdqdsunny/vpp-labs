"""
Protocol Analyzer Integration Tests

Tests for integrating security test results with the protocol analyzer.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock, patch

from services.protocol_analyzer_integration import (
    ProtocolAnalyzerIntegration,
    VulnerabilityTag,
    TestResultMetadata,
    get_integration_service,
    set_integration_service
)
from services.security_adapters.base_adapter import TestResult


@pytest.fixture
def integration_service():
    """Create an integration service instance"""
    service = ProtocolAnalyzerIntegration()
    yield service


@pytest.fixture
def sample_test_result():
    """Create a sample test result with vulnerabilities"""
    result = TestResult(
        test_type="connection",
        adapter_name="dnp3",
        target_host="192.168.1.100",
        target_port=20000,
    )
    result.mark_success()
    result.result_data = {
        "connection_status": "success",
        "response_time": 0.5
    }
    result.vulnerabilities_found = [
        {
            "description": "Weak authentication",
            "severity": "high"
        },
        {
            "description": "Unencrypted communication",
            "severity": "critical"
        }
    ]
    return result


class TestVulnerabilityTag:
    """Test VulnerabilityTag dataclass"""
    
    def test_tag_creation(self):
        """Test creating a vulnerability tag"""
        tag = VulnerabilityTag(
            vulnerability_id="vuln_001",
            severity="high",
            description="Test vulnerability",
            test_id="test_001",
            adapter_name="dnp3",
            timestamp=datetime.now().isoformat()
        )
        
        assert tag.vulnerability_id == "vuln_001"
        assert tag.severity == "high"
        assert tag.description == "Test vulnerability"


class TestTestResultMetadata:
    """Test TestResultMetadata dataclass"""
    
    def test_metadata_creation(self):
        """Test creating test result metadata"""
        metadata = TestResultMetadata(
            test_id="test_001",
            test_type="connection",
            adapter_name="dnp3",
            target_host="localhost",
            target_port=20000,
            status="success",
            start_time=datetime.now().isoformat(),
            end_time=datetime.now().isoformat(),
            duration=1.5,
            vulnerabilities=[],
            findings={}
        )
        
        assert metadata.test_id == "test_001"
        assert metadata.adapter_name == "dnp3"
        assert metadata.status == "success"


class TestProtocolAnalyzerIntegration:
    """Test ProtocolAnalyzerIntegration service"""
    
    def test_format_test_result_for_analyzer(self, integration_service, sample_test_result):
        """Test formatting test result for analyzer"""
        metadata = integration_service.format_test_result_for_analyzer(sample_test_result)
        
        assert metadata.test_id == sample_test_result.test_id
        assert metadata.test_type == "connection"
        assert metadata.adapter_name == "dnp3"
        assert metadata.target_host == "192.168.1.100"
        assert metadata.target_port == 20000
        assert metadata.status == "success"
        assert len(metadata.vulnerabilities) == 2
    
    def test_format_test_result_stores_metadata(self, integration_service, sample_test_result):
        """Test that formatting stores metadata for retrieval"""
        integration_service.format_test_result_for_analyzer(sample_test_result)
        
        retrieved = integration_service.get_test_result_metadata(sample_test_result.test_id)
        
        assert retrieved is not None
        assert retrieved.test_id == sample_test_result.test_id
    
    def test_format_test_result_with_no_vulnerabilities(self, integration_service):
        """Test formatting result with no vulnerabilities"""
        result = TestResult(
            test_type="connection",
            adapter_name="opcua",
            target_host="localhost",
            target_port=4840,
        )
        result.mark_success()
        result.vulnerabilities_found = []
        
        metadata = integration_service.format_test_result_for_analyzer(result)
        
        assert len(metadata.vulnerabilities) == 0
    
    def test_tag_flows_with_vulnerability(self, integration_service, sample_test_result):
        """Test tagging flows with vulnerability information"""
        # Mock the analyzer to return flows
        mock_flows = [
            {
                'source': '192.168.1.50',
                'destination': '192.168.1.100',
                'protocol': 'DNP3',
                'packet_count': 100,
                'total_bytes': 5000
            },
            {
                'source': '192.168.1.100',
                'destination': '192.168.1.50',
                'protocol': 'DNP3',
                'packet_count': 95,
                'total_bytes': 4500
            }
        ]
        
        integration_service.analyzer.get_flows = Mock(return_value=mock_flows)
        
        flows_tagged = integration_service.tag_flows_with_vulnerability(sample_test_result)
        
        # Should tag both flows (2 flows × 2 vulnerabilities = 4 tags)
        assert flows_tagged == 4
    
    def test_tag_flows_with_no_matching_flows(self, integration_service, sample_test_result):
        """Test tagging when no flows match the target"""
        # Mock the analyzer to return flows that don't match
        mock_flows = [
            {
                'source': '192.168.2.50',
                'destination': '192.168.2.100',
                'protocol': 'Modbus',
                'packet_count': 100,
                'total_bytes': 5000
            }
        ]
        
        integration_service.analyzer.get_flows = Mock(return_value=mock_flows)
        
        flows_tagged = integration_service.tag_flows_with_vulnerability(sample_test_result)
        
        assert flows_tagged == 0
    
    def test_get_vulnerabilities_for_flow(self, integration_service, sample_test_result):
        """Test retrieving vulnerabilities for a specific flow"""
        # Mock the analyzer
        mock_flows = [
            {
                'source': '192.168.1.50',
                'destination': '192.168.1.100',
                'protocol': 'DNP3',
                'packet_count': 100,
                'total_bytes': 5000
            }
        ]
        
        integration_service.analyzer.get_flows = Mock(return_value=mock_flows)
        integration_service.tag_flows_with_vulnerability(sample_test_result)
        
        vulns = integration_service.get_vulnerabilities_for_flow(
            '192.168.1.50',
            '192.168.1.100',
            'DNP3'
        )
        
        assert len(vulns) == 2
        assert all(v['severity'] in ['high', 'critical'] for v in vulns)
    
    def test_get_vulnerabilities_for_nonexistent_flow(self, integration_service):
        """Test retrieving vulnerabilities for non-existent flow"""
        vulns = integration_service.get_vulnerabilities_for_flow(
            '192.168.1.50',
            '192.168.1.100',
            'DNP3'
        )
        
        assert len(vulns) == 0
    
    def test_get_all_tagged_flows(self, integration_service, sample_test_result):
        """Test retrieving all tagged flows"""
        # Mock the analyzer
        mock_flows = [
            {
                'source': '192.168.1.50',
                'destination': '192.168.1.100',
                'protocol': 'DNP3',
                'packet_count': 100,
                'total_bytes': 5000
            }
        ]
        
        integration_service.analyzer.get_flows = Mock(return_value=mock_flows)
        integration_service.tag_flows_with_vulnerability(sample_test_result)
        
        tagged_flows = integration_service.get_all_tagged_flows()
        
        assert len(tagged_flows) > 0
        assert all('vulnerabilities' in f for f in tagged_flows)
        assert all('vulnerability_count' in f for f in tagged_flows)
    
    def test_get_integration_summary(self, integration_service, sample_test_result):
        """Test getting integration summary"""
        integration_service.format_test_result_for_analyzer(sample_test_result)
        
        summary = integration_service.get_integration_summary()
        
        assert summary['total_test_results'] == 1
        assert 'total_tagged_flows' in summary
        assert 'total_vulnerabilities' in summary
        assert 'timestamp' in summary
    
    def test_clear_old_tags(self, integration_service):
        """Test clearing old vulnerability tags"""
        # Create a tag with old timestamp
        old_tag = VulnerabilityTag(
            vulnerability_id="old_vuln",
            severity="high",
            description="Old vulnerability",
            test_id="test_001",
            adapter_name="dnp3",
            timestamp="2020-01-01T00:00:00"
        )
        
        integration_service.vulnerability_tags['flow_1'] = [old_tag]
        
        removed = integration_service.clear_old_tags(hours=24)
        
        assert removed == 1
        assert 'flow_1' not in integration_service.vulnerability_tags
    
    def test_clear_old_tags_preserves_recent(self, integration_service):
        """Test that clearing old tags preserves recent ones"""
        # Create a recent tag
        recent_tag = VulnerabilityTag(
            vulnerability_id="recent_vuln",
            severity="high",
            description="Recent vulnerability",
            test_id="test_001",
            adapter_name="dnp3",
            timestamp=datetime.now().isoformat()
        )
        
        integration_service.vulnerability_tags['flow_1'] = [recent_tag]
        
        removed = integration_service.clear_old_tags(hours=24)
        
        assert removed == 0
        assert 'flow_1' in integration_service.vulnerability_tags
    
    def test_get_test_result_metadata_not_found(self, integration_service):
        """Test retrieving non-existent metadata"""
        metadata = integration_service.get_test_result_metadata("nonexistent")
        
        assert metadata is None
    
    def test_multiple_vulnerabilities_per_flow(self, integration_service):
        """Test tagging flows with multiple vulnerabilities"""
        result = TestResult(
            test_type="scan",
            adapter_name="boofuzz",
            target_host="192.168.1.100",
            target_port=502,
        )
        result.mark_success()
        result.vulnerabilities_found = [
            {"description": "Vuln 1", "severity": "high"},
            {"description": "Vuln 2", "severity": "medium"},
            {"description": "Vuln 3", "severity": "low"},
        ]
        
        mock_flows = [
            {
                'source': '192.168.1.50',
                'destination': '192.168.1.100',
                'protocol': 'Modbus',
                'packet_count': 100,
                'total_bytes': 5000
            }
        ]
        
        integration_service.analyzer.get_flows = Mock(return_value=mock_flows)
        flows_tagged = integration_service.tag_flows_with_vulnerability(result)
        
        # 1 flow × 3 vulnerabilities = 3 tags
        assert flows_tagged == 3
        
        vulns = integration_service.get_vulnerabilities_for_flow(
            '192.168.1.50',
            '192.168.1.100',
            'Modbus'
        )
        
        assert len(vulns) == 3


class TestGlobalIntegrationService:
    """Test global integration service functions"""
    
    def test_get_integration_service(self):
        """Test getting global integration service"""
        service = get_integration_service()
        
        assert service is not None
        assert isinstance(service, ProtocolAnalyzerIntegration)
    
    def test_get_integration_service_singleton(self):
        """Test that global service is a singleton"""
        service1 = get_integration_service()
        service2 = get_integration_service()
        
        assert service1 is service2
    
    def test_set_integration_service(self):
        """Test setting global integration service"""
        new_service = ProtocolAnalyzerIntegration()
        set_integration_service(new_service)
        
        retrieved = get_integration_service()
        
        assert retrieved is new_service


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
