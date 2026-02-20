# VPP 流量可视化引擎 - 用户指南

## 目录

1. [系统概述](#系统概述)
2. [快速开始](#快速开始)
3. [系统架构](#系统架构)
4. [使用指南](#使用指南)
5. [部署指南](#部署指南)
6. [故障排除](#故障排除)
7. [常见问题](#常见问题)

---

## 系统概述

### 什么是VPP流量可视化引擎？

VPP流量可视化引擎是一个实时网络流量监控和可视化系统，专门为虚拟电力厂（VPP）系统设计。它能够：

- **实时采集**：从OVS镜像端口采集网络流量
- **智能分类**：自动识别控制流量和遥测流量
- **3D可视化**：在交互式3D拓扑图中实时展示流量流动
- **性能监控**：提供详细的流量统计和性能指标
- **数据导出**：支持截图、视频录制和数据导出

### 主要特性

✓ 实时流量采集和处理  
✓ 智能流量分类（控制/遥测）  
✓ 3D交互式可视化  
✓ WebSocket实时推送  
✓ 完整的REST API  
✓ 高性能设计（支持10000+ pps）  
✓ Docker容器化部署  
✓ 完整的测试覆盖  

---

## 快速开始

### 前置要求

- Docker 20.10+
- Docker Compose 1.29+
- 现代Web浏览器（Chrome, Firefox, Safari, Edge）
- 网络连接

### 使用Docker Compose启动

1. **克隆项目**

```bash
git clone <repository-url>
cd vpp-traffic-visualization
```

2. **启动服务**

```bash
docker-compose up -d
```

3. **验证服务**

```bash
# 检查容器状态
docker-compose ps

# 查看日志
docker-compose logs -f backend
```

4. **访问应用**

打开浏览器访问：`http://localhost:8080`

### 使用部署脚本启动

```bash
# 使用部署脚本
./deploy.sh

# 验证部署
./verify-docker.sh
```

### 停止服务

```bash
docker-compose down
```

---

## 系统架构

### 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                    前端 (Frontend)                       │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Three.js 3D场景 | 粒子系统 | 交互控制          │  │
│  │  HTML5 Canvas | WebGL | JavaScript              │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                          ↕ WebSocket
┌─────────────────────────────────────────────────────────┐
│                    后端 (Backend)                        │
│  ┌──────────────────────────────────────────────────┐  │
│  │  Flask应用 | Flask-SocketIO | REST API          │  │
│  └──────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────┐  │
│  │  流量采集 | 事件队列 | 流量分类 | 事件生成      │  │
│  │  WebSocket广播 | 统计计算                       │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                          ↕
┌─────────────────────────────────────────────────────────┐
│                  数据源 (Data Source)                    │
│  ┌──────────────────────────────────────────────────┐  │
│  │  OVS镜像端口 | PCAP文件 | JSON数据源           │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

### 核心组件

#### 1. 流量采集层 (Traffic Collection)

- **TrafficCollectorService**: 从多个数据源采集网络流量
- **EventQueue**: 缓存和管理采集的事件
- 支持PCAP文件和JSON数据源

#### 2. 转化层 (Transformation)

- **TrafficClassifier**: 将流量分类为控制或遥测类型
- **EventGenerator**: 将原始数据包转换为可视化事件
- **WebSocketBroadcaster**: 实时推送事件到前端

#### 3. 前端渲染层 (Frontend Rendering)

- **SceneManager**: 管理Three.js场景
- **ParticleSystem**: 渲染粒子流动画
- **CameraController**: 处理用户交互和相机控制

---

## 使用指南

### 1. 访问仪表板

打开浏览器访问 `http://localhost:8080`，您将看到：

- **左侧面板**：控制和统计信息
- **中央区域**：3D拓扑图和粒子流动画
- **右侧面板**：详细信息和设置

### 2. 3D场景交互

#### 鼠标操作

| 操作 | 功能 |
|------|------|
| 左键拖动 | 旋转场景 |
| 右键拖动 | 平移场景 |
| 滚轮 | 缩放场景 |
| 双击 | 重置视角 |

#### 键盘快捷键

| 快捷键 | 功能 |
|--------|------|
| R | 重置视角 |
| P | 暂停/继续动画 |
| + | 增加粒子数量 |
| - | 减少粒子数量 |
| S | 截图 |
| V | 开始/停止录制 |

### 3. 流量监控

#### 查看实时流量

1. 场景中的粒子代表实时流量
2. **暖色粒子**（红/橙）= 控制流量
3. **冷色粒子**（蓝/绿）= 遥测流量
4. 粒子大小和速度表示流量强度

#### 查看统计信息

左侧面板显示：

- **总流量统计**：总数据包数、总字节数、平均包大小
- **流量类型分布**：控制流量和遥测流量的比例
- **组件间流量**：各组件之间的流量分布
- **实时速率**：当前的数据包速率和字节速率

### 4. 组件交互

#### 点击组件

点击3D场景中的组件节点可以：

- 显示组件详细信息
- 高亮显示与该组件相关的流量
- 显示组件的统计数据

#### 悬停组件

将鼠标悬停在粒子上可以：

- 显示流量详情（源、目标、类型、大小）
- 高亮显示流量路径
- 显示流量时间戳

### 5. 时间范围选择

在左侧面板中选择时间范围：

- **1小时**：查看最近1小时的流量
- **6小时**：查看最近6小时的流量
- **24小时**：查看最近24小时的流量
- **7天**：查看最近7天的流量

### 6. 动画控制

#### 播放控制

- **暂停**：暂停粒子动画
- **继续**：继续播放动画
- **速度调整**：调整动画播放速度（0.5x - 2.0x）

#### 进度条

- 显示当前播放进度
- 可以拖动进度条跳转到特定时间

### 7. 数据导出

#### 截图导出

1. 点击"截图"按钮
2. 选择分辨率（标准/高分辨率）
3. 文件自动下载为PNG格式

#### 视频录制

1. 点击"开始录制"按钮
2. 进行所需的操作
3. 点击"停止录制"按钮
4. 文件自动下载为MP4格式

#### 数据导出

1. 点击"导出数据"按钮
2. 选择格式（JSON/CSV）
3. 选择时间范围
4. 文件自动下载

---

## 部署指南

### 前置要求

- Linux/macOS/Windows系统
- Docker和Docker Compose
- 至少2GB可用内存
- 至少1GB可用磁盘空间

### 部署步骤

#### 1. 准备环境

```bash
# 克隆项目
git clone <repository-url>
cd vpp-traffic-visualization

# 检查Docker
docker --version
docker-compose --version
```

#### 2. 配置环境变量

创建 `.env` 文件（可选）：

```env
# 后端配置
BACKEND_PORT=5000
BACKEND_HOST=0.0.0.0

# 前端配置
FRONTEND_PORT=8080

# 日志级别
LOG_LEVEL=INFO

# 数据源配置
DATA_SOURCE=json  # 或 pcap
```

#### 3. 启动服务

```bash
# 使用docker-compose
docker-compose up -d

# 或使用部署脚本
./deploy.sh
```

#### 4. 验证部署

```bash
# 检查容器状态
docker-compose ps

# 检查后端健康状态
curl http://localhost:5000/api/visualization/components

# 检查前端
curl http://localhost:8080
```

#### 5. 查看日志

```bash
# 查看所有日志
docker-compose logs

# 查看后端日志
docker-compose logs backend

# 查看前端日志
docker-compose logs frontend

# 实时查看日志
docker-compose logs -f
```

### 停止和清理

```bash
# 停止服务
docker-compose down

# 停止并删除数据
docker-compose down -v

# 删除镜像
docker-compose down --rmi all
```

### 生产环境部署

#### 使用Nginx反向代理

```nginx
upstream backend {
    server backend:5000;
}

upstream frontend {
    server frontend:8080;
}

server {
    listen 80;
    server_name your-domain.com;

    # 前端
    location / {
        proxy_pass http://frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # 后端API
    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # WebSocket
    location /socket.io {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

#### 使用SSL/TLS

```bash
# 生成自签名证书
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365

# 在docker-compose.yml中配置
volumes:
  - ./cert.pem:/etc/nginx/cert.pem
  - ./key.pem:/etc/nginx/key.pem
```

---

## 故障排除

### 常见问题

#### 1. 无法连接到服务

**症状**：浏览器显示"无法连接"

**解决方案**：

```bash
# 检查容器是否运行
docker-compose ps

# 检查端口是否开放
netstat -an | grep 8080

# 重启服务
docker-compose restart
```

#### 2. WebSocket连接失败

**症状**：控制台显示"WebSocket连接失败"

**解决方案**：

```bash
# 检查后端日志
docker-compose logs backend

# 检查防火墙设置
# 确保5000端口开放

# 重启后端服务
docker-compose restart backend
```

#### 3. 流量数据不显示

**症状**：3D场景中没有粒子

**解决方案**：

```bash
# 检查数据源配置
# 确保PCAP文件或JSON数据源正确配置

# 检查后端日志
docker-compose logs backend | grep -i error

# 验证API端点
curl http://localhost:5000/api/visualization/components
```

#### 4. 性能问题

**症状**：帧率低、卡顿

**解决方案**：

```bash
# 减少粒子数量
# 在前端设置中调整粒子数量

# 检查系统资源
docker stats

# 增加容器资源限制
# 在docker-compose.yml中修改
```

#### 5. 内存泄漏

**症状**：内存使用不断增加

**解决方案**：

```bash
# 检查内存使用
docker stats

# 重启容器
docker-compose restart

# 检查日志中的错误
docker-compose logs backend | grep -i memory
```

### 日志分析

#### 查看错误日志

```bash
# 查看所有错误
docker-compose logs | grep ERROR

# 查看特定时间的日志
docker-compose logs --since 10m

# 导出日志到文件
docker-compose logs > logs.txt
```

#### 启用调试模式

在 `.env` 文件中设置：

```env
LOG_LEVEL=DEBUG
```

然后重启服务：

```bash
docker-compose restart
```

---

## 常见问题

### Q1: 系统支持多少个并发客户端？

**A**: 系统设计支持至少100个并发客户端。实际数量取决于服务器硬件和网络带宽。

### Q2: 最大可以处理多少流量？

**A**: 系统设计支持至少10000 pps（每秒数据包数）和100 Mbps的吞吐量。

### Q3: 数据会被保存吗？

**A**: 当前版本不持久化数据。重启后数据会丢失。可以通过导出功能保存数据。

### Q4: 支持哪些数据源？

**A**: 支持PCAP文件、JSON数据源和OVS镜像端口。

### Q5: 如何自定义组件？

**A**: 编辑 `backend/services/traffic_classifier.py` 中的 `VPP_COMPONENTS` 字典。

### Q6: 如何修改流量分类规则？

**A**: 编辑 `backend/services/traffic_classifier.py` 中的分类方法。

### Q7: 支持哪些浏览器？

**A**: 支持所有现代浏览器（Chrome 90+, Firefox 88+, Safari 14+, Edge 90+）。

### Q8: 如何获取技术支持？

**A**: 请查看项目的GitHub Issues或联系开发团队。

---

## 性能优化建议

### 前端优化

1. **减少粒子数量**：在高流量场景下减少粒子数量以提高帧率
2. **降低渲染质量**：在低端设备上降低渲染质量
3. **启用硬件加速**：在浏览器设置中启用硬件加速

### 后端优化

1. **调整队列大小**：根据流量大小调整事件队列大小
2. **启用消息压缩**：启用WebSocket消息压缩
3. **批量发送**：批量发送事件以减少网络开销

### 系统优化

1. **增加内存**：为Docker容器分配更多内存
2. **使用SSD**：使用SSD存储以提高I/O性能
3. **网络优化**：使用有线网络而不是WiFi

---

## 更新和维护

### 检查更新

```bash
# 拉取最新代码
git pull origin main

# 重建镜像
docker-compose build

# 重启服务
docker-compose up -d
```

### 备份数据

```bash
# 导出数据
curl http://localhost:5000/api/visualization/statistics > backup.json

# 导出配置
docker-compose config > docker-compose.backup.yml
```

### 清理日志

```bash
# 清理Docker日志
docker system prune

# 清理容器日志
docker-compose logs --tail 0 > /dev/null
```

---

## 许可证

本项目采用MIT许可证。详见LICENSE文件。

---

## 联系方式

如有问题或建议，请通过以下方式联系：

- GitHub Issues: [项目地址]/issues
- Email: support@example.com
- 文档: [项目文档地址]

