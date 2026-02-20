#!/usr/bin/env python3
"""
VPP 虚拟电厂实时数据交换演示 - 简化版

实时展示三个运行中的服务的数据交换
"""

import requests
import json
import time
from datetime import datetime

# 颜色定义
class C:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_title(text):
    print(f"\n{C.BOLD}{C.CYAN}{'='*80}{C.ENDC}")
    print(f"{C.BOLD}{C.CYAN}{text:^80}{C.ENDC}")
    print(f"{C.BOLD}{C.CYAN}{'='*80}{C.ENDC}\n")

def print_service(name, port, emoji):
    print(f"\n{C.BOLD}{C.GREEN}{emoji} {name} (端口 {port}){C.ENDC}")
    print(f"{C.GREEN}{'-'*80}{C.ENDC}")

def get_data(url):
    try:
        resp = requests.get(url, timeout=3)
        return resp.json() if resp.status_code == 200 else None
    except:
        return None

def format_value(label, value, unit=""):
    return f"  {C.YELLOW}{label:20}{C.ENDC} {C.GREEN}{value:>10.2f}{C.ENDC} {unit}"

def main():
    print_title("VPP 虚拟电厂实时数据交换演示")
    
    print(f"{C.BOLD}系统架构：{C.ENDC}")
    print("""
    ┌─────────────────────────────────────────────────────────┐
    │                  VPP 虚拟电厂系统                         │
    ├─────────────────────────────────────────────────────────┤
    │                                                           │
    │  ⚡ 电源侧              🔋 储能侧              📊 需求侧   │
    │  (Power Gen)          (Storage)           (Demand)      │
    │  Port: 5001           Port: 5002          Port: 5003     │
    │                                                           │
    │  发电数据 ──────────→ 能量平衡 ←────── 负荷需求         │
    │                                                           │
    └─────────────────────────────────────────────────────────┘
    """)
    
    # 实时监控循环
    for cycle in range(1, 6):
        print(f"\n{C.BOLD}{C.CYAN}[{datetime.now().strftime('%H:%M:%S')}] 数据采集周期 {cycle}/5{C.ENDC}")
        
        # 获取数据
        power_data = get_data("http://localhost:5001/generation/status")
        storage_data = get_data("http://localhost:5002/load/status")
        demand_data = get_data("http://localhost:5003/load/status")
        
        # 显示电源侧
        print_service("⚡ 电源侧（Power Generation）", 5001, "⚡")
        if power_data:
            print(format_value("太阳能功率", power_data.get('solar_power', 0), "kW"))
            print(format_value("风能功率", power_data.get('wind_power', 0), "kW"))
            print(format_value("总发电功率", power_data.get('total_power', 0), "kW"))
            print(f"  {C.YELLOW}{'运行状态':20}{C.ENDC} {C.GREEN}{power_data.get('status', 'unknown'):>10}{C.ENDC}")
        else:
            print(f"{C.RED}  ✗ 无法获取数据{C.ENDC}")
        
        # 显示储能侧
        print_service("🔋 储能侧（Storage）", 5002, "🔋")
        if storage_data:
            print(format_value("当前负荷", storage_data.get('current_load', 0), "kW"))
            print(format_value("预测负荷", storage_data.get('forecasted_load', 0), "kW"))
            print(format_value("需求响应", storage_data.get('demand_response', 0), "kW"))
            print(f"  {C.YELLOW}{'运行状态':20}{C.ENDC} {C.GREEN}{storage_data.get('status', 'unknown'):>10}{C.ENDC}")
        else:
            print(f"{C.RED}  ✗ 无法获取数据{C.ENDC}")
        
        # 显示需求侧
        print_service("📊 需求侧（Demand）", 5003, "📊")
        if demand_data:
            print(format_value("当前负荷", demand_data.get('current_load', 0), "kW"))
            print(format_value("预测负荷", demand_data.get('forecasted_load', 0), "kW"))
            print(format_value("需求响应", demand_data.get('demand_response', 0), "kW"))
            print(f"  {C.YELLOW}{'运行状态':20}{C.ENDC} {C.GREEN}{demand_data.get('status', 'unknown'):>10}{C.ENDC}")
        else:
            print(f"{C.RED}  ✗ 无法获取数据{C.ENDC}")
        
        # 显示能量平衡
        if power_data and storage_data and demand_data:
            total_power = power_data.get('total_power', 0)
            current_load = demand_data.get('current_load', 0)
            balance = total_power - current_load
            
            print(f"\n{C.BOLD}{C.CYAN}⚖️ 能量平衡分析{C.ENDC}")
            print(f"{C.CYAN}{'-'*80}{C.ENDC}")
            print(format_value("总发电功率", total_power, "kW"))
            print(format_value("总负荷需求", current_load, "kW"))
            
            if balance > 0:
                print(f"  {C.YELLOW}{'能量盈余':20}{C.ENDC} {C.GREEN}+{balance:>9.2f}{C.ENDC} kW {C.GREEN}(充电){C.ENDC}")
            elif balance < 0:
                print(f"  {C.YELLOW}{'能量不足':20}{C.ENDC} {C.RED}{balance:>10.2f}{C.ENDC} kW {C.RED}(放电){C.ENDC}")
            else:
                print(f"  {C.YELLOW}{'能量平衡':20}{C.ENDC} {C.GREEN}{'完美平衡':>10}{C.ENDC}")
        
        # 显示数据流动
        print(f"\n{C.BOLD}{C.CYAN}🔄 实时数据流动{C.ENDC}")
        print(f"{C.CYAN}{'-'*80}{C.ENDC}")
        print("""
    ⚡ 电源侧
        ↓ 发电数据
    ┌─────────────────┐
    │   能量协调器     │
    └─────────────────┘
        ↙ ↓ ↘
    🔋 储能侧  📊 需求侧
        ↘ ↓ ↙
    ┌─────────────────┐
    │   能量平衡       │
    └─────────────────┘
        """)
        
        if cycle < 5:
            print(f"\n{C.YELLOW}等待 3 秒后进行下一次采集...{C.ENDC}")
            time.sleep(3)
    
    # 总结
    print_title("演示完成")
    print(f"""
{C.BOLD}✓ VPP 虚拟电厂实时数据交换演示已完成！{C.ENDC}

{C.BOLD}关键观察：{C.ENDC}
  • 电源侧实时发电数据（太阳能、风能）
  • 储能侧实时储能状态（充放电）
  • 需求侧实时负荷需求
  • 三侧实时数据交换和能量平衡

{C.BOLD}系统特点：{C.ENDC}
  ✓ 三个应用在同一容器中运行
  ✓ 实时数据同步和协调
  ✓ 完整的 REST API 接口
  ✓ 结构化日志记录
  ✓ 健康检查端点

{C.BOLD}有用的命令：{C.ENDC}
  • 查看日志：{C.YELLOW}docker logs -f vpp-simulation{C.ENDC}
  • 测试 API：{C.YELLOW}curl http://localhost:5001/health{C.ENDC}
  • 查看容器：{C.YELLOW}docker ps{C.ENDC}
  • 停止容器：{C.YELLOW}docker-compose -f docker-compose-simple.yml down{C.ENDC}

{C.BOLD}下一步：{C.ENDC}
  1. 查看 3D 可视化效果
  2. 运行集成测试
  3. 查看详细文档
    """)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{C.YELLOW}演示已中断{C.ENDC}")
    except Exception as e:
        print(f"{C.RED}错误：{str(e)}{C.ENDC}")
