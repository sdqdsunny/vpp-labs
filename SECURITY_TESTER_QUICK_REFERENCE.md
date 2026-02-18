# VPP 安全测试工具 - 快速参考

## 🚀 快速启动

```bash
# 安装依赖
pip install pymodbus dnp3 opcua boofuzz
sudo apt-get install can-utils  # Linux

# 启动应用
cd vpp-phase2-simulation
python3 app.py

# 访问Web界面
http://localhost:8080/security

# 运行测试
python3 -m pytest tests/test_security_tester.py -v
```

## 🎯 Web界面快速操作

| 工具 | 测试类型 | 参数 | 用途 |
|------|---------|------|------|
| Modbus | 扫描设备 | host, port | 发现Modbus设备 |
| Modbus | 读取线圈 | host, port, address, count | 读取线圈状态 |
| Modbus | 读取寄存器 | host, port, address, count | 读取寄存器值 |
| Modbus | 写入线圈 | host, port, address, value | 写入线圈状态 |
| DNP3 | 连接测试 | host, port | 测试连接 |
| DNP3 | 扫描点 | host, port | 扫描DNP3点 |
| OPC UA | 连接测试 | url | 测试连接 |
| OPC UA | 浏览命名空间 | url | 浏览命名空间 |
| CAN | 接口状态 | interface | 检查接口 |
| CAN | 嗅探流量 | interface, duration | 捕获消息 |
| CAN | 发送消息 | interface, can_id, data | 发送消息 |
| Boofuzz | Modbus模糊 | host, port, duration | 模糊测试 |
| Boofuzz | DNP3模糊 | host, port, duration | 模糊测试 |

## 🔌 API 快速参考

### 获取工具状态
```bash
curl http://localhost:8080/api/security/tools
```

### Modbus测试
```bash
# 扫描设备
curl -X POST http://localhost:8080/api/security/modbus/test \
  -H "Content-Type: application/json" \
  -d '{"test_type":"scan","host":"192.168.1.100","port":502}'

# 读取线圈
curl -X POST http://localhost:8080/api/security/modbus/test \
  -H "Content-Type: application/json" \
  -d '{"test_type":"read_coils","host":"192.168.1.100","port":502,"address":0,"count":10}'

# 读取寄存器
curl -X POST http://localhost:8080/api/security/modbus/test \
  -H "Content-Type: application/json" \
  -d '{"test_type":"read_registers","host":"192.168.1.100","port":502,"address":0,"count":10}'

# 写入线圈
curl -X POST http://localhost:8080/api/security/modbus/test \
  -H "Content-Type: application/json" \
  -d '{"test_type":"write_coil","host":"192.168.1.100","port":502,"address":0,"value":true}'
```

### DNP3测试
```bash
# 连接测试
curl -X POST http://localhost:8080/api/security/dnp3/test \
  -H "Content-Type: application/json" \
  -d '{"test_type":"connection","host":"192.168.1.100","port":20000}'

# 扫描点
curl -X POST http://localhost:8080/api/security/dnp3/test \
  -H "Content-Type: application/json" \
  -d '{"test_type":"scan","host":"192.168.1.100","port":20000}'
```

### OPC UA测试
```bash
# 连接测试
curl -X POST http://localhost:8080/api/security/opcua/test \
  -H "Content-Type: application/json" \
  -d '{"test_type":"connection","url":"opc.tcp://192.168.1.100:4840"}'

# 浏览命名空间
curl -X POST http://localhost:8080/api/security/opcua/test \
  -H "Content-Type: application/json" \
  -d '{"test_type":"browse","url":"opc.tcp://192.168.1.100:4840"}'
```

### CAN测试
```bash
# 接口状态
curl -X POST http://localhost:8080/api/security/can/test \
  -H "Content-Type: application/json" \
  -d '{"test_type":"status","interface":"can0"}'

# 嗅探流量
curl -X POST http://localhost:8080/api/security/can/test \
  -H "Content-Type: application/json" \
  -d '{"test_type":"sniff","interface":"can0","duration":5}'

# 发送消息
curl -X POST http://localhost:8080/api/security/can/test \
  -H "Content-Type: application/json" \
  -d '{"test_type":"send","interface":"can0","can_id":"123","data":"0102030405060708"}'
```

### Boofuzz测试
```bash
# Modbus模糊测试
curl -X POST http://localhost:8080/api/security/boofuzz/test \
  -H "Content-Type: application/json" \
  -d '{"test_type":"modbus_fuzz","host":"192.168.1.100","port":502,"duration":10}'

# DNP3模糊测试
curl -X POST http://localhost:8080/api/security/boofuzz/test \
  -H "Content-Type: application/json" \
  -d '{"test_type":"dnp3_fuzz","host":"192.168.1.100","port":20000,"duration":10}'
```

## 🐍 Python API 快速参考

```python
from services.security_tester import get_security_manager

manager = get_security_manager()

# Modbus
manager.run_modbus_test("scan", "192.168.1.100", 502)
manager.run_modbus_test("read_coils", "192.168.1.100", 502, address=0, count=10)
manager.run_modbus_test("read_registers", "192.168.1.100", 502, address=0, count=10)
manager.run_modbus_test("write_coil", "192.168.1.100", 502, address=0, value=True)

# DNP3
manager.run_dnp3_test("connection", "192.168.1.100", 20000)
manager.run_dnp3_test("scan", "192.168.1.100", 20000)

# OPC UA
manager.run_opcua_test("connection", "opc.tcp://192.168.1.100:4840")
manager.run_opcua_test("browse", "opc.tcp://192.168.1.100:4840")

# CAN
manager.run_can_test("status", "can0")
manager.run_can_test("sniff", "can0", duration=5)
manager.run_can_test("send", "can0", can_id="123", data="0102030405060708")

# Boofuzz
manager.run_boofuzz_test("modbus_fuzz", "192.168.1.100", 502, duration=10)
manager.run_boofuzz_test("dnp3_fuzz", "192.168.1.100", 20000, duration=10)

# 获取工具状态
tools = manager.get_available_tools()
```

## 📋 工具安装命令

```bash
# PyModbus
pip install pymodbus

# OpenDNP3
pip install dnp3

# python-opcua
pip install opcua

# SocketCAN (Linux)
sudo apt-get install can-utils

# SocketCAN (macOS)
brew install can-utils

# Boofuzz
pip install boofuzz
```

## 🔍 常见用例

### 1. 扫描Modbus设备
```bash
curl -X POST http://localhost:8080/api/security/modbus/test \
  -H "Content-Type: application/json" \
  -d '{"test_type":"scan","host":"192.168.1.0","port":502}'
```

### 2. 读取Modbus数据
```bash
curl -X POST http://localhost:8080/api/security/modbus/test \
  -H "Content-Type: application/json" \
  -d '{"test_type":"read_registers","host":"192.168.1.100","port":502,"address":0,"count":100}'
```

### 3. 测试OPC UA连接
```bash
curl -X POST http://localhost:8080/api/security/opcua/test \
  -H "Content-Type: application/json" \
  -d '{"test_type":"connection","url":"opc.tcp://192.168.1.100:4840"}'
```

### 4. 嗅探CAN流量
```bash
curl -X POST http://localhost:8080/api/security/can/test \
  -H "Content-Type: application/json" \
  -d '{"test_type":"sniff","interface":"can0","duration":10}'
```

### 5. 模糊测试Modbus
```bash
curl -X POST http://localhost:8080/api/security/boofuzz/test \
  -H "Content-Type: application/json" \
  -d '{"test_type":"modbus_fuzz","host":"192.168.1.100","port":502,"duration":30}'
```

## 📊 工具对比

| 工具 | 协议 | 功能 | 易用性 | 性能 |
|------|------|------|--------|------|
| PyModbus | Modbus | 读写、扫描 | ⭐⭐⭐⭐⭐ | 快速 |
| OpenDNP3 | DNP3 | 连接、扫描 | ⭐⭐⭐ | 中等 |
| python-opcua | OPC UA | 连接、浏览 | ⭐⭐⭐⭐ | 中等 |
| SocketCAN | CAN | 嗅探、发送 | ⭐⭐⭐ | 快速 |
| Boofuzz | 多种 | 模糊测试 | ⭐⭐ | 慢速 |

## 🔐 安全建议

1. **仅在测试环境使用**
2. **不要在生产系统上运行模糊测试**
3. **限制API访问权限**
4. **监控测试活动**
5. **备份重要数据**

## 🐛 常见问题

| 问题 | 解决方案 |
|------|---------|
| 工具显示未安装 | 运行 `pip install` 安装缺失的包 |
| 连接失败 | 检查目标主机和端口是否正确 |
| 权限错误 | CAN工具需要root权限，使用sudo |
| 超时错误 | 增加超时时间或检查网络连接 |

## 📚 文件结构

```
vpp-phase2-simulation/
├── services/
│   └── security_tester.py              # 核心服务
├── routes/
│   └── security_tester.py              # API路由
├── static/
│   └── security_tester.html            # Web界面
├── tests/
│   └── test_security_tester.py         # 单元测试
└── app.py                              # 主应用
```

## 📞 获取帮助

- 查看完整指南: `SECURITY_TESTER_GUIDE.md`
- 查看API文档: 访问 `/security` 页面
- 运行测试: `pytest tests/test_security_tester.py -v`

---

**快速参考** | VPP 安全测试工具 v1.0
