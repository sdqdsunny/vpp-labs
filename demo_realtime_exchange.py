#!/usr/bin/env python3
"""
VPP 虚拟电厂实时数据交换演示工具

实时展示：
1. 电源侧（Power Generation）的发电数据
2. 储能侧（Storage）的储能状态
3. 需求侧（Demand）的负荷需求
4. 三侧的实时数据交换
"""

import requests
import json
import time
from datetime import datetime
from typing import Dict, Any
import sys

# 配置
POWER_GEN_URL = "http://localhost:5001"
STORAGE_URL = "http://localhost:5002"
DEMAND_URL = "http://localhost:5003"
COORDINATOR_URL = "http://localhost:8000"

# 颜色定义
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text: str):
    """打印标题"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text:^70}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.ENDC}\n")

def print_section(title: str):
    """打印分段标题"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}▶ {title}{Colors.ENDC}")
    print(f"{Colors.BLUE}{'-'*70}{Colors.ENDC}")

def print_success(text: str):
    """打印成功信息"""
    print(f"{Colors.GREEN}✓ {text}{Colors.ENDC}")

def print_error(text: str):
    """打印错误信息"""
    print(f"{Colors.RED}✗ {text}{Colors.ENDC}")

def print_info(text: str):
    """打印信息"""
    print(f"{Colors.YELLOW}ℹ {text}{Colors.ENDC}")

def get_service_status(url: str, service_name: str) -> Dict[str, Any]:
    """获取服务状态"""
    try:
        response = requests.get(f"{url}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            return {
                "status": "healthy",
                "data": data
            }
        else:
            return {
                "status": "unhealthy",
                "error": f"HTTP {response.status_code}"
            }
    except requests.exceptions.ConnectionError:
        return {
            "status": "offline",
            "error": "Connection refused"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

def get_power_generation_data() -> Dict[str, Any]:
    """获取电源侧数据"""
    try:
        response = requests.get(f"{POWER_GEN_URL}/generation/status", timeout=5)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def get_storage_data() -> Dict[str, Any]:
    """获取储能侧数据"""
    try:
        response = requests.get(f"{STORAGE_URL}/load/status", timeout=5)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def get_demand_data() -> Dict[str, Any]:
    """获取需求侧数据"""
    try:
        response = requests.get(f"{DEMAND_URL}/load/status", timeout=5)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def display_power_generation(data: Dict[str, Any]):
    """显示电源侧数据"""
    print_section("⚡ 电源侧（Power Generation）")
    
    if data:
        print(f"  {Colors.YELLOW}太阳能功率{Colors.ENDC}：{Colors.GREEN}{data.get('solar_power', 0):.2f} kW{Colors.ENDC}")
        print(f"  {Colors.YELLOW}风能功率{Colors.ENDC}：{Colors.GREEN}{data.get('wind_power', 0):.2f} kW{Colors.ENDC}")
        print(f"  {Colors.YELLOW}总发电功率{Colors.ENDC}：{Colors.BOLD}{Colors.GREEN}{data.get('total_power', 0):.2f} kW{Colors.ENDC}")
        print(f"  {Colors.YELLOW}运行状态{Colors.ENDC}：{Colors.GREEN}{data.get('status', 'unknown')}{Colors.ENDC}")
    else:
        print_error("无法获取数据")

def display_storage(data: Dict[str, Any]):
    """显示储能侧数据"""
    print_section("🔋 储能侧（Storage）")
    
    if data:
        print(f"  {Colors.YELLOW}当前负荷{Colors.ENDC}：{Colors.GREEN}{data.get('current_load', 0):.2f} kW{Colors.ENDC}")
        print(f"  {Colors.YELLOW}预测负荷{Colors.ENDC}：{Colors.GREEN}{data.get('forecasted_load', 0):.2f} kW{Colors.ENDC}")
        print(f"  {Colors.YELLOW}需求响应{Colors.ENDC}：{Colors.GREEN}{data.get('demand_response', 0):.2f} kW{Colors.ENDC}")
        print(f"  {Colors.YELLOW}运行状态{Colors.ENDC}：{Colors.GREEN}{data.get('status', 'unknown')}{Colors.ENDC}")
    else:
        print_error("无法获取数据")

def display_demand(data: Dict[str, Any]):
    """显示需求侧数据"""
    print_section("📊 需求侧（Demand）")
    
    if data:
        print(f"  {Colors.YELLOW}当前负荷{Colors.ENDC}：{Colors.GREEN}{data.get('current_load', 0):.2f} kW{Colors.ENDC}")
        print(f"  {Colors.YELLOW}预测负荷{Colors.ENDC}：{Colors.GREEN}{data.get('forecasted_load', 0):.2f} kW{Colors.ENDC}")
        print(f"  {Colors.YELLOW}需求响应{Colors.ENDC}：{Colors.GREEN}{data.get('demand_response', 0):.2f} kW{Colors.ENDC}")
        print(f"  {Colors.YELLOW}运行状态{Colors.ENDC}：{Colors.GREEN}{data.get('status', 'unknown')}{Colors.ENDC}")
    else:
        print_error("无法获取数据")

def display_data_flow():
    """显示数据流动"""
    print_section("🔄 实时数据流动")
    
    print(f"""
    {Colors.BOLD}{Colors.GREEN}电源侧{Colors.ENDC}
        ↓ 发电数据
    {Colors.BOLD}{Colors.CYAN}协调器{Colors.ENDC}
        ↙ ↓ ↘
    {Colors.BOLD}{Colors.YELLOW}储能侧{Colors.ENDC}  {Colors.BOLD}{Colors.YELLOW}需求侧{Colors.ENDC}
        ↘ ↓ ↙
    {Colors.BOLD}{Colors.CYAN}协调器{Colors.ENDC}
        ↓ 平衡指令
    {Colors.BOLD}{Colors.GREEN}电源侧{Colors.ENDC}
    """)

def check_services():
    """检查所有服务状态"""
    print_header("VPP 虚拟电厂实时数据交换演示")
    
    print_section("🔍 服务健康检查")
    
    services = [
        ("电源侧", POWER_GEN_URL),
        ("储能侧", STORAGE_URL),
        ("需求侧", DEMAND_URL),
    ]
    
    all_healthy = True
    for name, url in services:
        status = get_service_status(url, name)
        if status["status"] == "healthy":
            print_success(f"{name} ({url}) - 运行正常")
        else:
            print_error(f"{name} ({url}) - {status.get('error', 'Unknown error')}")
            all_healthy = False
    
    return all_healthy

def display_realtime_data(iterations: int = 5):
    """实时显示数据"""
    print_header("实时数据交换监控")
    
    for i in range(iterations):
        print(f"\n{Colors.BOLD}{Colors.CYAN}[{datetime.now().strftime('%H:%M:%S')}] 数据采集周期 {i+1}/{iterations}{Colors.ENDC}")
        
        # 获取数据
        power_data = get_power_generation_data()
        storage_data = get_storage_data()
        demand_data = get_demand_data()
        
        # 显示数据
        display_power_generation(power_data)
        display_storage(storage_data)
        display_demand(demand_data)
        display_data_flow()
        
        # 计算能量平衡
        if power_data and storage_data and demand_data:
            total_power = power_data.get('total_power', 0)
            current_load = demand_data.get('current_load', 0)
            balance = total_power - current_load
            
            print_section("⚖️ 能量平衡")
            print(f"  {Colors.YELLOW}总发电功率{Colors.ENDC}：{Colors.GREEN}{total_power:.2f} kW{Colors.ENDC}")
            print(f"  {Colors.YELLOW}总负荷需求{Colors.ENDC}：{Colors.GREEN}{current_load:.2f} kW{Colors.ENDC}")
            
            if balance > 0:
                print(f"  {Colors.YELLOW}能量盈余{Colors.ENDC}：{Colors.GREEN}+{balance:.2f} kW{Colors.ENDC} (充电)")
            elif balance < 0:
                print(f"  {Colors.YELLOW}能量不足{Colors.ENDC}：{Colors.RED}{balance:.2f} kW{Colors.ENDC} (放电)")
            else:
                print(f"  {Colors.YELLOW}能量平衡{Colors.ENDC}：{Colors.GREEN}完美平衡{Colors.ENDC}")
        
        if i < iterations - 1:
            print(f"\n{Colors.YELLOW}等待 3 秒后进行下一次采集...{Colors.ENDC}")
            time.sleep(3)

def display_api_endpoints():
    """显示可用的 API 端点"""
    print_section("📡 可用的 API 端点")
    
    endpoints = [
        ("电源侧", POWER_GEN_URL, [
            "/health - 健康检查",
            "/generation/status - 发电状态",
        ]),
        ("储能侧", STORAGE_URL, [
            "/health - 健康检查",
            "/load/status - 负荷状态",
        ]),
        ("需求侧", DEMAND_URL, [
            "/health - 健康检查",
            "/load/status - 负荷状态",
        ]),
    ]
    
    for service, url, eps in endpoints:
        print(f"\n  {Colors.BOLD}{service}{Colors.ENDC} ({url})")
        for ep in eps:
            print(f"    • {ep}")

def main():
    """主函数"""
    try:
        # 检查服务
        if not check_services():
            print_error("\n某些服务不可用，请检查容器是否正常运行")
            print_info("运行以下命令查看容器状态：")
            print(f"  {Colors.YELLOW}docker ps{Colors.ENDC}")
            print(f"  {Colors.YELLOW}docker logs vpp-master{Colors.ENDC}")
            print(f"  {Colors.YELLOW}docker logs vpp-simulation{Colors.ENDC}")
            return
        
        # 显示 API 端点
        display_api_endpoints()
        
        # 实时显示数据
        display_realtime_data(iterations=5)
        
        # 显示总结
        print_header("演示完成")
        print(f"""
{Colors.BOLD}VPP 虚拟电厂实时数据交换演示已完成！{Colors.ENDC}

{Colors.BOLD}关键观察：{Colors.ENDC}
  ✓ 电源侧实时发电数据
  ✓ 储能侧实时储能状态
  ✓ 需求侧实时负荷需求
  ✓ 三侧实时数据交换
  ✓ 能量平衡计算

{Colors.BOLD}下一步：{Colors.ENDC}
  1. 查看 3D 可视化效果
  2. 运行集成测试
  3. 查看详细文档

{Colors.BOLD}有用的命令：{Colors.ENDC}
  • 查看日志：{Colors.YELLOW}docker logs -f vpp-simulation{Colors.ENDC}
  • 测试 API：{Colors.YELLOW}curl http://localhost:5001/health{Colors.ENDC}
  • 停止容器：{Colors.YELLOW}docker-compose -f docker-compose-simple.yml down{Colors.ENDC}
        """)
        
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}演示已中断{Colors.ENDC}")
    except Exception as e:
        print_error(f"发生错误：{str(e)}")

if __name__ == "__main__":
    main()
