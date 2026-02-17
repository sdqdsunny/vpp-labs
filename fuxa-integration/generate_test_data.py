#!/usr/bin/env python3
"""
Generate Test MQTT Data for FUXA Dashboard
Publishes simulated VPP traffic data to MQTT topics
"""

import json
import time
import random
from datetime import datetime
from mqtt_publisher import TrafficPublisher

def generate_test_stats():
    """Generate test statistics data"""
    return {
        'timestamp': datetime.now().isoformat(),
        'total_packets': random.randint(100000, 1000000),
        'packet_rate': round(random.uniform(100, 10000), 2),
        'protocol_distribution': {
            'IEC61850': random.randint(10000, 100000),
            'Modbus': random.randint(10000, 100000),
            'MQTT': random.randint(10000, 100000),
            'DNP3': random.randint(10000, 100000),
            'Unknown': random.randint(1000, 10000)
        },
        'top_flows': [
            {'src': '10.0.1.10', 'dst': '10.0.1.20', 'packets': random.randint(10000, 50000)},
            {'src': '10.0.1.20', 'dst': '10.0.1.30', 'packets': random.randint(10000, 50000)},
            {'src': '10.0.1.30', 'dst': '10.0.1.40', 'packets': random.randint(10000, 50000)}
        ],
        'components': {
            'master': {
                'packets': random.randint(10000, 100000),
                'bytes': random.randint(1000000, 10000000)
            },
            'vcc': {
                'packets': random.randint(10000, 100000),
                'bytes': random.randint(1000000, 10000000)
            },
            'upf': {
                'packets': random.randint(10000, 100000),
                'bytes': random.randint(1000000, 10000000)
            },
            'gen': {
                'packets': random.randint(10000, 100000),
                'bytes': random.randint(1000000, 10000000)
            }
        }
    }

def main():
    """Main function"""
    print("="*60)
    print("FUXA DASHBOARD TEST DATA GENERATOR")
    print("="*60)
    print("\nGenerating simulated VPP traffic data...")
    print("Publishing to MQTT broker at localhost:1883")
    print("Press Ctrl+C to stop\n")
    print("="*60 + "\n")
    
    # Create publisher
    publisher = TrafficPublisher(
        broker_host='localhost',
        broker_port=1883,
        topic_prefix='vpp/traffic',
        client_id='fuxa-test-publisher'
    )
    
    try:
        # Connect to broker
        print("Connecting to MQTT broker...")
        publisher.connect()
        time.sleep(2)
        
        if not publisher.is_connected():
            print("✗ Failed to connect to MQTT broker")
            return
        
        print("✓ Connected to MQTT broker\n")
        
        # Publish test data continuously
        iteration = 0
        while True:
            iteration += 1
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            # Generate test data
            stats = generate_test_stats()
            
            # Publish to all topics
            print(f"[{timestamp}] Publishing iteration {iteration}...")
            
            # Publish overall stats
            publisher.publish_stats(stats)
            print(f"  ✓ vpp/traffic/stats")
            
            # Publish packet rate
            publisher.publish_packet_rate({'rate': stats['packet_rate']})
            print(f"  ✓ vpp/traffic/rate")
            
            # Publish protocols
            publisher.publish_protocols({'protocols': stats['protocol_distribution']})
            print(f"  ✓ vpp/traffic/protocols")
            
            # Publish flows
            publisher.publish_flows({'flows': stats['top_flows']})
            print(f"  ✓ vpp/traffic/flows")
            
            # Publish component stats
            for component, data in stats['components'].items():
                publisher.publish_component_stats(component, data)
                print(f"  ✓ vpp/traffic/components/{component}")
            
            print()
            
            # Wait 1 second before next iteration
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\nTest data generation stopped by user")
    except Exception as e:
        print(f"\n✗ Error: {e}")
    finally:
        print("\nDisconnecting from MQTT broker...")
        publisher.disconnect()
        print("✓ Disconnected\n")

if __name__ == "__main__":
    main()
