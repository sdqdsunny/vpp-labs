"""
Protocol Analyzer Integration Service

Integrates security test results with the protocol analyzer for correlation
and vulnerability tagging of network flows.
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from dataclasses import dataclass, asdict

from services.protocol_analyzer import get_analyzer, PacketInfo

logger = logging.getLogger(__name__)


@dataclass
class VulnerabilityTag:
    """Tag for marking vulnerable network flows"""
    vulnerability_id: str
    severity: str  # "critical", "high", "medium", "low"
    description: str
    test_id: str
    adapter_name: str
    timestamp: str


@dataclass
class TestResultMetadata:
    """Metadata for test results compatible with protocol analyzer"""
    test_id: str
    test_type: str
    adapter_name: str
    target_host: str
    target_port: int
    status: str
    start_time: str
    end_time: str
    duration: float
    vulnerabilities: List[Dict[str, Any]]
    findings: Dict[str, Any]


class ProtocolAnalyzerIntegration:
    """Service for integrating test results with protocol analyzer"""
    
    def __init__(self):
        """Initialize the integration service"""
        self.analyzer = get_analyzer()
        self.vulnerability_tags: Dict[str, List[VulnerabilityTag]] = {}
        self.test_result_metadata: Dict[str, TestResultMetadata] = {}
    
    def format_test_result_for_analyzer(self, test_result: Any) -> TestResultMetadata:
        """Format a test result for protocol analyzer compatibility
        
        Args:
            test_result: TestResult object from security adapter
            
        Returns:
            TestResultMetadata formatted for protocol analyzer
        """
        try:
            # Extract vulnerabilities from result data
            vulnerabilities = []
            if hasattr(test_result, 'vulnerabilities_found'):
                for vuln in test_result.vulnerabilities_found:
                    if isinstance(vuln, dict):
                        vulnerabilities.append(vuln)
                    else:
                        vulnerabilities.append({
                            'description': str(vuln),
                            'severity': 'medium'
                        })
            
            # Extract findings from result data
            findings = {}
            if hasattr(test_result, 'result_data') and test_result.result_data:
                findings = test_result.result_data
            
            metadata = TestResultMetadata(
                test_id=test_result.test_id,
                test_type=test_result.test_type,
                adapter_name=test_result.adapter_name,
                target_host=test_result.target_host,
                target_port=test_result.target_port,
                status=test_result.status,
                start_time=test_result.start_time.isoformat() if hasattr(test_result.start_time, 'isoformat') else str(test_result.start_time),
                end_time=test_result.end_time.isoformat() if test_result.end_time and hasattr(test_result.end_time, 'isoformat') else str(test_result.end_time),
                duration=test_result.duration,
                vulnerabilities=vulnerabilities,
                findings=findings
            )
            
            # Store metadata for later retrieval
            self.test_result_metadata[test_result.test_id] = metadata
            
            logger.info(f"Formatted test result {test_result.test_id} for protocol analyzer")
            return metadata
        except Exception as e:
            logger.error(f"Failed to format test result: {e}", exc_info=True)
            raise
    
    def tag_flows_with_vulnerability(self, test_result: Any) -> int:
        """Tag network flows with vulnerability information
        
        Args:
            test_result: TestResult object containing vulnerabilities
            
        Returns:
            Number of flows tagged
        """
        try:
            flows_tagged = 0
            
            # Get all flows from analyzer
            flows = self.analyzer.get_flows(limit=1000)
            
            # Filter flows that match the test target
            matching_flows = [
                f for f in flows
                if f['destination'] == test_result.target_host or
                   f['source'] == test_result.target_host
            ]
            
            # Create vulnerability tags for each matching flow
            for vuln in test_result.vulnerabilities_found:
                vuln_id = f"{test_result.test_id}_{len(self.vulnerability_tags)}"
                
                # Extract severity if available
                severity = "medium"
                if isinstance(vuln, dict) and 'severity' in vuln:
                    severity = vuln['severity']
                
                # Extract description
                description = str(vuln) if not isinstance(vuln, dict) else vuln.get('description', str(vuln))
                
                tag = VulnerabilityTag(
                    vulnerability_id=vuln_id,
                    severity=severity,
                    description=description,
                    test_id=test_result.test_id,
                    adapter_name=test_result.adapter_name,
                    timestamp=datetime.now().isoformat()
                )
                
                # Tag each matching flow
                for flow in matching_flows:
                    flow_key = f"{flow['source']}_{flow['destination']}_{flow['protocol']}"
                    if flow_key not in self.vulnerability_tags:
                        self.vulnerability_tags[flow_key] = []
                    self.vulnerability_tags[flow_key].append(tag)
                    flows_tagged += 1
            
            logger.info(f"Tagged {flows_tagged} flows with vulnerabilities from test {test_result.test_id}")
            return flows_tagged
        except Exception as e:
            logger.error(f"Failed to tag flows: {e}", exc_info=True)
            return 0
    
    def get_test_result_metadata(self, test_id: str) -> Optional[TestResultMetadata]:
        """Retrieve test result metadata by test ID
        
        Args:
            test_id: The test ID to retrieve
            
        Returns:
            TestResultMetadata or None if not found
        """
        return self.test_result_metadata.get(test_id)
    
    def get_vulnerabilities_for_flow(self, source: str, destination: str, protocol: str) -> List[Dict[str, Any]]:
        """Get vulnerabilities tagged for a specific flow
        
        Args:
            source: Source IP address
            destination: Destination IP address
            protocol: Protocol name
            
        Returns:
            List of vulnerability tags for the flow
        """
        flow_key = f"{source}_{destination}_{protocol}"
        tags = self.vulnerability_tags.get(flow_key, [])
        return [asdict(tag) for tag in tags]
    
    def get_all_tagged_flows(self) -> List[Dict[str, Any]]:
        """Get all flows that have been tagged with vulnerabilities
        
        Returns:
            List of flows with their vulnerability tags
        """
        tagged_flows = []
        for flow_key, tags in self.vulnerability_tags.items():
            parts = flow_key.split('_')
            if len(parts) >= 3:
                source = parts[0]
                destination = parts[1]
                protocol = '_'.join(parts[2:])
                
                tagged_flows.append({
                    'source': source,
                    'destination': destination,
                    'protocol': protocol,
                    'vulnerabilities': [asdict(tag) for tag in tags],
                    'vulnerability_count': len(tags)
                })
        
        return sorted(tagged_flows, key=lambda x: x['vulnerability_count'], reverse=True)
    
    def get_integration_summary(self) -> Dict[str, Any]:
        """Get summary of protocol analyzer integration
        
        Returns:
            Dictionary with integration statistics
        """
        total_tests = len(self.test_result_metadata)
        total_tagged_flows = len(self.vulnerability_tags)
        total_vulnerabilities = sum(len(tags) for tags in self.vulnerability_tags.values())
        
        return {
            'total_test_results': total_tests,
            'total_tagged_flows': total_tagged_flows,
            'total_vulnerabilities': total_vulnerabilities,
            'timestamp': datetime.now().isoformat()
        }
    
    def clear_old_tags(self, hours: int = 24) -> int:
        """Clear vulnerability tags older than N hours
        
        Args:
            hours: Remove tags older than this many hours
            
        Returns:
            Number of tags removed
        """
        try:
            cutoff_time = datetime.fromisoformat(
                (datetime.now() - __import__('datetime').timedelta(hours=hours)).isoformat()
            )
            
            removed_count = 0
            flows_to_remove = []
            
            for flow_key, tags in self.vulnerability_tags.items():
                remaining_tags = []
                for tag in tags:
                    tag_time = datetime.fromisoformat(tag.timestamp)
                    if tag_time >= cutoff_time:
                        remaining_tags.append(tag)
                    else:
                        removed_count += 1
                
                if remaining_tags:
                    self.vulnerability_tags[flow_key] = remaining_tags
                else:
                    flows_to_remove.append(flow_key)
            
            for flow_key in flows_to_remove:
                del self.vulnerability_tags[flow_key]
            
            logger.info(f"Cleared {removed_count} old vulnerability tags")
            return removed_count
        except Exception as e:
            logger.error(f"Failed to clear old tags: {e}", exc_info=True)
            return 0


# Global integration service instance
_integration_service: Optional[ProtocolAnalyzerIntegration] = None


def get_integration_service() -> ProtocolAnalyzerIntegration:
    """Get or create the global integration service
    
    Returns:
        ProtocolAnalyzerIntegration instance
    """
    global _integration_service
    if _integration_service is None:
        _integration_service = ProtocolAnalyzerIntegration()
    return _integration_service


def set_integration_service(service: ProtocolAnalyzerIntegration) -> None:
    """Set the global integration service
    
    Args:
        service: ProtocolAnalyzerIntegration instance
    """
    global _integration_service
    _integration_service = service
