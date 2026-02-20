# VPP 流量可视化引擎 - API 文档

## 概述

本文档详细说明了VPP流量可视化引擎的所有API端点和WebSocket消息格式。系统采用REST API和WebSocket实时通信相结合的架构。

## 目录

1. [REST API 端点](#rest-api-端点)
2. [WebSocket 消息](#websocket-消息)
3. [数据模型](#数据模型)
4. [错误处理](#错误处理)
5. [示例](#示例)

---

## REST API 端点

### 基础信息

- **基础URL**: `http://localhost:5000`
- **内容类型**: `application/json`
- **认证**: 无（当前版本）

### 1. 获取组件信息

#### 请求

```
GET /api/visualization/components
```

#### 描述

获取所有VPP组件的信息，包括组件名称、IP地址、状态等。

#### 响应

**状态码**: 200 OK

```json
{
  "success": true,
  "data": {
    "components": [
      {
        "name": "Master",
        "ip": "10.0.8.1",
        "status": "active",
        "type": "control",
        "last_seen": "2024-02-20T10:30:45.123Z"
      },
      {
        "name": "Power_01",
        "ip": "10.0.8.2",
        "status": "active",
        "type": "power_generation",
        "last_seen": "2024-02-20T10:30:44.987Z"
      },
      {
        "name": "Storage_01",
        "ip": "10.0.8.3",
        "status": "active",
        "type": "storage",
        "last_seen": "2024-02-20T10:30:45.001Z"
      },
      {
        "name": "Demand_01",
        "ip": "10.0.8.4",
        "status": "active",
        "type": "demand",
        "last_seen": "2024-02-20T10:30:44.876Z"
      }
    ],
    "total_components": 4,
    "active_components": 4
  },
  "timestamp": "2024-02-20T10:30:45.234Z"
}
```

#### 错误响应

```json
{
  "success": false,
  "error": "Failed to retrieve components",
  "timestamp": "2024-02-20T10:30:45.234Z"
}
```

---

### 2. 获取流量统计信息

#### 请求

```
GET /api/visualization/statistics?start_time=<ISO8601>&end_time=<ISO8601>
```

#### 参数

| 参数 | 类型 | 必需 | 描述 |
|------|------|------|------|
| start_time | string | 否 | 开始时间（ISO8601格式），默认为1小时前 |
| end_time | string | 否 | 结束时间（ISO8601格式），默认为当前时间 |

#### 描述

获取指定时间范围内的流量统计信息，包括总流量、组件间流量分布、控制/遥测比例等。

#### 响应

**状态码**: 200 OK

```json
{
  "success": true,
  "data": {
    "time_range": {
      "start": "2024-02-20T09:30:45.000Z",
      "end": "2024-02-20T10:30:45.000Z"
    },
    "summary": {
      "total_packets": 15234,
      "total_bytes": 52847392,
      "average_packet_size": 3472,
      "packet_rate": 4.23,
      "byte_rate": 14679.3
    },
    "traffic_type_distribution": {
      "control": {
        "packets": 3456,
        "bytes": 8234567,
        "percentage": 22.7
      },
      "telemetry": {
        "packets": 11778,
        "bytes": 44612825,
        "percentage": 77.3
      }
    },
    "component_traffic": {
      "Master": {
        "sent": 5234,
        "received": 4123,
        "total": 9357
      },
      "Power_01": {
        "sent": 2134,
        "received": 2456,
        "total": 4590
      },
      "Storage_01": {
        "sent": 1876,
        "received": 2345,
        "total": 4221
      },
      "Demand_01": {
        "sent": 1234,
        "received": 1567,
        "total": 2801
      }
    },
    "top_flows": [
      {
        "from": "Master",
        "to": "Power_01",
        "packets": 3456,
        "bytes": 12345678,
        "type": "Control"
      },
      {
        "from": "Power_01",
        "to": "Master",
        "packets": 2876,
        "bytes": 9876543,
        "type": "Telemetry"
      }
    ]
  },
  "timestamp": "2024-02-20T10:30:45.234Z"
}
```

#### 错误响应

```json
{
  "success": false,
  "error": "Invalid time range",
  "timestamp": "2024-02-20T10:30:45.234Z"
}
```

---

## WebSocket 消息

### 连接信息

- **URL**: `ws://localhost:5000/socket.io/?transport=websocket`
- **协议**: Socket.IO
- **自动重连**: 是

### 1. 连接事件

#### 客户端连接

**事件**: `connect`

当客户端成功连接到服务器时自动触发。

**响应数据**:

```json
{
  "client_id": "abc123def456",
  "server_time": "2024-02-20T10:30:45.234Z",
  "message": "Connected to VPP Traffic Visualization Engine"
}
```

#### 客户端断开连接

**事件**: `disconnect`

当客户端断开连接时自动触发。

---

### 2. 流量事件

#### 接收流量事件

**事件**: `traffic_event`

服务器实时推送流量事件到所有连接的客户端。

**数据格式**:

```json
{
  "from": "Master",
  "to": "Power_01",
  "type": "Control",
  "intensity": 0.75,
  "packet_size": 1024,
  "timestamp": "2024-02-20T10:30:45.234Z"
}
```

**字段说明**:

| 字段 | 类型 | 描述 |
|------|------|------|
| from | string | 源组件名称 |
| to | string | 目标组件名称 |
| type | string | 流量类型（"Control" 或 "Telemetry"） |
| intensity | number | 流量强度（0.0-1.0） |
| packet_size | number | 数据包大小（字节） |
| timestamp | string | 事件时间戳（ISO8601格式） |

---

### 3. 心跳消息

#### 发送心跳

**事件**: `ping`

客户端定期发送心跳消息以保持连接活跃。

**请求**:

```json
{
  "timestamp": "2024-02-20T10:30:45.234Z"
}
```

**响应**:

```json
{
  "timestamp": "2024-02-20T10:30:45.234Z",
  "server_time": "2024-02-20T10:30:45.235Z",
  "latency_ms": 1
}
```

---

### 4. 订阅/取消订阅

#### 订阅特定组件流量

**事件**: `subscribe`

订阅来自或发往特定组件的流量事件。

**请求**:

```json
{
  "component": "Master",
  "filter_type": "all"
}
```

**参数说明**:

| 参数 | 类型 | 描述 |
|------|------|------|
| component | string | 组件名称 |
| filter_type | string | 过滤类型（"all", "control", "telemetry"） |

**响应**:

```json
{
  "success": true,
  "message": "Subscribed to Master traffic",
  "subscription_id": "sub_123456"
}
```

#### 取消订阅

**事件**: `unsubscribe`

取消对特定组件流量的订阅。

**请求**:

```json
{
  "subscription_id": "sub_123456"
}
```

**响应**:

```json
{
  "success": true,
  "message": "Unsubscribed from Master traffic"
}
```

---

### 5. 统计信息请求

#### 请求统计信息

**事件**: `request_statistics`

请求当前的流量统计信息。

**请求**:

```json
{
  "time_range": "1h"
}
```

**参数说明**:

| 参数 | 类型 | 描述 |
|------|------|------|
| time_range | string | 时间范围（"1h", "6h", "24h", "7d"） |

**响应**:

```json
{
  "success": true,
  "data": {
    "summary": {
      "total_packets": 15234,
      "total_bytes": 52847392,
      "average_packet_size": 3472
    },
    "traffic_type_distribution": {
      "control": 22.7,
      "telemetry": 77.3
    }
  }
}
```

---

### 6. 组件信息请求

#### 请求组件列表

**事件**: `request_components`

请求所有VPP组件的信息。

**请求**:

```json
{}
```

**响应**:

```json
{
  "success": true,
  "data": {
    "components": [
      {
        "name": "Master",
        "ip": "10.0.8.1",
        "status": "active"
      },
      {
        "name": "Power_01",
        "ip": "10.0.8.2",
        "status": "active"
      }
    ]
  }
}
```

---

### 7. 系统消息

#### 接收系统消息

**事件**: `system_message`

服务器推送系统级别的消息（如错误、警告、信息）。

**数据格式**:

```json
{
  "level": "info",
  "message": "System is running normally",
  "timestamp": "2024-02-20T10:30:45.234Z"
}
```

**消息级别**:

| 级别 | 描述 |
|------|------|
| info | 信息消息 |
| warning | 警告消息 |
| error | 错误消息 |
| critical | 严重错误 |

---

## 数据模型

### RawPacket

表示原始网络数据包。

```json
{
  "src_ip": "10.0.8.1",
  "dst_ip": "10.0.8.2",
  "src_port": 22,
  "dst_port": 12345,
  "protocol": "TCP",
  "packet_size": 1024,
  "timestamp": "2024-02-20T10:30:45.234Z"
}
```

### VisualizationEvent

表示可视化事件。

```json
{
  "from": "Master",
  "to": "Power_01",
  "type": "Control",
  "intensity": 0.75,
  "packet_size": 1024,
  "timestamp": "2024-02-20T10:30:45.234Z"
}
```

### ComponentInfo

表示VPP组件信息。

```json
{
  "name": "Master",
  "ip": "10.0.8.1",
  "status": "active",
  "type": "control",
  "last_seen": "2024-02-20T10:30:45.123Z",
  "packet_count": 15234,
  "byte_count": 52847392
}
```

---

## 错误处理

### 错误响应格式

所有错误响应遵循以下格式：

```json
{
  "success": false,
  "error": "Error message",
  "error_code": "ERROR_CODE",
  "timestamp": "2024-02-20T10:30:45.234Z"
}
```

### 常见错误代码

| 错误代码 | HTTP状态码 | 描述 |
|---------|-----------|------|
| INVALID_REQUEST | 400 | 请求格式无效 |
| INVALID_TIME_RANGE | 400 | 时间范围无效 |
| COMPONENT_NOT_FOUND | 404 | 组件未找到 |
| INTERNAL_ERROR | 500 | 服务器内部错误 |
| SERVICE_UNAVAILABLE | 503 | 服务不可用 |

---

## 示例

### 示例 1: 获取组件信息

**请求**:

```bash
curl -X GET http://localhost:5000/api/visualization/components
```

**响应**:

```json
{
  "success": true,
  "data": {
    "components": [
      {
        "name": "Master",
        "ip": "10.0.8.1",
        "status": "active",
        "type": "control"
      }
    ],
    "total_components": 1,
    "active_components": 1
  },
  "timestamp": "2024-02-20T10:30:45.234Z"
}
```

### 示例 2: 获取统计信息

**请求**:

```bash
curl -X GET "http://localhost:5000/api/visualization/statistics?start_time=2024-02-20T09:30:45Z&end_time=2024-02-20T10:30:45Z"
```

**响应**:

```json
{
  "success": true,
  "data": {
    "summary": {
      "total_packets": 15234,
      "total_bytes": 52847392
    }
  },
  "timestamp": "2024-02-20T10:30:45.234Z"
}
```

### 示例 3: WebSocket 连接和订阅

**JavaScript 客户端代码**:

```javascript
// 连接到服务器
const socket = io('http://localhost:5000');

// 连接成功
socket.on('connect', () => {
  console.log('Connected to server');
  
  // 订阅 Master 组件的流量
  socket.emit('subscribe', {
    component: 'Master',
    filter_type: 'all'
  });
});

// 接收流量事件
socket.on('traffic_event', (event) => {
  console.log('Traffic event:', event);
  // 更新前端可视化
});

// 接收系统消息
socket.on('system_message', (message) => {
  console.log('System message:', message);
});

// 断开连接
socket.on('disconnect', () => {
  console.log('Disconnected from server');
});
```

---

## 性能指标

### 延迟要求

| 操作 | 目标延迟 | 说明 |
|------|---------|------|
| 流量采集 | < 100ms | 从网络采集到事件生成 |
| 事件转化 | < 50ms | 从原始包到可视化事件 |
| WebSocket推送 | < 100ms | 从事件生成到客户端接收 |
| 总端到端延迟 | < 250ms | 从采集到前端渲染 |

### 吞吐量要求

| 指标 | 目标值 | 说明 |
|------|-------|------|
| 最大数据包处理速率 | >= 10000 pps | 每秒处理的数据包数 |
| 最大字节处理速率 | >= 100 Mbps | 每秒处理的字节数 |
| 最大并发客户端 | >= 100 | 同时连接的客户端数 |
| 最大粒子数量 | <= 10000 | 前端同时渲染的粒子数 |

---

## 版本历史

| 版本 | 日期 | 描述 |
|------|------|------|
| 1.0.0 | 2024-02-20 | 初始版本 |

---

## 联系方式

如有问题或建议，请联系开发团队。

