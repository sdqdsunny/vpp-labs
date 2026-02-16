# VPP Master - 虚拟电厂主站程序

基于Bottle.py框架开发的虚拟电厂（VPP）主站程序，用于电力系统协议安全评估与漏洞深度分析。

## 项目概述

VPP Master是一个全软件定义的仿真环境，用于：

- 🔒 **协议安全评估** - 对电力工控协议进行安全评估
- 🐛 **漏洞深度分析** - 支持漏洞挖掘、复现和分析
- 📊 **业务闭环验证** - 构建完整的虚拟电厂业务链路
- 🌐 **5G链路仿真** - 模拟5G无线通信过程

## 快速开始

### 前置要求

- Python 3.11+
- Docker & Docker Compose（可选）
- Git

### 本地开发

1. **克隆项目**
```bash
git clone <repository-url>
cd vpp-master
```

2. **创建虚拟环境**
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows
```

3. **安装依赖**
```bash
pip install -r requirements.txt
```

4. **配置环境变量**
```bash
cp .env.example .env
# 编辑.env文件，根据需要修改配置
```

5. **运行应用**
```bash
python app.py
```

访问 http://localhost:8080 查看应用。

### Docker部署

1. **构建镜像**
```bash
docker build -t vpp-master:latest .
```

2. **运行容器**
```bash
docker-compose up -d
```

3. **查看日志**
```bash
docker-compose logs -f vpp-master
```

## 项目结构

```
vpp-master/
├── app.py                      # 主应用入口
├── config.py                   # 配置管理
├── requirements.txt            # 依赖列表
├── Dockerfile                  # Docker配置
├── docker-compose.yml          # Docker Compose配置
├── .env                        # 环境变量
├── routes/                     # 路由模块
│   ├── __init__.py
│   ├── devices.py             # 设备管理
│   ├── dispatch.py            # 调度控制
│   ├── analysis.py            # 分析功能
│   └── protocol.py            # 协议转换
├── models/                     # 数据模型
│   ├── __init__.py
│   ├── device.py
│   ├── dispatch.py
│   └── analysis.py
├── services/                   # 业务逻辑
│   ├── __init__.py
│   ├── resource_manager.py    # 资源管理
│   ├── dispatch_engine.py     # 调度引擎
│   ├── protocol_converter.py  # 协议转换
│   ├── core_dump_analyzer.py  # Core Dump分析
│   └── report_generator.py    # 报告生成
├── utils/                      # 工具函数
│   ├── __init__.py
│   ├── logger.py              # 日志配置
│   ├── validators.py          # 数据验证
│   └── helpers.py             # 辅助函数
├── static/                     # 前端文件
│   ├── index.html
│   ├── css/
│   └── js/
├── tests/                      # 测试
│   ├── __init__.py
│   ├── test_api.py
│   └── test_services.py
└── README.md
```

## API文档

### 健康检查

```
GET /health
```

返回系统健康状态。

### 设备管理

```
GET /api/devices              # 获取所有设备
POST /api/devices             # 创建设备
GET /api/devices/<id>         # 获取设备详情
PUT /api/devices/<id>         # 更新设备
DELETE /api/devices/<id>      # 删除设备
```

### 调度控制

```
POST /api/dispatch            # 下发调度指令
GET /api/dispatch/<id>        # 获取调度详情
GET /api/dispatch/status      # 获取调度状态
```

### 协议转换

```
POST /api/protocol/convert    # 协议转换
GET /api/protocol/mappings    # 获取映射规则
POST /api/protocol/mappings   # 创建映射规则
```

### 分析功能

```
POST /api/analysis/core-dump/upload      # 上传Core Dump
GET /api/analysis/core-dump/<id>         # 获取分析结果
GET /api/analysis/vulnerability-report   # 获取漏洞报告
```

## 配置说明

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| ENVIRONMENT | 运行环境 | development |
| DEBUG | 调试模式 | true |
| HOST | 监听地址 | 0.0.0.0 |
| PORT | 监听端口 | 8080 |
| DATABASE_URL | 数据库URL | sqlite:///vpp_master.db |
| REDIS_URL | Redis URL | redis://localhost:6379/0 |
| LOG_LEVEL | 日志级别 | DEBUG |
| LOG_FORMAT | 日志格式 | standard |

## 开发指南

### 添加新的API端点

1. 在 `routes/` 目录下创建新的路由文件
2. 定义路由函数
3. 在 `app.py` 中注册路由

示例：

```python
# routes/my_route.py
from bottle import Bottle

app = Bottle()

@app.route('/api/my-endpoint')
def my_endpoint():
    return {'message': 'Hello'}
```

### 运行测试

```bash
pytest tests/
```

### 代码格式化

```bash
black .
flake8 .
```

## 监控和日志

### Prometheus指标

访问 http://localhost:9090 查看Prometheus。

### Grafana仪表板

访问 http://localhost:3000 查看Grafana（默认用户名/密码: admin/admin）。

### 日志查看

```bash
# 查看应用日志
docker-compose logs -f vpp-master

# 查看所有服务日志
docker-compose logs -f
```

## 故障排查

### 应用无法启动

1. 检查Python版本：`python --version`
2. 检查依赖安装：`pip list`
3. 查看日志：`docker-compose logs vpp-master`

### 数据库连接错误

1. 检查PostgreSQL是否运行：`docker-compose ps`
2. 检查数据库URL配置
3. 检查数据库凭证

### 端口被占用

修改 `.env` 文件中的 `PORT` 变量。

## 贡献指南

欢迎提交Issue和Pull Request！

## 许可证

MIT License

## 联系方式

如有问题，请提交Issue或联系项目维护者。

---

**版本**: 0.1.0  
**最后更新**: 2026年2月16日
