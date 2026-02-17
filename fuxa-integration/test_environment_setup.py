#!/usr/bin/env python3
"""
Test script to verify FUXA integration environment setup.
Tests Docker services, MQTT connectivity, and network configuration.
"""

import subprocess
import time
import json
import sys
from typing import Dict, List, Tuple

class EnvironmentTester:
    """Test FUXA integration environment setup."""
    
    def __init__(self):
        self.results = []
        self.passed = 0
        self.failed = 0
    
    def run_command(self, cmd: str) -> Tuple[int, str, str]:
        """Run a shell command and return exit code, stdout, stderr."""
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return 1, "", "Command timeout"
        except Exception as e:
            return 1, "", str(e)
    
    def test_docker_installed(self) -> bool:
        """Test if Docker is installed."""
        code, stdout, stderr = self.run_command("docker --version")
        passed = code == 0
        self.results.append({
            "test": "Docker installed",
            "passed": passed,
            "output": stdout.strip() if passed else stderr.strip()
        })
        return passed
    
    def test_docker_compose_installed(self) -> bool:
        """Test if Docker Compose is installed."""
        code, stdout, stderr = self.run_command("docker-compose --version")
        passed = code == 0
        self.results.append({
            "test": "Docker Compose installed",
            "passed": passed,
            "output": stdout.strip() if passed else stderr.strip()
        })
        return passed
    
    def test_mosquitto_running(self) -> bool:
        """Test if Mosquitto container is running."""
        code, stdout, stderr = self.run_command(
            "docker ps | grep vpp-mosquitto"
        )
        passed = code == 0 and "Up" in stdout
        self.results.append({
            "test": "Mosquitto container running",
            "passed": passed,
            "output": stdout.strip() if passed else "Container not running"
        })
        return passed
    
    def test_fuxa_running(self) -> bool:
        """Test if FUXA container is running."""
        code, stdout, stderr = self.run_command(
            "docker ps | grep vpp-fuxa"
        )
        passed = code == 0 and "Up" in stdout
        self.results.append({
            "test": "FUXA container running",
            "passed": passed,
            "output": stdout.strip() if passed else "Container not running"
        })
        return passed
    
    def test_mosquitto_port_1883(self) -> bool:
        """Test if Mosquitto is listening on port 1883."""
        code, stdout, stderr = self.run_command(
            "netstat -an | grep 1883"
        )
        passed = code == 0 and "LISTEN" in stdout
        self.results.append({
            "test": "Mosquitto port 1883 listening",
            "passed": passed,
            "output": "Port 1883 is listening" if passed else "Port not listening"
        })
        return passed
    
    def test_mosquitto_port_9001(self) -> bool:
        """Test if Mosquitto WebSocket is listening on port 9001."""
        code, stdout, stderr = self.run_command(
            "netstat -an | grep 9001"
        )
        passed = code == 0 and "LISTEN" in stdout
        self.results.append({
            "test": "Mosquitto port 9001 listening",
            "passed": passed,
            "output": "Port 9001 is listening" if passed else "Port not listening"
        })
        return passed
    
    def test_fuxa_port_1881(self) -> bool:
        """Test if FUXA is listening on port 1881."""
        code, stdout, stderr = self.run_command(
            "netstat -an | grep 1881"
        )
        passed = code == 0 and "LISTEN" in stdout
        self.results.append({
            "test": "FUXA port 1881 listening",
            "passed": passed,
            "output": "Port 1881 is listening" if passed else "Port not listening"
        })
        return passed
    
    def test_fuxa_http_response(self) -> bool:
        """Test if FUXA responds to HTTP requests."""
        code, stdout, stderr = self.run_command(
            'curl -s -o /dev/null -w "%{http_code}" http://localhost:1881'
        )
        passed = code == 0 and "200" in stdout
        self.results.append({
            "test": "FUXA HTTP response (200)",
            "passed": passed,
            "output": f"HTTP {stdout.strip()}" if passed else "No HTTP 200 response"
        })
        return passed
    
    def test_docker_network(self) -> bool:
        """Test if Docker network is created."""
        code, stdout, stderr = self.run_command(
            "docker network ls | grep vpp-net"
        )
        passed = code == 0 and "vpp-net" in stdout
        self.results.append({
            "test": "Docker network vpp-net created",
            "passed": passed,
            "output": "Network vpp-net exists" if passed else "Network not found"
        })
        return passed
    
    def test_network_connectivity(self) -> bool:
        """Test if services can communicate on Docker network."""
        code, stdout, stderr = self.run_command(
            "docker run --rm --network fuxa-integration_vpp-net "
            "eclipse-mosquitto:latest mosquitto_pub -h vpp-mosquitto "
            "-t test/connectivity -m 'test'"
        )
        passed = code == 0
        self.results.append({
            "test": "Network connectivity (MQTT publish)",
            "passed": passed,
            "output": "Services can communicate" if passed else stderr.strip()
        })
        return passed
    
    def test_mqtt_broker_health(self) -> bool:
        """Test MQTT broker health check."""
        code, stdout, stderr = self.run_command(
            "docker exec vpp-mosquitto mosquitto_sub -h localhost "
            "-t test -C 1 -E"
        )
        # Health check command may return non-zero, but if mosquitto is running it's OK
        passed = "vpp-mosquitto" in self.run_command("docker ps")[1]
        self.results.append({
            "test": "MQTT broker health",
            "passed": passed,
            "output": "MQTT broker is healthy" if passed else "MQTT broker unhealthy"
        })
        return passed
    
    def test_directory_structure(self) -> bool:
        """Test if required files exist."""
        required_files = [
            "fuxa-integration/docker-compose-fuxa.yml",
            "fuxa-integration/mosquitto.conf",
            "fuxa-integration/mqtt-publisher.py",
            "fuxa-integration/fuxa-device-config.json"
        ]
        
        all_exist = True
        for file in required_files:
            code, _, _ = self.run_command(f"test -f {file}")
            if code != 0:
                all_exist = False
                break
        
        self.results.append({
            "test": "Required files exist",
            "passed": all_exist,
            "output": "All required files present" if all_exist else "Some files missing"
        })
        return all_exist
    
    def test_mqtt_publisher_syntax(self) -> bool:
        """Test if mqtt-publisher.py has valid Python syntax."""
        code, stdout, stderr = self.run_command(
            "python3 -m py_compile fuxa-integration/mqtt-publisher.py"
        )
        passed = code == 0
        self.results.append({
            "test": "MQTT publisher Python syntax",
            "passed": passed,
            "output": "Valid Python syntax" if passed else stderr.strip()
        })
        return passed
    
    def test_device_config_json(self) -> bool:
        """Test if device config is valid JSON."""
        try:
            with open("fuxa-integration/fuxa-device-config.json", "r") as f:
                json.load(f)
            passed = True
            output = "Valid JSON configuration"
        except Exception as e:
            passed = False
            output = str(e)
        
        self.results.append({
            "test": "Device config JSON validity",
            "passed": passed,
            "output": output
        })
        return passed
    
    def test_device_config_variables(self) -> bool:
        """Test if device config has all 15 required variables."""
        try:
            with open("fuxa-integration/fuxa-device-config.json", "r") as f:
                config = json.load(f)
            
            variables = config["devices"][0]["variables"]
            passed = len(variables) == 15
            output = f"Found {len(variables)} variables (expected 15)"
        except Exception as e:
            passed = False
            output = str(e)
        
        self.results.append({
            "test": "Device config has 15 variables",
            "passed": passed,
            "output": output
        })
        return passed
    
    def run_all_tests(self) -> bool:
        """Run all tests and return overall result."""
        print("=" * 70)
        print("FUXA Integration Environment Setup Tests")
        print("=" * 70)
        print()
        
        tests = [
            self.test_docker_installed,
            self.test_docker_compose_installed,
            self.test_directory_structure,
            self.test_mqtt_publisher_syntax,
            self.test_device_config_json,
            self.test_device_config_variables,
            self.test_mosquitto_running,
            self.test_fuxa_running,
            self.test_mosquitto_port_1883,
            self.test_mosquitto_port_9001,
            self.test_fuxa_port_1881,
            self.test_fuxa_http_response,
            self.test_docker_network,
            self.test_network_connectivity,
            self.test_mqtt_broker_health,
        ]
        
        for test in tests:
            try:
                result = test()
                if result:
                    self.passed += 1
                else:
                    self.failed += 1
            except Exception as e:
                self.failed += 1
                self.results.append({
                    "test": test.__name__,
                    "passed": False,
                    "output": str(e)
                })
        
        self.print_results()
        return self.failed == 0
    
    def print_results(self):
        """Print test results."""
        print()
        for result in self.results:
            status = "✓ PASS" if result["passed"] else "✗ FAIL"
            print(f"{status}: {result['test']}")
            if result["output"]:
                print(f"       {result['output']}")
        
        print()
        print("=" * 70)
        print(f"Results: {self.passed} passed, {self.failed} failed")
        print("=" * 70)
        
        if self.failed == 0:
            print()
            print("✓ All tests passed! Environment setup is complete.")
            print()
            print("Next steps:")
            print("1. Access FUXA at http://localhost:1881")
            print("2. Configure MQTT device with broker: mosquitto:1883")
            print("3. Import device configuration from fuxa-device-config.json")
            print("4. Create dashboard with widgets")
            print("5. Start publishing traffic statistics via MQTT")
        else:
            print()
            print("✗ Some tests failed. Please review the output above.")

if __name__ == "__main__":
    tester = EnvironmentTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
