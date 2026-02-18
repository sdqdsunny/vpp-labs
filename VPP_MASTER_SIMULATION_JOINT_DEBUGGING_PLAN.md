# VPP Master主站与仿真模块联合调试与功能验证方案

## 第一部分：方案概述

### 1.1 方案目标

本方案旨在建立VPP Master主站与虚拟电厂场景仿真靶标（Phase 2 Simulation）之间的完整联合调试与功能验证体系，确保：

1. **系统集成** - VPP Master与Phase 2 Simulation完全集成
2. **功能验证** - 所有功能模块正常工作
3. **性能测试** - 系统性能满足要求
4. **可靠性验证** - 系统稳定性和容错能力
5. **生产就绪** - 系统可投入生产使用

### 1.2 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                    VPP Master主站                           │
│  ┌──────────────┬──────────────┬──────────────┐             │
│  │ 设备管理     │ 调度控制     │ 协议转换     │             │
│  │ Device Mgr   │ Dispatch Eng │ Protocol Conv│             │
│  └──────────────┴──────────────┴──────────────┘             │
│                        ↕                                     │
│              通信接口 (REST API / WebSocket)                │
│                        ↕                                     │
└─────────────────────────────────────────────────────────────┘
                         ↕
┌─────────────────────────────────────────────────────────────┐
│          虚拟电厂场景仿真靶标 (Phase 2 Simulation)         │
│  ┌──────────────┬──────────────┬──────────────┐             │
│  │ VCC协调中心  │ 电源侧模块   │ 储能侧模块   │             │
│  │ (VCC)        │ (Power Gen)  │ (Storage)    │             │
│  └──────────────┴──────────────┴──────────────┘             │
│  ┌──────────────┬──────────────┬──────────────┐             │
│  │ 需求侧模块   │ 协议适配器   │ 场景引擎     │             │
│  │ (Demand)     │ (Adapters)   │ (Scenario)   │             │
│  └──────────────┴──────────────┴──────────────┘             │
└─────────────────────────────────────────────────────────────┘
```

### 1.3 调试阶段划分

| 阶段 | 名称 | 目标 | 时间 |
|------|------|------|------|
| 1 | 环境准备 | 搭建测试环境 | 1天 |
| 2 | 基础连接 | 验证通信连接 | 1天 |
| 3 | 功能验证 | 验证各模块功能 | 3天 |
| 4 | 集成测试 | 端到端集成测试 | 2天 |
| 5 | 性能测试 | 性能和压力测试 | 2天 |
| 6 | 可靠性测试 | 稳定性和容错测试 | 2天 |
| 7 | 生产验证 | 生产环境验证 | 1天 |

---

## 第二部分：环境准备阶段

### 2.1 硬件和网络要求

#### 2.1.1 硬件配置

```
VPP Master主站服务器:
- CPU: 4核或以上
- 内存: 8GB或以上
- 存储: 50GB或以上
- 网络: 千兆网卡

Phase 2 Simulation服务器:
- CPU: 8核或以上
- 内存: 16GB或以上
- 存储: 100GB或以上
- 网络: 千兆网卡

测试客户端:
- CPU: 2核或以上
- 内存: 4GB或以上
- 网络: 千兆网卡
```

#### 2.1.2 网络配置

```
VPP Master:
- IP: 192.168.1.100
- Port: 8080 (HTTP API)
- Port: 8081 (WebSocket)
- Port: 9090 (Prometheus)

Phase 2 Simulation:
- IP: 192.168.1.101
- Port: 5000 (HTTP API)
- Port: 5001 (WebSocket)
- Port: 9091 (Prometheus)

测试客户端:
- IP: 192.168.1.102
```

### 2.2 软件环境准备

#### 2.2.1 依赖安装

```bash
# VPP Master依赖
cd vpp-master
pip install -r requirements.txt

# Phase 2 Simulation依赖
cd vpp-phase2-simulation
pip install -r requirements.txt

# 测试工具依赖
pip install pytest pytest-cov hypothesis
pip install requests websocket-client
pip install locust  # 性能测试
pip install docker  # Docker支持
```

#### 2.2.2 数据库初始化

```bash
# VPP Master数据库
cd vpp-master
python -c "from models import init_db; init_db()"

# Phase 2 Simulation数据库
cd vpp-phase2-simulation
python -c "from models import init_db; init_db()"
```

#### 2.2.3 配置文件准备

```bash
# VPP Master配置
cp vpp-master/.env.example vpp-master/.env
# 编辑.env文件，设置：
# - MASTER_HOST=192.168.1.100
# - MASTER_PORT=8080
# - SIMULATION_HOST=192.168.1.101
# - SIMULATION_PORT=5000

# Phase 2 Simulation配置
cp vpp-phase2-simulation/.env.example vpp-phase2-simulation/.env
# 编辑.env文件，设置：
# - SIMULATION_HOST=192.168.1.101
# - SIMULATION_PORT=5000
# - MASTER_HOST=192.168.1.100
# - MASTER_PORT=8080
```

### 2.3 测试环境验证

#### 2.3.1 环境检查清单

```
□ VPP Master服务器可访问
□ Phase 2 Simulation服务器可访问
□ 网络连接正常
□ 防火墙规则配置正确
□ 数据库连接正常
□ 日志目录可写
□ 临时文件目录可写
```

#### 2.3.2 环境验证脚本

```python
# verify_environment.py
import requests
import socket
import sys

def check_connectivity(host, port):
    """检查主机连接"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except:
        return False

def check_api(url):
    """检查API可用性"""
    try:
        response = requests.get(url, timeout=5)
        return response.status_code == 200
    except:
        return False

# 检查VPP Master
if not check_connectivity('192.168.1.100', 8080):
    print("❌ VPP Master不可访问")
    sys.exit(1)
print("✅ VPP Master可访问")

# 检查Phase 2 Simulation
if not check_connectivity('192.168.1.101', 5000):
    print("❌ Phase 2 Simulation不可访问")
    sys.exit(1)
print("✅ Phase 2 Simulation可访问")

# 检查API
if not check_api('http://192.168.1.100:8080/health'):
    print("❌ VPP Master API不可用")
    sys.exit(1)
print("✅ VPP Master API可用")

if not check_api('http://192.168.1.101:5000/health'):
    print("❌ Phase 2 Simulation API不可用")
    sys.exit(1)
print("✅ Phase 2 Simulation API可用")

print("\n✅ 环境准备完成")
```

---

## 第三部分：基础连接验证阶段

### 3.1 通信连接测试

#### 3.1.1 REST API连接测试

```python
# test_rest_connection.py
import requests
import json

class RestConnectionTest:
    def __init__(self, master_url, simulation_url):
        self.master_url = master_url
        self.simulation_url = simulation_url
    
    def test_master_health(self):
        """测试VPP Master健康状态"""
        response = requests.get(f'{self.master_url}/health')
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'
        print("✅ VPP Master健康检查通过")
    
    def test_simulation_health(self):
        """测试Phase 2 Simulation健康状态"""
        response = requests.get(f'{self.simulation_url}/health')
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'
        print("✅ Phase 2 Simulation健康检查通过")
    
    def test_master_api_endpoints(self):
        """测试VPP Master API端点"""
        endpoints = [
            '/api/v1/devices',
            '/api/v1/dispatch',
            '/api/v1/protocol',
            '/api/v1/analysis'
        ]
        for endpoint in endpoints:
            response = requests.get(f'{self.master_url}{endpoint}')
            assert response.status_code in [200, 401]  # 可能需要认证
            print(f"✅ {endpoint} 可访问")
    
    def test_simulation_api_endpoints(self):
        """测试Phase 2 Simulation API端点"""
        endpoints = [
            '/api/v1/devices',
            '/api/v1/scenarios',
            '/api/v1/metrics'
        ]
        for endpoint in endpoints:
            response = requests.get(f'{self.simulation_url}{endpoint}')
            assert response.status_code in [200, 401]
            print(f"✅ {endpoint} 可访问")
    
    def run_all_tests(self):
        """运行所有连接测试"""
        print("开始REST API连接测试...\n")
        self.test_master_health()
        self.test_simulation_health()
        self.test_master_api_endpoints()
        self.test_simulation_api_endpoints()
        print("\n✅ 所有连接测试通过")

# 运行测试
if __name__ == '__main__':
    test = RestConnectionTest(
        'http://192.168.1.100:8080',
        'http://192.168.1.101:5000'
    )
    test.run_all_tests()
```

#### 3.1.2 WebSocket连接测试

```python
# test_websocket_connection.py
import websocket
import json
import time

class WebSocketConnectionTest:
    def __init__(self, master_ws_url, simulation_ws_url):
        self.master_ws_url = master_ws_url
        self.simulation_ws_url = simulation_ws_url
    
    def test_master_websocket(self):
        """测试VPP Master WebSocket连接"""
        try:
            ws = websocket.create_connection(self.master_ws_url)
            
            # 发送连接消息
            msg = json.dumps({
                'type': 'connect',
                'client': 'test_client'
            })
            ws.send(msg)
            
            # 接收响应
            response = ws.recv()
            data = json.loads(response)
            assert data['type'] == 'connected'
            
            ws.close()
            print("✅ VPP Master WebSocket连接成功")
        except Exception as e:
            print(f"❌ VPP Master WebSocket连接失败: {e}")
            raise
    
    def test_simulation_websocket(self):
        """测试Phase 2 Simulation WebSocket连接"""
        try:
            ws = websocket.create_connection(self.simulation_ws_url)
            
            # 发送连接消息
            msg = json.dumps({
                'type': 'connect',
                'client': 'test_client'
            })
            ws.send(msg)
            
            # 接收响应
            response = ws.recv()
            data = json.loads(response)
            assert data['type'] == 'connected'
            
            ws.close()
            print("✅ Phase 2 Simulation WebSocket连接成功")
        except Exception as e:
            print(f"❌ Phase 2 Simulation WebSocket连接失败: {e}")
            raise
    
    def run_all_tests(self):
        """运行所有WebSocket测试"""
        print("开始WebSocket连接测试...\n")
        self.test_master_websocket()
        self.test_simulation_websocket()
        print("\n✅ 所有WebSocket测试通过")

# 运行测试
if __name__ == '__main__':
    test = WebSocketConnectionTest(
        'ws://192.168.1.100:8081',
        'ws://192.168.1.101:5001'
    )
    test.run_all_tests()
```

### 3.2 数据交互测试

#### 3.2.1 设备注册测试

```python
# test_device_registration.py
import requests
import json

class DeviceRegistrationTest:
    def __init__(self, master_url, simulation_url):
        self.master_url = master_url
        self.simulation_url = simulation_url
    
    def test_register_solar_device(self):
        """测试注册太阳能设备"""
        device_data = {
            'device_id': 'solar-001',
            'device_type': 'solar',
            'name': 'Solar Panel 1',
            'capacity': 100.0,
            'location': 'Building A'
        }
        
        # 在Simulation中创建设备
        response = requests.post(
            f'{self.simulation_url}/api/v1/devices',
            json=device_data
        )
        assert response.status_code == 201
        print("✅ 太阳能设备在Simulation中创建成功")
        
        # 在Master中注册设备
        response = requests.post(
            f'{self.master_url}/api/v1/devices',
            json=device_data
        )
        assert response.status_code == 201
        print("✅ 太阳能设备在Master中注册成功")
    
    def test_register_battery_device(self):
        """测试注册电池设备"""
        device_data = {
            'device_id': 'battery-001',
            'device_type': 'battery',
            'name': 'Battery Storage 1',
            'capacity': 50.0,
            'soc': 0.5
        }
        
        # 在Simulation中创建设备
        response = requests.post(
            f'{self.simulation_url}/api/v1/devices',
            json=device_data
        )
        assert response.status_code == 201
        print("✅ 电池设备在Simulation中创建成功")
        
        # 在Master中注册设备
        response = requests.post(
            f'{self.master_url}/api/v1/devices',
            json=device_data
        )
        assert response.status_code == 201
        print("✅ 电池设备在Master中注册成功")
    
    def test_register_load_device(self):
        """测试注册负荷设备"""
        device_data = {
            'device_id': 'load-001',
            'device_type': 'load',
            'name': 'Load 1',
            'capacity': 30.0,
            'current_load': 15.0
        }
        
        # 在Simulation中创建设备
        response = requests.post(
            f'{self.simulation_url}/api/v1/devices',
            json=device_data
        )
        assert response.status_code == 201
        print("✅ 负荷设备在Simulation中创建成功")
        
        # 在Master中注册设备
        response = requests.post(
            f'{self.master_url}/api/v1/devices',
            json=device_data
        )
        assert response.status_code == 201
        print("✅ 负荷设备在Master中注册成功")
    
    def run_all_tests(self):
        """运行所有设备注册测试"""
        print("开始设备注册测试...\n")
        self.test_register_solar_device()
        self.test_register_battery_device()
        self.test_register_load_device()
        print("\n✅ 所有设备注册测试通过")

# 运行测试
if __name__ == '__main__':
    test = DeviceRegistrationTest(
        'http://192.168.1.100:8080',
        'http://192.168.1.101:5000'
    )
    test.run_all_tests()
```

---

## 第四部分：功能验证阶段

### 4.1 VCC协调中心功能验证

#### 4.1.1 命令映射验证

```python
# test_vcc_command_mapping.py
import requests
import json

class VCCCommandMappingTest:
    def __init__(self, master_url, simulation_url):
        self.master_url = master_url
        self.simulation_url = simulation_url
    
    def test_command_to_iec104(self):
        """测试命令映射到IEC 61850"""
        command = {
            'command_type': 'set_power',
            'device_id': 'solar-001',
            'target_protocol': 'iec61850',
            'payload': {
                'power': 50.0
            }
        }
        
        response = requests.post(
            f'{self.master_url}/api/v1/dispatch/command',
            json=command
        )
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        print("✅ 命令成功映射到IEC 61850")
    
    def test_command_to_mqtt(self):
        """测试命令映射到MQTT"""
        command = {
            'command_type': 'set_power',
            'device_id': 'battery-001',
            'target_protocol': 'mqtt',
            'payload': {
                'power': 25.0
            }
        }
        
        response = requests.post(
            f'{self.master_url}/api/v1/dispatch/command',
            json=command
        )
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        print("✅ 命令成功映射到MQTT")
    
    def test_response_conversion(self):
        """测试响应转换"""
        # 从Simulation获取设备状态
        response = requests.get(
            f'{self.simulation_url}/api/v1/devices/solar-001/state'
        )
        assert response.status_code == 200
        state = response.json()
        
        # 在Master中转换响应
        response = requests.post(
            f'{self.master_url}/api/v1/protocol/convert',
            json={
                'source_protocol': 'iec61850',
                'target_protocol': 'mqtt',
                'data': state
            }
        )
        assert response.status_code == 200
        print("✅ 响应成功转换")
    
    def run_all_tests(self):
        """运行所有VCC功能测试"""
        print("开始VCC协调中心功能验证...\n")
        self.test_command_to_iec104()
        self.test_command_to_mqtt()
        self.test_response_conversion()
        print("\n✅ 所有VCC功能验证通过")

# 运行测试
if __name__ == '__main__':
    test = VCCCommandMappingTest(
        'http://192.168.1.100:8080',
        'http://192.168.1.101:5000'
    )
    test.run_all_tests()
```

### 4.2 电源侧模块功能验证

```python
# test_power_generation_module.py
import requests
import json

class PowerGenerationModuleTest:
    def __init__(self, simulation_url):
        self.simulation_url = simulation_url
    
    def test_solar_power_generation(self):
        """测试太阳能发电"""
        # 设置天气条件
        weather_data = {
            'irradiance': 800.0,
            'temperature': 25.0
        }
        
        response = requests.post(
            f'{self.simulation_url}/api/v1/devices/solar-001/command',
            json={
                'command': 'set_weather',
                'data': weather_data
            }
        )
        assert response.status_code == 200
        print("✅ 太阳能天气条件设置成功")
        
        # 获取发电功率
        response = requests.get(
            f'{self.simulation_url}/api/v1/devices/solar-001/state'
        )
        assert response.status_code == 200
        state = response.json()
        assert state['power'] > 0
        print(f"✅ 太阳能发电功率: {state['power']}W")
    
    def test_wind_power_generation(self):
        """测试风力发电"""
        # 设置风速
        wind_data = {
            'wind_speed': 10.0
        }
        
        response = requests.post(
            f'{self.simulation_url}/api/v1/devices/wind-001/command',
            json={
                'command': 'set_weather',
                'data': wind_data
            }
        )
        assert response.status_code == 200
        print("✅ 风力天气条件设置成功")
        
        # 获取发电功率
        response = requests.get(
            f'{self.simulation_url}/api/v1/devices/wind-001/state'
        )
        assert response.status_code == 200
        state = response.json()
        assert state['power'] > 0
        print(f"✅ 风力发电功率: {state['power']}W")
    
    def test_generation_forecast(self):
        """测试发电预测"""
        response = requests.get(
            f'{self.simulation_url}/api/v1/devices/solar-001/forecast?hours=24'
        )
        assert response.status_code == 200
        forecast = response.json()
        assert len(forecast['forecast']) == 24
        print("✅ 发电预测获取成功")
    
    def run_all_tests(self):
        """运行所有电源侧功能测试"""
        print("开始电源侧模块功能验证...\n")
        self.test_solar_power_generation()
        self.test_wind_power_generation()
        self.test_generation_forecast()
        print("\n✅ 所有电源侧功能验证通过")

# 运行测试
if __name__ == '__main__':
    test = PowerGenerationModuleTest(
        'http://192.168.1.101:5000'
    )
    test.run_all_tests()
```

