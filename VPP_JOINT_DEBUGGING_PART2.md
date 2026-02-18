# VPP Master与仿真模块联合调试方案 - 第二部分

## 第五部分：集成测试阶段

### 5.1 端到端工作流测试

#### 5.1.1 完整场景测试

```python
# test_e2e_workflow.py
import requests
import json
import time

class E2EWorkflowTest:
    def __init__(self, master_url, simulation_url):
        self.master_url = master_url
        self.simulation_url = simulation_url
    
    def test_complete_dispatch_workflow(self):
        """测试完整的调度工作流"""
        print("开始完整调度工作流测试...")
        
        # 1. 创建场景
        scenario = {
            'name': 'Test Scenario',
            'duration': 3600,
            'devices': ['solar-001', 'battery-001', 'load-001']
        }
        response = requests.post(
            f'{self.simulation_url}/api/v1/scenarios',
            json=scenario
        )
        scenario_id = response.json()['scenario_id']
        print(f"✅ 场景创建成功: {scenario_id}")
        
        # 2. 启动场景
        response = requests.post(
            f'{self.simulation_url}/api/v1/scenarios/{scenario_id}/start'
        )
        assert response.status_code == 200
        print("✅ 场景启动成功")
        
        # 3. 获取设备状态
        response = requests.get(
            f'{self.master_url}/api/v1/devices'
        )
        devices = response.json()['devices']
        print(f"✅ 获取设备列表: {len(devices)}个设备")
        
        # 4. 发送调度命令
        dispatch_cmd = {
            'command_type': 'optimize_dispatch',
            'target_power': 100.0,
            'devices': ['solar-001', 'battery-001']
        }
        response = requests.post(
            f'{self.master_url}/api/v1/dispatch/optimize',
            json=dispatch_cmd
        )
        assert response.status_code == 200
        print("✅ 调度命令发送成功")
        
        # 5. 等待执行
        time.sleep(2)
        
        # 6. 获取执行结果
        response = requests.get(
            f'{self.simulation_url}/api/v1/scenarios/{scenario_id}/metrics'
        )
        metrics = response.json()
        print(f"✅ 获取执行指标: {metrics}")
        
        # 7. 停止场景
        response = requests.post(
            f'{self.simulation_url}/api/v1/scenarios/{scenario_id}/stop'
        )
        assert response.status_code == 200
        print("✅ 场景停止成功")
        
        return True
    
    def test_multi_device_coordination(self):
        """测试多设备协调"""
        print("\n开始多设备协调测试...")
        
        # 创建多个设备
        devices = [
            {'id': 'solar-001', 'type': 'solar', 'capacity': 100},
            {'id': 'solar-002', 'type': 'solar', 'capacity': 100},
            {'id': 'battery-001', 'type': 'battery', 'capacity': 50},
            {'id': 'load-001', 'type': 'load', 'capacity': 80},
            {'id': 'load-002', 'type': 'load', 'capacity': 60}
        ]
        
        for device in devices:
            response = requests.post(
                f'{self.master_url}/api/v1/devices',
                json=device
            )
            assert response.status_code == 201
        
        print(f"✅ 创建{len(devices)}个设备成功")
        
        # 发送协调命令
        coord_cmd = {
            'command_type': 'coordinate',
            'target_power': 150.0,
            'strategy': 'balance'
        }
        response = requests.post(
            f'{self.master_url}/api/v1/dispatch/coordinate',
            json=coord_cmd
        )
        assert response.status_code == 200
        print("✅ 多设备协调成功")
        
        return True
    
    def run_all_tests(self):
        """运行所有端到端测试"""
        print("=" * 50)
        print("端到端集成测试")
        print("=" * 50)
        self.test_complete_dispatch_workflow()
        self.test_multi_device_coordination()
        print("\n✅ 所有端到端测试通过")

# 运行测试
if __name__ == '__main__':
    test = E2EWorkflowTest(
        'http://192.168.1.100:8080',
        'http://192.168.1.101:5000'
    )
    test.run_all_tests()
```

### 5.2 协议互操作性测试

```python
# test_protocol_interoperability.py
import requests
import json

class ProtocolInteroperabilityTest:
    def __init__(self, master_url, simulation_url):
        self.master_url = master_url
        self.simulation_url = simulation_url
    
    def test_iec61850_mqtt_conversion(self):
        """测试IEC 61850与MQTT的转换"""
        # IEC 61850格式的数据
        iec_data = {
            'protocol': 'iec61850',
            'voltage': 230.0,
            'current': 10.5,
            'power': 2415.0
        }
        
        # 转换为MQTT格式
        response = requests.post(
            f'{self.master_url}/api/v1/protocol/convert',
            json={
                'source': 'iec61850',
                'target': 'mqtt',
                'data': iec_data
            }
        )
        assert response.status_code == 200
        mqtt_data = response.json()['data']
        print("✅ IEC 61850 → MQTT转换成功")
        
        # 转换回IEC 61850
        response = requests.post(
            f'{self.master_url}/api/v1/protocol/convert',
            json={
                'source': 'mqtt',
                'target': 'iec61850',
                'data': mqtt_data
            }
        )
        assert response.status_code == 200
        print("✅ MQTT → IEC 61850转换成功")
    
    def test_modbus_dnp3_conversion(self):
        """测试Modbus与DNP3的转换"""
        modbus_data = {
            'protocol': 'modbus',
            'registers': [100, 200, 300]
        }
        
        response = requests.post(
            f'{self.master_url}/api/v1/protocol/convert',
            json={
                'source': 'modbus',
                'target': 'dnp3',
                'data': modbus_data
            }
        )
        assert response.status_code == 200
        print("✅ Modbus → DNP3转换成功")
    
    def test_protocol_chain_conversion(self):
        """测试协议链转换"""
        data = {'value': 100}
        
        # IEC61850 → Modbus → DNP3 → MQTT
        protocols = ['iec61850', 'modbus', 'dnp3', 'mqtt']
        
        for i in range(len(protocols) - 1):
            response = requests.post(
                f'{self.master_url}/api/v1/protocol/convert',
                json={
                    'source': protocols[i],
                    'target': protocols[i+1],
                    'data': data
                }
            )
            assert response.status_code == 200
            data = response.json()['data']
        
        print("✅ 协议链转换成功")
    
    def run_all_tests(self):
        """运行所有协议互操作性测试"""
        print("\n" + "=" * 50)
        print("协议互操作性测试")
        print("=" * 50)
        self.test_iec61850_mqtt_conversion()
        self.test_modbus_dnp3_conversion()
        self.test_protocol_chain_conversion()
        print("\n✅ 所有协议互操作性测试通过")

# 运行测试
if __name__ == '__main__':
    test = ProtocolInteroperabilityTest(
        'http://192.168.1.100:8080',
        'http://192.168.1.101:5000'
    )
    test.run_all_tests()
```

---

## 第六部分：性能测试阶段

### 6.1 吞吐量测试

```python
# test_throughput.py
import requests
import json
import time
from concurrent.futures import ThreadPoolExecutor

class ThroughputTest:
    def __init__(self, master_url, simulation_url):
        self.master_url = master_url
        self.simulation_url = simulation_url
    
    def test_device_query_throughput(self):
        """测试设备查询吞吐量"""
        print("开始设备查询吞吐量测试...")
        
        num_requests = 1000
        start_time = time.time()
        
        def query_device():
            response = requests.get(
                f'{self.master_url}/api/v1/devices/solar-001'
            )
            return response.status_code == 200
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(lambda _: query_device(), range(num_requests)))
        
        elapsed_time = time.time() - start_time
        throughput = num_requests / elapsed_time
        
        print(f"✅ 吞吐量: {throughput:.2f} 请求/秒")
        print(f"   总请求数: {num_requests}")
        print(f"   总耗时: {elapsed_time:.2f}秒")
        print(f"   成功率: {sum(results)/len(results)*100:.1f}%")
    
    def test_command_dispatch_throughput(self):
        """测试命令调度吞吐量"""
        print("\n开始命令调度吞吐量测试...")
        
        num_commands = 500
        start_time = time.time()
        
        def send_command():
            response = requests.post(
                f'{self.master_url}/api/v1/dispatch/command',
                json={
                    'device_id': 'solar-001',
                    'command': 'set_power',
                    'value': 50.0
                }
            )
            return response.status_code == 200
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(lambda _: send_command(), range(num_commands)))
        
        elapsed_time = time.time() - start_time
        throughput = num_commands / elapsed_time
        
        print(f"✅ 吞吐量: {throughput:.2f} 命令/秒")
        print(f"   总命令数: {num_commands}")
        print(f"   总耗时: {elapsed_time:.2f}秒")
        print(f"   成功率: {sum(results)/len(results)*100:.1f}%")
    
    def run_all_tests(self):
        """运行所有吞吐量测试"""
        print("\n" + "=" * 50)
        print("性能测试 - 吞吐量")
        print("=" * 50)
        self.test_device_query_throughput()
        self.test_command_dispatch_throughput()
        print("\n✅ 所有吞吐量测试完成")

# 运行测试
if __name__ == '__main__':
    test = ThroughputTest(
        'http://192.168.1.100:8080',
        'http://192.168.1.101:5000'
    )
    test.run_all_tests()
```

### 6.2 延迟测试

```python
# test_latency.py
import requests
import json
import time
import statistics

class LatencyTest:
    def __init__(self, master_url, simulation_url):
        self.master_url = master_url
        self.simulation_url = simulation_url
    
    def test_api_response_latency(self):
        """测试API响应延迟"""
        print("开始API响应延迟测试...")
        
        latencies = []
        num_requests = 100
        
        for _ in range(num_requests):
            start_time = time.time()
            response = requests.get(
                f'{self.master_url}/api/v1/devices/solar-001'
            )
            latency = (time.time() - start_time) * 1000  # 转换为毫秒
            latencies.append(latency)
        
        avg_latency = statistics.mean(latencies)
        min_latency = min(latencies)
        max_latency = max(latencies)
        p95_latency = sorted(latencies)[int(len(latencies) * 0.95)]
        
        print(f"✅ API响应延迟统计:")
        print(f"   平均延迟: {avg_latency:.2f}ms")
        print(f"   最小延迟: {min_latency:.2f}ms")
        print(f"   最大延迟: {max_latency:.2f}ms")
        print(f"   P95延迟: {p95_latency:.2f}ms")
    
    def test_command_execution_latency(self):
        """测试命令执行延迟"""
        print("\n开始命令执行延迟测试...")
        
        latencies = []
        num_commands = 100
        
        for _ in range(num_commands):
            start_time = time.time()
            response = requests.post(
                f'{self.master_url}/api/v1/dispatch/command',
                json={
                    'device_id': 'solar-001',
                    'command': 'set_power',
                    'value': 50.0
                }
            )
            latency = (time.time() - start_time) * 1000
            latencies.append(latency)
        
        avg_latency = statistics.mean(latencies)
        p95_latency = sorted(latencies)[int(len(latencies) * 0.95)]
        
        print(f"✅ 命令执行延迟统计:")
        print(f"   平均延迟: {avg_latency:.2f}ms")
        print(f"   P95延迟: {p95_latency:.2f}ms")
    
    def run_all_tests(self):
        """运行所有延迟测试"""
        print("\n" + "=" * 50)
        print("性能测试 - 延迟")
        print("=" * 50)
        self.test_api_response_latency()
        self.test_command_execution_latency()
        print("\n✅ 所有延迟测试完成")

# 运行测试
if __name__ == '__main__':
    test = LatencyTest(
        'http://192.168.1.100:8080',
        'http://192.168.1.101:5000'
    )
    test.run_all_tests()
```

---

## 第七部分：可靠性测试阶段

### 7.1 容错能力测试

```python
# test_fault_tolerance.py
import requests
import json
import time

class FaultToleranceTest:
    def __init__(self, master_url, simulation_url):
        self.master_url = master_url
        self.simulation_url = simulation_url
    
    def test_device_failure_recovery(self):
        """测试设备故障恢复"""
        print("开始设备故障恢复测试...")
        
        # 1. 正常状态下获取设备
        response = requests.get(
            f'{self.master_url}/api/v1/devices/solar-001'
        )
        assert response.status_code == 200
        print("✅ 设备正常状态")
        
        # 2. 模拟设备故障
        response = requests.post(
            f'{self.simulation_url}/api/v1/devices/solar-001/fault',
            json={'fault_type': 'connection_loss'}
        )
        print("✅ 模拟设备故障")
        
        # 3. 等待故障检测
        time.sleep(2)
        
        # 4. 验证故障状态
        response = requests.get(
            f'{self.master_url}/api/v1/devices/solar-001/status'
        )
        status = response.json()
        assert status['state'] == 'fault'
        print("✅ 故障状态检测成功")
        
        # 5. 恢复设备
        response = requests.post(
            f'{self.simulation_url}/api/v1/devices/solar-001/recover'
        )
        print("✅ 设备恢复")
        
        # 6. 验证恢复状态
        time.sleep(2)
        response = requests.get(
            f'{self.master_url}/api/v1/devices/solar-001/status'
        )
        status = response.json()
        assert status['state'] == 'normal'
        print("✅ 设备恢复成功")
    
    def test_network_interruption_recovery(self):
        """测试网络中断恢复"""
        print("\n开始网络中断恢复测试...")
        
        # 1. 正常通信
        response = requests.get(
            f'{self.master_url}/api/v1/devices'
        )
        assert response.status_code == 200
        print("✅ 网络正常")
        
        # 2. 模拟网络中断
        print("⏳ 模拟网络中断...")
        time.sleep(2)
        
        # 3. 尝试通信（可能失败）
        try:
            response = requests.get(
                f'{self.master_url}/api/v1/devices',
                timeout=1
            )
        except:
            print("✅ 网络中断检测")
        
        # 4. 网络恢复
        print("⏳ 网络恢复...")
        time.sleep(2)
        
        # 5. 验证通信恢复
        response = requests.get(
            f'{self.master_url}/api/v1/devices'
        )
        assert response.status_code == 200
        print("✅ 网络恢复成功")
    
    def run_all_tests(self):
        """运行所有容错能力测试"""
        print("\n" + "=" * 50)
        print("可靠性测试 - 容错能力")
        print("=" * 50)
        self.test_device_failure_recovery()
        self.test_network_interruption_recovery()
        print("\n✅ 所有容错能力测试完成")

# 运行测试
if __name__ == '__main__':
    test = FaultToleranceTest(
        'http://192.168.1.100:8080',
        'http://192.168.1.101:5000'
    )
    test.run_all_tests()
```

