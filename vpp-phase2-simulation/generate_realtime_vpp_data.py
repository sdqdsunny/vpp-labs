#!/usr/bin/env python3
"""
VPP 实时数据生成脚本

持续生成虚拟电厂的实时数据，用于测试和演示实时数据展示功能。
"""

import sys
import os
sys.path.insert(0, '/app')

import time
import random
from datetime import datetime

# 导入数据存储
from services.vpp_data_store import get_vpp_data_store

def generate_power_data():
    """生成电源数据"""
    return {
        "current_power": round(random.uniform(50, 200), 2),
        "solar_power": round(random.uniform(30, 150), 2),
        "wind_power": round(random.uniform(10, 80), 2),
        "efficiency": round(random.uniform(85, 98), 1),
        "device_status": "running"
    }

def generate_storage_data():
    """生成储能数据"""
    return {
        "soc": round(random.uniform(30, 90), 1),
        "soh": round(random.uniform(95, 100), 1),
        "current_power": round(random.uniform(-50, 50), 2),
        "charge_status": random.choice(["charging", "discharging", "idle"]),
        "temperature": round(random.uniform(20, 35), 1)
    }

def generate_demand_data():
    """生成需求数据"""
    return {
        "current_demand": round(random.uniform(50, 180), 2),
        "flexible_demand": round(random.uniform(10, 50), 2),
        "dr_status": random.choice(["active", "inactive"])
    }

def main():
    """主函数"""
    print("=" * 60)
    print("VPP 实时数据生成脚本")
    print("=" * 60)
    print()
    
    # 获取数据存储
    store = get_vpp_data_store()
    print("✅ 数据存储已初始化")
    print()
    
    # 开始生成数据
    print("2️⃣  开始生成实时数据...")
    print("   按 Ctrl+C 停止")
    print()
    
    iteration = 0
    try:
        while True:
            iteration += 1
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            # 生成数据
            power_data = generate_power_data()
            storage_data = generate_storage_data()
            demand_data = generate_demand_data()
            
            # 更新存储
            store.update_power_data(power_data)
            store.update_storage_data(storage_data)
            store.update_demand_data(demand_data)
            
            # 显示状态
            print(f"[{timestamp}] ✅ 第 {iteration} 次更新")
            print(f"  电源: {power_data['current_power']} kW | "
                  f"储能: {storage_data['soc']}% | "
                  f"需求: {demand_data['current_demand']} kW")
            
            # 等待 2 秒
            time.sleep(2)
            
    except KeyboardInterrupt:
        print()
        print()
        print("=" * 60)
        print("✅ 数据生成已停止")
        print(f"   共生成 {iteration} 次数据更新")
        print("=" * 60)

if __name__ == "__main__":
    main()
