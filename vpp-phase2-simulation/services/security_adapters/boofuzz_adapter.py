"""
Boofuzz Security Testing Adapter

This adapter wraps Boofuzz functionality for protocol fuzzing and vulnerability discovery.
"""

import logging
from typing import List
import socket

from .base_adapter import TestAdapter, TestRequest, TestResult

logger = logging.getLogger(__name__)


class BoofuzzAdapter(TestAdapter):
    """Adapter for protocol fuzzing using Boofuzz"""

    def __init__(self):
        """Initialize Boofuzz adapter"""
        super().__init__("boofuzz")

    def _check_availability(self) -> bool:
        """Check if Boofuzz is available"""
        try:
            import boofuzz
            logger.info("Boofuzz library is available")
            return True
        except ImportError:
            logger.warning("Boofuzz library is not installed")
            return False

    def get_supported_tests(self) -> List[str]:
        """Get list of supported test types"""
        return [
            "modbus_fuzz",
            "dnp3_fuzz",
            "opcua_fuzz",
            "generic_fuzz",
        ]

    def execute_test(self, test_request: TestRequest) -> TestResult:
        """Execute a fuzzing test"""
        result = self._create_result(test_request)

        if not self.available:
            result.mark_error("Boofuzz is not installed")
            return result

        try:
            if test_request.test_type == "modbus_fuzz":
                return self._fuzz_modbus(test_request)
            elif test_request.test_type == "dnp3_fuzz":
                return self._fuzz_dnp3(test_request)
            elif test_request.test_type == "opcua_fuzz":
                return self._fuzz_opcua(test_request)
            elif test_request.test_type == "generic_fuzz":
                return self._fuzz_generic(test_request)
            else:
                result.mark_error(f"Unsupported test type: {test_request.test_type}")
                return result
        except Exception as e:
            logger.error(f"Boofuzz test error: {str(e)}", exc_info=True)
            result.mark_error(f"Boofuzz test failed: {str(e)}")
            return result

    def _fuzz_modbus(self, test_request: TestRequest) -> TestResult:
        """Fuzz Modbus protocol"""
        result = self._create_result(test_request)

        try:
            # Check if target is reachable
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(test_request.timeout)

            try:
                sock.connect((test_request.target_host, test_request.target_port))
                sock.close()

                # Simulate Modbus fuzzing
                result.result_data = {
                    "fuzz_status": "simulated",
                    "protocol": "Modbus",
                    "test_cases_sent": 0,
                    "crashes_found": 0,
                    "errors_found": 0,
                    "message": "Modbus fuzzing requires Boofuzz library configuration",
                    "note": "This is a simulated result. Configure Boofuzz for real fuzzing.",
                }
                result.mark_success()
            except (socket.timeout, ConnectionRefusedError) as e:
                result.mark_failed(f"Target not reachable: {str(e)}")
            finally:
                sock.close()

        except Exception as e:
            logger.error(f"Modbus fuzzing error: {str(e)}", exc_info=True)
            result.mark_error(f"Modbus fuzzing failed: {str(e)}")

        return result

    def _fuzz_dnp3(self, test_request: TestRequest) -> TestResult:
        """Fuzz DNP3 protocol"""
        result = self._create_result(test_request)

        try:
            # Check if target is reachable
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(test_request.timeout)

            try:
                sock.connect((test_request.target_host, test_request.target_port))
                sock.close()

                # Simulate DNP3 fuzzing
                result.result_data = {
                    "fuzz_status": "simulated",
                    "protocol": "DNP3",
                    "test_cases_sent": 0,
                    "crashes_found": 0,
                    "errors_found": 0,
                    "message": "DNP3 fuzzing requires Boofuzz library configuration",
                }
                result.mark_success()
            except (socket.timeout, ConnectionRefusedError) as e:
                result.mark_failed(f"Target not reachable: {str(e)}")
            finally:
                sock.close()

        except Exception as e:
            logger.error(f"DNP3 fuzzing error: {str(e)}", exc_info=True)
            result.mark_error(f"DNP3 fuzzing failed: {str(e)}")

        return result

    def _fuzz_opcua(self, test_request: TestRequest) -> TestResult:
        """Fuzz OPC UA protocol"""
        result = self._create_result(test_request)

        try:
            # Check if target is reachable
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(test_request.timeout)

            try:
                sock.connect((test_request.target_host, test_request.target_port))
                sock.close()

                # Simulate OPC UA fuzzing
                result.result_data = {
                    "fuzz_status": "simulated",
                    "protocol": "OPC UA",
                    "test_cases_sent": 0,
                    "crashes_found": 0,
                    "errors_found": 0,
                    "message": "OPC UA fuzzing requires Boofuzz library configuration",
                }
                result.mark_success()
            except (socket.timeout, ConnectionRefusedError) as e:
                result.mark_failed(f"Target not reachable: {str(e)}")
            finally:
                sock.close()

        except Exception as e:
            logger.error(f"OPC UA fuzzing error: {str(e)}", exc_info=True)
            result.mark_error(f"OPC UA fuzzing failed: {str(e)}")

        return result

    def _fuzz_generic(self, test_request: TestRequest) -> TestResult:
        """Generic protocol fuzzing"""
        result = self._create_result(test_request)

        try:
            # Check if target is reachable
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(test_request.timeout)

            try:
                sock.connect((test_request.target_host, test_request.target_port))
                sock.close()

                # Simulate generic fuzzing
                result.result_data = {
                    "fuzz_status": "simulated",
                    "protocol": "Generic",
                    "test_cases_sent": 0,
                    "crashes_found": 0,
                    "errors_found": 0,
                    "message": "Generic fuzzing requires Boofuzz library configuration",
                }
                result.mark_success()
            except (socket.timeout, ConnectionRefusedError) as e:
                result.mark_failed(f"Target not reachable: {str(e)}")
            finally:
                sock.close()

        except Exception as e:
            logger.error(f"Generic fuzzing error: {str(e)}", exc_info=True)
            result.mark_error(f"Generic fuzzing failed: {str(e)}")

        return result
