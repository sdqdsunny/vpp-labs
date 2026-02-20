# 工控协议库集成 - 设计文档

**版本**: 1.0
**日期**: 2026年2月17日
**状态**: 已批准

---

## 🏗️ 架构设计

### 三层架构

```
┌─────────────────────────────────────────┐
│  应用层 (VCC, 设备模拟器)               │
├─────────────────────────────────────────┤
│  适配器层 (统一接口)                    │
│  - ProtocolAdapter (基类)               │
│  - ProtocolRegistry (注册表)            │
│  - ProtocolMessageMapper (映射器)       │
├─────────────────────────────────────────┤
│  库层 (原生实现)                        │
│  - libiec61850 (C)                      │
│  - pymodbus (Python)                    │
│  - opendnp3 (C++)                       │
│  - paho-mqtt (C)                        │
└─────────────────────────────────────────┘
```

### 核心组件

#### 1. ProtocolAdapter (基类)

```python
class ProtocolAdapter(ABC):
    def connect(config: Dict) -> bool
    def disconnect() -> bool
    def send_message(message: ProtocolMessage) -> bool
    def receive_message(timeout: float) -> Optional[ProtocolMessage]
    def parse_message(data: bytes) -> Dict
    def encode_message(message: Dict) -> bytes
    def validate_message(data: bytes) -> bool
    def get_status() -> Dict
```

**职责**:
- 定义统一的协议接口
- 管理连接生命周期
- 处理消息收发
- 记录错误和统计

#### 2. ProtocolRegistry (注册表)

```python
class ProtocolRegistry:
    @classmethod
    def register(protocol_name: str, adapter_class: Type)
    @classmethod
    def create_adapter(protocol_name: str, adapter_id: str) -> ProtocolAdapter
    @classmethod
    def get_adapter(adapter_id: str) -> Optional[ProtocolAdapter]
    @classmethod
    def list_protocols() -> List[str]
    @classmethod
    def is_protocol_supported(protocol_name: str) -> bool
```

**职责**:
- 管理适配器注册
- 创建适配器实例
- 查询适配器信息
- 维护适配器生命周期

#### 3. ProtocolMessageMapper (映射器)

```python
class ProtocolMessageMapper:
    def register_mapping(source: str, target: str, rules: Dict)
    def register_transformer(name: str, transformer: Callable)
    def register_validator(name: str, validator: Callable)
    def map_message(source: str, target: str, message: Dict) -> Dict
    def transform_data(transformer_name: str, data: Dict) -> Any
    def validate_message(validator_name: str, message: Dict) -> bool
```

**职责**:
- 定义协议间映射规则
- 执行消息转换
- 验证消息有效性
- 支持自定义转换器

#### 4. ProtocolMessage (统一消息格式)

```python
@dataclass
class ProtocolMessage:
    protocol: str
    message_id: str
    source: str
    destination: str
    timestamp: float
    data: Dict[str, Any]
    metadata: Dict[str, Any]
```

**职责**:
- 统一的消息格式
- 支持序列化/反序列化
- 包含元数据信息

---

## 📊 协议适配器设计

### IEC 61850 适配器

**特点**:
- 微秒级精度时间戳
- 支持 GOOSE 和 SV 消息
- 完整的标准实现

**关键方法**:
- `connect()`: 建立 IEC 61850 连接
- `send_goose()`: 发送 GOOSE 消息
- `send_sv()`: 发送 SV 消息
- `receive_goose()`: 接收 GOOSE 消息

### Modbus 适配器

**特点**:
- 纯 Python 实现
- 支持 TCP 和 RTU
- 异步操作

**关键方法**:
- `connect()`: 建立 Modbus 连接
- `read_registers()`: 读取寄存器
- `write_registers()`: 写入寄存器
- `read_coils()`: 读取线圈

### DNP3 适配器

**特点**:
- 安全认证
- 可靠的消息传输
- 事件报告

**关键方法**:
- `connect()`: 建立 DNP3 连接
- `send_command()`: 发送命令
- `read_data()`: 读取数据
- `report_event()`: 报告事件

### MQTT 适配器

**特点**:
- 标准 MQTT 支持
- SSL/TLS 加密
- 主题订阅/发布

**关键方法**:
- `connect()`: 建立 MQTT 连接
- `publish()`: 发布消息
- `subscribe()`: 订阅主题
- `on_message()`: 消息回调

---

## 🔄 消息流程

### 发送消息流程

```
应用层
  ↓
ProtocolRegistry.get_adapter(adapter_id)
  ↓
adapter.send_message(ProtocolMessage)
  ↓
adapter.encode_message(message.data)
  ↓
协议库
  ↓
网络传输
```

### 接收消息流程

```
网络传输
  ↓
协议库
  ↓
adapter.receive_message()
  ↓
adapter.parse_message(raw_data)
  ↓
ProtocolMessage
  ↓
应用层
```

### 消息转换流程

```
源协议消息
  ↓
ProtocolMessageMapper.map_message(source, target, message)
  ↓
应用映射规则
  ↓
执行转换器
  ↓
验证消息
  ↓
目标协议消息
```

---

## 📈 映射规则设计

### 直接字段映射

```python
rules = {
    "voltage": "source_voltage",
    "current": "source_current",
}
```

### 转换器映射

```python
rules = {
    "current_ma": {
        "transformer": "scale_current",
    }
}

mapper.register_transformer("scale_current", lambda data: data["current"] * 1000)
```

### 条件映射

```python
rules = {
    "status": {
        "condition": {
            "field": "voltage",
            "operator": "gt",
            "value": 200,
        },
        "value": "normal",
    }
}
```

### 默认值映射

```python
rules = {
    "frequency": {"default": 50},
}
```

---

## 🔐 错误处理

### 异常层次

```
ProtocolException (基类)
├── ConnectionException (连接错误)
├── MessageException (消息错误)
└── ValidationException (验证错误)
```

### 错误恢复

- 自动重连机制
- 指数退避算法
- 最大重试次数限制
- 错误日志记录

---

## 📊 状态管理

### 适配器状态

```python
{
    "adapter_id": "iec61850-adapter-1",
    "protocol_type": "iec61850",
    "is_connected": True,
    "message_count": 1000,
    "error_count": 5,
    "last_error": "Connection timeout",
    "uptime_seconds": 3600,
}
```

### 注册表状态

```python
{
    "registered_protocols": ["iec61850", "modbus", "dnp3", "mqtt"],
    "active_adapters": ["adapter-1", "adapter-2"],
    "total_protocols": 4,
    "total_instances": 2,
}
```

---

## 🧪 测试策略

### 单元测试

- 适配器基类测试
- 注册表功能测试
- 映射器功能测试
- 消息格式测试

### 集成测试

- 协议适配器集成测试
- 消息转换集成测试
- 端到端流程测试

### 性能测试

- 消息处理延迟测试
- 吞吐量测试
- 内存占用测试
- CPU 占用测试

---

## 📚 API 设计

### 适配器 API

```python
# 创建适配器
adapter = ProtocolRegistry.create_adapter("iec61850", "adapter-1")

# 连接
adapter.connect({"host": "localhost", "port": 102})

# 发送消息
message = ProtocolMessage(...)
adapter.send_message(message)

# 接收消息
received = adapter.receive_message(timeout=1.0)

# 获取状态
status = adapter.get_status()

# 断开连接
adapter.disconnect()
```

### 映射器 API

```python
# 创建映射器
mapper = ProtocolMessageMapper()

# 注册映射规则
mapper.register_mapping("iec61850", "modbus", rules)

# 注册转换器
mapper.register_transformer("scale_current", transformer_func)

# 映射消息
result = mapper.map_message("iec61850", "modbus", message)

# 验证消息
is_valid = mapper.validate_message("validate_voltage", message)
```

---

## 🔧 配置设计

### 适配器配置

```yaml
adapters:
  iec61850:
    host: localhost
    port: 102
    timeout: 5
    retry_count: 3
  
  modbus:
    host: localhost
    port: 502
    mode: tcp
    timeout: 5
  
  dnp3:
    host: localhost
    port: 20000
    timeout: 5
  
  mqtt:
    host: localhost
    port: 1883
    use_tls: false
```

### 映射规则配置

```yaml
mappings:
  iec61850_to_modbus:
    voltage: source_voltage
    current:
      transformer: scale_current
    frequency:
      default: 50
```

---

## 📋 实现清单

- [x] ProtocolAdapter 基类
- [x] ProtocolRegistry 注册表
- [x] ProtocolMessageMapper 映射器
- [x] ProtocolMessage 消息格式
- [ ] IEC 61850 适配器
- [ ] Modbus 适配器
- [ ] DNP3 适配器
- [ ] MQTT 适配器
- [ ] 协议映射规则
- [ ] VCC 集成
- [ ] 完整测试套件
- [ ] 文档

---

## 📞 相关文档

- requirements.md - 需求文档
- tasks.md - 任务清单
- PROTOCOL_LIBRARIES_ANALYSIS.md - 库分析
- PROTOCOL_INTEGRATION_IMPLEMENTATION_PLAN.md - 实施计划
