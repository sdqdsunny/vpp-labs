#!/usr/bin/env python3
"""
Tests for FUXA device configuration.

Tests verify:
- Configuration file is valid JSON
- All required variables are defined
- MQTT topics are correctly mapped
- Dashboard configuration is valid
"""

import json
import pytest
from pathlib import Path


class TestFUXADeviceConfiguration:
    """Test FUXA device configuration file."""

    @classmethod
    def setup_class(cls):
        """Load configuration file."""
        config_path = Path(__file__).parent.parent / "fuxa-device-config.json"
        with open(config_path, 'r') as f:
            cls.config = json.load(f)

    def test_config_is_valid_json(self):
        """Test that configuration file is valid JSON."""
        assert self.config is not None
        assert isinstance(self.config, dict)

    def test_config_has_devices(self):
        """Test that configuration has devices section."""
        assert 'devices' in self.config
        assert isinstance(self.config['devices'], list)
        assert len(self.config['devices']) > 0

    def test_mqtt_device_configured(self):
        """Test that MQTT device is configured."""
        devices = self.config['devices']
        mqtt_device = next((d for d in devices if d.get('type') == 'mqtt'), None)
        
        assert mqtt_device is not None, "No MQTT device found"
        assert mqtt_device['id'] == 'vpp-traffic-analyzer'
        assert mqtt_device['name'] == 'VPP Traffic Analyzer'

    def test_mqtt_device_connection_settings(self):
        """Test MQTT device connection settings."""
        devices = self.config['devices']
        mqtt_device = next((d for d in devices if d.get('type') == 'mqtt'), None)
        
        assert 'config' in mqtt_device
        assert 'broker' in mqtt_device['config']
        assert 'mosquitto' in mqtt_device['config']['broker']

    def test_all_required_variables_defined(self):
        """Test that all 15 required variables are defined."""
        required_variables = [
            'total_packets',
            'packet_rate',
            'iec61850_count',
            'modbus_count',
            'mqtt_count',
            'dnp3_count',
            'unknown_count',
            'master_packets',
            'vcc_packets',
            'upf_packets',
            'gen_packets',
            'master_bytes',
            'vcc_bytes',
            'upf_bytes',
            'gen_bytes'
        ]
        
        # Variables are nested inside the device
        devices = self.config['devices']
        mqtt_device = next((d for d in devices if d.get('type') == 'mqtt'), None)
        assert 'variables' in mqtt_device
        variables = mqtt_device['variables']
        variable_ids = [v['id'] for v in variables]
        
        for var in required_variables:
            assert var in variable_ids, f"Required variable '{var}' not found"

    def test_variables_have_mqtt_topics(self):
        """Test that all variables have MQTT topic mappings."""
        devices = self.config['devices']
        mqtt_device = next((d for d in devices if d.get('type') == 'mqtt'), None)
        variables = mqtt_device['variables']
        
        for var in variables:
            assert 'topic' in var, f"Variable {var['id']} missing topic"
            assert var['topic'].startswith('vpp/traffic/'), \
                f"Variable {var['id']} has invalid topic: {var['topic']}"

    def test_variables_have_required_fields(self):
        """Test that all variables have required fields."""
        devices = self.config['devices']
        mqtt_device = next((d for d in devices if d.get('type') == 'mqtt'), None)
        variables = mqtt_device['variables']
        required_fields = ['id', 'name', 'topic', 'type']
        
        for var in variables:
            for field in required_fields:
                assert field in var, \
                    f"Variable {var.get('id', 'unknown')} missing field: {field}"

    def test_statistics_variables(self):
        """Test statistics variables configuration."""
        devices = self.config['devices']
        mqtt_device = next((d for d in devices if d.get('type') == 'mqtt'), None)
        variables = mqtt_device['variables']
        var_dict = {v['id']: v for v in variables}
        
        # Test total_packets
        assert 'total_packets' in var_dict
        assert var_dict['total_packets']['topic'] == 'vpp/traffic/stats'
        assert var_dict['total_packets']['type'] == 'number'
        
        # Test packet_rate
        assert 'packet_rate' in var_dict
        assert var_dict['packet_rate']['topic'] == 'vpp/traffic/rate'
        assert var_dict['packet_rate']['type'] == 'number'

    def test_protocol_variables(self):
        """Test protocol distribution variables configuration."""
        devices = self.config['devices']
        mqtt_device = next((d for d in devices if d.get('type') == 'mqtt'), None)
        variables = mqtt_device['variables']
        var_dict = {v['id']: v for v in variables}
        
        protocol_vars = ['iec61850_count', 'modbus_count', 'mqtt_count', 'dnp3_count', 'unknown_count']
        
        for var_id in protocol_vars:
            assert var_id in var_dict
            assert var_dict[var_id]['topic'] == 'vpp/traffic/protocols'
            assert var_dict[var_id]['type'] == 'number'

    def test_component_variables(self):
        """Test component statistics variables configuration."""
        devices = self.config['devices']
        mqtt_device = next((d for d in devices if d.get('type') == 'mqtt'), None)
        variables = mqtt_device['variables']
        var_dict = {v['id']: v for v in variables}
        
        components = ['master', 'vcc', 'upf', 'gen']
        
        for component in components:
            # Test packets variable
            packets_var = f'{component}_packets'
            assert packets_var in var_dict
            assert var_dict[packets_var]['topic'] == f'vpp/traffic/components/{component}'
            
            # Test bytes variable
            bytes_var = f'{component}_bytes'
            assert bytes_var in var_dict
            assert var_dict[bytes_var]['topic'] == f'vpp/traffic/components/{component}'

    def test_dashboard_configuration(self):
        """Test dashboard configuration."""
        assert 'dashboards' in self.config
        dashboards = self.config['dashboards']
        assert len(dashboards) > 0
        
        dashboard = dashboards[0]
        assert dashboard['name'] == 'VPP Traffic Visualization'
        assert 'widgets' in dashboard
        assert len(dashboard['widgets']) == 6

    def test_dashboard_widgets(self):
        """Test dashboard widgets configuration."""
        dashboard = self.config['dashboards'][0]
        widgets = dashboard['widgets']
        
        # Check widget count
        assert len(widgets) == 6, f"Expected 6 widgets, found {len(widgets)}"
        
        # Check widget types (actual types in config)
        widget_types = [w['type'] for w in widgets]
        expected_types = ['custom', 'gauge', 'gauge', 'chart', 'chart', 'custom']
        
        assert widget_types == expected_types, f"Widget types mismatch: {widget_types}"

    def test_dashboard_refresh_rate(self):
        """Test dashboard refresh rate."""
        dashboard = self.config['dashboards'][0]
        assert 'refreshRate' in dashboard
        assert dashboard['refreshRate'] == 1000  # 1 second

    def test_mqtt_topics_structure(self):
        """Test MQTT topics follow correct structure."""
        if 'topics' in self.config:
            topics = self.config['topics']
            
            for topic in topics:
                assert 'path' in topic
                assert topic['path'].startswith('vpp/traffic/')
                assert 'interval' in topic
                assert isinstance(topic['interval'], int)

    def test_variable_data_types(self):
        """Test that all variables have correct data types."""
        devices = self.config['devices']
        mqtt_device = next((d for d in devices if d.get('type') == 'mqtt'), None)
        variables = mqtt_device['variables']
        
        for var in variables:
            assert var['type'] == 'number', \
                f"Variable {var['id']} has invalid type: {var['type']}"

    def test_variable_ranges(self):
        """Test that variables have appropriate ranges."""
        devices = self.config['devices']
        mqtt_device = next((d for d in devices if d.get('type') == 'mqtt'), None)
        variables = mqtt_device['variables']
        var_dict = {v['id']: v for v in variables}
        
        # Check total_packets has large range
        if 'min' in var_dict['total_packets'] and 'max' in var_dict['total_packets']:
            assert var_dict['total_packets']['max'] >= 10000000
        
        # Check packet_rate has reasonable range
        if 'min' in var_dict['packet_rate'] and 'max' in var_dict['packet_rate']:
            assert var_dict['packet_rate']['max'] >= 100000

    def test_configuration_completeness(self):
        """Test that configuration is complete and ready for import."""
        # Check all major sections exist
        assert 'devices' in self.config
        assert 'dashboards' in self.config
        
        # Check device is complete
        device = self.config['devices'][0]
        assert 'id' in device
        assert 'name' in device
        assert 'type' in device
        assert 'config' in device
        assert 'broker' in device['config']
        
        # Check variables are complete (nested in device)
        assert 'variables' in device
        assert len(device['variables']) == 15
        
        # Check dashboard is complete
        assert len(self.config['dashboards']) == 1
        assert len(self.config['dashboards'][0]['widgets']) == 6


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
