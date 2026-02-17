# 工控协议库集成实施计划

**版本**: 1.0
**日期**: 2026年2月17日
**状态**: 待审批

---

## 📋 执行摘要

本文档详细规划了将 4 个标准工控协议库集成到 VPP Phase 2 Simulation 的实施步骤。

**集成库**:
1. libiec61850 - IEC 61850 协议
2. pymodbus - Modbus 协议
3. opendnp3 - DNP3 协议
4. paho.mqtt.c - MQTT 协议

**预期成果**:
- 统一的协议适配器框架
- 4 个完整的协议实现
- 协议间消息映射
- 完整的测试套件
- 详细的文档

**总工作量**: 26 人天
**预计周期**: 10-16 天

---

## 🎯 Phase 1: 基础设施准备 (1-2 天)

### 1.1 创建协议适配器框架

**文件**: `vpp-phase2-simulation/services/protocol_adapters/base.py`

```python
# 统一的协议适配器基类
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from enum import Enum

class ProtocolType(Enum):
    """支持的协议类型"""
    IEC61850 = "iec61850"
    MODBUS = "modbus"
    DNP3 = "dnp3"
    MQTT = "mqtt"

@dataclass
class ProtocolMessage:
    """统一的协议消息格式"""
    protocol: str
    message_id: str
    source: str
    destination: str
    timestamp: float
    data: Dict[str, Any]
    metadata: Dict[str, Any] = None

class ProtocolAdapter(ABC):
    """协议适配器基类"""
    
    def __init__(self, adapter_id: str):
        self.adapter_id = adapter_id
        self.is_connected = False
        self.message_count = 0
        self.error_count = 0
    
    @abstractmethod
    def connect(self, config: Dict[str, Any]) -> bool:
        """建立连接"""
        pass
    
    @abstractmethod
    def disconnect(self) -> bool:
        """断开连接"""
        pass
    
    @abstractmethod
    def send_message(self, message: ProtocolMessage) -> bool:
        """发送消息"""
        pass
    
    @abstractmethod
    def receive_message(self, timeout: float = 1.0) -> Optional[ProtocolMessage]:
        """接收消息"""
        pass
    
    @abstractmethod
    def parse_message(self, data: bytes) -> Dict[str, Any]:
        """解析消息"""
        pass
    
    @abstractmethod
    def encode_message(self, message: Dict[str, Any]) -> bytes:
        """编码消息"""
        pass
    
    @abstractmethod
    def validate_message(self, data: bytes) -> bool:
        """验证消息"""
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """获取适配器状态"""
        return {
            "adapter_id": self.adapter_id,
            "is_connected": self.is_connected,
            "message_count": self.message_count,
            "error_count": self.error_count
        }
```

### 1.2 创建协议注册表

**文件**: `vpp-phase2-simulation/services/protocol_adapters/registry.py`

```python
from typing import Dict, Type, List
from .base import ProtocolAdapter, ProtocolType

class ProtocolRegistry:
    """协议适配器注册表"""
    
    _adapters: Dict[str, Type[ProtocolAdapter]] = {}
    
    @classmethod
    def register(cls, protocol_name: str, adapter_class: Type[ProtocolAdapter]):
        """注册协议适配器"""
        cls._adapters[protocol_name] = adapter_class
    
    @classmethod
    def get_adapter(cls, protocol_name: str) -> ProtocolAdapter:
        """获取协议适配器实例"""
        if protocol_name not in cls._adapters:
            raise ValueError(f"Unknown protocol: {protocol_name}")
        return cls._adapters[protocol_name]()
    
    @classmethod
    def list_protocols(cls) -> List[str]:
        """列出所有支持的协议"""
        return list(cls._adapters.keys())
    
    @classmethod
    def is_protocol_supported(cls, protocol_name: str) -> bool:
        """检查协议是否支持"""
        return protocol_name in cls._adapters
```

### 1.3 创建消息映射器

**文件**: `vpp-phase2-simulation/services/protocol_adapters/mapper.py`

```python
from typing import Dict, Any, Callable
from .base import ProtocolMessage

class ProtocolMessageMapper:
    """协议消息映射器"""
    
    def __init__(self):
        self.mappings: Dict[str, Dict[str, Any]] = {}
        self.transformers: Dict[str, Callable] = {}
    
    def register_mapping(self, source_protocol: str, target_protocol: str,
                        mapping_rules: Dict[str, Any]):
        """注册协议映射规则"""
        key = f"{source_protocol}->{target_protocol}"
        self.mappings[key] = mapping_rules
    
    def register_transformer(self, name: str, transformer: Callable):
        """注册数据转换器"""
        self.transformers[name] = transformer
    
    def map_message(self, source_protocol: str, target_protocol: str,
                   message: Dict[str, Any]) -> Dict[str, Any]:
        """将消息从一个协议映射到另一个协议"""
        key = f"{source_protocol}->{target_protocol}"
        if key not in self.mappings:
            raise ValueError(f"No mapping found: {key}")
        
        mapping_rules = self.mappings[key]
        return self._apply_mapping(message, mapping_rules)
    
    def _apply_mapping(self, message: Dict[str, Any], 
                      rules: Dict[str, Any]) -> Dict[str, Any]:
        """应用映射规则"""
        result = {}
        for target_field, rule in rules.items():
            if isinstance(rule, str):
                # 直接字段映射
                result[target_field] = message.get(rule)
            elif isinstance(rule, dict):
                # 条件映射
                if "transformer" in rule:
                    transformer = self.transformers[rule["transformer"]]
                    result[target_field] = transformer(message)
                elif "source" in rule:
                    result[target_field] = message.get(rule["source"])
        return result
```

### 1.4 更新 Docker 配置

**文件**: `vpp-phase2-simulation/Dockerfile`

```dockerfile
FROM python:3.9-slim

# 系统依赖
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    libssl-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# 编译 libiec61850
RUN git clone https://github.com/mzautomation/libiec61850.git /tmp/libiec61850 && \
    cd /tmp/libiec61850 && \
    mkdir build && cd build && \
    cmake .. -DBUILD_PYTHON_BINDING=ON && \
    make && make install && \
    ldconfig

# 编译 opendnp3
RUN git clone https://github.com/dnp3/opendnp3.git /tmp/opendnp3 && \
    cd /tmp/opendnp3 && \
    mkdir build && cd build && \
    cmake .. -DPYTHON=ON && \
    make && make install && \
    ldconfig

# Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 应用代码
WORKDIR /app
COPY . .

CMD ["python", "app.py"]
```

**文件**: `vpp-phase2-simulation/requirements.txt` (添加)

```
pymodbus==3.0.0
paho-mqtt==1.6.1
```

### 1.5 创建测试框架

**文件**: `vpp-phase2-simulation/tests/test_protocol_adapters_base.py`

```python
import pytest
from abc import ABC
from services.protocol_adapters.base import ProtocolAdapter, ProtocolMessage

class ProtocolAdapterTestBase(ABC):
    """协议适配器测试基类"""
    
    @pytest.fixture
    def adapter(self):
        """创建适配器实例"""
        raise NotImplementedError
    
    def test_connect(self, adapter):
        """测试连接"""
        config = self.get_test_config()
        assert adapter.connect(config) == True
        assert adapter.is_connected == True
    
    def test_disconnect(self, adapter):
        """测试断开连接"""
        config = self.get_test_config()
        adapter.connect(config)
        assert adapter.disconnect() == True
        assert adapter.is_connected == False
    
    def test_send_message(self, adapter):
        """测试发送消息"""
        config = self.get_test_config()
        adapter.connect(config)
        
        message = self.get_test_message()
        assert adapter.send_message(message) == True
        assert adapter.message_count > 0
    
    def test_parse_message(self, adapter):
        """测试解析消息"""
        test_data = self.get_test_data()
        parsed = adapter.parse_message(test_data)
        assert isinstance(parsed, dict)
    
    def test_encode_message(self, adapter):
        """测试编码消息"""
        message = self.get_test_message()
        encoded = adapter.encode_message(message.data)
        assert isinstance(encoded, bytes)
    
    def test_validate_message(self, adapter):
        """测试验证消息"""
        test_data = self.get_test_data()
        assert adapter.validate_message(test_data) == True
    
    def get_test_config(self) -> dict:
        """获取测试配置"""
        raise NotImplementedError
    
    def get_test_message(self) -> ProtocolMessage:
        """获取测试消息"""
        raise NotImplementedError
    
    def get_test_data(self) -> bytes:
        """获取测试数据"""
        raise NotImplementedError
```

---

## 🔧 Phase 2: 协议适配器实现 (3-5 天)

### 2.1 IEC 61850 适配器

**文件**: `vpp-phase2-simulation/services/protocol_adapters/iec61850_adapter.py`

```python
from .base import ProtocolAdapter, ProtocolMessage, ProtocolType
from typing import Dict, Any, Optional
import iec61850  # libiec61850 Python 绑定

class IEC61850Adapter(ProtocolAdapter):
    """IEC 61850 协议适配器"""
    
    def __init__(self, adapter_id: str = "iec61850-adapter"):
        super().__init__(adapter_id)
        self.server = None
        self.client = None
        self.model = None
    
    def connect(self, config: Dict[str, Any]) -> bool:
        """建立 IEC 61850 连接"""
        try:
            if config.get("mode") == "server":
                self.server = iec61850.IedServer()
                self.server.start()
            else:
                self.client = iec61850.IedConnection()
                self.client.connect(config.get("host"), config.get("port", 102))
            
            self.is_connected = True
            return True
        except Exception as e:
            self.error_count += 1
            return False
    
    def disconnect(self) -> bool:
        """断开 IEC 61850 连接"""
        try:
            if self.server:
                self.server.stop()
            if self.client:
                self.client.close()
            self.is_connected = False
            return True
        except Exception as e:
            self.error_count += 1
            return False
    
    def send_message(self, message: ProtocolMessage) -> bool:
        """发送 IEC 61850 消息"""
        try:
            # 实现消息发送逻辑
            self.message_count += 1
            return True
        except Exception as e:
            self.error_count += 1
            return False
    
    def receive_message(self, timeout: float = 1.0) -> Optional[ProtocolMessage]:
        """接收 IEC 61850 消息"""
        try:
            # 实现消息接收逻辑
            return None
        except Exception as e:
            self.error_count += 1
            return None
    
    def parse_message(self, data: bytes) -> Dict[str, Any]:
        """解析 IEC 61850 消息"""
        # 实现消息解析逻辑
        return {}
    
    def encode_message(self, message: Dict[str, Any]) -> bytes:
        """编码 IEC 61850 消息"""
        # 实现消息编码逻辑
        return b""
    
    def validate_message(self, data: bytes) -> bool:
        """验证 IEC 61850 消息"""
        # 实现消息验证逻辑
        return True
```

### 2.2 Modbus 适配器

**文件**: `vpp-phase2-simulation/services/protocol_adapters/modbus_adapter.py`

```python
from .base import ProtocolAdapter, ProtocolMessage, ProtocolType
from typing import Dict, Any, Optional
from pymodbus.client import ModbusTcpClient, ModbusSerialClient
from pymodbus.server import StartAsyncTcpServer
import asyncio

class ModbusAdapter(ProtocolAdapter):
    """Modbus 协议适配器"""
    
    def __init__(self, adapter_id: str = "modbus-adapter"):
        super().__init__(adapter_id)
        self.client = None
        self.server = None
    
    def connect(self, config: Dict[str, Any]) -> bool:
        """建立 Modbus 连接"""
        try:
            if config.get("mode") == "tcp":
                self.client = ModbusTcpClient(
                    host=config.get("host", "localhost"),
                    port=config.get("port", 502)
                )
            else:
                self.client = ModbusSerialClient(
                    port=config.get("port", "/dev/ttyUSB0"),
                    baudrate=config.get("baudrate", 9600)
                )
            
            self.is_connected = self.client.connect()
            return self.is_connected
        except Exception as e:
            self.error_count += 1
            return False
    
    def disconnect(self) -> bool:
        """断开 Modbus 连接"""
        try:
            if self.client:
                self.client.close()
            self.is_connected = False
            return True
        except Exception as e:
            self.error_count += 1
            return False
    
    def send_message(self, message: ProtocolMessage) -> bool:
        """发送 Modbus 消息"""
        try:
            # 实现消息发送逻辑
            self.message_count += 1
            return True
        except Exception as e:
            self.error_count += 1
            return False
    
    def receive_message(self, timeout: float = 1.0) -> Optional[ProtocolMessage]:
        """接收 Modbus 消息"""
        try:
            # 实现消息接收逻辑
            return None
        except Exception as e:
            self.error_count += 1
            return None
    
    def parse_message(self, data: bytes) -> Dict[str, Any]:
        """解析 Modbus 消息"""
        # 实现消息解析逻辑
        return {}
    
    def encode_message(self, message: Dict[str, Any]) -> bytes:
        """编码 Modbus 消息"""
        # 实现消息编码逻辑
        return b""
    
    def validate_message(self, data: bytes) -> bool:
        """验证 Modbus 消息"""
        # 实现消息验证逻辑
        return True
```

### 2.3 DNP3 适配器

**文件**: `vpp-phase2-simulation/services/protocol_adapters/dnp3_adapter.py`

```python
from .base import ProtocolAdapter, ProtocolMessage, ProtocolType
from typing import Dict, Any, Optional
import opendnp3

class DNP3Adapter(ProtocolAdapter):
    """DNP3 协议适配器"""
    
    def __init__(self, adapter_id: str = "dnp3-adapter"):
        super().__init__(adapter_id)
        self.manager = None
        self.channel = None
        self.master = None
    
    def connect(self, config: Dict[str, Any]) -> bool:
        """建立 DNP3 连接"""
        try:
            # 实现 DNP3 连接逻辑
            self.is_connected = True
            return True
        except Exception as e:
            self.error_count += 1
            return False
    
    def disconnect(self) -> bool:
        """断开 DNP3 连接"""
        try:
            # 实现 DNP3 断开连接逻辑
            self.is_connected = False
            return True
        except Exception as e:
            self.error_count += 1
            return False
    
    def send_message(self, message: ProtocolMessage) -> bool:
        """发送 DNP3 消息"""
        try:
            # 实现消息发送逻辑
            self.message_count += 1
            return True
        except Exception as e:
            self.error_count += 1
            return False
    
    def receive_message(self, timeout: float = 1.0) -> Optional[ProtocolMessage]:
        """接收 DNP3 消息"""
        try:
            # 实现消息接收逻辑
            return None
        except Exception as e:
            self.error_count += 1
            return None
    
    def parse_message(self, data: bytes) -> Dict[str, Any]:
        """解析 DNP3 消息"""
        # 实现消息解析逻辑
        return {}
    
    def encode_message(self, message: Dict[str, Any]) -> bytes:
        """编码 DNP3 消息"""
        # 实现消息编码逻辑
        return b""
    
    def validate_message(self, data: bytes) -> bool:
        """验证 DNP3 消息"""
        # 实现消息验证逻辑
        return True
```

### 2.4 MQTT 适配器

**文件**: `vpp-phase2-simulation/services/protocol_adapters/mqtt_adapter.py`

```python
from .base import ProtocolAdapter, ProtocolMessage, ProtocolType
from typing import Dict, Any, Optional
import paho.mqtt.client as mqtt
import json

class MQTTAdapter(ProtocolAdapter):
    """MQTT 协议适配器"""
    
    def __init__(self, adapter_id: str = "mqtt-adapter"):
        super().__init__(adapter_id)
        self.client = mqtt.Client()
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        self.messages = []
    
    def connect(self, config: Dict[str, Any]) -> bool:
        """建立 MQTT 连接"""
        try:
            if config.get("use_tls"):
                self.client.tls_set(
                    ca_certs=config.get("ca_certs"),
                    certfile=config.get("certfile"),
                    keyfile=config.get("keyfile")
                )
            
            self.client.connect(
                config.get("host", "localhost"),
                config.get("port", 1883),
                config.get("keepalive", 60)
            )
            self.client.loop_start()
            self.is_connected = True
            return True
        except Exception as e:
            self.error_count += 1
            return False
    
    def disconnect(self) -> bool:
        """断开 MQTT 连接"""
        try:
            self.client.loop_stop()
            self.client.disconnect()
            self.is_connected = False
            return True
        except Exception as e:
            self.error_count += 1
            return False
    
    def send_message(self, message: ProtocolMessage) -> bool:
        """发送 MQTT 消息"""
        try:
            topic = f"vpp/{message.source}/{message.destination}"
            payload = json.dumps(message.data)
            self.client.publish(topic, payload)
            self.message_count += 1
            return True
        except Exception as e:
            self.error_count += 1
            return False
    
    def receive_message(self, timeout: float = 1.0) -> Optional[ProtocolMessage]:
        """接收 MQTT 消息"""
        try:
            if self.messages:
                return self.messages.pop(0)
            return None
        except Exception as e:
            self.error_count += 1
            return None
    
    def parse_message(self, data: bytes) -> Dict[str, Any]:
        """解析 MQTT 消息"""
        try:
            return json.loads(data.decode('utf-8'))
        except Exception as e:
            return {}
    
    def encode_message(self, message: Dict[str, Any]) -> bytes:
        """编码 MQTT 消息"""
        return json.dumps(message).encode('utf-8')
    
    def validate_message(self, data: bytes) -> bool:
        """验证 MQTT 消息"""
        try:
            json.loads(data.decode('utf-8'))
            return True
        except:
            return False
    
    def _on_connect(self, client, userdata, flags, rc):
        """MQTT 连接回调"""
        if rc == 0:
            client.subscribe("vpp/#")
    
    def _on_message(self, client, userdata, msg):
        """MQTT 消息回调"""
        try:
            data = self.parse_message(msg.payload)
            message = ProtocolMessage(
                protocol="mqtt",
                message_id=str(len(self.messages)),
                source="mqtt",
                destination="vpp",
                timestamp=0,
                data=data
            )
            self.messages.append(message)
        except Exception as e:
            self.error_count += 1
```

---

## 📊 Phase 3-5 概览

### Phase 3: 协议映射与转换 (2-3 天)
- 定义协议间映射规则
- 实现消息转换引擎
- 编写转换测试

### Phase 4: VCC 集成 (2-3 天)
- 更新 VCC 协调器
- 集成协议注册表
- 更新设备模拟器

### Phase 5: 测试与验证 (2-3 天)
- 单元测试
- 集成测试
- 性能测试
- 文档编写

---

## ✅ 验收标准

- [ ] 所有 4 个协议库成功编译和集成
- [ ] 统一的适配器接口实现完成
- [ ] 每个适配器都有完整的单元测试
- [ ] 协议间消息映射正常工作
- [ ] 集成测试全部通过
- [ ] 性能满足要求 (< 100ms 延迟)
- [ ] 文档完整 (API 文档、集成指南、示例代码)

---

**下一步**: 等待审批，然后开始 Phase 1 实施

