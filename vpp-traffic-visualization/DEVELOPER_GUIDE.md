# VPP 流量可视化引擎 - 开发者指南

## 目录

1. [项目结构](#项目结构)
2. [开发环境设置](#开发环境设置)
3. [代码架构](#代码架构)
4. [扩展指南](#扩展指南)
5. [性能优化指南](#性能优化指南)
6. [测试指南](#测试指南)
7. [贡献指南](#贡献指南)

---

## 项目结构

```
vpp-traffic-visualization/
├── backend/                          # 后端代码
│   ├── app.py                       # Flask应用入口
│   ├── requirements.txt              # Python依赖
│   ├── models/                       # 数据模型
│   │   ├── raw_packet.py            # 原始数据包模型
│   │   ├── visualization_event.py   # 可视化事件模型
│   │   └── component_info.py        # 组件信息模型
│   ├── services/                     # 业务逻辑服务
│   │   ├── traffic_collector.py     # 流量采集服务
│   │   ├── event_queue.py           # 事件队列
│   │   ├── traffic_classifier.py    # 流量分类器
│   │   ├── event_generator.py       # 事件生成器
│   │   └── websocket_broadcaster.py # WebSocket广播器
│   ├── routes/                       # API路由
│   │   ├── rest_api_routes.py       # REST API路由
│   │   └── websocket_routes.py      # WebSocket路由
│   └── tests/                        # 测试代码
│       ├── test_models.py           # 模型测试
│       ├── test_traffic_collector.py # 采集服务测试
│       ├── test_event_queue.py      # 队列测试
│       ├── test_traffic_classifier.py # 分类器测试
│       ├── test_event_generator.py  # 事件生成器测试
│       ├── test_websocket_broadcaster.py # 广播器测试
│       ├── test_rest_api.py         # REST API测试
│       ├── test_websocket_routes.py # WebSocket路由测试
│       ├── test_integration_simple.py # 集成测试
│       └── test_performance.py      # 性能测试
├── frontend/                         # 前端代码
│   ├── index.html                   # 主HTML文件
│   ├── css/                          # 样式文件
│   │   └── style.css                # 主样式表
│   └── js/                           # JavaScript文件
│       ├── main.js                  # 主入口
│       ├── scene-manager.js         # 场景管理器
│       ├── camera-controller.js     # 相机控制器
│       └── particle-system.js       # 粒子系统
├── docker-compose.yml               # Docker Compose配置
├── Dockerfile                        # Docker镜像配置
├── nginx.conf                        # Nginx配置
├── deploy.sh                         # 部署脚本
├── verify-docker.sh                 # 验证脚本
└── README.md                         # 项目说明

```

---

## 开发环境设置

### 前置要求

- Python 3.8+
- Node.js 14+（可选，用于前端开发）
- Git
- Docker（可选）

### 本地开发设置

#### 1. 克隆项目

```bash
git clone <repository-url>
cd vpp-traffic-visualization
```

#### 2. 设置Python环境

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
# macOS/Linux
source venv/bin/activate
# Windows
venv\Scripts\activate

# 安装依赖
cd backend
pip install -r requirements.txt
```

#### 3. 运行后端

```bash
# 在backend目录中
python app.py

# 或使用Flask开发服务器
export FLASK_APP=app.py
export FLASK_ENV=development
flask run
```

#### 4. 运行前端

```bash
# 在frontend目录中
# 使用简单的HTTP服务器
python3 -m http.server 8080

# 或使用Node.js http-server
npx http-server -p 8080
```

#### 5. 访问应用

打开浏览器访问 `http://localhost:8080`

### 使用Docker开发

```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

---

## 代码架构

### 后端架构

#### 数据流

```
数据源 (PCAP/JSON)
    ↓
TrafficCollectorService (采集)
    ↓
RawPacket (原始数据包)
    ↓
EventQueue (事件队列)
    ↓
TrafficClassifier (分类)
    ↓
EventGenerator (生成事件)
    ↓
VisualizationEvent (可视化事件)
    ↓
WebSocketBroadcaster (广播)
    ↓
前端客户端
```

#### 核心类

##### 1. TrafficCollectorService

```python
class TrafficCollectorService:
    """流量采集服务"""
    
    def __init__(self):
        """初始化采集器"""
        pass
    
    def read_pcap_file(self, file_path: str) -> List[RawPacket]:
        """从PCAP文件读取数据包"""
        pass
    
    def read_json_source(self, data: List[Dict]) -> List[RawPacket]:
        """从JSON数据源读取数据包"""
        pass
    
    def parse_packet(self, packet_data: Dict) -> RawPacket:
        """解析单个数据包"""
        pass
```

##### 2. TrafficClassifier

```python
class TrafficClassifier:
    """流量分类器"""
    
    def classify(self, src_ip: str, dst_ip: str, src_port: int, 
                 dst_port: int, protocol: str) -> Literal['Control', 'Telemetry']:
        """分类流量类型"""
        pass
    
    def is_control_traffic(self, src_ip: str, dst_ip: str, 
                          src_port: int, dst_port: int, protocol: str) -> bool:
        """检查是否为控制流量"""
        pass
    
    def is_telemetry_traffic(self, src_ip: str, dst_ip: str, 
                            src_port: int, dst_port: int, protocol: str) -> bool:
        """检查是否为遥测流量"""
        pass
```

##### 3. EventGenerator

```python
class EventGenerator:
    """事件生成器"""
    
    def generate_event(self, packet: RawPacket) -> Optional[VisualizationEvent]:
        """从数据包生成可视化事件"""
        pass
    
    def calculate_intensity(self, packet_size: int, flow_key: tuple, 
                           timestamp: datetime) -> float:
        """计算流量强度"""
        pass
    
    def map_ip_to_component(self, ip: str) -> str:
        """将IP映射到组件名称"""
        pass
```

##### 4. WebSocketBroadcaster

```python
class WebSocketBroadcaster:
    """WebSocket广播器"""
    
    def register_client(self, client_id: str, client):
        """注册客户端"""
        pass
    
    def unregister_client(self, client_id: str):
        """注销客户端"""
        pass
    
    async def broadcast(self, event: Dict):
        """广播事件到所有客户端"""
        pass
```

### 前端架构

#### 核心类

##### 1. SceneManager

```javascript
class SceneManager {
    constructor(canvas) {
        // 初始化Three.js场景
        this.scene = new THREE.Scene();
        this.camera = new THREE.PerspectiveCamera(...);
        this.renderer = new THREE.WebGLRenderer({ canvas });
    }
    
    addComponent(name, position) {
        // 添加组件节点
    }
    
    addConnection(from, to) {
        // 添加组件间连接
    }
    
    render() {
        // 渲染场景
    }
}
```

##### 2. ParticleSystem

```javascript
class ParticleSystem {
    constructor(scene) {
        this.particles = [];
        this.particlePool = [];
    }
    
    createParticle(from, to, type, intensity) {
        // 创建粒子
    }
    
    updateParticles(deltaTime) {
        // 更新粒子位置和状态
    }
    
    render() {
        // 渲染粒子
    }
}
```

##### 3. CameraController

```javascript
class CameraController {
    constructor(camera, canvas) {
        this.camera = camera;
        this.canvas = canvas;
    }
    
    handleMouseMove(event) {
        // 处理鼠标移动
    }
    
    handleMouseWheel(event) {
        // 处理鼠标滚轮
    }
    
    reset() {
        // 重置相机
    }
}
```

---

## 扩展指南

### 添加新的数据源

#### 步骤1：创建数据源适配器

```python
# backend/services/data_sources/custom_source.py

class CustomDataSource:
    """自定义数据源"""
    
    def __init__(self, config: Dict):
        self.config = config
    
    def connect(self):
        """连接到数据源"""
        pass
    
    def read_packets(self) -> List[Dict]:
        """读取数据包"""
        pass
    
    def disconnect(self):
        """断开连接"""
        pass
```

#### 步骤2：集成到TrafficCollectorService

```python
# backend/services/traffic_collector.py

class TrafficCollectorService:
    def __init__(self, data_source=None):
        self.data_source = data_source
    
    def collect_from_custom_source(self, config: Dict):
        """从自定义数据源采集"""
        source = CustomDataSource(config)
        source.connect()
        packets = source.read_packets()
        source.disconnect()
        return [self.parse_packet(p) for p in packets]
```

### 添加新的流量分类规则

#### 步骤1：扩展TrafficClassifier

```python
# backend/services/traffic_classifier.py

class TrafficClassifier:
    def __init__(self):
        self.custom_rules = []
    
    def add_custom_rule(self, rule_func):
        """添加自定义分类规则"""
        self.custom_rules.append(rule_func)
    
    def classify(self, src_ip: str, dst_ip: str, src_port: int, 
                 dst_port: int, protocol: str) -> Literal['Control', 'Telemetry']:
        # 先检查自定义规则
        for rule in self.custom_rules:
            result = rule(src_ip, dst_ip, src_port, dst_port, protocol)
            if result:
                return result
        
        # 再检查默认规则
        if self.is_control_traffic(...):
            return 'Control'
        return 'Telemetry'
```

#### 步骤2：使用自定义规则

```python
# 定义自定义规则
def my_custom_rule(src_ip, dst_ip, src_port, dst_port, protocol):
    if src_port == 9999:
        return 'Control'
    return None

# 添加规则
classifier = TrafficClassifier()
classifier.add_custom_rule(my_custom_rule)
```

### 添加新的可视化效果

#### 步骤1：创建自定义粒子类

```javascript
// frontend/js/custom-particles.js

class CustomParticle extends Particle {
    constructor(from, to, type, intensity) {
        super(from, to, type, intensity);
        this.customProperty = 0;
    }
    
    update(deltaTime) {
        super.update(deltaTime);
        // 自定义更新逻辑
        this.customProperty += deltaTime;
    }
    
    render(renderer) {
        // 自定义渲染逻辑
        super.render(renderer);
    }
}
```

#### 步骤2：集成到ParticleSystem

```javascript
// frontend/js/particle-system.js

class ParticleSystem {
    createParticle(from, to, type, intensity) {
        if (type === 'custom') {
            return new CustomParticle(from, to, type, intensity);
        }
        return new Particle(from, to, type, intensity);
    }
}
```

### 添加新的API端点

#### 步骤1：创建路由处理器

```python
# backend/routes/custom_routes.py

class CustomRoutes:
    def __init__(self, app):
        self.app = app
        self._register_routes()
    
    def _register_routes(self):
        @self.app.route('/api/custom/endpoint', methods=['GET'])
        def custom_endpoint():
            return {
                'success': True,
                'data': {...}
            }
```

#### 步骤2：注册到Flask应用

```python
# backend/app.py

from routes.custom_routes import CustomRoutes

app = Flask(__name__)
custom_routes = CustomRoutes(app)
```

---

## 性能优化指南

### 后端优化

#### 1. 事件队列优化

```python
# 调整队列大小
queue = EventQueue(max_size=50000)  # 增加队列大小

# 使用优先级队列
from queue import PriorityQueue
priority_queue = PriorityQueue()
```

#### 2. 批量处理

```python
# 批量生成事件
def batch_generate_events(packets: List[RawPacket], batch_size=100):
    for i in range(0, len(packets), batch_size):
        batch = packets[i:i+batch_size]
        events = [generator.generate_event(p) for p in batch]
        yield events
```

#### 3. 缓存优化

```python
# 使用缓存减少重复计算
from functools import lru_cache

@lru_cache(maxsize=1000)
def map_ip_to_component(ip: str) -> str:
    return VPP_COMPONENTS.get(ip, 'Unknown')
```

#### 4. 异步处理

```python
# 使用异步处理提高吞吐量
import asyncio

async def process_packets_async(packets: List[RawPacket]):
    tasks = [process_packet_async(p) for p in packets]
    return await asyncio.gather(*tasks)
```

### 前端优化

#### 1. 粒子池优化

```javascript
// 预分配粒子池
class ParticleSystem {
    constructor(scene, poolSize = 10000) {
        this.particlePool = [];
        for (let i = 0; i < poolSize; i++) {
            this.particlePool.push(new Particle());
        }
    }
    
    getParticle() {
        return this.particlePool.pop() || new Particle();
    }
    
    releaseParticle(particle) {
        particle.reset();
        this.particlePool.push(particle);
    }
}
```

#### 2. 渲染优化

```javascript
// 使用LOD（细节层次）技术
class SceneManager {
    updateLOD(cameraDistance) {
        if (cameraDistance > 100) {
            // 降低粒子数量
            this.particleSystem.setMaxParticles(5000);
        } else {
            // 增加粒子数量
            this.particleSystem.setMaxParticles(10000);
        }
    }
}
```

#### 3. 网络优化

```javascript
// 启用消息压缩
const socket = io('http://localhost:5000', {
    transportOptions: {
        polling: {
            extraHeaders: {
                'Accept-Encoding': 'gzip, deflate'
            }
        }
    }
});

// 批量接收事件
let eventBatch = [];
socket.on('traffic_event', (event) => {
    eventBatch.push(event);
    if (eventBatch.length >= 100) {
        processEventBatch(eventBatch);
        eventBatch = [];
    }
});
```

---

## 测试指南

### 运行测试

#### 运行所有测试

```bash
cd backend
python -m pytest tests/ -v
```

#### 运行特定测试

```bash
# 运行单个测试文件
python -m pytest tests/test_traffic_classifier.py -v

# 运行特定测试类
python -m pytest tests/test_traffic_classifier.py::TestTrafficClassifier -v

# 运行特定测试方法
python -m pytest tests/test_traffic_classifier.py::TestTrafficClassifier::test_classify -v
```

#### 运行性能测试

```bash
python -m pytest tests/test_performance.py -v
```

#### 生成覆盖率报告

```bash
python -m pytest tests/ --cov=backend --cov-report=html
```

### 编写测试

#### 单元测试示例

```python
# backend/tests/test_custom_service.py

import pytest
from services.custom_service import CustomService

class TestCustomService:
    def setup_method(self):
        """测试前准备"""
        self.service = CustomService()
    
    def test_custom_method(self):
        """测试自定义方法"""
        result = self.service.custom_method()
        assert result is not None
        assert result['success'] is True
    
    def test_custom_method_with_error(self):
        """测试错误处理"""
        with pytest.raises(ValueError):
            self.service.custom_method_with_error()
```

#### 集成测试示例

```python
# backend/tests/test_custom_integration.py

class TestCustomIntegration:
    def setup_method(self):
        """测试前准备"""
        self.collector = TrafficCollectorService()
        self.classifier = TrafficClassifier()
        self.generator = EventGenerator()
    
    def test_complete_flow(self):
        """测试完整流程"""
        # 采集
        packets = self.collector.read_json_source([...])
        
        # 分类
        for packet in packets:
            traffic_type = self.classifier.classify(...)
        
        # 生成事件
        for packet in packets:
            event = self.generator.generate_event(packet)
            assert event is not None
```

---

## 贡献指南

### 代码风格

#### Python代码风格

遵循PEP 8标准：

```python
# 好的例子
def calculate_intensity(packet_size: int, flow_key: tuple) -> float:
    """计算流量强度"""
    return min(packet_size / 1024.0, 1.0)

# 不好的例子
def calc_int(ps,fk):
    return min(ps/1024.0,1.0)
```

#### JavaScript代码风格

遵循Google JavaScript风格指南：

```javascript
// 好的例子
class ParticleSystem {
    constructor(scene) {
        this.scene = scene;
        this.particles = [];
    }
    
    createParticle(from, to) {
        const particle = new Particle(from, to);
        this.particles.push(particle);
        return particle;
    }
}

// 不好的例子
class ParticleSystem{
constructor(s){this.s=s;this.p=[]}
createParticle(f,t){let p=new Particle(f,t);this.p.push(p);return p}}
```

### 提交代码

#### 1. 创建分支

```bash
git checkout -b feature/your-feature-name
```

#### 2. 提交更改

```bash
git add .
git commit -m "feat: add your feature description"
```

#### 3. 推送分支

```bash
git push origin feature/your-feature-name
```

#### 4. 创建Pull Request

在GitHub上创建Pull Request，描述您的更改。

### 提交消息格式

遵循Conventional Commits格式：

```
<type>(<scope>): <subject>

<body>

<footer>
```

类型：
- `feat`: 新功能
- `fix`: 修复bug
- `docs`: 文档更新
- `style`: 代码风格
- `refactor`: 代码重构
- `perf`: 性能优化
- `test`: 测试

示例：

```
feat(traffic-classifier): add custom classification rules

- Add support for custom classification rules
- Add rule priority system
- Add rule validation

Closes #123
```

---

## 常见开发问题

### Q1: 如何添加新的组件？

**A**: 编辑 `backend/services/traffic_classifier.py` 中的 `VPP_COMPONENTS` 字典：

```python
VPP_COMPONENTS = {
    '10.0.8.1': 'Master',
    '10.0.8.2': 'Power_01',
    '10.0.8.3': 'Storage_01',
    '10.0.8.4': 'Demand_01',
    '10.0.8.5': 'NewComponent',  # 添加新组件
}
```

### Q2: 如何修改粒子颜色？

**A**: 编辑 `frontend/js/particle-system.js` 中的颜色定义：

```javascript
const COLORS = {
    control: 0xFF6B6B,      // 红色
    telemetry: 0x4ECDC4,    // 青色
    custom: 0xFFD93D        // 黄色
};
```

### Q3: 如何增加WebSocket消息频率？

**A**: 编辑 `backend/routes/websocket_routes.py` 中的广播间隔：

```python
# 减少广播间隔（毫秒）
BROADCAST_INTERVAL = 50  # 从100ms改为50ms
```

### Q4: 如何调试WebSocket连接？

**A**: 在浏览器控制台中启用调试：

```javascript
// 启用Socket.IO调试
localStorage.debug = 'socket.io-client:*';

// 或在代码中
const socket = io('http://localhost:5000', {
    reconnection: true,
    reconnectionDelay: 1000,
    reconnectionDelayMax: 5000,
    reconnectionAttempts: 5
});

socket.on('connect', () => console.log('Connected'));
socket.on('disconnect', () => console.log('Disconnected'));
socket.on('error', (error) => console.error('Error:', error));
```

---

## 参考资源

- [Flask文档](https://flask.palletsprojects.com/)
- [Flask-SocketIO文档](https://flask-socketio.readthedocs.io/)
- [Three.js文档](https://threejs.org/docs/)
- [Python PEP 8](https://www.python.org/dev/peps/pep-0008/)
- [Google JavaScript风格指南](https://google.github.io/styleguide/jsguide.html)

---

## 许可证

本项目采用MIT许可证。详见LICENSE文件。

