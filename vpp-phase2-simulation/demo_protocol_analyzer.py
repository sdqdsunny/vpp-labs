#!/usr/bin/env python3
"""
Protocol Analyzer Demo Script

Demonstrates how to use the protocol traffic analyzer with simulated data
"""

import json
import time
import random
from datetime import datetime
from services.protocol_analyzer import get_analyzer, PacketInfo, ProtocolType


def generate_sample_packets():
    """Generate sample packets for demonstration"""
    
    protocols = [
        ("IEC61850", 61850),
        ("Modbus", 502),
        ("DNP3", 20000),
        ("MQTT", 1883),
        ("OPC_UA", 4840),
        ("CAN", 0),
        ("RS-232", 0),
        ("RS-485", 0),
        ("LoRaWAN", 8883),
        ("XMPP", 5222),
        ("DL/T", 2404),
        ("PROFINET", 34962),
    ]
    
    ip_pairs = [
        ("192.168.1.100", "192.168.1.200"),
        ("192.168.1.101", "192.168.1.201"),
        ("10.0.0.50", "10.0.0.100"),
        ("172.16.0.10", "172.16.0.20"),
    ]
    
    analyzer = get_analyzer()
    
    print("🔄 生成示例数据包...")
    print("-" * 60)
    
    # Generate 100 sample packets
    for i in range(100):
        protocol, port = random.choice(protocols)
        src_ip, dst_ip = random.choice(ip_pairs)
        
        packet = PacketInfo(
            timestamp=datetime.now().isoformat(),
            protocol=protocol,
            src_ip=src_ip,
            dst_ip=dst_ip,
            src_port=random.randint(10000, 60000),
            dst_port=port if port > 0 else random.randint(10000, 60000),
            size=random.randint(64, 1500),
            payload_preview=f"{protocol} data frame {i}",
            direction=random.choice(["inbound", "outbound"])
        )
        
        analyzer.add_packet(packet)
        
        if (i + 1) % 20 == 0:
            print(f"✓ 已生成 {i + 1} 个数据包")
    
    print("-" * 60)
    print("✅ 数据包生成完成！\n")


def display_summary():
    """Display analysis summary"""
    analyzer = get_analyzer()
    summary = analyzer.get_summary()
    
    print("📊 分析摘要")
    print("=" * 60)
    print(f"总数据包数:     {summary['total_packets']:,}")
    print(f"总数据量:       {summary['total_bytes']:,} 字节")
    print(f"协议类型数:     {summary['total_protocols']}")
    print(f"活跃流数:       {summary['total_flows']}")
    print(f"分析时间:       {summary['timestamp']}")
    print("=" * 60)
    print()


def display_protocol_stats():
    """Display protocol statistics"""
    analyzer = get_analyzer()
    stats = analyzer.get_protocol_stats()
    
    print("📈 协议统计")
    print("=" * 80)
    print(f"{'协议':<15} {'数据包数':<12} {'总字节数':<12} {'平均包大小':<12} {'包/秒':<10}")
    print("-" * 80)
    
    for stat in stats:
        print(f"{stat.protocol:<15} {stat.packet_count:<12,} {stat.total_bytes:<12,} "
              f"{stat.avg_packet_size:<12.2f} {stat.packets_per_second:<10.2f}")
    
    print("=" * 80)
    print()


def display_recent_packets(limit=10):
    """Display recent packets"""
    analyzer = get_analyzer()
    packets = analyzer.get_recent_packets(limit=limit)
    
    print(f"📦 最近 {limit} 个数据包")
    print("=" * 100)
    print(f"{'时间':<20} {'协议':<12} {'源IP':<15} {'目标IP':<15} {'大小':<8} {'方向':<10}")
    print("-" * 100)
    
    for packet in packets:
        time_str = packet['timestamp'].split('T')[1][:8]
        print(f"{time_str:<20} {packet['protocol']:<12} {packet['src_ip']:<15} "
              f"{packet['dst_ip']:<15} {packet['size']:<8} {packet['direction']:<10}")
    
    print("=" * 100)
    print()


def display_flows(limit=10):
    """Display active flows"""
    analyzer = get_analyzer()
    flows = analyzer.get_flows(limit=limit)
    
    print(f"🔗 前 {limit} 条活跃流")
    print("=" * 100)
    print(f"{'源地址':<15} {'目标地址':<15} {'协议':<12} {'数据包数':<12} {'总字节数':<12}")
    print("-" * 100)
    
    for flow in flows:
        print(f"{flow['source']:<15} {flow['destination']:<15} {flow['protocol']:<12} "
              f"{flow['packet_count']:<12,} {flow['total_bytes']:<12,}")
    
    print("=" * 100)
    print()


def display_protocol_breakdown():
    """Display protocol breakdown chart"""
    analyzer = get_analyzer()
    stats = analyzer.get_protocol_stats()
    
    if not stats:
        return
    
    total = sum(s.packet_count for s in stats)
    
    print("📊 协议分布图")
    print("=" * 60)
    
    for stat in stats:
        percentage = (stat.packet_count / total) * 100
        bar_length = int(percentage / 2)
        bar = "█" * bar_length + "░" * (50 - bar_length)
        print(f"{stat.protocol:<12} {bar} {percentage:>5.1f}% ({stat.packet_count})")
    
    print("=" * 60)
    print()


def main():
    """Main demo function"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "VPP 协议流量分析工具 - 演示程序" + " " * 16 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    # Generate sample data
    generate_sample_packets()
    
    # Display analysis results
    display_summary()
    display_protocol_stats()
    display_protocol_breakdown()
    display_recent_packets(limit=15)
    display_flows(limit=10)
    
    # Show how to access via API
    print("🌐 Web 界面访问")
    print("=" * 60)
    print("打开浏览器访问以下地址查看实时分析：")
    print("  http://localhost:8080/analyzer")
    print()
    print("API 端点：")
    print("  GET  /api/analyzer/summary      - 获取分析摘要")
    print("  GET  /api/analyzer/stats        - 获取协议统计")
    print("  GET  /api/analyzer/packets      - 获取数据包列表")
    print("  GET  /api/analyzer/flows        - 获取流量分析")
    print("  POST /api/analyzer/packet       - 添加新数据包")
    print("  POST /api/analyzer/reset        - 重置统计数据")
    print("  GET  /api/analyzer/protocols    - 获取支持的协议列表")
    print("=" * 60)
    print()
    
    # Show example API usage
    print("📝 API 使用示例")
    print("=" * 60)
    print()
    print("1. 添加数据包：")
    print("""
curl -X POST http://localhost:8080/api/analyzer/packet \\
  -H "Content-Type: application/json" \\
  -d '{
    "protocol": "Modbus",
    "src_ip": "192.168.1.100",
    "dst_ip": "192.168.1.200",
    "src_port": 502,
    "dst_port": 502,
    "size": 256,
    "payload_preview": "01 03 00 00 00 0A",
    "direction": "outbound"
  }'
    """)
    
    print("2. 获取协议统计：")
    print("curl http://localhost:8080/api/analyzer/stats")
    print()
    
    print("3. 获取最近数据包（限制100条）：")
    print("curl 'http://localhost:8080/api/analyzer/packets?limit=100'")
    print()
    
    print("4. 按协议过滤数据包：")
    print("curl 'http://localhost:8080/api/analyzer/packets?protocol=Modbus&limit=50'")
    print()
    
    print("=" * 60)
    print()
    
    print("✅ 演示完成！")
    print()


if __name__ == "__main__":
    main()
