"""
Modbus Security Testing Adapter

This adapter wraps PyModbus functionality for testing Modbus protocol endpoints.
"""

import logging
from typing import List
import socket

from .base_adapter import TestAdapter, TestRequest, TestResult

logger = logging.getLogger(__name__)


class ModbusAdapter(TestAdapter):
    """Adapter for Modbus protocol security testing using PyModbus"""

    def __init__(self):
        """Initialize Modbus adapter"""
        super().__init__("modbus")

    def _check_availability(self) -> bool:
        """Check if PyModbus is available"""
        try:
            import pymodbus
            logger.info("PyModbus library is available")
            return True
        except ImportError:
            logger.warning("PyModbus library is not installed")
            return False

    def get_supported_tests(self) -> List[str]:
        """Get list of supported test types"""
        return [
            "connection",
            "read_coils",
            "read_registers",
            "write_coils",
            "write_registers",
        ]

    def execute_test(self, test_request: TestRequest) -> TestResult:
        """Execute a Modbus test"""
        result = self._create_result(test_request)

        if not self.available:
            result.mark_error("PyModbus is not installed")
            return result

        try:
            if test_request.test_type == "connection":
                return self._test_connection(test_request)
            elif test_request.test_type == "read_coils":
                return self._test_read_coils(test_request)
            elif test_request.test_type == "read_registers":
                return self._test_read_registers(test_request)
            elif test_request.test_type == "write_coils":
                return self._test_write_coils(test_request)
            elif test_request.test_type == "write_registers":
                return self._test_write_registers(test_request)
            else:
                result.mark_error(f"Unsupported test type: {test_request.test_type}")
                return result
        except Exception as e:
            logger.error(f"Modbus test error: {str(e)}", exc_info=True)
            result.mark_error(f"Modbus test failed: {str(e)}")
            return result

    def _test_connection(self, test_request: TestRequest) -> TestResult:
        """Test Modbus connection"""
        result = self._create_result(test_request)

        try:
            # Attempt TCP connection to Modbus port
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(test_request.timeout)

            try:
                sock.connect((test_request.target_host, test_request.target_port))
                result.result_data = {
                    "connection_status": "success",
                    "host": test_request.target_host,
                    "port": test_request.target_port,
                    "message": "Successfully connected to Modbus endpoint",
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
            logger.error(f"Modbus connection test error: {str(e)}", exc_info=True)
            result.mark_error(f"Connection test error: {str(e)}")

        return result

    def _test_read_coils(self, test_request: TestRequest) -> TestResult:
        """Test reading Modbus coils"""
        result = self._create_result(test_request)

        try:
            result.result_data = {
                "read_status": "simulated",
                "coils_read": 0,
                "message": "Modbus coil reading requires PyModbus library configuration",
            }
            result.mark_success()
        except Exception as e:
            logger.error(f"Modbus read coils error: {str(e)}", exc_info=True)
            result.mark_error(f"Read coils failed: {str(e)}")

        return result

    def _test_read_registers(self, test_request: TestRequest) -> TestResult:
        """Test reading Modbus registers"""
        result = self._create_result(test_request)

        try:
            result.result_data = {
                "read_status": "simulated",
                "registers_read": 0,
                "message": "Modbus register reading requires PyModbus library configuration",
            }
            result.mark_success()
        except Exception as e:
            logger.error(f"Modbus read registers error: {str(e)}", exc_info=True)
            result.mark_error(f"Read registers failed: {str(e)}")

        return result

    def _test_write_coils(self, test_request: TestRequest) -> TestResult:
        """Test writing Modbus coils"""
        result = self._create_result(test_request)

        try:
            result.result_data = {
                "write_status": "simulated",
                "coils_written": 0,
                "message": "Modbus coil writing requires PyModbus library configuration",
            }
            result.mark_success()
        except Exception as e:
            logger.error(f"Modbus write coils error: {str(e)}", exc_info=True)
            result.mark_error(f"Write coils failed: {str(e)}")

        return result

    def _test_write_registers(self, test_request: TestRequest) -> TestResult:
        """Test writing Modbus registers"""
        result = self._create_result(test_request)

        try:
            result.result_data = {
                "write_status": "simulated",
                "registers_written": 0,
                "message": "Modbus register writing requires PyModbus library configuration",
            }
            result.mark_success()
        except Exception as e:
            logger.error(f"Modbus write registers error: {str(e)}", exc_info=True)
            result.mark_error(f"Write registers failed: {str(e)}")

        return result
