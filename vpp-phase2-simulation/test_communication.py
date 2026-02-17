#!/usr/bin/env python3
"""
Test script for Phase 1 (Bottle) and Phase 2 (Simulation) communication.

This script verifies that the simulation models can successfully communicate
with the Bottle master station.
"""

import requests
import json
import time
import sys
from datetime import datetime

# Configuration
PHASE2_URL = "http://localhost:5000"
PHASE1_URL = "http://localhost:8080"
TIMEOUT = 10

def print_header(text):
    """Print a formatted header."""
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")

def print_status(status, message):
    """Print a status message."""
    symbol = "✓" if status else "✗"
    print(f"  [{symbol}] {message}")

def test_phase2_health():
    """Test Phase 2 health endpoint."""
    print_header("Testing Phase 2 (Simulation) Health")
    
    try:
        response = requests.get(f"{PHASE2_URL}/health", timeout=TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            print_status(True, f"Phase 2 is healthy: {data.get('status')}")
            return True
        else:
            print_status(False, f"Phase 2 returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_status(False, f"Cannot connect to Phase 2 at {PHASE2_URL}")
        return False
    except Exception as e:
        print_status(False, f"Error: {str(e)}")
        return False

def test_phase1_health():
    """Test Phase 1 health endpoint."""
    print_header("Testing Phase 1 (Bottle Master) Health")
    
    try:
        response = requests.get(f"{PHASE1_URL}/health", timeout=TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            print_status(True, f"Phase 1 is healthy: {data.get('status')}")
            return True
        else:
            print_status(False, f"Phase 1 returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_status(False, f"Cannot connect to Phase 1 at {PHASE1_URL}")
        return False
    except Exception as e:
        print_status(False, f"Error: {str(e)}")
        return False

def test_phase1_integration_health():
    """Test Phase 1 integration health check."""
    print_header("Testing Phase 1 Integration Health Check")
    
    try:
        response = requests.get(f"{PHASE2_URL}/api/phase1/health", timeout=TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            status = data.get('status')
            print_status(True, f"Phase 1 integration health: {status}")
            print(f"    Response time: {data.get('response_time_ms', 'N/A')}ms")
            return status == "healthy"
        else:
            print_status(False, f"Integration health check returned status {response.status_code}")
            return False
    except Exception as e:
        print_status(False, f"Error: {str(e)}")
        return False

def test_phase1_integration_status():
    """Test Phase 1 integration status."""
    print_header("Testing Phase 1 Integration Status")
    
    try:
        response = requests.get(f"{PHASE2_URL}/api/phase1/status", timeout=TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            status = data.get('status')
            print_status(True, f"Integration status: {status}")
            print(f"    Last sync time: {data.get('last_sync_time', 'Never')}")
            print(f"    Last sync type: {data.get('last_sync_type', 'N/A')}")
            print(f"    Sync history count: {data.get('sync_history_count', 0)}")
            return True
        else:
            print_status(False, f"Status check returned status {response.status_code}")
            return False
    except Exception as e:
        print_status(False, f"Error: {str(e)}")
        return False

def test_device_sync():
    """Test device synchronization."""
    print_header("Testing Device Synchronization")
    
    try:
        # Trigger device sync
        response = requests.post(f"{PHASE2_URL}/api/phase1/sync/devices", timeout=TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            status = data.get('status')
            synced = data.get('synced_count', 0)
            errors = data.get('error_count', 0)
            
            print_status(True, f"Device sync completed: {status}")
            print(f"    Synced: {synced} devices")
            print(f"    Errors: {errors}")
            
            if errors > 0:
                print(f"    Error details: {data.get('errors', [])}")
            
            return status == "success"
        else:
            print_status(False, f"Device sync returned status {response.status_code}")
            return False
    except Exception as e:
        print_status(False, f"Error: {str(e)}")
        return False

def test_bottle_devices():
    """Test retrieving devices from Bottle."""
    print_header("Testing Bottle Device Retrieval")
    
    try:
        response = requests.get(f"{PHASE1_URL}/api/v1/devices", timeout=TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            devices = data.get('data', [])
            total = data.get('total_count', 0)
            
            print_status(True, f"Retrieved devices from Bottle")
            print(f"    Total devices: {total}")
            print(f"    Devices in response: {len(devices)}")
            
            if devices:
                print(f"    Sample device: {devices[0].get('device_id', 'N/A')}")
            
            return True
        else:
            print_status(False, f"Device retrieval returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print_status(False, f"Cannot connect to Bottle at {PHASE1_URL}")
        return False
    except Exception as e:
        print_status(False, f"Error: {str(e)}")
        return False

def test_sync_history():
    """Test sync history retrieval."""
    print_header("Testing Sync History")
    
    try:
        response = requests.get(f"{PHASE2_URL}/api/phase1/sync/history?limit=5", timeout=TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            records = data.get('records', [])
            total = data.get('total_count', 0)
            
            print_status(True, f"Retrieved sync history")
            print(f"    Total records: {total}")
            print(f"    Recent records: {len(records)}")
            
            if records:
                for i, record in enumerate(records[-3:], 1):
                    print(f"    Record {i}: {record.get('sync_type')} - {record.get('status')}")
            
            return True
        else:
            print_status(False, f"History retrieval returned status {response.status_code}")
            return False
    except Exception as e:
        print_status(False, f"Error: {str(e)}")
        return False

def test_metrics():
    """Test Prometheus metrics."""
    print_header("Testing Prometheus Metrics")
    
    try:
        response = requests.get(f"{PHASE2_URL}/metrics", timeout=TIMEOUT)
        if response.status_code == 200:
            metrics_text = response.text
            
            # Check for Phase 1 metrics
            has_sync_counter = "phase1_sync_total" in metrics_text
            has_sync_duration = "phase1_sync_duration_seconds" in metrics_text
            has_connection_status = "phase1_connection_status" in metrics_text
            
            print_status(has_sync_counter, "Sync counter metric found")
            print_status(has_sync_duration, "Sync duration metric found")
            print_status(has_connection_status, "Connection status metric found")
            
            return has_sync_counter and has_sync_duration and has_connection_status
        else:
            print_status(False, f"Metrics retrieval returned status {response.status_code}")
            return False
    except Exception as e:
        print_status(False, f"Error: {str(e)}")
        return False

def main():
    """Run all communication tests."""
    print("\n" + "="*60)
    print("  VPP Phase 1 & Phase 2 Communication Test Suite")
    print("  " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("="*60)
    
    results = {}
    
    # Run tests
    results["Phase 2 Health"] = test_phase2_health()
    results["Phase 1 Health"] = test_phase1_health()
    results["Phase 1 Integration Health"] = test_phase1_integration_health()
    results["Phase 1 Integration Status"] = test_phase1_integration_status()
    results["Device Sync"] = test_device_sync()
    results["Bottle Devices"] = test_bottle_devices()
    results["Sync History"] = test_sync_history()
    results["Prometheus Metrics"] = test_metrics()
    
    # Print summary
    print_header("Test Summary")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        symbol = "✓" if result else "✗"
        print(f"  [{symbol}] {test_name}")
    
    print(f"\n  Total: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n  ✓ All tests passed! Communication is working correctly.")
        return 0
    else:
        print(f"\n  ✗ {total - passed} test(s) failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
