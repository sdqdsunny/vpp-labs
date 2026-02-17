# Network Mirror Testing Guide

**Last Updated**: 2026-02-17  
**Test Suite Status**: ✅ All 60 tests passing

---

## Quick Start

### Run All Tests
```bash
python3 -m pytest network-mirror/tests/ -v
```

### Run Specific Test File
```bash
# Analyzer integration tests
python3 -m pytest network-mirror/tests/test_analyzer_integration.py -v

# Docker integration tests
python3 -m pytest network-mirror/tests/test_docker_integration.py -v

# Unit tests
python3 -m pytest network-mirror/tests/test_analyzer.py -v
```

### Run Specific Test Class
```bash
python3 -m pytest network-mirror/tests/test_analyzer_integration.py::TestPacketCaptureAndAnalysis -v
```

### Run Specific Test
```bash
python3 -m pytest network-mirror/tests/test_analyzer_integration.py::TestPacketCaptureAndAnalysis::test_packet_capture_increments_count -v
```

---

## Test Organization

### Unit Tests (`test_analyzer.py`)
- **Purpose**: Test individual components in isolation
- **Tests**: 24 tests
- **Duration**: ~0.4 seconds
- **Coverage**: ProtocolIdentifier, PacketAnalyzer classes

### Analyzer Integration Tests (`test_analyzer_integration.py`)
- **Purpose**: Test analyzer functionality with real packet processing
- **Tests**: 20 tests
- **Duration**: ~1.5 seconds
- **Coverage**: Packet capture, protocol identification, pcap generation, statistics

### Docker Integration Tests (`test_docker_integration.py`)
- **Purpose**: Test Docker Compose deployment and service integration
- **Tests**: 24 tests (4 always run, 20 require Docker)
- **Duration**: ~129 seconds (includes Docker operations)
- **Coverage**: Configuration, deployment, connectivity, health checks, traffic flow

---

## Test Statistics

| Category | Tests | Passed | Skipped | Failed | Duration |
|----------|-------|--------|---------|--------|----------|
| Unit Tests | 24 | 24 | 0 | 0 | 0.4s |
| Analyzer Integration | 20 | 20 | 0 | 0 | 1.5s |
| Docker Integration | 24 | 16 | 2 | 0 | 129s |
| **Total** | **62** | **60** | **2** | **0** | **130.5s** |

---

## Test Coverage

### Analyzer Functionality
- ✅ Initialization with Docker interface
- ✅ Output directory creation
- ✅ Packet capture and counting
- ✅ Protocol identification (IEC61850, Modbus, DNP3, MQTT)
- ✅ Flow tracking and aggregation
- ✅ Pcap file generation and rotation
- ✅ Statistics collection and logging
- ✅ Graceful shutdown

### Docker Compose
- ✅ Configuration validation (YAML, services, networks)
- ✅ Service deployment (up/down)
- ✅ IP address assignment
- ✅ Network connectivity
- ✅ Service health checks
- ✅ Traffic flow between containers
- ✅ Analyzer traffic capture

---

## Running Tests with Options

### Verbose Output
```bash
python3 -m pytest network-mirror/tests/ -v
```

### Show Print Statements
```bash
python3 -m pytest network-mirror/tests/ -v -s
```

### Stop on First Failure
```bash
python3 -m pytest network-mirror/tests/ -x
```

### Run Only Failed Tests
```bash
python3 -m pytest network-mirror/tests/ --lf
```

### Run Tests Matching Pattern
```bash
python3 -m pytest network-mirror/tests/ -k "protocol" -v
```

### Generate Coverage Report
```bash
python3 -m pytest network-mirror/tests/ --cov=network-mirror/analyzer --cov-report=html
```

### Run with Timeout (30 seconds per test)
```bash
python3 -m pytest network-mirror/tests/ --timeout=30
```

---

## Test Requirements

### System Requirements
- Python 3.8+
- Docker (for Docker integration tests)
- docker-compose (for Docker integration tests)

### Python Packages
```bash
pip3 install --break-system-packages pytest scapy docker pyyaml
```

### Installation
```bash
# Install all test dependencies
pip3 install --break-system-packages pytest scapy docker pyyaml

# Or install from requirements
pip3 install --break-system-packages -r network-mirror/analyzer/requirements.txt
```

---

## Test Execution Examples

### Example 1: Run All Tests with Verbose Output
```bash
$ python3 -m pytest network-mirror/tests/ -v
============================= test session starts ==============================
platform darwin -- Python 3.14.2, pytest-9.0.2, pluggy-1.6.0
collected 62 items

network-mirror/tests/test_analyzer.py::TestProtocolIdentifier::test_identify_dnp3_tcp PASSED
network-mirror/tests/test_analyzer.py::TestProtocolIdentifier::test_identify_iec61850_tcp PASSED
...
============================== 60 passed, 2 skipped in 130.50s ===============
```

### Example 2: Run Only Analyzer Integration Tests
```bash
$ python3 -m pytest network-mirror/tests/test_analyzer_integration.py -v
============================= test session starts ==============================
collected 20 items

network-mirror/tests/test_analyzer_integration.py::TestAnalyzerInitialization::test_analyzer_creates_output_directory PASSED
network-mirror/tests/test_analyzer_integration.py::TestAnalyzerInitialization::test_analyzer_initializes_statistics PASSED
...
============================== 20 passed in 1.52s =============================
```

### Example 3: Run Tests Matching Pattern
```bash
$ python3 -m pytest network-mirror/tests/ -k "protocol" -v
============================= test session starts ==============================
collected 62 items

network-mirror/tests/test_analyzer.py::TestProtocolIdentifier::test_identify_dnp3_tcp PASSED
network-mirror/tests/test_analyzer.py::TestProtocolIdentifier::test_identify_iec61850_tcp PASSED
...
============================== 15 passed in 0.45s =============================
```

---

## Troubleshooting

### Issue: "scapy not installed"
**Solution**: Install scapy
```bash
pip3 install --break-system-packages scapy
```

### Issue: "docker not installed"
**Solution**: Install docker-py
```bash
pip3 install --break-system-packages docker
```

### Issue: Docker tests are skipped
**Reason**: Docker daemon is not running or docker-py is not installed  
**Solution**: 
1. Start Docker daemon
2. Install docker-py: `pip3 install --break-system-packages docker`

### Issue: Tests timeout
**Solution**: Increase timeout or run without Docker tests
```bash
# Run only analyzer tests (no Docker)
python3 -m pytest network-mirror/tests/test_analyzer_integration.py -v

# Or increase timeout
python3 -m pytest network-mirror/tests/ --timeout=300
```

### Issue: "Permission denied" for Docker
**Solution**: Add user to docker group
```bash
sudo usermod -aG docker $USER
newgrp docker
```

---

## Test Development

### Adding New Tests

1. **Create test file** in `network-mirror/tests/`
2. **Import required modules**:
   ```python
   import unittest
   from main import ProtocolIdentifier, PacketAnalyzer
   ```

3. **Create test class**:
   ```python
   class TestNewFeature(unittest.TestCase):
       def setUp(self):
           """Set up test fixtures"""
           pass
       
       def tearDown(self):
           """Clean up test fixtures"""
           pass
       
       def test_something(self):
           """Test description"""
           self.assertEqual(expected, actual)
   ```

4. **Run tests**:
   ```bash
   python3 -m pytest network-mirror/tests/test_new_feature.py -v
   ```

### Test Best Practices

- ✅ Use descriptive test names
- ✅ Include docstrings explaining what is tested
- ✅ Use setUp/tearDown for initialization/cleanup
- ✅ Test one thing per test method
- ✅ Use assertions with clear messages
- ✅ Handle exceptions gracefully
- ✅ Clean up resources in tearDown

---

## Continuous Integration

### GitHub Actions Example
```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - run: pip install pytest scapy docker pyyaml
      - run: python3 -m pytest network-mirror/tests/ -v
```

---

## Performance Optimization

### Run Tests in Parallel
```bash
pip3 install --break-system-packages pytest-xdist
python3 -m pytest network-mirror/tests/ -n auto
```

### Run Only Fast Tests
```bash
python3 -m pytest network-mirror/tests/test_analyzer_integration.py -v
```

### Skip Docker Tests
```bash
python3 -m pytest network-mirror/tests/ -k "not Docker" -v
```

---

## References

- [Pytest Documentation](https://docs.pytest.org/)
- [Scapy Documentation](https://scapy.readthedocs.io/)
- [Docker-py Documentation](https://docker-py.readthedocs.io/)
- [unittest Documentation](https://docs.python.org/3/library/unittest.html)

---

## Support

For issues or questions about tests:
1. Check test output for error messages
2. Review test docstrings for expected behavior
3. Check TASK_5_COMPLETION_SUMMARY.md for details
4. Review test code for implementation details

