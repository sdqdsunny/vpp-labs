#!/usr/bin/env python3
"""
UAT Test: Generate test data and verify FUXA visualization
"""

import json
import time
import random
from datetime import datetime
import paho.mqtt.client as mqtt

# MQTT Configuration
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
TOPIC_PREFIX = "vpp/traffic"

def generate_test_stats():
    """Generate realistic test statistics"""
    return {
        'timestamp': datetime.now().isoformat(),
        'total_packets': random.randint(500000, 2000000),
        'packet_rate': round(random.uniform(1000, 15000), 2),
        'protocol_distribution': {
            'IEC61850': random.randint(50000, 200000),
            'Modbus': random.randint(40000, 180000),
            'MQTT': random.randint(30000, 150000),
            'DNP3': random.randint(20000, 120000),
            'Unknown': random.randint(5000, 30000)
        },
        'top_flows': [
            {'src': '10.0.1.10', 'dst': '10.0.1.20', 'packets': random.randint(50000, 150000)},
            {'src': '10.0.1.20', 'dst': '10.0.1.30', 'packets': random.randint(40000, 120000)},
            {'src': '10.0.1.30', 'dst': '10.0.1.40', 'packets': random.randint(30000, 100000)}
        ],
        'components': {
            'master': {
                'packets': random.randint(50000, 200000),
                'bytes': random.randint(5000000, 20000000)
            },
            'vcc': {
                'packets': random.randint(40000, 180000),
                'bytes': random.randint(4000000, 18000000)
            },
            'upf': {
                'packets': random.randint(30000, 150000),
                'bytes': random.randint(3000000, 15000000)
            },
            'gen': {
                'packets': random.randint(20000, 120000),
                'bytes': random.randint(2000000, 12000000)
            }
        }
    }

def main():
    """Main UAT test function"""
    print("="*70)
    print("FUXA UAT TEST - Real-time Data Visualization")
    print("="*70)
    print(f"\nTest Configuration:")
    print(f"  MQTT Broker: {MQTT_BROKER}:{MQTT_PORT}")
    print(f"  Topic Prefix: {TOPIC_PREFIX}")
    print(f"  FUXA Dashboard: http://localhost:1881")
    print(f"\nTest Duration: Continuous (Press Ctrl+C to stop)")
    print("="*70 + "\n")
    
    # Create MQTT client
    client = mqtt.Client(client_id="fuxa-uat-test-publisher")
    
    try:
        # Connect to broker
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Connecting to MQTT broker...")
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()
        time.sleep(1)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ✓ Connected to MQTT broker\n")
        
        print("Publishing test data to FUXA dashboard...")
        print("Open http://localhost:1881 to view real-time visualization\n")
        print("-"*70)
        
        iteration = 0
        while True:
            iteration += 1
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            # Generate test data
            stats = generate_test_stats()
            
            # Publish overall stats
            client.publish(
                f"{TOPIC_PREFIX}/stats",
                json.dumps(stats),
                qos=1
            )
            
            # Publish packet rate
            client.publish(
                f"{TOPIC_PREFIX}/rate",
                json.dumps({'timestamp': stats['timestamp'], 'rate': stats['packet_rate']}),
                qos=1
            )
            
            # Publish protocols
            client.publish(
                f"{TOPIC_PREFIX}/protocols",
                json.dumps({'timestamp': stats['timestamp'], 'protocols': stats['protocol_distribution']}),
                qos=1
            )
            
            # Publish flows
            client.publish(
                f"{TOPIC_PREFIX}/flows",
                json.dumps({'timestamp': stats['timestamp'], 'flows': stats['top_flows']}),
                qos=1
            )
            
            # Publish component stats
            for component, data in stats['components'].items():
                client.publish(
                    f"{TOPIC_PREFIX}/components/{component}",
                    json.dumps({
                        'timestamp': stats['timestamp'],
                        'component': component,
                        'packets': data['packets'],
                        'bytes': data['bytes']
                    }),
                    qos=1
                )
            
            # Print summary
            print(f"[{timestamp}] Iteration {iteration:3d} | "
                  f"Packets: {stats['total_packets']:,} | "
                  f"Rate: {stats['packet_rate']:,.1f} pps | "
                  f"Topics: 8")
            
            # Wait 1 second
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\n" + "="*70)
        print("UAT Test stopped by user")
        print("="*70)
    except Exception as e:
        print(f"\n✗ Error: {e}")
    finally:
        client.loop_stop()
        client.disconnect()
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Disconnected from MQTT broker")
        print("\nUAT Test Summary:")
        print(f"  Total iterations: {iteration}")
        print(f"  Total messages published: {iteration * 8}")
        print(f"  FUXA Dashboard: http://localhost:1881")
        print()

if __name__ == "__main__":
    main()
