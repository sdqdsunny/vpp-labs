#!/usr/bin/env python3
"""
Test MQTT Data Flow for FUXA Dashboard
Verifies that MQTT topics are publishing data correctly
"""

import json
import time
import paho.mqtt.client as mqtt
from datetime import datetime

# Configuration
MQTT_BROKER = "localhost"
MQTT_PORT = 1883
TOPICS = [
    "vpp/traffic/stats",
    "vpp/traffic/rate",
    "vpp/traffic/protocols",
    "vpp/traffic/flows",
    "vpp/traffic/components/master",
    "vpp/traffic/components/vcc",
    "vpp/traffic/components/upf",
    "vpp/traffic/components/gen"
]

# Track received messages
received_messages = {}
message_count = 0

def on_connect(client, userdata, flags, rc):
    """Callback when connected to MQTT broker"""
    if rc == 0:
        print(f"✓ Connected to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}")
        print(f"\nSubscribing to {len(TOPICS)} topics...")
        for topic in TOPICS:
            client.subscribe(topic)
            print(f"  - {topic}")
        print("\nListening for messages (Ctrl+C to stop)...\n")
    else:
        print(f"✗ Connection failed with code {rc}")

def on_message(client, userdata, msg):
    """Callback when message received"""
    global message_count, received_messages
    
    message_count += 1
    topic = msg.topic
    
    try:
        payload = json.loads(msg.payload.decode())
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Store message
        if topic not in received_messages:
            received_messages[topic] = []
        received_messages[topic].append({
            'timestamp': timestamp,
            'payload': payload
        })
        
        # Print message
        print(f"[{timestamp}] Topic: {topic}")
        print(f"  Payload: {json.dumps(payload, indent=2)}")
        print()
        
    except json.JSONDecodeError:
        print(f"✗ Invalid JSON on topic {topic}: {msg.payload}")
    except Exception as e:
        print(f"✗ Error processing message: {e}")

def on_disconnect(client, userdata, rc):
    """Callback when disconnected"""
    if rc != 0:
        print(f"✗ Unexpected disconnection (code {rc})")

def print_summary():
    """Print summary of received messages"""
    print("\n" + "="*60)
    print("MQTT DATA FLOW TEST SUMMARY")
    print("="*60)
    print(f"\nTotal messages received: {message_count}")
    print(f"Topics with data: {len(received_messages)}/{len(TOPICS)}")
    print("\nMessages per topic:")
    for topic in TOPICS:
        count = len(received_messages.get(topic, []))
        status = "✓" if count > 0 else "✗"
        print(f"  {status} {topic}: {count} messages")
    
    print("\n" + "="*60)
    print("FUXA DASHBOARD READINESS CHECK")
    print("="*60)
    
    # Check if all required topics have data
    all_topics_ok = all(topic in received_messages for topic in TOPICS)
    
    if all_topics_ok:
        print("\n✓ All MQTT topics are publishing data")
        print("✓ FUXA dashboard can receive real-time updates")
        print("\nNext steps:")
        print("1. Open FUXA at http://localhost:1881")
        print("2. Import device configuration")
        print("3. Create dashboard with widgets")
        print("4. Verify real-time updates")
    else:
        print("\n✗ Some MQTT topics are not publishing data")
        print("\nMissing topics:")
        for topic in TOPICS:
            if topic not in received_messages:
                print(f"  - {topic}")
        print("\nTroubleshooting:")
        print("1. Check if MQTT publisher is running")
        print("2. Check if analyzer is running")
        print("3. Verify MQTT broker is accessible")

def main():
    """Main function"""
    print("="*60)
    print("MQTT DATA FLOW TEST FOR FUXA DASHBOARD")
    print("="*60)
    print(f"\nBroker: {MQTT_BROKER}:{MQTT_PORT}")
    print(f"Topics: {len(TOPICS)}")
    print(f"Duration: 30 seconds (or Ctrl+C to stop)")
    print("\n" + "="*60 + "\n")
    
    # Create MQTT client
    client = mqtt.Client(client_id="fuxa-test-subscriber")
    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    
    try:
        # Connect to broker
        print(f"Connecting to MQTT broker at {MQTT_BROKER}:{MQTT_PORT}...")
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        
        # Start loop
        client.loop_start()
        
        # Wait for messages (30 seconds)
        time.sleep(30)
        
        # Stop loop
        client.loop_stop()
        client.disconnect()
        
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        client.loop_stop()
        client.disconnect()
    except Exception as e:
        print(f"\n✗ Error: {e}")
    finally:
        print_summary()

if __name__ == "__main__":
    main()
