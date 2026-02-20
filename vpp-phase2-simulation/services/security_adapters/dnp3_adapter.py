"""
DNP3 Security Testing Adapter

This adapter wraps OpenDNP3 functionality for testing DNP3 protocol endpoints.
"""

import logging
from typing import List
import socket
import time

from .base_adapter import TestAdapter, TestRequest, TestResult
from ..dnp3_attack_detection import DNP3AttackDetector

logger = logging.getLogger(__name__)


class DNP3Adapter(TestAdapter):
    """Adapter for DNP3 protocol security testing using OpenDNP3"""

    def __init__(self):
        """Initialize DNP3 adapter"""
        super().__init__("dnp3")
        self.attack_detector = DNP3AttackDetector()

    def _check_availability(self) -> bool:
        """Check if OpenDNP3 is available"""
        try:
            import dnp3
            logger.info("OpenDNP3 library is available")
            return True
        except ImportError:
            logger.warning("OpenDNP3 library is not installed")
            return False

    def get_supported_tests(self) -> List[str]:
        """Get list of supported test types"""
        return [
            "connection",
            "scan",
            "read_points",
            "write_points",
            "authentication",
            "detect_attack",
            "analyze_anomaly",
        ]

    def execute_test(self, test_request: TestRequest) -> TestResult:
        """Execute a DNP3 test"""
        result = self._create_result(test_request)

        if not self.available:
            result.mark_error("OpenDNP3 is not installed")
            return result

        try:
            if test_request.test_type == "connection":
                return self._test_connection(test_request)
            elif test_request.test_type == "scan":
                return self._test_scan(test_request)
            elif test_request.test_type == "read_points":
                return self._test_read_points(test_request)
            elif test_request.test_type == "write_points":
                return self._test_write_points(test_request)
            elif test_request.test_type == "authentication":
                return self._test_authentication(test_request)
            elif test_request.test_type == "detect_attack":
                return self._test_detect_attack(test_request)
            elif test_request.test_type == "analyze_anomaly":
                return self._test_analyze_anomaly(test_request)
            else:
                result.mark_error(f"Unsupported test type: {test_request.test_type}")
                return result
        except Exception as e:
            logger.error(f"DNP3 test error: {str(e)}", exc_info=True)
            result.mark_error(f"DNP3 test failed: {str(e)}")
            return result

    def _test_connection(self, test_request: TestRequest) -> TestResult:
        """Test DNP3 connection"""
        result = self._create_result(test_request)

        try:
            # Attempt TCP connection to DNP3 port
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(test_request.timeout)

            try:
                sock.connect((test_request.target_host, test_request.target_port))
                result.result_data = {
                    "connection_status": "success",
                    "host": test_request.target_host,
                    "port": test_request.target_port,
                    "message": "Successfully connected to DNP3 endpoint",
                }
                result.mark_success()
            except socket.timeout:
                result.mark_failed("Connection timeout")
            except ConnectionRefusedError:
                result.mark_failed("Connection refused")
            except Exception as e:
                result.mark_failed(f"Connection failed: {str(e)}")
            finally:
                sock.close()

        except Exception as e:
            logger.error(f"DNP3 connection test error: {str(e)}", exc_info=True)
            result.mark_error(f"Connection test error: {str(e)}")

        return result

    def _test_scan(self, test_request: TestRequest) -> TestResult:
        """Scan DNP3 points"""
        result = self._create_result(test_request)

        try:
            # Simulate DNP3 point scanning
            # In a real implementation, this would use OpenDNP3 library
            result.result_data = {
                "scan_status": "simulated",
                "points_found": 0,
                "message": "DNP3 point scanning requires OpenDNP3 library configuration",
                "note": "This is a simulated result. Configure OpenDNP3 for real scanning.",
            }
            result.mark_success()
        except Exception as e:
            logger.error(f"DNP3 scan error: {str(e)}", exc_info=True)
            result.mark_error(f"Scan failed: {str(e)}")

        return result

    def _test_read_points(self, test_request: TestRequest) -> TestResult:
        """Test reading DNP3 points"""
        result = self._create_result(test_request)

        try:
            result.result_data = {
                "read_status": "simulated",
                "points_read": 0,
                "message": "DNP3 point reading requires OpenDNP3 library configuration",
            }
            result.mark_success()
        except Exception as e:
            logger.error(f"DNP3 read points error: {str(e)}", exc_info=True)
            result.mark_error(f"Read points failed: {str(e)}")

        return result

    def _test_write_points(self, test_request: TestRequest) -> TestResult:
        """Test writing DNP3 points"""
        result = self._create_result(test_request)

        try:
            result.result_data = {
                "write_status": "simulated",
                "points_written": 0,
                "message": "DNP3 point writing requires OpenDNP3 library configuration",
            }
            result.mark_success()
        except Exception as e:
            logger.error(f"DNP3 write points error: {str(e)}", exc_info=True)
            result.mark_error(f"Write points failed: {str(e)}")

        return result

    def _test_authentication(self, test_request: TestRequest) -> TestResult:
        """Test DNP3 authentication"""
        result = self._create_result(test_request)

        try:
            result.result_data = {
                "auth_status": "simulated",
                "vulnerabilities": [],
                "message": "DNP3 authentication testing requires OpenDNP3 library configuration",
            }
            result.mark_success()
        except Exception as e:
            logger.error(f"DNP3 authentication test error: {str(e)}", exc_info=True)
            result.mark_error(f"Authentication test failed: {str(e)}")

        return result
    def _test_detect_attack(self, test_request: TestRequest) -> TestResult:
        """Test DNP3 attack detection"""
        result = self._create_result(test_request)

        try:
            # Extract packet data from test parameters
            packet_data = test_request.parameters.get("packet_data", {})
            
            # Analyze packet for attacks
            anomaly_result = self.attack_detector.analyze_packet(packet_data)
            
            result.result_data = {
                "attack_detected": anomaly_result.is_anomalous,
                "anomalies": anomaly_result.anomalies,
                "severity": anomaly_result.severity,
                "timestamp": anomaly_result.timestamp.isoformat(),
                "alarm_state": self.attack_detector.get_alarm_state(),
                "statistics": self.attack_detector.get_statistics(),
            }
            
            if anomaly_result.is_anomalous:
                result.mark_failed(f"Attack detected: {', '.join(anomaly_result.anomalies)}")
            else:
                result.mark_success()
                
        except Exception as e:
            logger.error(f"DNP3 attack detection error: {str(e)}", exc_info=True)
            result.mark_error(f"Attack detection failed: {str(e)}")

        return result

    def _test_analyze_anomaly(self, test_request: TestRequest) -> TestResult:
        """Test DNP3 anomaly analysis"""
        result = self._create_result(test_request)

        try:
            # Extract packet data from test parameters
            packet_data = test_request.parameters.get("packet_data", {})
            
            # Analyze packet for anomalies
            anomaly_result = self.attack_detector.analyze_packet(packet_data)
            
            result.result_data = {
                "is_anomalous": anomaly_result.is_anomalous,
                "anomalies": anomaly_result.anomalies,
                "severity": anomaly_result.severity,
                "timestamp": anomaly_result.timestamp.isoformat(),
                "details": anomaly_result.details,
                "alarm_state": self.attack_detector.get_alarm_state(),
            }
            
            result.mark_success()
                
        except Exception as e:
            logger.error(f"DNP3 anomaly analysis error: {str(e)}", exc_info=True)
            result.mark_error(f"Anomaly analysis failed: {str(e)}")

        return result
