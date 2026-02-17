#!/usr/bin/env python3
"""
FUXA Configuration Import Script
Imports device configuration and dashboard into FUXA via REST API
"""

import json
import requests
import time
import sys

FUXA_URL = "http://localhost:1881"
CONFIG_FILE = "fuxa-device-config.json"

def check_fuxa_health():
    """Check if FUXA is running"""
    try:
        response = requests.get(f"{FUXA_URL}/api/project", timeout=5)
        return response.status_code == 200
    except Exception as e:
        print(f"❌ FUXA不可访问: {e}")
        return False

def load_config():
    """Load configuration from JSON file"""
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ 无法读取配置文件: {e}")
        sys.exit(1)

def import_devices(config):
    """Import MQTT devices into FUXA"""
    print("\n📡 导入MQTT设备配置...")
    
    devices = config.get('devices', [])
    for device in devices:
        try:
            # FUXA API endpoint for adding devices
            response = requests.post(
                f"{FUXA_URL}/api/device",
                json=device,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                print(f"  ✅ 设备 '{device['name']}' 导入成功")
            else:
                print(f"  ⚠️  设备 '{device['name']}' 导入失败: {response.status_code}")
                print(f"     响应: {response.text}")
        except Exception as e:
            print(f"  ❌ 设备 '{device['name']}' 导入错误: {e}")

def import_dashboards(config):
    """Import dashboards into FUXA"""
    print("\n📊 导入Dashboard配置...")
    
    dashboards = config.get('dashboards', [])
    for dashboard in dashboards:
        try:
            # FUXA API endpoint for adding views/dashboards
            response = requests.post(
                f"{FUXA_URL}/api/view",
                json=dashboard,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code in [200, 201]:
                print(f"  ✅ Dashboard '{dashboard['name']}' 导入成功")
            else:
                print(f"  ⚠️  Dashboard '{dashboard['name']}' 导入失败: {response.status_code}")
                print(f"     响应: {response.text}")
        except Exception as e:
            print(f"  ❌ Dashboard '{dashboard['name']}' 导入错误: {e}")

def get_project_info():
    """Get current FUXA project information"""
    try:
        response = requests.get(f"{FUXA_URL}/api/project", timeout=5)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def main():
    print("=" * 60)
    print("FUXA配置导入工具")
    print("=" * 60)
    
    # Check FUXA health
    print("\n🔍 检查FUXA服务状态...")
    if not check_fuxa_health():
        print("\n❌ FUXA服务未运行或不可访问")
        print("   请确保FUXA运行在 http://localhost:1881")
        sys.exit(1)
    print("✅ FUXA服务正常运行")
    
    # Get project info
    project = get_project_info()
    if project:
        print(f"\n📋 当前项目: {project.get('name', 'Unknown')}")
    
    # Load configuration
    print(f"\n📂 加载配置文件: {CONFIG_FILE}")
    config = load_config()
    print(f"✅ 配置文件加载成功")
    print(f"   - 设备数量: {len(config.get('devices', []))}")
    print(f"   - Dashboard数量: {len(config.get('dashboards', []))}")
    
    # Import devices
    import_devices(config)
    
    # Wait a bit for devices to be registered
    time.sleep(2)
    
    # Import dashboards
    import_dashboards(config)
    
    print("\n" + "=" * 60)
    print("✅ 配置导入完成!")
    print("=" * 60)
    print(f"\n🌐 请在浏览器中打开: {FUXA_URL}")
    print("   1. 点击 'Editor' 按钮进入编辑器")
    print("   2. 在左侧查看已导入的设备和Dashboard")
    print("   3. 点击 'Home' 查看实时Dashboard")
    print("\n💡 提示: 如果API导入不成功，请使用手动配置方式")
    print("   参考文件: dashboard-setup-guide.md")

if __name__ == "__main__":
    main()
