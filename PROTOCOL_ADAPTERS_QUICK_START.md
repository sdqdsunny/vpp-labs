# 工控协议适配器框架 - 快速开始指南

**版本**: 1.0
**日期**: 2026年2月17日

---

## 🚀 快速开始

### 1. 导入必要的类

```python
from services.protocol_adapters import (
    ProtocolAdapter,
    ProtocolMessage,
    ProtocolType,
    ProtocolRegistry,
    ProtocolMessageMapper,
)
```

### 2. 创建自定义适配器

```python
class MyProtocolAdapter(ProtocolAdapter):
    def __init__(self, adapter_id: str):
        super().__init__(adapter_id, ProtocolType.MQTT)
    
    def connect(self, config):
        # 实现连接逻辑
        self.is_connected = True
        return True
    
    def disconnect(self):
        # 实现断开连接逻辑
        self.is_connected = False
        return True
    
    def send_message(self, message):
        # 实现发送消息逻辑
        self._record_message()
        return True
    
    def receive_message(self, timeout=1.0):
        # 实现接收消息逻辑
        return None
    
    def parse_message(self, data):
        # 实现解析消息逻辑
        return {}
    
    def encode_message(self, message):
        # 实现编码消息逻辑
        return b""
    
    def validate_message(self, data):
        # 实现验证消息逻辑
        return True
```

### 3. 注册适配器

```python
# 注册适配器类
ProtocolRegistry.register("my_protocol", MyProtocolAdapter)

# 创建适配器实例
adapter = ProtocolRegistry.create_adapter("my_protocol", "adapter-1")

# 连接
adapter.connect({"host": "localhost", "port": 8080})

# 发送消息
message = ProtocolMessage(
    protocol="my_protocol",
    message_id="msg-1",
    source="device-1",
    destination="device-2",
    timestamp=time.time(),
    data={"value": 100},
)
adapter.send_message(message)

# 接收消息
received = adapter.receive_message(timeout=1.0)

# 获取状态
status = adapter.get_status()
print(status)

# 断开连接
adapter.disconnect()
```

---

## 📊 消息映射示例

### 1. 直接字段映射

```python
mapper = ProtocolMessageMapper()

# 定义映射规则
rules = {
    "voltage": "source_voltage",
    "current": "source_current",
}

# 注册映射
mapper.register_mapping("iec61850", "modbus", rules)

# 映射消息
message = {
    "source_voltage": 230,
    "source_current": 10,
}
result = mapper.map_message("iec61850", "modbus", message)
# 结果: {"voltage": 230, "current": 10}
```

### 2. 转换器映射

```python
# 定义转换器
def scale_current(data):
    return data.get("current", 0) * 1000

# 注册转换器
mapper.register_transformer("scale_current", scale_current)

# 定义映射规则
rules = {
    "voltage": "voltage",
    "current_ma": {"transformer": "scale_current"},
}

mapper.register_mapping("iec61850", "modbus", rules)

# 映射消息
message = {"voltage": 230, "current": 0.01}
result = mapper.map_message("iec61850", "modbus", message)
# 结果: {"voltage": 230, "current_ma": 10}
```

### 3. 条件映射

```python
# 定义映射规则
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

mapper.register_mapping("iec61850", "modbus", rules)

# 映射消息
message = {"voltage": 230}
result = mapper.map_message("iec61850", "modbus", message)
# 结果: {"status": "normal"}
```

### 4. 消息验证

```python
# 定义验证器
def validate_voltage(message):
    return 0 <= message.get("voltage", 0) <= 400

# 注册验证器
mapper.register_validator("validate_voltage", validate_voltage)

# 验证消息
is_valid = mapper.validate_message("validate_voltage", {"voltage": 230})
# 结果: True
```

---

## 🔧 常见操作

### 查询已注册的协议

```python
protocols = ProtocolRegistry.list_protocols()
print(protocols)  # ['iec61850', 'modbus', 'dnp3', 'mqtt']
```

### 查询活跃的适配器

```python
adapters = ProtocolRegistry.list_adapters()
print(adapters)  # ['adapter-1', 'adapter-2']
```

### 获取适配器状态

```python
adapter = ProtocolRegistry.get_adapter("adapter-1")
status = adapter.get_status()
print(status)
# {
#     "adapter_id": "adapter-1",
#     "protocol_type": "mqtt",
#     "is_connected": True,
#     "message_count": 100,
#     "error_count": 2,
#     "last_error": "Connection timeout",
#     "uptime_seconds": 3600,
# }
```

### 获取注册表状态

```python
status = ProtocolRegistry.get_status()
print(status)
# {
#     "registered_protocols": ["iec61850", "modbus", "dnp3", "mqtt"],
#     "active_adapters": ["adapter-1", "adapter-2"],
#     "total_protocols": 4,
#     "total_instances": 2,
# }
```

### 获取映射器信息

```python
mapper = ProtocolMessageMapper()
info = mapper.get_mapping_info()
print(info)
# {
#     "mappings": ["iec61850->modbus", "modbus->dnp3"],
#     "transformers": ["scale_current", "convert_voltage"],
#     "validators": ["validate_voltage", "validate_current"],
#     "total_mappings": 2,
#     "total_transformers": 2,
#     "total_validators": 2,
# }
```

---

## 🧪 测试示例

### 运行所有测试

```bash
python3 -m pytest vpp-phase2-simulation/tests/test_protocol_*.py -v
```

### 运行特定测试

```bash
# 运行注册表测试
python3 -m pytest vpp-phase2-simulation/tests/test_protocol_registry.py -v

# 运行映射器测试
python3 -m pytest vpp-phase2-simulation/tests/test_protocol_mapper.py -v

# 运行特定测试用例
python3 -m pytest vpp-phase2-simulation/tests/test_protocol_registry.py::TestProtocolRegistry::test_register_adapter -v
```

### 查看测试覆盖率

```bash
python3 -m pytest vpp-phase2-simulation/tests/test_protocol_*.py --cov=services.protocol_adapters --cov-report=html
```

---

## 📚 API 参考

### ProtocolAdapter 基类

```python
class ProtocolAdapter(ABC):
    # 属性
    adapter_id: str
    protocol_type: ProtocolType
    is_connected: bool
    message_count: int
    error_count: int
    last_error: Optional[str]
    
    # 方法
    def connect(config: Dict[str, Any]) -> bool
    def disconnect() -> bool
    def send_message(message: ProtocolMessage) -> bool
    def receive_message(timeout: float = 1.0) -> Optional[ProtocolMessage]
    def parse_message(data: bytes) -> Dict[str, Any]
    def encode_message(message: Dict[str, Any]) -> bytes
    def validate_message(data: bytes) -> bool
    def get_status() -> Dict[str, Any]
```

### ProtocolRegistry 类

```python
class ProtocolRegistry:
    @classmethod
    def register(protocol_name: str, adapter_class: Type[ProtocolAdapter]) -> None
    
    @classmethod
    def unregister(protocol_name: str) -> None
    
    @classmethod
    def get_adapter_class(protocol_name: str) -> Type[ProtocolAdapter]
    
    @classmethod
    def create_adapter(protocol_name: str, adapter_id: str) -> ProtocolAdapter
    
    @classmethod
    def get_adapter(adapter_id: str) -> Optional[ProtocolAdapter]
    
    @classmethod
    def list_protocols() -> List[str]
    
    @classmethod
    def list_adapters() -> List[str]
    
    @classmethod
    def is_protocol_supported(protocol_name: str) -> bool
    
    @classmethod
    def remove_adapter(adapter_id: str) -> None
    
    @classmethod
    def clear() -> None
    
    @classmethod
    def get_status() -> Dict[str, Any]
```

### ProtocolMessageMapper 类

```python
class ProtocolMessageMapper:
    def register_mapping(source_protocol: str, target_protocol: str, 
                        mapping_rules: Dict[str, Any]) -> None
    
    def register_transformer(name: str, 
                            transformer: Callable[[Dict[str, Any]], Any]) -> None
    
    def register_validator(name: str, 
                          validator: Callable[[Dict[str, Any]], bool]) -> None
    
    def map_message(source_protocol: str, target_protocol: str, 
                   message: Dict[str, Any]) -> Dict[str, Any]
    
    def transform_data(transformer_name: str, 
                      data: Dict[str, Any]) -> Any
    
    def validate_message(validator_name: str, 
                        message: Dict[str, Any]) -> bool
    
    def get_mapping_info() -> Dict[str, Any]
```

---

## 🐛 常见问题

### Q: 如何处理连接失败？

A: 使用 try-except 捕获异常：

```python
try:
    adapter.connect(config)
except ConnectionException as e:
    print(f"Connection failed: {e}")
```

### Q: 如何自定义错误处理？

A: 在适配器中重写错误处理逻辑：

```python
def send_message(self, message):
    try:
        # 发送消息
        return True
    except Exception as e:
        self._record_error(str(e))
        return False
```

### Q: 如何添加新的映射规则？

A: 使用 register_mapping 方法：

```python
mapper.register_mapping("protocol1", "protocol2", {
    "field1": "source_field1",
    "field2": {"transformer": "my_transformer"},
})
```

### Q: 如何验证消息？

A: 使用 validate_message 方法：

```python
is_valid = mapper.validate_message("my_validator", message)
if not is_valid:
    print("Message validation failed")
```

---

## 📖 更多资源

- `requirements.md` - 需求文档
- `design.md` - 设计文档
- `tasks.md` - 任务清单
- `PROTOCOL_LIBRARIES_ANALYSIS.md` - 库分析
- `PROTOCOL_INTEGRATION_IMPLEMENTATION_PLAN.md` - 实施计划

---

**版本**: 1.0
**最后更新**: 2026年2月17日
