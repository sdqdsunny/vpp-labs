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
                return {
                    "interface": interface,
                    "status": "not_found",
                    "error": result.stderr
                }
        except Exception as e:
            return {
                "interface": interface,
                "status": "error",
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
                "messages": messages[:20]  # Limit to first 20
            }
        except Exception as e:
            return {
                "interface": interface,
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
                "status": "success" if result.returncode == 0 else "failed"
            }
        except Exception as e:
            return {
                "interface": interface,
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
    """Manages all security tests"""
    
    def __init__(self):
        self.modbus_tester = ModbusSecurityTester()
        self.dnp3_tester = DNP3SecurityTester()
        self.opcua_tester = OPCUASecurityTester()
        self.can_tester = CANSecurityTester()
        self.boofuzz_tester = BoofuzzSecurityTester()
        
        self.test_results: Dict[str, TestResult] = {}
        self.lock = threading.RLock()
    
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
    
    def get_available_tools(self) -> Dict[str, bool]:
        """Get availability of all tools"""
        return {
            "pymodbus": self.modbus_tester.available,
            "opendnp3": self.dnp3_tester.available,
            "python_opcua": self.opcua_tester.available,
            "socketcan": self.can_tester.available,
            "boofuzz": self.boofuzz_tester.available
        }


# Global manager instance
_manager_instance: Optional[SecurityTestManager] = None


def get_security_manager() -> SecurityTestManager:
    """Get or create the global security test manager"""
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = SecurityTestManager()
    return _manager_instance
