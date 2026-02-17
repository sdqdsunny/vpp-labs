#!/usr/bin/env python3
"""Unit tests for MQTT Publisher"""

import json
import pytest
from unittest.mock import MagicMock
import sys
import os
import importlib.util

# Load mqtt_publisher module
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location("mqtt_publisher", os.path.join(parent_dir, "mqtt-publisher.py"))
mqtt_publisher_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mqtt_publisher_module)
TrafficPublisher = mqtt_publisher_module.TrafficPublisher


class TestTrafficPublisherInit:
    def test_init_default_parameters(self):
        publisher = TrafficPublisher()
        assert publisher.broker_host == 'localhost'
        assert publisher.broker_port == 1883
        assert publisher.topic_prefix == 'vpp/traffic'
        assert publisher.client_id == 'vpp-analyzer'
        assert publisher.connected is False


class TestTrafficPublisherPublishStats:
    def test_publish_stats_success(self):
        mock_client = MagicMock()
        mock_result = MagicMock()
        mock_result.rc = 0
        mock_client.publish.return_value = mock_result
        
        publisher = TrafficPublisher()
        publisher.client = mock_client
        
        stats = {
            'total_packets': 1234567,
            'packet_rate': 12.3,
            'protocol_distribution': {'IEC61850': 450000},
            'top_flows': [('10.0.1.10->10.0.1.20', 450000)],
            'components': {'master': {'packets': 450000, 'bytes': 123456789}}
        }
        
        result = publisher.publish_stats(stats)
        assert result is True
        
        call_args = mock_client.publish.call_args
        assert call_args[0][0] == 'vpp/traffic/stats'
        payload = json.loads(call_args[0][1])
        assert payload['total_packets'] == 1234567
        assert 'timestamp' in payload


class TestTrafficPublisherPublishAll:
    def test_publish_all_success(self):
        mock_client = MagicMock()
        mock_result = MagicMock()
        mock_result.rc = 0
        mock_client.publish.return_value = mock_result
        
        publisher = TrafficPublisher()
        publisher.client = mock_client
        
        stats = {
            'total_packets': 1234567,
            'packet_rate': 12.3,
            'protocol_distribution': {'IEC61850': 450000},
            'top_flows': [('10.0.1.10->10.0.1.20', 450000)],
            'components': {
                'master': {'packets': 450000, 'bytes': 123456789},
                'vcc': {'packets': 370000, 'bytes': 98765432},
                'upf': {'packets': 250000, 'bytes': 87654321},
                'gen': {'packets': 150000, 'bytes': 65432109}
            }
        }
        
        result = publisher.publish_all(stats)
        assert result is True
        assert mock_client.publish.call_count == 8


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
