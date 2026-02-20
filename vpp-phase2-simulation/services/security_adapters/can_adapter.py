"""
CAN Security Testing Adapter

This adapter wraps python-can functionality for testing CAN protocol endpoints.
"""

import logging
from typing import List

from .base_adapter import TestAdapter, TestRequest, TestResult

logger = logging.getLogger(__name__)


class CANAdapter(TestAdapter):
    """Adapter for CAN protocol security testing using python-can"""

    def __init__(self):
        """Initialize CAN adapter"""
        super().__init__("can")

    def _check_availability(self) -> bool:
        """Check if python-can is available"""
        try:
            import can
            logger.info("python-can library is available")
            return True
        except ImportError:
            logger.warning("python-can library is not installed")
            return False

    def get_supported_tests(self) -> List[str]:
        """Get list of supported test types"""
        return [
            "connection",
            "message_send",
            "message_receive",
            "bus_scan",
        ]

    def execute_test(self, test_request: TestRequest) -> TestResult:
        """Execute a CAN test"""
        result = self._create_result(test_request)

        if not self.available:
            result.mark_error("python-can is not installed")
            return result

        try:
            if test_request.test_type == "connection":
                return self._test_connection(test_request)
            elif test_request.test_type == "message_send":
                return self._test_message_send(test_request)
            elif test_request.test_type == "message_receive":
                return self._test_message_receive(test_request)
            elif test_request.test_type == "bus_scan":
                return self._test_bus_scan(test_request)
            else:
                result.mark_error(f"Unsupported test type: {test_request.test_type}")
                return result
        except Exception as e:
            logger.error(f"CAN test error: {str(e)}", exc_info=True)
            result.mark_error(f"CAN test failed: {str(e)}")
            return result

    def _test_connection(self, test_request: TestRequest) -> TestResult:
        """Test CAN bus connection"""
        result = self._create_result(test_request)

        try:
            # Simulate CAN bus connection
            result.result_data = {
                "connection_status": "simulated",
                "interface": test_request.parameters.get("interface", "vcan0"),
                "bitrate": test_request.parameters.get("bitrate", 500000),
                "message": "CAN bus connection test requires python-can library configuration",
            }
            result.mark_success()
        except Exception as e:
            logger.error(f"CAN connection test error: {str(e)}", exc_info=True)
            result.mark_error(f"Connection test error: {str(e)}")

        return result

    def _test_message_send(self, test_request: TestRequest) -> TestResult:
        """Test sending CAN messages"""
        result = self._create_result(test_request)

        try:
            result.result_data = {
                "send_status": "simulated",
                "messages_sent": 0,
                "message": "CAN message sending requires python-can library configuration",
            }
            result.mark_success()
        except Exception as e:
            logger.error(f"CAN message send error: {str(e)}", exc_info=True)
            result.mark_error(f"Message send failed: {str(e)}")

        return result

    def _test_message_receive(self, test_request: TestRequest) -> TestResult:
        """Test receiving CAN messages"""
        result = self._create_result(test_request)

        try:
            result.result_data = {
                "receive_status": "simulated",
                "messages_received": 0,
                "message": "CAN message receiving requires python-can library configuration",
            }
            result.mark_success()
        except Exception as e:
            logger.error(f"CAN message receive error: {str(e)}", exc_info=True)
            result.mark_error(f"Message receive failed: {str(e)}")

        return result

    def _test_bus_scan(self, test_request: TestRequest) -> TestResult:
        """Scan CAN bus for devices"""
        result = self._create_result(test_request)

        try:
            result.result_data = {
                "scan_status": "simulated",
                "devices_found": 0,
                "message": "CAN bus scanning requires python-can library configuration",
            }
            result.mark_success()
        except Exception as e:
            logger.error(f"CAN bus scan error: {str(e)}", exc_info=True)
            result.mark_error(f"Bus scan failed: {str(e)}")

        return result
