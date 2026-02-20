# VPP 流量可视化引擎 - 设计文档

## 概述

本设计文档描述了VPP流量可视化引擎的架构和实现方案。系统采用三层架构：后端采集层、中间转化层、前端渲染层，通过WebSocket实现实时通信。

### 核心目标

1. 实时采集OVS镜像端口的网络流量
2. 将流量转化为标准化的事件流
3. 通过WebSocket推送到前端
4. 在3D拓扑图中渲染粒子流动画
5. 提供交互和数据导出功能

### 架构原则

- 分层设计确保各层独立
- 异步处理确保高性能
- 事件驱动确保实时性
- 缓冲队列确保可靠性

## 系统架构

### 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                  VPP 流量可视化引擎                          │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              后端采集层 (Backend)                     │   │
│  ├──────────────────────────────────────────────────────┤   │
│  │                                                      │   │
│  │  ┌─────────────────┐  ┌──────────────────────────┐  │   │
│  │  │  OVS镜像端口    │  │  PCAP/JSON读取器         │  │   │
│  │  │  (Mirror Port)  │──│  (Traffic Collector)     │  │   │
│  │  └─────────────────┘  └──────────────────────────┘  │   │
│  │                              │                       │   │
│  │                              ▼                       │   │
│  │                    ┌──────────────────┐             │   │
│  │                    │  缓冲队列         │             │   │
│  │                    │  (Event Queue)   │             │   │
│  │                    └──────────────────┘             │   │
│  └──────────────────────────────────────────────────────┘   │
│                              │                               │
│  ┌──────────────────────────▼──────────────────────────────┐ │
│  │              中间转化层 (Transformation)                │ │
│  ├──────────────────────────────────────────────────────────┤ │
│  │                                                          │ │
│  │  ┌──────────────────┐  ┌──────────────────────────────┐ │ │
│  │  │  流量分类器      │  │  事件生成器                  │ │ │
│  │  │  (Classifier)    │──│  (Event Generator)           │ │ │
│  │  └──────────────────┘  └──────────────────────────────┘ │ │
│  │                              │                           │ │
│  │                              ▼                           │ │
│  │                    ┌──────────────────┐                 │ │
│  │                    │  WebSocket推送   │                 │ │
│  │                    │  (WS Broadcaster)│                 │ │
│  │                    └──────────────────┘                 │ │
│  └──────────────────────────────────────────────────────────┘ │
│                              │                               │
│  ┌──────────────────────────▼──────────────────────────────┐ │
│  │              前端渲染层 (Frontend)                       │ │
│  ├──────────────────────────────────────────────────────────┤ │
│  │                                                          │ │
│  │  ┌──────────────────┐  ┌──────────────────────────────┐ │ │
│  │  │  WebSocket客户端 │  │  3D场景管理器                │ │ │
│  │  │  (WS Client)     │──│  (Scene Manager)             │ │ │
│  │  └──────────────────┘  └──────────────────────────────┘ │ │
│  │                              │                           │ │
│  │                              ▼                           │ │
│  │  ┌──────────────────────────────────────────────────┐   │ │
│  │  │  粒子系统 (Particle System)                      │   │ │
│  │  │  - 粒子生成                                      │   │ │
│  │  │  - 粒子动画                                      │   │ │
│  │  │  - 粒子销毁                                      │   │ │
│  │  └──────────────────────────────────────────────────┘   │ │
│  │                              │                           │ │
│  │                              ▼                           │ │
│  │  ┌──────────────────────────────────────────────────┐   │ │
│  │  │  Three.js 3D渲染引擎                            │   │ │
│  │  │  - 拓扑图渲染                                    │   │ │
│  │  │  - 粒子流渲染                                    │   │ │
│  │  │  - 发光效果                                      │   │ │
│  │  └──────────────────────────────────────────────────┘   │ │
│  │                              │                           │ │
│  │                              ▼                           │ │
│  │                    ┌──────────────────┐                 │ │
│  │                    │  Canvas/WebGL    │                 │ │
│  │                    │  (Rendering)     │                 │ │
│  │                    └──────────────────┘                 │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## 后端采集层设计

### 1. 流量采集服务 (TrafficCollectorService)

```python
class TrafficCollectorService:
    """采集OVS镜像端口的网络流量"""
    
    def __init__(self, pcap_file: str = None, json_source: str = None):
        """初始化采集器
        
        Args:
            pcap_file: PCAP文件路径
            json_source: JSON数据源（文件或URL）
        """
        pass
    
    def start_collection(self):
        """启动流量采集"""
        pass
    
    def stop_collection(self):
        """停止流量采集"""
        pass
    
    def read_pcap(self) -> List[Dict]:
        """读取PCAP文件并解析"""
        pass
    
    def read_json(self) -> List[Dict]:
        """读取JSON数据源"""
        pass
    
    def parse_packet(self, packet: Any) -> Dict:
        """解析单个报文
        
        Returns:
            {
                "src_ip": "10.0.8.1",
                "dst_ip": "10.0.8.2",
                "protocol": "TCP",
                "packet_size": 1024,
                "timestamp": "2024-01-15T10:30:00Z"
            }
        """
        pass
```

### 2. 事件队列 (EventQueue)

```python
class EventQueue:
    """缓冲流量事件的队列"""
    
    def __init__(self, max_size: int = 10000):
        """初始化队列
        
        Args:
            max_size: 最大队列大小
        """
        pass
    
    def put(self, event: Dict) -> bool:
        """添加事件到队列
        
        Returns:
            True if successful, False if queue is full
        """
        pass
    
    def get(self) -> Dict:
        """从队列获取事件"""
        pass
    
    def size(self) -> int:
        """获取队列大小"""
        pass
    
    def clear(self):
        """清空队列"""
        pass
```

## 中间转化层设计

### 1. 流量分类器 (TrafficClassifier)

```python
class TrafficClassifier:
    """分类网络流量"""
    
    def classify(self, packet: Dict) -> str:
        """分类流量类型
        
        Args:
            packet: 报文信息
        
        Returns:
            "Control" 或 "Telemetry"
        """
        pass
    
    def is_control_traffic(self, src_ip: str, dst_ip: str, port: int) -> bool:
        """判断是否为控制流量"""
        pass
    
    def is_telemetry_traffic(self, src_ip: str, dst_ip: str, port: int) -> bool:
        """判断是否为遥测流量"""
        pass
```

### 2. 事件生成器 (EventGenerator)

```python
class EventGenerator:
    """生成标准化的可视化事件"""
    
    def generate_event(self, packet: Dict, traffic_type: str) -> Dict:
        """生成可视化事件
        
        Returns:
            {
                "from": "Master",
                "to": "Storage_01",
                "type": "Control",
                "intensity": 0.8,
                "packet_size": 1024,
                "timestamp": "2024-01-15T10:30:00Z"
            }
        """
        pass
    
    def calculate_intensity(self, packet_size: int, frequency: float) -> float:
        """计算流量强度 (0.0-1.0)"""
        pass
    
    def map_ip_to_component(self, ip: str) -> str:
        """将IP地址映射到VPP组件名称"""
        pass
```

### 3. WebSocket广播器 (WebSocketBroadcaster)

```python
class WebSocketBroadcaster:
    """通过WebSocket推送事件到前端"""
    
    def __init__(self):
        """初始化广播器"""
        pass
    
    def register_client(self, client_id: str, websocket):
        """注册WebSocket客户端"""
        pass
    
    def unregister_client(self, client_id: str):
        """注销WebSocket客户端"""
        pass
    
    def broadcast(self, event: Dict):
        """广播事件到所有连接的客户端"""
        pass
    
    def send_to_client(self, client_id: str, event: Dict):
        """发送事件到特定客户端"""
        pass
```

## 前端渲染层设计

### 1. 3D场景管理器 (SceneManager)

```javascript
class SceneManager {
    constructor(canvas) {
        // 初始化Three.js场景
        this.scene = new THREE.Scene();
        this.camera = new THREE.PerspectiveCamera(...);
        this.renderer = new THREE.WebGLRenderer({ canvas });
        
        // 设置暗色背景
        this.scene.background = new THREE.Color(0x0a0e27);
        
        // 初始化拓扑图
        this.initTopology();
    }
    
    initTopology() {
        // 创建VPP组件节点
        // 创建连接线
        // 设置相机位置
    }
    
    addComponent(name, position) {
        // 添加组件到场景
    }
    
    addConnection(from, to) {
        // 添加组件间的连接
    }
    
    render() {
        // 渲染场景
    }
}
```

### 2. 粒子系统 (ParticleSystem)

```javascript
class ParticleSystem {
    constructor(scene) {
        this.scene = scene;
        this.particles = [];
        this.maxParticles = 10000;
    }
    
    createParticle(from, to, type, size, intensity) {
        // 创建粒子
        // 设置起点和终点
        // 设置大小、颜色、透明度
        // 返回粒子对象
    }
    
    updateParticles(deltaTime) {
        // 更新所有粒子位置
        // 更新粒子动画
        // 删除已到达终点的粒子
    }
    
    applyGlowEffect(particle, intensity) {
        // 为控制指令粒子应用发光效果
    }
    
    setTransparency(particle, alpha) {
        // 设置粒子透明度
    }
    
    optimizePerformance() {
        // 当粒子过多时优化性能
        // 合并或删除旧粒子
    }
}
```

### 3. 交互管理器 (InteractionManager)

```javascript
class InteractionManager {
    constructor(scene, camera, renderer) {
        this.scene = scene;
        this.camera = camera;
        this.renderer = renderer;
        
        // 初始化鼠标控制
        this.controls = new THREE.OrbitControls(camera, renderer.domElement);
    }
    
    onComponentClick(component) {
        // 显示组件详细信息
    }
    
    onParticleHover(particle) {
        // 显示流量详情
    }
    
    onTimeRangeSelect(startTime, endTime) {
        // 回放指定时间范围的流量
    }
    
    pauseAnimation() {
        // 暂停粒子动画
    }
    
    resumeAnimation() {
        // 恢复粒子动画
    }
    
    setAnimationSpeed(speed) {
        // 调整粒子流动速度
    }
}
```

## 数据模型

### 1. 原始报文数据

```python
class RawPacket:
    """原始网络报文"""
    src_ip: str
    dst_ip: str
    src_port: int
    dst_port: int
    protocol: str
    packet_size: int
    timestamp: datetime
    payload: bytes
```

### 2. 可视化事件

```python
class VisualizationEvent:
    """可视化事件"""
    from_component: str      # 源组件名称
    to_component: str        # 目标组件名称
    traffic_type: str        # "Control" 或 "Telemetry"
    intensity: float         # 0.0-1.0
    packet_size: int         # 字节数
    timestamp: datetime
    
    def to_dict(self) -> Dict:
        """转换为字典格式用于JSON序列化"""
        pass
```

### 3. 组件信息

```python
class ComponentInfo:
    """VPP组件信息"""
    name: str
    ip_address: str
    position: Tuple[float, float, float]  # 3D坐标
    status: str  # "online" 或 "offline"
    color: str   # 组件颜色
```

## API 端点规范

### WebSocket 端点

```
WS /ws/traffic-visualization
```

#### 连接消息

```json
{
  "type": "connect",
  "client_id": "client_001"
}
```

#### 事件消息

```json
{
  "type": "traffic_event",
  "data": {
    "from": "Master",
    "to": "Storage_01",
    "type": "Control",
    "intensity": 0.8,
    "packet_size": 1024,
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

### REST API 端点

```
GET /api/visualization/components
Response: 200 OK
{
  "components": [
    {
      "name": "Master",
      "ip": "10.0.8.1",
      "status": "online"
    },
    ...
  ]
}
```

```
GET /api/visualization/statistics?start_time=...&end_time=...
Response: 200 OK
{
  "total_packets": 10000,
  "total_bytes": 5242880,
  "control_ratio": 0.3,
  "telemetry_ratio": 0.7,
  "traffic_by_component": {...}
}
```

```
POST /api/visualization/export/screenshot
Response: 200 OK
{
  "image_url": "/downloads/screenshot_001.png"
}
```

```
POST /api/visualization/export/video
Response: 200 OK
{
  "video_url": "/downloads/video_001.mp4"
}
```

## 性能优化策略

### 1. 粒子优化

- 使用粒子池（Object Pool）复用粒子对象
- 限制最大粒子数量为10000
- 使用LOD（Level of Detail）技术
- 合并粒子几何体以减少draw calls

### 2. 渲染优化

- 使用WebGL 2.0
- 启用硬件加速
- 使用着色器优化
- 实现视锥体剔除

### 3. 网络优化

- 使用消息压缩
- 批量发送事件
- 实现背压机制
- 使用二进制协议

### 4. 内存优化

- 定期清理过期事件
- 使用对象池
- 避免频繁的GC
- 监控内存使用

## 正确性属性

### 属性1：流量采集完整性
*对于任何OVS镜像端口导出的报文*，系统应该在100ms内采集并处理该报文。
**验证需求：1.1, 1.2, 1.3**

### 属性2：事件转化准确性
*对于任何采集的报文*，系统应该正确转化为标准化事件格式，包含所有必需字段。
**验证需求：2.1, 2.2, 2.3**

### 属性3：WebSocket推送及时性
*对于任何生成的事件*，系统应该在50ms内通过WebSocket推送到所有连接的客户端。
**验证需求：3.1, 3.2**

### 属性4：粒子渲染正确性
*对于任何可视化事件*，前端应该正确渲染粒子流，包括大小、颜色、透明度、发光效果。
**验证需求：4.1, 5.1, 5.2, 5.3, 6.1, 6.2, 6.3, 6.4, 6.5**

### 属性5：性能指标达成
*在高流量情况下*，系统应该满足所有性能指标：采集延迟<100ms、转化延迟<50ms、推送延迟<100ms、渲染帧率>=30fps。
**验证需求：8.1, 8.2, 8.3, 8.4, 8.5**

### 属性6：交互响应性
*对于任何用户交互*，系统应该在100ms内响应并更新场景。
**验证需求：9.1, 9.2, 9.3, 9.4, 9.5**

### 属性7：数据导出完整性
*对于任何导出请求*，系统应该生成完整的数据或媒体文件，包含时间戳和元数据。
**验证需求：10.1, 10.2, 10.3, 10.4**
