"""
Security Testing Service

Integrates multiple open-source security testing tools:
- PyModbus: Modbus protocol testing
- Boofuzz: Protocol fuzzing
- OpenDNP3: DNP3 protocol testing
- SocketCAN: CAN protocol testing
- python-opcua: OPC UA protocol testing
"""

import logging
import threading
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime
import subprocess
import os

logger = logging.getLogger(__name__)


class TestType(Enum):
    """Security test types"""
    MODBUS_READ = "modbus_read"
    MODBUS_WRITE = "modbus_write"
    MODBUS_SCAN = "modbus_scan"
    DNP3_SCAN = "dnp3_scan"
    DNP3_FUZZ = "dnp3_fuzz"
    OPCUA_CONNECT = "opcua_connect"
    OPCUA_BROWSE = "opcua_browse"
    CAN_SNIFF = "can_sniff"
    CAN_SEND = "can_send"
    BOOFUZZ_MODBUS = "boofuzz_modbus"
    BOOFUZZ_DNP3 = "boofuzz_dnp3"


class TestStatus(Enum):
    """Test execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"


@dataclass
class TestResult:
    """Result of a security test"""
    test_id: str
    test_type: str
    status: str
    start_time: str
    end_time: Optional[str]
    duration: float
    target_host: str
    target_port: int
    result_data: Dict[str, Any]
    error_message: Optional[str]
    vulnerabilities_found: List[str]


class ModbusSecurityTester:
    """Modbus protocol security testing"""
    
    def __init__(self):
        try:
            from pymodbus.client import ModbusTcpClient
            self.ModbusTcpClient = ModbusTcpClient
            self.available = True
        except ImportError:
            logger.warning("PyModbus not installed")
            self.available = False
    
    def test_read_coils(self, host: str, port: int, address: int, count: int = 1) -> Dict:
        """Test reading coils"""
        if not self.available:
            return {"error": "PyModbus not installed"}
        
        try:
            client = self.ModbusTcpClient(host=host, port=port)
            if not client.connect():
                return {"error": "Connection failed"}
            
            result = client.read_coils(address, count)
            client.close()
            
            return {
                "success": True,
                "coils": result.bits if hasattr(result, 'bits') else [],
                "address": address,
                "count": count
            }
        except Exception as e:
            return {"error": str(e)}
    
    def test_read_registers(self, host: str, port: int, address: int, count: int = 1) -> Dict:
        """Test reading registers"""
        if not self.available:
            return {"error": "PyModbus not installed"}
        
        try:
            client = self.ModbusTcpClient(host=host, port=port)
            if not client.connect():
                return {"error": "Connection failed"}
            
            result = client.read_holding_registers(address, count)
            client.close()
            
            return {
                "success": True,
                "registers": result.registers if hasattr(result, 'registers') else [],
                "address": address,
                "count": count
            }
        except Exception as e:
            return {"error": str(e)}
    
    def test_write_coil(self, host: str, port: int, address: int, value: bool) -> Dict:
        """Test writing a coil"""
        if not self.available:
            return {"error": "PyModbus not installed"}
        
        try:
            client = self.ModbusTcpClient(host=host, port=port)
            if not client.connect():
                return {"error": "Connection failed"}
            
            result = client.write_coil(address, value)
            client.close()
            
            return {
                "success": True,
                "address": address,
                "value": value,
                "written": result.isError() == False
            }
        except Exception as e:
            return {"error": str(e)}
    
    def test_scan_devices(self, host: str, port: int = 502) -> Dict:
        """Scan for Modbus devices"""
        if not self.available:
            return {"error": "PyModbus not installed"}
        
        devices = []
        try:
            client = self.ModbusTcpClient(host=host, port=port)
            if client.connect():
                # Try to read from unit ID 1
                result = client.read_coils(0, 1, unit=1)
                if not result.isError():
                    devices.append({
                        "host": host,
                        "port": port,
                        "unit_id": 1,
                        "accessible": True
                    })
                client.close()
        except Exception as e:
            logger.error(f"Scan error: {e}")
        
        return {
            "devices_found": len(devices),
            "devices": devices
        }


class DNP3SecurityTester:
    """DNP3 protocol security testing"""
    
    def __init__(self):
        try:
            import dnp3
            self.dnp3 = dnp3
            self.available = True
        except ImportError:
            logger.warning("OpenDNP3 not installed")
            self.available = False
    
    def test_connection(self, host: str, port: int) -> Dict:
        """Test DNP3 connection"""
        if not self.available:
            return {"error": "OpenDNP3 not installed"}
        
        try:
            # Attempt to connect to DNP3 master
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((host, port))
            sock.close()
            
            return {
                "host": host,
                "port": port,
                "accessible": result == 0,
                "status": "reachable" if result == 0 else "unreachable"
            }
        except Exception as e:
            return {"error": str(e)}
    
    def test_scan_points(self, host: str, port: int) -> Dict:
        """Scan DNP3 points"""
        if not self.available:
            return {"error": "OpenDNP3 not installed"}
        
        return {
            "host": host,
            "port": port,
            "status": "DNP3 scanning requires full OpenDNP3 setup",
            "note": "Install opendnp3 package for full functionality"
        }


class OPCUASecurityTester:
    """OPC UA protocol security testing"""
    
    def __init__(self):
        try:
            from opcua import Client
            self.Client = Client
            self.available = True
        except ImportError:
            logger.warning("python-opcua not installed")
            self.available = False
    
    def test_connection(self, url: str) -> Dict:
        """Test OPC UA connection"""
        if not self.available:
            return {"error": "python-opcua not installed"}
        
        try:
            client = self.Client(url)
            client.connect()
            
            # Get server info
            server_node = client.get_node("i=2257")  # Server node
            server_name = server_node.get_browse_name()
            
            client.disconnect()
            
            return {
                "url": url,
                "connected": True,
                "server_name": str(server_name),
                "status": "accessible"
            }
        except Exception as e:
            return {
                "url": url,
                "connected": False,
                "error": str(e),
                "status": "unreachable"
            }
    
    def test_browse_namespace(self, url: str) -> Dict:
        """Browse OPC UA namespace"""
        if not self.available:
            return {"error": "python-opcua not installed"}
        
        try:
            client = self.Client(url)
            client.connect()
            
            root = client.get_root_node()
            children = []
            
            for child in root.get_children():
                children.append({
                    "name": str(child.get_browse_name()),
                    "node_id": str(child.nodeid)
                })
            
            client.disconnect()
            
            return {
                "url": url,
                "children_count": len(children),
                "children": children[:10]  # Limit to first 10
            }
        except Exception as e:
            return {"error": str(e)}


class CANSecurityTester:
    """CAN protocol security testing"""
    
    def __init__(self):
        self.available = True  # SocketCAN is usually available on Linux
    
    def test_interface_status(self, interface: str = "can0") -> Dict:
        """Check CAN interface status"""
        try:
            result = subprocess.run(
                ["ip", "link", "show", interface],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                return {
                    "interface": interface,
                    "status": "available",
                    "output": result.stdout
                }
            else:
                # CAN interface not found - this is normal in Docker containers
                return {
                    "interface": interface,
                    "status": "not_found",
                    "message": f"CAN interface '{interface}' not found. This is normal in Docker containers without CAN hardware support.",
                    "note": "To test CAN functionality, run on a system with CAN hardware (e.g., Raspberry Pi, industrial PC with CAN adapter)",
                    "error": result.stderr
                }
        except Exception as e:
            return {
                "interface": interface,
                "status": "error",
                "message": "Error checking CAN interface status",
                "note": "This is normal in Docker containers without CAN hardware support",
                "error": str(e)
            }
    
    def test_sniff_traffic(self, interface: str = "can0", duration: int = 5) -> Dict:
        """Sniff CAN traffic"""
        try:
            result = subprocess.run(
                ["candump", interface, "-n", str(duration)],
                capture_output=True,
                text=True,
                timeout=duration + 5
            )
            
            messages = []
            for line in result.stdout.split('\n'):
                if line.strip():
                    messages.append(line)
            
            return {
                "interface": interface,
                "duration": duration,
                "messages_captured": len(messages),
                "messages": messages[:20],  # Limit to first 20
                "note": "No CAN traffic captured. This is normal if no CAN interface exists or no traffic is present."
            }
        except Exception as e:
            return {
                "interface": interface,
                "status": "error",
                "message": "Error sniffing CAN traffic",
                "note": "This is normal in Docker containers without CAN hardware support. To test CAN functionality, run on a system with CAN hardware.",
                "error": str(e)
            }
    
    def test_send_message(self, interface: str, can_id: str, data: str) -> Dict:
        """Send CAN message"""
        try:
            # Format: cansend interface id#data
            result = subprocess.run(
                ["cansend", interface, f"{can_id}#{data}"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            return {
                "interface": interface,
                "can_id": can_id,
                "data": data,
                "sent": result.returncode == 0,
                "status": "success" if result.returncode == 0 else "failed",
                "note": "Failed to send message. This is normal if no CAN interface exists.",
                "error": result.stderr if result.returncode != 0 else None
            }
        except Exception as e:
            return {
                "interface": interface,
                "status": "error",
                "message": "Error sending CAN message",
                "note": "This is normal in Docker containers without CAN hardware support. To test CAN functionality, run on a system with CAN hardware.",
                "error": str(e)
            }


class BoofuzzSecurityTester:
    """Boofuzz protocol fuzzing"""
    
    def __init__(self):
        try:
            import boofuzz
            self.boofuzz = boofuzz
            self.available = True
        except ImportError:
            logger.warning("Boofuzz not installed")
            self.available = False
    
    def test_modbus_fuzz(self, host: str, port: int, duration: int = 10) -> Dict:
        """Fuzz Modbus protocol"""
        if not self.available:
            return {"error": "Boofuzz not installed"}
        
        return {
            "protocol": "Modbus",
            "host": host,
            "port": port,
            "duration": duration,
            "status": "Boofuzz fuzzing requires manual setup",
            "note": "Use boofuzz CLI for full fuzzing capabilities"
        }
    
    def test_dnp3_fuzz(self, host: str, port: int, duration: int = 10) -> Dict:
        """Fuzz DNP3 protocol"""
        if not self.available:
            return {"error": "Boofuzz not installed"}
        
        return {
            "protocol": "DNP3",
            "host": host,
            "port": port,
            "duration": duration,
            "status": "Boofuzz fuzzing requires manual setup",
            "note": "Use boofuzz CLI for full fuzzing capabilities"
        }


class SecurityTestManager:
    """Manages all security tests using adapter pattern"""
    
    def __init__(self):
        """Initialize SecurityTestManager with all available adapters"""
        self.adapters: Dict[str, Any] = {}
        self.test_results: Dict[str, TestResult] = {}
        self.lock = threading.RLock()
        
        # Initialize legacy testers for backward compatibility
        self.modbus_tester = ModbusSecurityTester()
        self.dnp3_tester = DNP3SecurityTester()
        self.opcua_tester = OPCUASecurityTester()
        self.can_tester = CANSecurityTester()
        self.boofuzz_tester = BoofuzzSecurityTester()
        
        # Initialize protocol analyzer integration (optional)
        self.protocol_analyzer_integration = None
        self.persistence_service = None
        
        # Register adapters
        self._register_adapters()
        
        # Initialize optional services
        self._initialize_optional_services()
    
    def _register_adapters(self) -> None:
        """Register all available test adapters"""
        try:
            # Import adapters
            from services.security_adapters.modbus_adapter import ModbusAdapter
            from services.security_adapters.dnp3_adapter import DNP3Adapter
            from services.security_adapters.opcua_adapter import OPCUAAdapter
            from services.security_adapters.can_adapter import CANAdapter
            from services.security_adapters.boofuzz_adapter import BoofuzzAdapter
            
            # Create and register adapters
            adapters_to_register = [
                ModbusAdapter(),
                DNP3Adapter(),
                OPCUAAdapter(),
                CANAdapter(),
                BoofuzzAdapter(),
            ]
            
            for adapter in adapters_to_register:
                self.register_adapter(adapter.name, adapter)
                logger.info(f"Registered adapter: {adapter.name} (available: {adapter.is_available()})")
        except ImportError as e:
            logger.warning(f"Failed to import adapters: {e}. Using legacy testers only.")
    
    def _initialize_optional_services(self) -> None:
        """Initialize optional services like protocol analyzer integration and persistence"""
        try:
            from services.protocol_analyzer_integration import get_integration_service
            self.protocol_analyzer_integration = get_integration_service()
            logger.info("Protocol analyzer integration initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize protocol analyzer integration: {e}")
        
        try:
            from services.test_result_persistence import get_persistence_service
            self.persistence_service = get_persistence_service()
            logger.info("Test result persistence service initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize persistence service: {e}")
    
    def register_adapter(self, name: str, adapter: Any) -> None:
        """Register a test adapter"""
        with self.lock:
            self.adapters[name] = adapter
            logger.debug(f"Adapter '{name}' registered")
    
    def get_adapter(self, adapter_name: str) -> Optional[Any]:
        """Get a registered adapter by name"""
        with self.lock:
            return self.adapters.get(adapter_name)
    
    def get_registered_adapters(self) -> Dict[str, Any]:
        """Get all registered adapters"""
        with self.lock:
            return dict(self.adapters)
    
    def run_modbus_test(self, test_type: str, host: str, port: int, **kwargs) -> Dict:
        """Run Modbus security test"""
        try:
            if test_type == "read_coils":
                return self.modbus_tester.test_read_coils(host, port, **kwargs)
            elif test_type == "read_registers":
                return self.modbus_tester.test_read_registers(host, port, **kwargs)
            elif test_type == "write_coil":
                return self.modbus_tester.test_write_coil(host, port, **kwargs)
            elif test_type == "scan":
                return self.modbus_tester.test_scan_devices(host, port)
            else:
                return {"error": f"Unknown test type: {test_type}"}
        except Exception as e:
            logger.error(f"Modbus test error: {e}")
            return {"error": str(e)}
    
    def run_dnp3_test(self, test_type: str, host: str, port: int, **kwargs) -> Dict:
        """Run DNP3 security test"""
        try:
            if test_type == "connection":
                return self.dnp3_tester.test_connection(host, port)
            elif test_type == "scan":
                return self.dnp3_tester.test_scan_points(host, port)
            else:
                return {"error": f"Unknown test type: {test_type}"}
        except Exception as e:
            logger.error(f"DNP3 test error: {e}")
            return {"error": str(e)}
    
    def run_opcua_test(self, test_type: str, url: str, **kwargs) -> Dict:
        """Run OPC UA security test"""
        try:
            if test_type == "connection":
                return self.opcua_tester.test_connection(url)
            elif test_type == "browse":
                return self.opcua_tester.test_browse_namespace(url)
            else:
                return {"error": f"Unknown test type: {test_type}"}
        except Exception as e:
            logger.error(f"OPC UA test error: {e}")
            return {"error": str(e)}
    
    def run_can_test(self, test_type: str, interface: str = "can0", **kwargs) -> Dict:
        """Run CAN security test"""
        try:
            if test_type == "status":
                return self.can_tester.test_interface_status(interface)
            elif test_type == "sniff":
                duration = kwargs.get("duration", 5)
                return self.can_tester.test_sniff_traffic(interface, duration)
            elif test_type == "send":
                can_id = kwargs.get("can_id", "123")
                data = kwargs.get("data", "0102030405060708")
                return self.can_tester.test_send_message(interface, can_id, data)
            else:
                return {"error": f"Unknown test type: {test_type}"}
        except Exception as e:
            logger.error(f"CAN test error: {e}")
            return {"error": str(e)}
    
    def run_boofuzz_test(self, test_type: str, host: str, port: int, **kwargs) -> Dict:
        """Run Boofuzz fuzzing test"""
        try:
            if test_type == "modbus_fuzz":
                duration = kwargs.get("duration", 10)
                return self.boofuzz_tester.test_modbus_fuzz(host, port, duration)
            elif test_type == "dnp3_fuzz":
                duration = kwargs.get("duration", 10)
                return self.boofuzz_tester.test_dnp3_fuzz(host, port, duration)
            else:
                return {"error": f"Unknown test type: {test_type}"}
        except Exception as e:
            logger.error(f"Boofuzz test error: {e}")
            return {"error": str(e)}
    
    def run_test_with_adapter(self, adapter_name: str, test_request: Any) -> Any:
        """Execute a test using the adapter pattern
        
        Args:
            adapter_name: Name of the adapter to use
            test_request: TestRequest object with test parameters
            
        Returns:
            TestResult object with test results
        """
        adapter = self.get_adapter(adapter_name)
        if not adapter:
            logger.error(f"Adapter '{adapter_name}' not found")
            # Create error result
            from services.security_adapters.base_adapter import TestResult
            result = TestResult()
            result.adapter_name = adapter_name
            result.mark_error(f"Adapter '{adapter_name}' not found")
            return result
        
        if not adapter.is_available():
            logger.warning(f"Adapter '{adapter_name}' is not available")
            from services.security_adapters.base_adapter import TestResult
            result = TestResult()
            result.adapter_name = adapter_name
            result.mark_error(f"Adapter '{adapter_name}' is not available")
            return result
        
        try:
            # Execute test using adapter
            result = adapter.execute_test(test_request)
            
            # Store result
            with self.lock:
                self.test_results[result.test_id] = result
            
            # Integrate with protocol analyzer if available
            if self.protocol_analyzer_integration:
                try:
                    self.protocol_analyzer_integration.format_test_result_for_analyzer(result)
                    if result.vulnerabilities_found:
                        self.protocol_analyzer_integration.tag_flows_with_vulnerability(result)
                    logger.debug(f"Test result {result.test_id} integrated with protocol analyzer")
                except Exception as e:
                    logger.warning(f"Failed to integrate with protocol analyzer: {e}")
            
            # Persist result if service is available
            if self.persistence_service:
                try:
                    self.persistence_service.store_result(result)
                    logger.debug(f"Test result {result.test_id} persisted to database")
                except Exception as e:
                    logger.warning(f"Failed to persist test result: {e}")
            
            logger.info(f"Test {result.test_id} completed with status: {result.status}")
            return result
        except Exception as e:
            logger.error(f"Error executing test with adapter '{adapter_name}': {e}", exc_info=True)
            from services.security_adapters.base_adapter import TestResult
            result = TestResult()
            result.adapter_name = adapter_name
            result.mark_error(f"Test execution failed: {str(e)}")
            return result
    
    def get_test_result(self, test_id: str) -> Optional[Any]:
        """Retrieve a test result by ID
        
        Args:
            test_id: The test ID to retrieve
            
        Returns:
            TestResult object or None if not found
        """
        with self.lock:
            return self.test_results.get(test_id)
    
    def get_available_tools(self) -> Dict[str, bool]:
        """Get availability of all tools
        
        Returns:
            Dictionary with tool names and their availability status
        """
        tools = {
            "pymodbus": self.modbus_tester.available,
            "opendnp3": self.dnp3_tester.available,
            "python_opcua": self.opcua_tester.available,
            "socketcan": self.can_tester.available,
            "boofuzz": self.boofuzz_tester.available
        }
        
        # Add adapter-based tools
        with self.lock:
            for adapter_name, adapter in self.adapters.items():
                tools[adapter_name] = adapter.is_available()
        
        return tools
    
    def get_adapter_info(self) -> Dict[str, Dict[str, Any]]:
        """Get detailed information about all registered adapters
        
        Returns:
            Dictionary with adapter names and their details
        """
        info = {}
        with self.lock:
            for adapter_name, adapter in self.adapters.items():
                info[adapter_name] = {
                    "available": adapter.is_available(),
                    "supported_tests": adapter.get_supported_tests() if hasattr(adapter, 'get_supported_tests') else [],
                }
        return info
    
    def get_test_result_metadata(self, test_id: str) -> Optional[Dict[str, Any]]:
        """Get test result metadata from protocol analyzer integration
        
        Args:
            test_id: The test ID to retrieve
            
        Returns:
            Dictionary with test result metadata or None if not found
        """
        if not self.protocol_analyzer_integration:
            return None
        
        try:
            metadata = self.protocol_analyzer_integration.get_test_result_metadata(test_id)
            if metadata:
                return {
                    'test_id': metadata.test_id,
                    'test_type': metadata.test_type,
                    'adapter_name': metadata.adapter_name,
                    'target_host': metadata.target_host,
                    'target_port': metadata.target_port,
                    'status': metadata.status,
                    'start_time': metadata.start_time,
                    'end_time': metadata.end_time,
                    'duration': metadata.duration,
                    'vulnerabilities': metadata.vulnerabilities,
                    'findings': metadata.findings
                }
            return None
        except Exception as e:
            logger.warning(f"Failed to get test result metadata: {e}")
            return None
    
    def get_vulnerabilities_for_flow(self, source: str, destination: str, protocol: str) -> List[Dict[str, Any]]:
        """Get vulnerabilities tagged for a specific network flow
        
        Args:
            source: Source IP address
            destination: Destination IP address
            protocol: Protocol name
            
        Returns:
            List of vulnerability tags for the flow
        """
        if not self.protocol_analyzer_integration:
            return []
        
        try:
            return self.protocol_analyzer_integration.get_vulnerabilities_for_flow(source, destination, protocol)
        except Exception as e:
            logger.warning(f"Failed to get vulnerabilities for flow: {e}")
            return []
    
    def get_all_tagged_flows(self) -> List[Dict[str, Any]]:
        """Get all network flows tagged with vulnerabilities
        
        Returns:
            List of flows with their vulnerability tags
        """
        if not self.protocol_analyzer_integration:
            return []
        
        try:
            return self.protocol_analyzer_integration.get_all_tagged_flows()
        except Exception as e:
            logger.warning(f"Failed to get tagged flows: {e}")
            return []
    
    def run_dnp3_attack_detection(self, host: str, port: int, packet_data: dict = None, **kwargs) -> Dict:
        """Run DNP3 attack detection test
        
        Args:
            host: Target host
            port: Target port
            packet_data: DNP3 packet data to analyze
            **kwargs: Additional parameters
            
        Returns:
            Dictionary with test results
        """
        try:
            adapter = self.get_adapter("dnp3")
            if not adapter:
                return {
                    "status": "error",
                    "message": "DNP3 adapter not available",
                    "error": "DNP3 adapter not registered"
                }
            
            test_request = TestRequest(
                test_id=f"dnp3_attack_detection_{int(time.time() * 1000)}",
                test_type="detect_attack",
                adapter_name="dnp3",
                target_host=host,
                target_port=port,
                parameters={"packet_data": packet_data or {}},
                timeout=kwargs.get("timeout", 30)
            )
            
            result = adapter.execute_test(test_request)
            return self._format_test_result(result)
        except Exception as e:
            logger.error(f"DNP3 attack detection error: {e}", exc_info=True)
            return {
                "status": "error",
                "message": "DNP3 attack detection failed",
                "error": str(e)
            }

    def run_dnp3_anomaly_analysis(self, host: str, port: int, packet_data: dict = None, **kwargs) -> Dict:
        """Run DNP3 anomaly analysis test
        
        Args:
            host: Target host
            port: Target port
            packet_data: DNP3 packet data to analyze
            **kwargs: Additional parameters
            
        Returns:
            Dictionary with test results
        """
        try:
            adapter = self.get_adapter("dnp3")
            if not adapter:
                return {
                    "status": "error",
                    "message": "DNP3 adapter not available",
                    "error": "DNP3 adapter not registered"
                }
            
            test_request = TestRequest(
                test_id=f"dnp3_anomaly_analysis_{int(time.time() * 1000)}",
                test_type="analyze_anomaly",
                adapter_name="dnp3",
                target_host=host,
                target_port=port,
                parameters={"packet_data": packet_data or {}},
                timeout=kwargs.get("timeout", 30)
            )
            
            result = adapter.execute_test(test_request)
            return self._format_test_result(result)
        except Exception as e:
            logger.error(f"DNP3 anomaly analysis error: {e}", exc_info=True)
            return {
                "status": "error",
                "message": "DNP3 anomaly analysis failed",
                "error": str(e)
            }

    def get_dnp3_alarm_state(self) -> Dict:
        """Get current DNP3 alarm state
        
        Returns:
            Dictionary with alarm state information
        """
        try:
            adapter = self.get_adapter("dnp3")
            if not adapter:
                return {
                    "status": "error",
                    "message": "DNP3 adapter not available"
                }
            
            # Access the attack detector from the adapter
            if hasattr(adapter, 'attack_detector'):
                alarm_state = adapter.attack_detector.get_alarm_state()
                return {
                    "status": "success",
                    "alarm_state": alarm_state,
                    "timestamp": __import__('datetime').datetime.now().isoformat()
                }
            else:
                return {
                    "status": "error",
                    "message": "Attack detector not available in adapter"
                }
        except Exception as e:
            logger.error(f"Error getting DNP3 alarm state: {e}", exc_info=True)
            return {
                "status": "error",
                "message": "Failed to get alarm state",
                "error": str(e)
            }

    def get_dnp3_statistics(self) -> Dict:
        """Get DNP3 detection statistics
        
        Returns:
            Dictionary with detection statistics
        """
        try:
            adapter = self.get_adapter("dnp3")
            if not adapter:
                return {
                    "status": "error",
                    "message": "DNP3 adapter not available"
                }
            
            # Access the attack detector from the adapter
            if hasattr(adapter, 'attack_detector'):
                statistics = adapter.attack_detector.get_statistics()
                return {
                    "status": "success",
                    "statistics": statistics,
                    "timestamp": __import__('datetime').datetime.now().isoformat()
                }
            else:
                return {
                    "status": "error",
                    "message": "Attack detector not available in adapter"
                }
        except Exception as e:
            logger.error(f"Error getting DNP3 statistics: {e}", exc_info=True)
            return {
                "status": "error",
                "message": "Failed to get statistics",
                "error": str(e)
            }

    def get_integration_summary(self) -> Dict[str, Any]:
        """Get summary of protocol analyzer integration
        
        Returns:
            Dictionary with integration statistics
        """
        if not self.protocol_analyzer_integration:
            return {}
        
        try:
            return self.protocol_analyzer_integration.get_integration_summary()
        except Exception as e:
            logger.warning(f"Failed to get integration summary: {e}")
            return {}


# Global manager instance
_manager_instance: Optional[SecurityTestManager] = None


def get_security_manager() -> SecurityTestManager:
    """Get or create the global security test manager"""
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = SecurityTestManager()
    return _manager_instance
