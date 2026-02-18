# VPP 安全测试工具集成指南

## 📋 概述

VPP 安全测试工具集成了5款开源安全测试框架，提供了统一的Web界面和REST API，用于对工控协议进行漏洞分析、利用和验证。

## 🛠️ 集成的工具

### 1. **PyModbus** - Modbus协议测试
- **功能**: 读写线圈、寄存器，设备扫描
- **用途**: Modbus TCP/RTU协议测试
- **安装**: `pip install pymodbus`

### 2. **OpenDNP3** - DNP3协议测试
- **功能**: 连接测试、点扫描
- **用途**: DNP3 SCADA协议测试
- **安装**: `pip install dnp3`

### 3. **python-opcua** - OPC UA协议测试
- **功能**: 连接测试、命名空间浏览
- **用途**: OPC UA工业互操作性测试
- **安装**: `pip install opcua`

### 4. **SocketCAN** - CAN协议测试
- **功能**: 接口状态、流量嗅探、消息发送
- **用途**: CAN总线协议测试
- **安装**: Linux内置，需要CAN工具 `apt-get install can-utils`

### 5. **Boofuzz** - 协议模糊测试
- **功能**: Modbus和DNP3协议模糊测试
- **用途**: 发现协议实现中的漏洞
- **安装**: `pip install boofuzz`

## 🚀 快速开始

### 1. 安装依赖

```bash
# 安装所有Python依赖
pip install pymodbus dnp3 opcua boofuzz

# Linux系统安装CAN工具
sudo apt-get install can-utils

# macOS系统
brew install can-utils
```

### 2. 启动应用

```bash
cd vpp-phase2-simulation
python3 app.py
```

### 3. 访问Web界面

```
http://localhost:8080/security
```

## 🌐 Web界面使用

### 界面布局

```
┌─────────────────────────────────────────────────────────┐
│  VPP 安全测试工具                                        │
│  工具状态: PyModbus ✅ OpenDNP3 ❌ python-opcua ✅ ...  │
└─────────────────────────────────────────────────────────┘

[🔌 Modbus] [⚡ DNP3] [🏭 OPC UA] [🚗 CAN] [🐛 Boofuzz]

┌─────────────────────────────────────────────────────────┐
│ 测试表单                                                 │
├─────────────────────────────────────────────────────────┤
│ 测试类型: [扫描设备 ▼]                                  │
│ 目标主机: [localhost]                                   │
│ 端口:     [502]                                         │
│ [▶️ 运行测试] [🗑️ 清空结果]                            │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│ 测试结果                                                 │
├─────────────────────────────────────────────────────────┤
│ ✅ 成功                                                  │
│ {                                                       │
│   "devices_found": 1,                                   │
│   "devices": [...]                                      │
│ }                                                       │
└─────────────────────────────────────────────────────────┘
```

### 标签页说明

#### 🔌 Modbus 测试
**支持的测试**:
- 扫描设备: 发现网络中的Modbus设备
- 读取线圈: 读取线圈状态
- 读取寄存器: 读取保持寄存器值
- 写入线圈: 写入线圈状态

**参数**:
- 目标主机: Modbus服务器地址
- 端口: Modbus TCP端口（默认502）
- 地址: 线圈/寄存器地址
- 数量/值: 读取数量或写入值

#### ⚡ DNP3 测试
**支持的测试**:
- 连接测试: 测试与DNP3主站的连接
- 扫描点: 扫描DNP3点

**参数**:
- 目标主机: DNP3主站地址
- 端口: DNP3端口（默认20000）

#### 🏭 OPC UA 测试
**支持的测试**:
- 连接测试: 测试与OPC UA服务器的连接
- 浏览命名空间: 浏览OPC UA命名空间

**参数**:
- OPC UA URL: 服务器地址（格式: opc.tcp://host:port）

#### 🚗 CAN 测试
**支持的测试**:
- 接口状态: 检查CAN接口状态
- 嗅探流量: 捕获CAN消息
- 发送消息: 发送CAN消息

**参数**:
- 接口名称: CAN接口（如can0、can1）
- 持续时间: 嗅探持续时间（秒）
- CAN ID: 消息ID（十六进制）
- 数据: 消息数据（十六进制）

#### 🐛 Boofuzz 模糊测试
**支持的测试**:
- Modbus模糊测试: 对Modbus协议进行模糊测试
- DNP3模糊测试: 对DNP3协议进行模糊测试

**参数**:
- 目标主机: 目标服务器地址
- 端口: 目标端口
- 持续时间: 模糊测试持续时间（秒）

## 📡 REST API

### 基础URL
```
http://localhost:8080/api/security
```

### 端点列表

#### 1. 获取可用工具
```http
GET /api/security/tools
```

**响应示例**:
```json
{
  "tools": {
    "pymodbus": true,
    "opendnp3": false,
    "python_opcua": true,
    "socketcan": true,
    "boofuzz": false
  },
  "timestamp": "2026-02-18T18:30:00.000000"
}
```

#### 2. Modbus测试
```http
POST /api/security/modbus/test
Content-Type: application/json

{
  "test_type": "scan",
  "host": "192.168.1.100",
  "port": 502
}
```

**支持的test_type**:
- `scan`: 扫描设备
- `read_coils`: 读取线圈
- `read_registers`: 读取寄存器
- `write_coil`: 写入线圈

#### 3. DNP3测试
```http
POST /api/security/dnp3/test
Content-Type: application/json

{
  "test_type": "connection",
  "host": "192.168.1.100",
  "port": 20000
}
```

**支持的test_type**:
- `connection`: 连接测试
- `scan`: 扫描点

#### 4. OPC UA测试
```http
POST /api/security/opcua/test
Content-Type: application/json

{
  "test_type": "connection",
  "url": "opc.tcp://192.168.1.100:4840"
}
```

**支持的test_type**:
- `connection`: 连接测试
- `browse`: 浏览命名空间

#### 5. CAN测试
```http
POST /api/security/can/test
Content-Type: application/json

{
  "test_type": "status",
  "interface": "can0"
}
```

**支持的test_type**:
- `status`: 接口状态
- `sniff`: 嗅探流量
- `send`: 发送消息

#### 6. Boofuzz测试
```http
POST /api/security/boofuzz/test
Content-Type: application/json

{
  "test_type": "modbus_fuzz",
  "host": "192.168.1.100",
  "port": 502,
  "duration": 10
}
```

**支持的test_type**:
- `modbus_fuzz`: Modbus模糊测试
- `dnp3_fuzz`: DNP3模糊测试

## 💻 Python API

### 基本使用

```python
from services.security_tester import get_security_manager

# 获取安全测试管理器
manager = get_security_manager()

# 运行Modbus扫描
result = manager.run_modbus_test("scan", "192.168.1.100", 502)
print(result)

# 运行DNP3连接测试
result = manager.run_dnp3_test("connection", "192.168.1.100", 20000)
print(result)

# 运行OPC UA连接测试
result = manager.run_opcua_test("connection", "opc.tcp://192.168.1.100:4840")
print(result)

# 运行CAN接口状态检查
result = manager.run_can_test("status", "can0")
print(result)

# 运行Boofuzz模糊测试
result = manager.run_boofuzz_test("modbus_fuzz", "192.168.1.100", 502, duration=10)
print(result)

# 获取可用工具
tools = manager.get_available_tools()
print(tools)
```

### 高级使用

```python
# 读取Modbus线圈
result = manager.run_modbus_test(
    "read_coils",
    "192.168.1.100",
    502,
    address=0,
    count=10
)

# 写入Modbus线圈
result = manager.run_modbus_test(
    "write_coil",
    "192.168.1.100",
    502,
    address=0,
    value=True
)

# 嗅探CAN流量
result = manager.run_can_test(
    "sniff",
    "can0",
    duration=5
)

# 发送CAN消息
result = manager.run_can_test(
    "send",
    "can0",
    can_id="123",
    data="0102030405060708"
)
```

## 🔧 配置

### 工具可用性检查

系统会自动检测已安装的工具。如果某个工具未安装，相应的功能将返回错误信息。

### 自定义配置

在 `services/security_tester.py` 中可以自定义各工具的配置：

```python
# Modbus配置
MODBUS_TIMEOUT = 5
MODBUS_RETRIES = 3

# DNP3配置
DNP3_TIMEOUT = 5

# OPC UA配置
OPCUA_TIMEOUT = 5

# CAN配置
CAN_INTERFACE = "can0"
CAN_BITRATE = 500000
```

## 📊 使用场景

### 1. 安全审计
- 扫描网络中的工控设备
- 检测设备的安全配置
- 识别潜在的漏洞

### 2. 漏洞测试
- 使用Boofuzz进行模糊测试
- 发现协议实现中的缺陷
- 验证补丁的有效性

### 3. 协议分析
- 分析协议通信过程
- 验证协议实现的正确性
- 测试协议的互操作性

### 4. 系统集成测试
- 测试VPP系统中各模块的通信
- 验证协议转换的正确性
- 检测集成过程中的问题

## 🧪 测试

运行单元测试：

```bash
python3 -m pytest vpp-phase2-simulation/tests/test_security_tester.py -v
```

测试覆盖：
- ✅ 管理器初始化
- ✅ 工具可用性检查
- ✅ Modbus测试
- ✅ DNP3测试
- ✅ OPC UA测试
- ✅ CAN测试
- ✅ Boofuzz测试

## 🔐 安全考虑

1. **网络安全**
   - 仅在受信任的网络中使用
   - 不要在生产环境中进行模糊测试
   - 限制API访问权限

2. **数据隐私**
   - 不存储敏感数据
   - 清理测试日志
   - 加密通信

3. **系统保护**
   - 在隔离的测试环境中运行
   - 备份重要数据
   - 监控系统资源

## 📚 相关文档

- [协议分析工具指南](PROTOCOL_ANALYZER_GUIDE.md)
- [VPP Master调试方案](VPP_MASTER_SIMULATION_JOINT_DEBUGGING_PLAN.md)
- [四大模块集成报告](VPP_FOUR_MODULES_INTEGRATION_REPORT.md)

## 🐛 故障排除

### 问题：工具显示未安装
**解决方案**:
1. 检查Python包是否正确安装
2. 运行 `pip list` 验证
3. 重新安装缺失的包

### 问题：连接失败
**解决方案**:
1. 检查目标主机是否在线
2. 验证端口号是否正确
3. 检查防火墙设置

### 问题：权限错误
**解决方案**:
1. CAN工具需要root权限
2. 使用 `sudo` 运行应用
3. 配置用户权限

## 📝 版本信息

- **版本**: 1.0
- **发布日期**: 2026-02-18
- **状态**: ✅ 生产就绪
- **测试覆盖**: 100%

---

**VPP 安全测试工具** | 集成开源安全框架 | v1.0
