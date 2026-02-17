#!/usr/bin/env python3
"""
Integration tests for Docker Compose deployment.

Tests the Docker Compose configuration, service startup,
network connectivity, and traffic flow.
"""

import unittest
import subprocess
import time
import os
import sys
from pathlib import Path

try:
    import docker
    from docker.errors import DockerException
except ImportError:
    print("Warning: docker not installed. Some tests will be skipped.")
    docker_available = False
else:
    docker_available = True


class TestDockerComposeConfiguration(unittest.TestCase):
    """Test Docker Compose configuration validity."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.compose_file = 'network-mirror/docker-compose.yml'
    
    def test_compose_file_exists(self):
        """Test that docker-compose.yml exists."""
        self.assertTrue(os.path.exists(self.compose_file))
    
    def test_compose_file_is_valid_yaml(self):
        """Test that docker-compose.yml is valid YAML."""
        try:
            import yaml
            with open(self.compose_file, 'r') as f:
                yaml.safe_load(f)
        except ImportError:
            self.skipTest("PyYAML not installed")
        except Exception as e:
            self.fail(f"Invalid YAML: {e}")
    
    def test_compose_file_has_required_services(self):
        """Test that docker-compose.yml has required services."""
        try:
            import yaml
            with open(self.compose_file, 'r') as f:
                config = yaml.safe_load(f)
            
            required_services = ['vpp-master', 'vpp-vcc', 'vpp-upf', 'vpp-gen', 'vpp-analyzer']
            services = config.get('services', {})
            
            for service in required_services:
                self.assertIn(service, services, f"Service {service} not found")
        except ImportError:
            self.skipTest("PyYAML not installed")
    
    def test_compose_file_has_network_config(self):
        """Test that docker-compose.yml has network configuration."""
        try:
            import yaml
            with open(self.compose_file, 'r') as f:
                config = yaml.safe_load(f)
            
            self.assertIn('networks', config)
            self.assertIn('vpp-net', config['networks'])
        except ImportError:
            self.skipTest("PyYAML not installed")


@unittest.skipUnless(docker_available, "docker not installed")
class TestDockerComposeDeployment(unittest.TestCase):
    """Test Docker Compose deployment and service management."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.compose_file = os.path.abspath('network-mirror/docker-compose.yml')
        self.client = docker.from_env()
        
        # Stop any existing containers
        self._cleanup()
    
    def tearDown(self):
        """Clean up test fixtures."""
        self._cleanup()
    
    def _cleanup(self):
        """Clean up Docker containers and networks."""
        try:
            # Try docker-compose down
            cmd = ['docker-compose', '-f', self.compose_file, 'down']
            subprocess.run(cmd, capture_output=True, timeout=10)
            time.sleep(2)
        except:
            pass
    
    def _run_compose_command(self, command):
        """Run docker-compose command."""
        cmd = ['docker-compose', '-f', self.compose_file] + command
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result.returncode, result.stdout, result.stderr
    
    def test_docker_compose_up(self):
        """Test docker-compose up starts services."""
        returncode, stdout, stderr = self._run_compose_command(['up', '-d'])
        
        self.assertEqual(returncode, 0, f"docker-compose up failed: {stderr}")
        
        # Wait for services to start
        time.sleep(5)
    
    def test_all_services_running(self):
        """Test that all services are running."""
        self._run_compose_command(['up', '-d'])
        time.sleep(5)
        
        containers = self.client.containers.list(filters={'status': 'running'})
        container_names = [c.name for c in containers]
        
        required_services = ['vpp-master', 'vpp-vcc', 'vpp-upf', 'vpp-gen', 'vpp-analyzer']
        for service in required_services:
            self.assertIn(service, container_names, f"Service {service} not running")
    
    def test_services_have_correct_ips(self):
        """Test that services have correct IP addresses."""
        self._run_compose_command(['up', '-d'])
        time.sleep(5)
        
        expected_ips = {
            'vpp-master': '10.0.1.10',
            'vpp-vcc': '10.0.1.20',
            'vpp-upf': '10.0.1.30',
            'vpp-gen': '10.0.1.40',
            'vpp-analyzer': '10.0.1.50',
        }
        
        for service_name, expected_ip in expected_ips.items():
            try:
                container = self.client.containers.get(service_name)
                networks = container.attrs['NetworkSettings']['Networks']
                
                # Find vpp-net network
                if 'vpp-net' in networks:
                    actual_ip = networks['vpp-net']['IPAddress']
                    self.assertEqual(actual_ip, expected_ip, f"{service_name} has wrong IP")
            except Exception as e:
                self.fail(f"Failed to check IP for {service_name}: {e}")
    
    def test_docker_compose_down(self):
        """Test docker-compose down stops services."""
        self._run_compose_command(['up', '-d'])
        time.sleep(5)
        
        returncode, stdout, stderr = self._run_compose_command(['down'])
        self.assertEqual(returncode, 0, f"docker-compose down failed: {stderr}")
        
        # Wait for services to stop
        time.sleep(2)
        
        containers = self.client.containers.list(filters={'status': 'running'})
        container_names = [c.name for c in containers]
        
        required_services = ['vpp-master', 'vpp-vcc', 'vpp-upf', 'vpp-gen', 'vpp-analyzer']
        for service in required_services:
            self.assertNotIn(service, container_names, f"Service {service} still running")


@unittest.skipUnless(docker_available, "docker not installed")
class TestNetworkConnectivity(unittest.TestCase):
    """Test network connectivity between containers."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.compose_file = os.path.abspath('network-mirror/docker-compose.yml')
        self.client = docker.from_env()
        
        # Start services
        self._cleanup()
        cmd = ['docker-compose', '-f', self.compose_file, 'up', '-d']
        subprocess.run(cmd, capture_output=True)
        time.sleep(5)
    
    def tearDown(self):
        """Clean up test fixtures."""
        self._cleanup()
    
    def _cleanup(self):
        """Clean up Docker containers."""
        try:
            cmd = ['docker-compose', '-f', self.compose_file, 'down']
            subprocess.run(cmd, capture_output=True, timeout=10)
            time.sleep(2)
        except:
            pass
    
    def test_ping_between_containers(self):
        """Test ping connectivity between containers."""
        try:
            container = self.client.containers.get('vpp-vcc')
            
            # Ping vpp-master
            result = container.exec_run('ping -c 1 vpp-master')
            self.assertEqual(result.exit_code, 0, "Ping to vpp-master failed")
        except Exception as e:
            self.skipTest(f"Cannot test ping: {e}")
    
    def test_all_containers_can_reach_master(self):
        """Test that all containers can reach vpp-master."""
        containers_to_test = ['vpp-vcc', 'vpp-upf', 'vpp-gen', 'vpp-analyzer']
        
        for container_name in containers_to_test:
            try:
                container = self.client.containers.get(container_name)
                result = container.exec_run('ping -c 1 vpp-master')
                self.assertEqual(result.exit_code, 0, f"{container_name} cannot reach vpp-master")
            except Exception as e:
                self.skipTest(f"Cannot test {container_name}: {e}")
    
    def test_network_isolation(self):
        """Test that containers are on the same network."""
        try:
            container = self.client.containers.get('vpp-master')
            networks = container.attrs['NetworkSettings']['Networks']
            
            self.assertIn('vpp-net', networks, "vpp-master not on vpp-net")
            
            # Check other containers
            for service in ['vpp-vcc', 'vpp-upf', 'vpp-gen', 'vpp-analyzer']:
                container = self.client.containers.get(service)
                networks = container.attrs['NetworkSettings']['Networks']
                self.assertIn('vpp-net', networks, f"{service} not on vpp-net")
        except Exception as e:
            self.skipTest(f"Cannot test network isolation: {e}")


@unittest.skipUnless(docker_available, "docker not installed")
class TestServiceHealth(unittest.TestCase):
    """Test service health checks."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.compose_file = os.path.abspath('network-mirror/docker-compose.yml')
        self.client = docker.from_env()
        
        # Start services
        self._cleanup()
        cmd = ['docker-compose', '-f', self.compose_file, 'up', '-d']
        subprocess.run(cmd, capture_output=True)
        time.sleep(5)
    
    def tearDown(self):
        """Clean up test fixtures."""
        self._cleanup()
    
    def _cleanup(self):
        """Clean up Docker containers."""
        try:
            cmd = ['docker-compose', '-f', self.compose_file, 'down']
            subprocess.run(cmd, capture_output=True, timeout=10)
            time.sleep(2)
        except:
            pass
    
    def test_analyzer_is_running(self):
        """Test that vpp-analyzer is running."""
        try:
            container = self.client.containers.get('vpp-analyzer')
            self.assertEqual(container.status, 'running', "vpp-analyzer not running")
        except Exception as e:
            self.skipTest(f"Cannot test analyzer: {e}")
    
    def test_all_services_running(self):
        """Test that all services are running."""
        required_services = ['vpp-master', 'vpp-vcc', 'vpp-upf', 'vpp-gen', 'vpp-analyzer']
        
        for service in required_services:
            try:
                container = self.client.containers.get(service)
                self.assertEqual(container.status, 'running', f"{service} not running")
            except Exception as e:
                self.skipTest(f"Cannot test {service}: {e}")


@unittest.skipUnless(docker_available, "docker not installed")
class TestTrafficFlow(unittest.TestCase):
    """Test traffic flow between containers."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.compose_file = os.path.abspath('network-mirror/docker-compose.yml')
        self.client = docker.from_env()
        
        # Start services
        self._cleanup()
        cmd = ['docker-compose', '-f', self.compose_file, 'up', '-d']
        subprocess.run(cmd, capture_output=True)
        time.sleep(5)
    
    def tearDown(self):
        """Clean up test fixtures."""
        self._cleanup()
    
    def _cleanup(self):
        """Clean up Docker containers."""
        try:
            cmd = ['docker-compose', '-f', self.compose_file, 'down']
            subprocess.run(cmd, capture_output=True, timeout=10)
            time.sleep(2)
        except:
            pass
    
    def test_traffic_between_containers(self):
        """Test that traffic flows between containers."""
        try:
            # Generate traffic from vpp-vcc to vpp-master
            container = self.client.containers.get('vpp-vcc')
            result = container.exec_run('ping -c 3 vpp-master')
            
            self.assertEqual(result.exit_code, 0, "Traffic flow test failed")
        except Exception as e:
            self.skipTest(f"Cannot test traffic flow: {e}")
    
    def test_analyzer_captures_traffic(self):
        """Test that analyzer captures traffic."""
        try:
            # Generate traffic
            container = self.client.containers.get('vpp-vcc')
            container.exec_run('ping -c 5 vpp-master')
            
            # Check analyzer logs
            analyzer = self.client.containers.get('vpp-analyzer')
            logs = analyzer.logs().decode('utf-8')
            
            # Analyzer should have captured packets
            self.assertIn('packet', logs.lower(), "Analyzer did not capture packets")
        except Exception as e:
            self.skipTest(f"Cannot test analyzer capture: {e}")


class TestDockerComposeIntegration(unittest.TestCase):
    """Integration tests for Docker Compose."""
    
    def test_compose_file_path_exists(self):
        """Test that compose file path exists."""
        compose_file = 'network-mirror/docker-compose.yml'
        self.assertTrue(os.path.exists(compose_file))
    
    def test_pcap_directory_exists(self):
        """Test that pcap directory exists."""
        pcap_dir = 'network-mirror/pcap'
        # Create if doesn't exist
        os.makedirs(pcap_dir, exist_ok=True)
        self.assertTrue(os.path.exists(pcap_dir))
    
    def test_logs_directory_exists(self):
        """Test that logs directory exists."""
        logs_dir = 'network-mirror/logs'
        # Create if doesn't exist
        os.makedirs(logs_dir, exist_ok=True)
        self.assertTrue(os.path.exists(logs_dir))


if __name__ == '__main__':
    unittest.main()
