# VPP 实时数据交换系统 - 设计文档

## 概述

本设计文档描述了VPP虚拟电厂实时数据交换系统的架构和实现方案。系统采用微服务架构，通过REST API和后台任务服务实现VCC协调中心与电源侧、储能侧、需求侧模块之间的双向通信。

### 核心目标

1. 实现各侧模块与VCC之间的实时数据交换
2. 支持VCC对各侧的协调控制
3. 持久化所有数据交换记录
4. 提供实时监控仪表板

### 架构原则

- 微服务独立部署和扩展
- 异步通信确保系统解耦
- 数据持久化保证可靠性
- 实时更新支持监控需求

## 架构设计

### 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    VPP 实时数据交换系统                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ 电源侧模块   │  │ 储能侧模块   │  │ 需求侧模块   │       │
│  │(Power Gen)   │  │(Storage)     │  │(Demand)      │       │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘       │
│         │                 │                 │                │
│         └─────────────────┼─────────────────┘                │
│                           │                                  │
│                    ┌──────▼──────┐                           │
│                    │  VCC Master  │                          │
│                    │ (Coordinator)│                          │
│                    └──────┬───────┘                          │
│                           │                                  │
│         ┌─────────────────┼─────────────────┐               │
│         │                 │                 │               │
│    ┌────▼────┐      ┌────▼────┐      ┌────▼────┐          │
│    │ 数据库   │      │ 缓存层   │      │ 消息队列 │          │
│    │(Database)│      │(Redis)  │      │(Queue)  │          │
│    └─────────┘      └─────────┘      └─────────┘          │
│         │                                                   │
│    ┌────▼──────────────────────────────────────┐           │
│    │     实时监控仪表板 (Dashboard)             │           │
│    └───────────────────────────────────────────┘           │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### 通信流程

#### 1. 数据上报流程

```
Side Module (Power/Storage/Demand)
    │
    ├─ 收集本地数据
    │
    ├─ 构建数据包
    │
    └─► POST /api/vcc/report
            │
            ▼
        VCC Master
            │
            ├─ 验证数据
            │
            ├─ 存储到数据库
            │
            ├─ 更新缓存
            │
            └─► 返回 200 OK
```

#### 2. 协调决策流程

```
VCC Background Task (每10秒)
    │
    ├─ 收集所有侧的最新数据
    │
    ├─ 执行协调算法
    │
    ├─ 生成控制命令
    │
    └─► 发送命令到各侧
            │
            ▼
        Side Modules
            │
            ├─ 接收命令
            │
            ├─ 执行命令
            │
            └─► 报告执行结果
```

## 组件设计

### 1. VCC Master (vpp-master)

**职责**：
- 接收各侧数据上报
- 执行协调决策
- 发送控制命令
- 管理数据持久化

**核心模块**：

#### 1.1 数据接收服务 (DataReceptionService)

```python
class DataReceptionService:
    """处理各侧数据上报"""
    
    def receive_power_generation_data(self, data: PowerGenerationData) -> bool:
        """接收电源侧数据"""
        # 验证数据
        # 存储到数据库
        # 更新缓存
        # 返回成功/失败
        pass
    
    def receive_storage_data(self, data: StorageData) -> bool:
        """接收储能侧数据"""
        pass
    
    def receive_demand_data(self, data: DemandData) -> bool:
        """接收需求侧数据"""
        pass
```

#### 1.2 协调决策服务 (CoordinationService)

```python
class CoordinationService:
    """执行VCC协调决策"""
    
    def coordinate(self) -> CoordinationResult:
        """执行一次协调"""
        # 收集所有侧的最新数据
        # 执行协调算法
        # 生成控制命令
        # 发送命令到各侧
        # 记录协调结果
        pass
    
    def calculate_optimal_schedule(self, 
                                   power_data: PowerGenerationData,
                                   storage_data: StorageData,
                                   demand_data: DemandData) -> Schedule:
        """计算最优调度方案"""
        pass
```

#### 1.3 命令发送服务 (CommandService)

```python
class CommandService:
    """向各侧发送控制命令"""
    
    def send_power_command(self, command: PowerCommand) -> bool:
        """向电源侧发送命令"""
        pass
    
    def send_storage_command(self, command: StorageCommand) -> bool:
        """向储能侧发送命令"""
        pass
    
    def send_demand_command(self, command: DemandCommand) -> bool:
        """向需求侧发送命令"""
        pass
```

#### 1.4 后台任务服务 (BackgroundTaskService)

```python
class BackgroundTaskService:
    """管理后台任务"""
    
    def start_coordination_task(self):
        """启动协调任务（每10秒执行一次）"""
        pass
    
    def start_data_cleanup_task(self):
        """启动数据清理任务"""
        pass
```

### 2. 各侧模块 (Power/Storage/Demand)

**职责**：
- 收集本地数据
- 定期向VCC上报数据
- 接收并执行VCC命令
- 报告执行结果

**核心模块**：

#### 2.1 数据收集服务 (DataCollectionService)

```python
class DataCollectionService:
    """收集本地数据"""
    
    def collect_power_data(self) -> PowerGenerationData:
        """收集电源侧数据"""
        pass
    
    def collect_storage_data(self) -> StorageData:
        """收集储能侧数据"""
        pass
    
    def collect_demand_data(self) -> DemandData:
        """收集需求侧数据"""
        pass
```

#### 2.2 数据上报服务 (DataReportingService)

```python
class DataReportingService:
    """定期向VCC上报数据"""
    
    def start_reporting(self, interval: int = 5):
        """启动数据上报（每5秒）"""
        pass
    
    def report_data(self, data: Any) -> bool:
        """上报数据，支持重试"""
        pass
```

#### 2.3 命令执行服务 (CommandExecutionService)

```python
class CommandExecutionService:
    """接收并执行VCC命令"""
    
    def execute_power_command(self, command: PowerCommand) -> CommandResult:
        """执行电源侧命令"""
        pass
    
    def execute_storage_command(self, command: StorageCommand) -> CommandResult:
        """执行储能侧命令"""
        pass
    
    def execute_demand_command(self, command: DemandCommand) -> CommandResult:
        """执行需求侧命令"""
        pass
```

## 数据模型

### 1. 电源侧数据模型

```python
class PowerGenerationData:
    """电源侧数据"""
    timestamp: datetime
    current_power: float  # 当前发电功率 (kW)
    solar_power: float    # 太阳能功率 (kW)
    wind_power: float     # 风能功率 (kW)
    efficiency: float     # 发电效率 (%)
    device_status: str    # 设备状态 (running/idle/error)
    module_id: str        # 模块ID
```

### 2. 储能侧数据模型

```python
class StorageData:
    """储能侧数据"""
    timestamp: datetime
    soc: float            # 充电状态 (%)
    soh: float            # 健康状态 (%)
    current_power: float  # 当前功率 (kW)
    charge_status: str    # 充放电状态 (charging/discharging/idle)
    temperature: float    # 温度 (°C)
    module_id: str        # 模块ID
```

### 3. 需求侧数据模型

```python
class DemandData:
    """需求侧数据"""
    timestamp: datetime
    current_load: float   # 当前负荷 (kW)
    forecast_load: float  # 预测负荷 (kW)
    adjustable_range: tuple  # 可调节范围 (min, max)
    dr_status: str        # 需求响应状态 (active/inactive)
    module_id: str        # 模块ID
```

### 4. 协调结果数据模型

```python
class CoordinationResult:
    """协调结果"""
    timestamp: datetime
    power_schedule: PowerCommand
    storage_schedule: StorageCommand
    demand_schedule: DemandCommand
    optimization_score: float  # 优化评分 (0-100)
    status: str  # 成功/失败
```

### 5. 命令数据模型

```python
class PowerCommand:
    """电源侧命令"""
    command_id: str
    target_power: float  # 目标功率 (kW)
    duration: int        # 持续时间 (秒)
    priority: int        # 优先级

class StorageCommand:
    """储能侧命令"""
    command_id: str
    action: str          # 充电/放电/待机
    target_power: float  # 目标功率 (kW)
    duration: int        # 持续时间 (秒)

class DemandCommand:
    """需求侧命令"""
    command_id: str
    action: str          # 增加/减少/维持
    target_load: float   # 目标负荷 (kW)
    duration: int        # 持续时间 (秒)
```

## API 端点规范

### VCC Master API

#### 1. 数据上报端点

```
POST /api/vcc/report/power
Content-Type: application/json

{
  "timestamp": "2024-01-15T10:30:00Z",
  "current_power": 150.5,
  "solar_power": 100.0,
  "wind_power": 50.5,
  "efficiency": 95.5,
  "device_status": "running"
}

Response: 200 OK
{
  "status": "success",
  "message": "Data received and stored"
}
```

```
POST /api/vcc/report/storage
Content-Type: application/json

{
  "timestamp": "2024-01-15T10:30:00Z",
  "soc": 75.5,
  "soh": 98.0,
  "current_power": 50.0,
  "charge_status": "charging",
  "temperature": 25.5
}

Response: 200 OK
```

```
POST /api/vcc/report/demand
Content-Type: application/json

{
  "timestamp": "2024-01-15T10:30:00Z",
  "current_load": 200.0,
  "forecast_load": 210.0,
  "adjustable_range": [180.0, 220.0],
  "dr_status": "active"
}

Response: 200 OK
```

#### 2. 命令接收端点

```
POST /api/side/command/power
Content-Type: application/json

{
  "command_id": "cmd_001",
  "target_power": 160.0,
  "duration": 300,
  "priority": 1
}

Response: 200 OK
{
  "status": "accepted",
  "execution_time": "2024-01-15T10:30:05Z"
}
```

#### 3. 数据查询端点

```
GET /api/vcc/data/power?start_time=2024-01-15T10:00:00Z&end_time=2024-01-15T11:00:00Z

Response: 200 OK
{
  "data": [
    {
      "timestamp": "2024-01-15T10:30:00Z",
      "current_power": 150.5,
      ...
    }
  ],
  "count": 12
}
```

#### 4. 协调结果查询端点

```
GET /api/vcc/coordination/results?limit=10

Response: 200 OK
{
  "results": [
    {
      "timestamp": "2024-01-15T10:30:00Z",
      "optimization_score": 92.5,
      "status": "success"
    }
  ]
}
```

## 数据库设计

### 表结构

#### 1. power_generation_data 表

```sql
CREATE TABLE power_generation_data (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  timestamp DATETIME NOT NULL,
  current_power FLOAT NOT NULL,
  solar_power FLOAT NOT NULL,
  wind_power FLOAT NOT NULL,
  efficiency FLOAT NOT NULL,
  device_status VARCHAR(50) NOT NULL,
  module_id VARCHAR(100) NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_timestamp (timestamp),
  INDEX idx_module_id (module_id)
);
```

#### 2. storage_data 表

```sql
CREATE TABLE storage_data (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  timestamp DATETIME NOT NULL,
  soc FLOAT NOT NULL,
  soh FLOAT NOT NULL,
  current_power FLOAT NOT NULL,
  charge_status VARCHAR(50) NOT NULL,
  temperature FLOAT NOT NULL,
  module_id VARCHAR(100) NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_timestamp (timestamp),
  INDEX idx_module_id (module_id)
);
```

#### 3. demand_data 表

```sql
CREATE TABLE demand_data (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  timestamp DATETIME NOT NULL,
  current_load FLOAT NOT NULL,
  forecast_load FLOAT NOT NULL,
  adjustable_range_min FLOAT NOT NULL,
  adjustable_range_max FLOAT NOT NULL,
  dr_status VARCHAR(50) NOT NULL,
  module_id VARCHAR(100) NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_timestamp (timestamp),
  INDEX idx_module_id (module_id)
);
```

#### 4. coordination_results 表

```sql
CREATE TABLE coordination_results (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  timestamp DATETIME NOT NULL,
  power_command JSON NOT NULL,
  storage_command JSON NOT NULL,
  demand_command JSON NOT NULL,
  optimization_score FLOAT NOT NULL,
  status VARCHAR(50) NOT NULL,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_timestamp (timestamp)
);
```

#### 5. commands 表

```sql
CREATE TABLE commands (
  id BIGINT PRIMARY KEY AUTO_INCREMENT,
  command_id VARCHAR(100) NOT NULL UNIQUE,
  command_type VARCHAR(50) NOT NULL,
  target_module VARCHAR(100) NOT NULL,
  command_data JSON NOT NULL,
  status VARCHAR(50) NOT NULL,
  result JSON,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  executed_at DATETIME,
  INDEX idx_command_id (command_id),
  INDEX idx_status (status)
);
```

## 实时监控仪表板设计

### 仪表板功能

1. **实时数据展示**
   - 电源侧：当前功率、太阳能/风能功率、效率、设备状态
   - 储能侧：SOC、SOH、当前功率、充放电状态、温度
   - 需求侧：当前负荷、预测负荷、需求响应状态

2. **协调决策展示**
   - 最新协调结果
   - 优化评分
   - 发送的命令

3. **历史数据查询**
   - 时间范围选择
   - 数据导出（JSON/CSV）

4. **报告生成**
   - PDF报告导出
   - 包含性能指标和优化结果

### 仪表板架构

```
Frontend (HTML/CSS/JavaScript)
    │
    ├─ 实时数据展示组件
    ├─ 图表组件 (Chart.js)
    ├─ 历史数据查询组件
    └─ 报告生成组件
    │
    ▼
Backend API
    │
    ├─ /api/dashboard/realtime
    ├─ /api/dashboard/history
    └─ /api/dashboard/report
    │
    ▼
Database & Cache
```

## 错误处理

### 1. 数据上报错误

- **验证失败**：返回 400 Bad Request，包含错误详情
- **存储失败**：返回 500 Internal Server Error，自动重试
- **网络超时**：客户端自动重试（最多3次）

### 2. 协调决策错误

- **数据不完整**：跳过本次协调，记录警告
- **算法异常**：使用上次的结果，记录错误
- **命令发送失败**：重试发送，记录失败

### 3. 命令执行错误

- **命令格式错误**：返回 400 Bad Request
- **执行失败**：返回执行结果和失败原因
- **超时**：返回超时错误，客户端可重试

## 测试策略

### 单元测试

- 数据模型验证
- 协调算法逻辑
- 命令生成逻辑
- 错误处理逻辑

### 集成测试

- 数据上报流程
- 协调决策流程
- 命令执行流程
- 数据持久化流程

### 性能测试

- 数据上报延迟 < 1秒
- 协调决策 < 2秒
- 仪表板刷新 < 500ms

### 属性测试

待在下一步中定义...


## 正确性属性

属性是系统应该满足的特征或行为，在所有有效执行中都应该成立。属性充当人类可读规范和机器可验证正确性保证之间的桥梁。

### 属性1：定期数据上报
*对于任何启动的侧模块*，模块应该在启动后的5秒内发送第一条数据，然后每5秒发送一次数据。
**验证需求：1.1, 2.1, 3.1**

### 属性2：电源侧数据完整性
*对于任何电源侧数据上报*，数据应该包含所有必需字段：当前发电功率、太阳能功率、风能功率、发电效率、设备状态。
**验证需求：1.2**

### 属性3：储能侧数据完整性
*对于任何储能侧数据上报*，数据应该包含所有必需字段：SOC、SOH、当前功率、充放电状态、温度。
**验证需求：2.2**

### 属性4：需求侧数据完整性
*对于任何需求侧数据上报*，数据应该包含所有必需字段：当前负荷、预测负荷、可调节范围、需求响应状态。
**验证需求：3.2**

### 属性5：数据持久化往返
*对于任何上报到VCC的数据*，发送数据后查询数据库应该能够检索到相同的数据。
**验证需求：1.3, 2.3, 3.3, 6.1**

### 属性6：重试机制
*对于任何失败的数据上报*，模块应该自动重试最多3次，然后记录错误日志但继续运行。
**验证需求：1.4, 1.5, 2.4, 2.5, 3.4, 3.5**

### 属性7：协调任务启动
*对于启动的VCC*，协调后台任务应该在启动后的10秒内执行第一次协调。
**验证需求：4.1**

### 属性8：协调数据收集
*对于任何协调执行*，VCC应该收集所有侧（电源、储能、需求）的最新数据。
**验证需求：4.2**

### 属性9：协调结果有效性
*对于任何协调执行*，协调结果应该包含有效的发电、储能、负荷调度方案。
**验证需求：4.3**

### 属性10：命令发送
*对于任何协调决策*，VCC应该向所有相关侧发送控制命令。
**验证需求：4.4, 5.1, 5.2, 5.3**

### 属性11：协调结果持久化
*对于任何完成的协调*，协调结果应该被存储到数据库。
**验证需求：4.5**

### 属性12：命令执行报告
*对于任何接收到的命令*，侧模块应该执行命令并报告执行结果。
**验证需求：5.4, 5.5**

### 属性13：历史数据查询
*对于任何时间范围查询*，系统应该返回该时间范围内的所有数据。
**验证需求：6.2**

### 属性14：数据导出格式
*对于任何数据导出请求*，导出的数据应该是有效的JSON或CSV格式。
**验证需求：6.4**

### 属性15：仪表板实时更新
*对于任何数据更新*，仪表板应该在500ms内刷新显示。
**验证需求：7.2**

### 属性16：PDF报告生成
*对于任何报告生成请求*，系统应该生成有效的PDF文件。
**验证需求：7.4**

