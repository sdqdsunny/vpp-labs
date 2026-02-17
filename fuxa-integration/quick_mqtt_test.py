#!/usr/bin/env python3
"""快速测试MQTT数据流"""
import paho.mqtt.client as mqtt
import json
import time

received_topics = []

def on_message(client, userdata, msg):
    """接收消息回调"""
    try:
        data = json.loads(msg.payload.decode())
        print(f"✅ {msg.topic}")
        print(f"   数据: {json.dumps(data, indent=2)[:200]}...")
        received_topics.append(msg.topic)
    except:
        print(f"⚠️  {msg.topic}: {msg.payload.decode()[:100]}")

def on_connect(client, userdata, flags, rc):
    """连接回调"""
    if rc == 0:
        print("✅ 已连接到MQTT Broker")
        client.subscribe("vpp/traffic/#")
        print("📡 订阅主题: vpp/traffic/#\n")
    else:
        print(f"❌ 连接失败，返回码: {rc}")

# 创建客户端
client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

try:
    print("🔍 连接到 localhost:1883...")
    client.connect("localhost", 1883, 60)
    
    # 运行3秒
    client.loop_start()
    time.sleep(3)
    client.loop_stop()
    
    print(f"\n📊 总共接收到 {len(set(received_topics))} 个不同的主题")
    print("主题列表:")
    for topic in sorted(set(received_topics)):
        print(f"  - {topic}")
    
except Exception as e:
    print(f"❌ 错误: {e}")
finally:
    client.disconnect()
