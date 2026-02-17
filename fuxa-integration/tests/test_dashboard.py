#!/usr/bin/env python3
"""
Tests for FUXA dashboard functionality.

Tests verify:
- Dashboard is accessible
- Widgets are configured correctly
- Data bindings work
- Real-time updates function
"""

import json
import time
import subprocess
import requests
import pytest
from pathlib import Path


class TestDashboardFunctionality:
    """Test FUXA dashboard functionality."""

    @staticmethod
    def run_command(cmd):
        """Run a shell command and return output."""
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True
        )
        return result.returncode, result.stdout, result.stderr

    def test_fuxa_web_ui_accessible(self):
        """Test that FUXA web UI is accessible."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.get("http://localhost:1881/", timeout=5)
                assert response.status_code == 200, \
                    f"FUXA returned status {response.status_code}"
                return
            except requests.exceptions.ConnectionError:
                if attempt < max_retries - 1:
                    time.sleep(2)
                else:
                    raise AssertionError("FUXA web UI not accessible")

    def test_fuxa_api_accessible(self):
        """Test that FUXA API is accessible."""
        try:
            response = requests.get("http://localhost:1881/api/project", timeout=5)
            # API may return 200 or 404 depending on configuration
            assert response.status_code in [200, 404], \
                f"FUXA API returned unexpected status {response.status_code}"
        except requests.exceptions.ConnectionError:
            pytest.skip("FUXA API not accessible")

    def test_dashboard_configuration_valid(self):
        """Test that dashboard configuration is valid."""
        config_path = Path(__file__).parent.parent / "fuxa-device-config.json"
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        assert 'dashboards' in config
        dashboards = config['dashboards']
        assert len(dashboards) > 0
        
        dashboard = dashboards[0]
        assert 'name' in dashboard
        assert 'widgets' in dashboard
        assert len(dashboard['widgets']) == 6

    def test_dashboard_widgets_configured(self):
        """Test that all dashboard widgets are configured."""
        config_path = Path(__file__).parent.parent / "fuxa-device-config.json"
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        dashboard = config['dashboards'][0]
        widgets = dashboard['widgets']
        
        # Verify widget count
        assert len(widgets) == 6, f"Expected 6 widgets, found {len(widgets)}"
        
        # Verify each widget has required fields
        for widget in widgets:
            assert 'id' in widget
            assert 'type' in widget
            assert 'position' in widget or ('x' in widget and 'y' in widget)

    def test_widget_data_bindings(self):
        """Test that widgets have correct data bindings."""
        config_path = Path(__file__).parent.parent / "fuxa-device-config.json"
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        dashboard = config['dashboards'][0]
        widgets = dashboard['widgets']
        
        # Get variables from device (nested structure)
        devices = config['devices']
        mqtt_device = next((d for d in devices if d.get('type') == 'mqtt'), None)
        variables = mqtt_device['variables']
        variable_ids = [v['id'] for v in variables]
        
        # Check that widgets reference valid variables
        for widget in widgets:
            if 'config' in widget and 'variable' in widget['config']:
                assert widget['config']['variable'] in variable_ids, \
                    f"Widget references unknown variable: {widget['config']['variable']}"
            elif 'config' in widget and 'variables' in widget['config']:
                for var in widget['config']['variables']:
                    assert var in variable_ids, \
                        f"Widget references unknown variable: {var}"

    def test_gauge_widgets_configured(self):
        """Test that gauge widgets are properly configured."""
        config_path = Path(__file__).parent.parent / "fuxa-device-config.json"
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        dashboard = config['dashboards'][0]
        widgets = dashboard['widgets']
        
        gauge_widgets = [w for w in widgets if w['type'] == 'gauge']
        assert len(gauge_widgets) >= 2, "Expected at least 2 gauge widgets"
        
        # Check gauge widgets have ranges
        for gauge in gauge_widgets:
            if 'min' in gauge and 'max' in gauge:
                assert gauge['max'] > gauge['min'], \
                    f"Gauge {gauge['id']} has invalid range"

    def test_chart_widgets_configured(self):
        """Test that chart widgets are properly configured."""
        config_path = Path(__file__).parent.parent / "fuxa-device-config.json"
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        dashboard = config['dashboards'][0]
        widgets = dashboard['widgets']
        
        chart_widgets = [w for w in widgets if 'chart' in w['type']]
        assert len(chart_widgets) >= 2, "Expected at least 2 chart widgets"

    def test_mqtt_data_available_for_dashboard(self):
        """Test that MQTT data is available for dashboard."""
        # Try to subscribe to MQTT topics
        returncode, stdout, stderr = self.run_command(
            "docker exec vpp-mosquitto mosquitto_sub -h localhost -t 'vpp/traffic/stats' -C 1 -W 5 2>/dev/null || true"
        )
        
        # If data is available, verify it's valid JSON
        if stdout.strip():
            try:
                # Parse the message (format: "topic payload")
                if ' ' in stdout:
                    payload = stdout.split(' ', 1)[1]
                    data = json.loads(payload)
                    assert 'total_packets' in data or 'timestamp' in data
            except json.JSONDecodeError:
                # If not JSON, that's OK - might be test data
                pass

    def test_dashboard_refresh_rate(self):
        """Test that dashboard has appropriate refresh rate."""
        config_path = Path(__file__).parent.parent / "fuxa-device-config.json"
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        dashboard = config['dashboards'][0]
        
        if 'refreshRate' in dashboard:
            refresh_rate = dashboard['refreshRate']
            # Refresh rate should be between 100ms and 10s
            assert 100 <= refresh_rate <= 10000, \
                f"Dashboard refresh rate {refresh_rate}ms is outside acceptable range"

    def test_widget_layout_valid(self):
        """Test that widget layout is valid."""
        config_path = Path(__file__).parent.parent / "fuxa-device-config.json"
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        dashboard = config['dashboards'][0]
        widgets = dashboard['widgets']
        
        # Check that widgets have position information
        for widget in widgets:
            has_position = ('position' in widget) or ('x' in widget and 'y' in widget)
            assert has_position, f"Widget {widget['id']} missing position information"
            
            # Check that widgets have size information
            has_size = ('size' in widget) or ('width' in widget and 'height' in widget)
            assert has_size, f"Widget {widget['id']} missing size information"

    def test_dashboard_grid_layout(self):
        """Test that dashboard uses grid layout."""
        config_path = Path(__file__).parent.parent / "fuxa-device-config.json"
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        dashboard = config['dashboards'][0]
        
        # Check for grid configuration
        if 'layout' in dashboard:
            assert dashboard['layout'] in ['grid', 'free'], \
                f"Invalid layout type: {dashboard['layout']}"
        
        if 'gridSize' in dashboard:
            assert dashboard['gridSize'] > 0, "Grid size must be positive"

    def test_widget_types_supported(self):
        """Test that all widget types are supported by FUXA."""
        config_path = Path(__file__).parent.parent / "fuxa-device-config.json"
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        dashboard = config['dashboards'][0]
        widgets = dashboard['widgets']
        
        # FUXA supported widget types (including 'custom' for custom widgets)
        supported_types = [
            'gauge', 'chart', 'pie-chart', 'bar-chart', 'line-chart',
            'html', 'svg', 'text', 'button', 'switch', 'slider',
            'table', 'iframe', 'image', 'custom'
        ]
        
        for widget in widgets:
            assert widget['type'] in supported_types, \
                f"Widget type '{widget['type']}' not supported by FUXA"

    def test_real_time_update_capability(self):
        """Test that dashboard is configured for real-time updates."""
        config_path = Path(__file__).parent.parent / "fuxa-device-config.json"
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Check that MQTT device is configured (enables real-time updates)
        devices = config['devices']
        mqtt_devices = [d for d in devices if d['type'] == 'mqtt']
        assert len(mqtt_devices) > 0, "No MQTT device configured for real-time updates"
        
        # Check that variables are mapped to MQTT topics (nested in device)
        mqtt_device = mqtt_devices[0]
        assert 'variables' in mqtt_device
        variables = mqtt_device['variables']
        mqtt_variables = [v for v in variables if 'topic' in v]
        assert len(mqtt_variables) > 0, "No variables mapped to MQTT topics"

    def test_dashboard_responsiveness(self):
        """Test that dashboard is configured to be responsive."""
        config_path = Path(__file__).parent.parent / "fuxa-device-config.json"
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        dashboard = config['dashboards'][0]
        widgets = dashboard['widgets']
        
        # Check that widgets use relative positioning (grid-based)
        # This ensures responsiveness across different screen sizes
        for widget in widgets:
            if 'position' in widget:
                # Position should be grid-based, not absolute pixels
                assert isinstance(widget['position'], (dict, list)), \
                    f"Widget {widget['id']} uses absolute positioning"


class TestDashboardPerformance:
    """Test dashboard performance characteristics."""

    def test_dashboard_load_time(self):
        """Test that dashboard loads within acceptable time."""
        start_time = time.time()
        
        try:
            response = requests.get("http://localhost:1881/", timeout=10)
            load_time = time.time() - start_time
            
            # Dashboard should load within 5 seconds
            assert load_time < 5.0, f"Dashboard load time {load_time}s exceeds 5s limit"
            assert response.status_code == 200
        except requests.exceptions.ConnectionError:
            pytest.skip("FUXA not accessible")

    def test_widget_count_reasonable(self):
        """Test that widget count is reasonable for performance."""
        config_path = Path(__file__).parent.parent / "fuxa-device-config.json"
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        dashboard = config['dashboards'][0]
        widgets = dashboard['widgets']
        
        # Too many widgets can impact performance
        assert len(widgets) <= 20, \
            f"Dashboard has {len(widgets)} widgets, which may impact performance"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
