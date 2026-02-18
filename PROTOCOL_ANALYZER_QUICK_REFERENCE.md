# VPP 协议流量分析工具 - 快速参考

## 🚀 快速启动

```bash
# 启动应用
cd vpp-phase2-simulation
python3 app.py

# 访问Web界面
http://localhost:8080/analyzer

# 运行演示
python3 demo_protocol_analyzer.py

# 运行测试
python3 -m pytest tests/test_protocol_analyzer.py -v
```

## 🎯 Web界面快速操作

| 操作 | 按钮 | 说明 |
|------|------|------|
| 刷新数据 | 🔄 | 立即刷新所有数据 |
| 自动刷新 | ▶️ | 每2秒自动刷新 |
| 停止刷新 | ⏹️ | 停止自动刷新 |
| 重置统计 | 🗑️ | 清空所有统计数据 |

## 📊 标签页功能

| 标签 | 功能 | 用途 |
|------|------|------|
| 📊 协议统计 | 显示所有协议的聚合统计 | 了解整体流量分布 |
| 📦 数据包 | 显示最近捕获的数据包 | 检查具体数据包内容 |
| 🔗 流量分析 | 显示源到目标的通信流 | 追踪通信路径 |

## 🔌 API 快速参考

### 获取摘要
```bash
curl http://localhost:8080/api/analyzer/summary
```

### 获取协议统计
```bash
curl http://localhost:8080/api/analyzer/stats
```

### 获取数据包（限制100条）
```bash
curl 'http://localhost:8080/api/analyzer/packets?limit=100'
```

### 按协议过滤
```bash
curl 'http://localhost:8080/api/analyzer/packets?protocol=Modbus&limit=50'
```

### 获取流量分析
```bash
curl 'http://localhost:8080/api/analyzer/flows?limit=50'
```

### 添加数据包
```bash
curl -X POST http://localhost:8080/api/analyzer/packet \
  -H "Content-Type: application/json" \
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
```

### 重置统计
```bash
curl -X POST http://localhost:8080/api/analyzer/reset
```

### 获取支持的协议
```bash
curl http://localhost:8080/api/analyzer/protocols
```

## 🐍 Python API 快速参考

### 基本使用
```python
from services.protocol_analyzer import get_analyzer, PacketInfo
from datetime import datetime

# 获取分析器
analyzer = get_analyzer()

# 添加数据包
packet = PacketInfo(
    timestamp=datetime.now().isoformat(),
    protocol="Modbus",
    src_ip="192.168.1.100",
    dst_ip="192.168.1.200",
    src_port=502,
    dst_port=502,
    size=256,
    payload_preview="01 03 00 00 00 0A",
    direction="outbound"
)
analyzer.add_packet(packet)

# 获取统计
stats = analyzer.get_protocol_stats()

# 获取数据包
packets = analyzer.get_recent_packets(limit=10)

# 获取流
flows = analyzer.get_flows(limit=20)

# 获取摘要
summary = analyzer.get_summary()

# 重置
analyzer.reset()
```

## 📋 支持的协议

| 协议 | 标准 | 用途 |
|------|------|------|
| IEC61850 | 电力系统通信 | 电力系统SCADA |
| Modbus | 工业自动化 | 设备通信 |
| DNP3 | 电力系统 | SCADA协议 |
| MQTT | 物联网 | 消息发布/订阅 |
| OPC UA | 工业互操作 | 数据交换 |
| CAN | 车载网络 | 实时通信 |
| RS-232 | 串行通信 | 点对点通信 |
| RS-485 | 串行通信 | 多点通信 |
| LoRaWAN | 远程广域网 | 长距离通信 |
| XMPP | 即时通讯 | 消息通信 |
| DL/T | 中国电力标准 | 电力行业 |
| PROFINET | 工业以太网 | 实时通信 |

## 📊 统计指标说明

| 指标 | 说明 | 单位 |
|------|------|------|
| 总数据包 | 捕获的数据包总数 | 个 |
| 总数据量 | 所有数据包的总字节数 | 字节 |
| 协议类型 | 不同协议的数量 | 种 |
| 活跃流 | 源到目标的通信流数 | 条 |
| 平均包大小 | 平均每个数据包的大小 | 字节 |
| 包/秒 | 每秒传输的数据包数 | 个/秒 |
| 错误数 | 检测到的错误数量 | 个 |

## 🔍 过滤和搜索

### Web界面过滤
- **协议过滤**: 从下拉菜单选择协议
- **IP搜索**: 输入IP地址搜索
- **数量限制**: 设置显示的数据包数量

### API过滤
```bash
# 按协议过滤
?protocol=Modbus

# 限制数量
?limit=50

# 组合过滤
?protocol=MQTT&limit=100
```

## ⚙️ 配置参数

### 分析器配置
```python
# 最大保存数据包数
max_packets = 10000

# 历史数据保留时间（秒）
history_duration = 3600  # 1小时
```

### 自动刷新
- 默认间隔: 2秒
- 可手动启动/停止
- 支持自定义间隔

## 🧪 测试命令

```bash
# 运行所有测试
python3 -m pytest vpp-phase2-simulation/tests/test_protocol_analyzer.py -v

# 运行特定测试
python3 -m pytest vpp-phase2-simulation/tests/test_protocol_analyzer.py::TestProtocolAnalyzer::test_add_single_packet -v

# 运行演示
python3 vpp-phase2-simulation/demo_protocol_analyzer.py
```

## 📈 性能基准

| 操作 | 时间 | 备注 |
|------|------|------|
| 添加数据包 | < 1 ms | 单个操作 |
| 统计计算 | < 10 ms | 所有协议 |
| 查询操作 | < 5 ms | 单个查询 |
| 内存占用 | ~5 MB | 10,000个数据包 |

## 🔐 安全建议

1. **生产环境**
   - 添加身份验证
   - 限制API访问
   - 启用HTTPS

2. **数据保护**
   - 定期备份统计数据
   - 配置访问日志
   - 监控异常流量

3. **资源管理**
   - 设置合理的max_packets
   - 定期清理过期数据
   - 监控内存使用

## 🐛 常见问题

| 问题 | 解决方案 |
|------|---------|
| Web界面无法访问 | 检查应用是否运行，确认端口8080 |
| 数据包未显示 | 确认数据包已通过API添加 |
| 性能下降 | 减少max_packets或清理旧数据 |
| 内存占用过高 | 减少history_duration或重置数据 |

## 📚 文件结构

```
vpp-phase2-simulation/
├── services/
│   └── protocol_analyzer.py      # 核心分析服务
├── routes/
│   └── protocol_analyzer.py      # API路由
├── static/
│   └── protocol_analyzer.html    # Web界面
├── tests/
│   └── test_protocol_analyzer.py # 单元测试
├── demo_protocol_analyzer.py     # 演示脚本
└── app.py                        # 主应用
```

## 🔗 相关链接

- [完整使用指南](PROTOCOL_ANALYZER_GUIDE.md)
- [VPP Master调试方案](VPP_MASTER_SIMULATION_JOINT_DEBUGGING_PLAN.md)
- [Phase 3集成指南](vpp-phase2-simulation/PHASE3_INTEGRATION_GUIDE.md)

## 💡 使用技巧

1. **实时监控**: 使用自动刷新功能持续监控流量
2. **性能分析**: 查看"包/秒"指标了解吞吐量
3. **故障诊断**: 按IP搜索追踪特定通信
4. **协议验证**: 检查数据包预览验证协议格式
5. **流量追踪**: 使用流量分析标签追踪通信路径

---

**快速参考** | VPP 协议流量分析工具 v1.0
