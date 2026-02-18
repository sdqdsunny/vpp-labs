#!/usr/bin/env python3
"""
VPP 流量生成脚本
用于生成虚拟电厂系统的协议流量
"""

import requests
import time
import json
import sys
from datetime import datetime

# 配置 - 支持容器内和容器外运行
import os

# 检测是否在容器内运行
IN_CONTAINER = os.path.exists('/.dockerenv')

if IN_CONTAINER:
    # 容器内使用容器网络名称
    MASTER_URL = "http://vpp-master:8080"
    POWER_GEN_URL = "http://vpp-power-generation:8081"
    STORAGE_URL = "http://vpp-storage:8082"
    DEMAND_URL = "http://vpp-demand:8083"
else:
    # 容器外使用 localhost
    MASTER_URL = "http://localhost:8080"
    POWER_GEN_URL = "http://localhost:8081"
    STORAGE_URL = "http://localhost:8082"
    DEMAND_URL = "http://localhost:8083"

class TrafficGenerator:
    def __init__(self):
        self.session = requests.Session()
        self.packet_count = 0
        
    def log(self, message):
        """打印日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {message}")
    
    def generate_health_checks(self):
        """生成健康检查流量"""
        self.log("=" * 60)
        self.log("生成健康检查流量...")
        self.log("=" * 60)
        
        services = [
            ("主站", MASTER_URL),
            ("电源侧", POWER_GEN_URL),
            ("储能侧", STORAGE_URL),
            ("需求侧", DEMAND_URL),
        ]
        
        self.log(f"检查 {len(services)} 个服务的健康状态...")
        for name, url in services:
            try:
                resp = self.session.get(f"{url}/health", timeout=3)
                if resp.status_code == 200:
                    self.log(f"  ✓ {name} 健康检查: OK")
                    self.packet_count += 1
                else:
                    self.log(f"  ✗ {name} 健康检查失败: {resp.status_code}")
            except Exception as e:
                self.log(f"  ✗ {name} 健康检查异常: {e}")
            time.sleep(0.3)
    
    def generate_analyzer_traffic(self):
        """生成协议分析工具流量"""
        self.log("\n" + "=" * 60)
        self.log("生成协议分析工具流量...")
        self.log("=" * 60)
        
        # 生成模拟数据包
        protocols = ["Modbus", "MQTT", "OPC_UA", "IEC61850", "CAN", "DNP3"]
        services = [
            ("10.0.8.2", "10.0.8.4", "主站->电源侧"),
            ("10.0.8.4", "10.0.8.2", "电源侧->主站"),
            ("10.0.8.2", "10.0.8.5", "主站->储能侧"),
            ("10.0.8.5", "10.0.8.2", "储能侧->主站"),
            ("10.0.8.2", "10.0.8.6", "主站->需求侧"),
            ("10.0.8.6", "10.0.8.2", "需求侧->主站"),
        ]
        
        self.log("添加模拟数据包到分析工具...")
        packet_id = 0
        for protocol in protocols:
            for src_ip, dst_ip, direction_name in services:
                try:
                    packet_data = {
                        "timestamp": datetime.now().isoformat(),
                        "protocol": protocol,
                        "src_ip": src_ip,
                        "dst_ip": dst_ip,
                        "src_port": 5000 + packet_id,
                        "dst_port": 8000 + packet_id,
                        "size": 256 + (packet_id % 512),
                        "payload_preview": f"Protocol: {protocol}, Direction: {direction_name}",
                        "direction": "outbound" if src_ip == "10.0.8.2" else "inbound"
                    }
                    
                    resp = self.session.post(
                        f"{MASTER_URL}/api/analyzer/packet",
                        json=packet_data,
                        timeout=3
                    )
                    
                    if resp.status_code == 200:
                        self.packet_count += 1
                        packet_id += 1
                    
                    time.sleep(0.05)  # 小延迟避免过快
                    
                except Exception as e:
                    self.log(f"  ⚠ 添加数据包失败: {type(e).__name__}")
        
        self.log(f"  ✓ 成功添加 {self.packet_count} 个数据包到分析工具")
        
        # 查询分析摘要
        self.log("\n查询协议分析摘要...")
        try:
            resp = self.session.get(f"{MASTER_URL}/api/analyzer/summary", timeout=3)
            if resp.status_code == 200:
                data = resp.json()
                self.log(f"  ✓ 分析摘要: {data['total_packets']} 个数据包")
        except Exception as e:
            self.log(f"  ⚠ 查询分析摘要失败: {type(e).__name__}")
        
        # 获取协议统计
        self.log("查询协议统计...")
        try:
            resp = self.session.get(f"{MASTER_URL}/api/analyzer/stats", timeout=3)
            if resp.status_code == 200:
                stats = resp.json()
                self.log(f"  ✓ 协议统计: {len(stats)} 种协议")
                for stat in stats[:3]:
                    self.log(f"    - {stat['protocol']}: {stat['packet_count']} 个数据包")
        except Exception as e:
            self.log(f"  ⚠ 查询协议统计失败: {type(e).__name__}")
    
    def generate_test_dashboard_traffic(self):
        """生成测试仪表板流量"""
        self.log("\n" + "=" * 60)
        self.log("生成测试仪表板流量...")
        self.log("=" * 60)
        
        # 获取测试状态
        self.log("查询测试状态...")
        try:
            resp = self.session.get(f"{MASTER_URL}/api/test/status", timeout=3)
            if resp.status_code == 200:
                data = resp.json()
                self.log(f"  ✓ 测试状态: {data['status']}")
                self.packet_count += 1
        except Exception as e:
            self.log(f"  ⚠ 查询测试状态失败: {type(e).__name__}")
    
    def generate_phase1_integration_traffic(self):
        """生成 Phase1 集成流量"""
        self.log("\n" + "=" * 60)
        self.log("生成 Phase1 集成流量...")
        self.log("=" * 60)
        
        # 获取集成状态
        self.log("查询 Phase1 集成状态...")
        try:
            resp = self.session.get(f"{MASTER_URL}/api/phase1/status", timeout=2)
            if resp.status_code == 200:
                data = resp.json()
                self.log(f"  ✓ 集成状态: {data.get('status', 'OK')}")
                self.packet_count += 1
        except requests.Timeout:
            self.log(f"  ⚠ Phase1 集成状态查询超时 (跳过)")
        except Exception as e:
            self.log(f"  ⚠ Phase1 集成状态查询失败: {type(e).__name__}")
    
    def run(self):
        """运行流量生成"""
        self.log("VPP 流量生成脚本启动")
        self.log(f"主站地址: {MASTER_URL}")
        self.log("")
        
        try:
            # 生成各类流量
            self.generate_health_checks()
            self.generate_analyzer_traffic()
            self.generate_test_dashboard_traffic()
            self.generate_phase1_integration_traffic()
            
            # 总结
            self.log("\n" + "=" * 60)
            self.log("流量生成完成！")
            self.log(f"总共生成 {self.packet_count} 个数据包")
            self.log("=" * 60)
            self.log("\n现在打开协议分析工具查看数据:")
            self.log("  http://localhost:8080/analyzer")
            self.log("\n提示:")
            self.log("  1. 点击 '🔄 刷新数据' 获取最新数据")
            self.log("  2. 点击 '▶️ 自动刷新' 启动自动更新")
            self.log("  3. 在三个标签页中查看不同的数据视图")
            
        except KeyboardInterrupt:
            self.log("\n\n脚本被中断")
            sys.exit(0)
        except Exception as e:
            self.log(f"\n\n发生错误: {e}")
            sys.exit(1)

if __name__ == "__main__":
    generator = TrafficGenerator()
    generator.run()
