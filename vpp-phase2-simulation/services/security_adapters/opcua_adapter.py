"""
OPC UA Security Testing Adapter

This adapter wraps python-opcua functionality for testing OPC UA protocol endpoints.
"""

import logging
from typing import List
import socket

from .base_adapter import TestAdapter, TestRequest, TestResult

logger = logging.getLogger(__name__)


class OPCUAAdapter(TestAdapter):
    """Adapter for OPC UA protocol security testing using python-opcua"""

    def __init__(self):
        """Initialize OPC UA adapter"""
        super().__init__("opcua")

    def _check_availability(self) -> bool:
        """Check if python-opcua is available"""
        try:
            import opcua
            logger.info("python-opcua library is available")
            return True
        except ImportError:
            logger.warning("python-opcua library is not installed")
            return False

    def get_supported_tests(self) -> List[str]:
        """Get list of supported test types"""
        return [
            "connection",
            "browse",
            "read_attributes",
            "write_attributes",
            "security_scan",
        ]

    def execute_test(self, test_request: TestRequest) -> TestResult:
        """Execute an OPC UA test"""
        result = self._create_result(test_request)

        if not self.available:
            result.mark_error("python-opcua is not installed")
            return result

        try:
            if test_request.test_type == "connection":
                return self._test_connection(test_request)
            elif test_request.test_type == "browse":
                return self._test_browse(test_request)
            elif test_request.test_type == "read_attributes":
                return self._test_read_attributes(test_request)
            elif test_request.test_type == "write_attributes":
                return self._test_write_attributes(test_request)
            elif test_request.test_type == "security_scan":
                return self._test_security_scan(test_request)
            else:
                result.mark_error(f"Unsupported test type: {test_request.test_type}")
                return result
        except Exception as e:
            logger.error(f"OPC UA test error: {str(e)}", exc_info=True)
            result.mark_error(f"OPC UA test failed: {str(e)}")
            return result

    def _test_connection(self, test_request: TestRequest) -> TestResult:
        """Test OPC UA connection"""
        result = self._create_result(test_request)

        try:
            # Extract host and port from URL or use provided values
            url = test_request.target_url or f"opc.tcp://{test_request.target_host}:{test_request.target_port}"

            # Attempt TCP connection to OPC UA port
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(test_request.timeout)

            try:
                sock.connect((test_request.target_host, test_request.target_port))
                result.result_data = {
                    "connection_status": "success",
                    "url": url,
                    "host": test_request.target_host,
                    "port": test_request.target_port,
                    "message": "Successfully connected to OPC UA endpoint",
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
            logger.error(f"OPC UA connection test error: {str(e)}", exc_info=True)
            result.mark_error(f"Connection test error: {str(e)}")

        return result

    def _test_browse(self, test_request: TestRequest) -> TestResult:
        """Browse OPC UA namespace"""
        result = self._create_result(test_request)

        try:
            # Simulate OPC UA namespace browsing
            # In a real implementation, this would use python-opcua library
            result.result_data = {
                "browse_status": "simulated",
                "nodes_found": 0,
                "message": "OPC UA namespace browsing requires python-opcua library configuration",
                "note": "This is a simulated result. Configure python-opcua for real browsing.",
            }
            result.mark_success()
        except Exception as e:
            logger.error(f"OPC UA browse error: {str(e)}", exc_info=True)
            result.mark_error(f"Browse failed: {str(e)}")

        return result

    def _test_read_attributes(self, test_request: TestRequest) -> TestResult:
        """Test reading OPC UA node attributes"""
        result = self._create_result(test_request)

        try:
            result.result_data = {
                "read_status": "simulated",
                "attributes_read": 0,
                "message": "OPC UA attribute reading requires python-opcua library configuration",
            }
            result.mark_success()
        except Exception as e:
            logger.error(f"OPC UA read attributes error: {str(e)}", exc_info=True)
            result.mark_error(f"Read attributes failed: {str(e)}")

        return result

    def _test_write_attributes(self, test_request: TestRequest) -> TestResult:
        """Test writing OPC UA node attributes"""
        result = self._create_result(test_request)

        try:
            result.result_data = {
                "write_status": "simulated",
                "attributes_written": 0,
                "message": "OPC UA attribute writing requires python-opcua library configuration",
            }
            result.mark_success()
        except Exception as e:
            logger.error(f"OPC UA write attributes error: {str(e)}", exc_info=True)
            result.mark_error(f"Write attributes failed: {str(e)}")

        return result

    def _test_security_scan(self, test_request: TestRequest) -> TestResult:
        """Scan OPC UA for security vulnerabilities"""
        result = self._create_result(test_request)

        try:
            result.result_data = {
                "scan_status": "simulated",
                "vulnerabilities": [],
                "message": "OPC UA security scanning requires python-opcua library configuration",
            }
            result.mark_success()
        except Exception as e:
            logger.error(f"OPC UA security scan error: {str(e)}", exc_info=True)
            result.mark_error(f"Security scan failed: {str(e)}")

        return result
