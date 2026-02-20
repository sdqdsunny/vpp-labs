# VPP Master 快速启动指南

**最后更新**: 2026年2月16日

---

## 🚀 5分钟快速启动

### 方式1：本地Python运行（最快）

```bash
# 1. 进入项目目录
cd vpp-master

# 2. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 运行应用
python app.py
```

**访问**: http://localhost:8080/health

---

### 方式2：Docker Compose运行（推荐）

```bash
# 1. 进入项目目录
cd vpp-master

# 2. 启动所有服务
docker-compose up -d

# 3. 查看日志
docker-compose logs -f vpp-master
```

**访问**:
- VPP Master: http://localhost:8080/health
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin)

---

## 📋 验证安装

### 测试API

```bash
# 健康检查
curl http://localhost:8080/health

# 预期响应
{
  "status": "healthy",
  "version": "0.1.0",
  "environment": "development"
}
```

### 查看日志

```bash
# 本地运行
# 日志会直接输出到终端

# Docker运行
docker-compose logs -f vpp-master
```

---

## 🛠️ 常用命令

### 本地开发

```bash
# 激活虚拟环境
source venv/bin/activate

# 运行应用
python app.py

# 运行测试
pytest tests/

# 代码格式化
black .

# 代码检查
flake8 .

# 停止应用
Ctrl+C
```

### Docker操作

```bash
# 启动服务
docker-compose up -d

# 停止服务
docker-compose down

# 查看日志
docker-compose logs -f

# 重启服务
docker-compose restart vpp-master

# 进入容器
docker-compose exec vpp-master bash

# 查看服务状态
docker-compose ps
```

---

## 🔧 配置修改

### 修改端口

编辑 `.env` 文件：
```env
PORT=8080  # 改为其他端口，如9000
```

### 修改日志级别

编辑 `.env` 文件：
```env
LOG_LEVEL=DEBUG  # 改为INFO、WARNING、ERROR等
```

### 使用PostgreSQL

编辑 `.env` 文件：
```env
DATABASE_URL=postgresql://vpp:vpp@postgres:5432/vpp_master
```

---

## 📊 监控和调试

### 查看应用日志

```bash
# 本地运行
# 日志直接输出到终端

# Docker运行
docker-compose logs -f vpp-master
```

### 查看Prometheus指标

访问 http://localhost:9090

### 查看Grafana仪表板

访问 http://localhost:3000
- 用户名: admin
- 密码: admin

---

## ❌ 故障排查

### 问题1：端口被占用

**错误信息**: `Address already in use`

**解决方案**:
1. 修改 `.env` 中的 `PORT`
2. 或者杀死占用端口的进程：
   ```bash
   # Linux/Mac
   lsof -i :8080
   kill -9 <PID>
   
   # Windows
   netstat -ano | findstr :8080
   taskkill /PID <PID> /F
   ```

### 问题2：依赖安装失败

**错误信息**: `pip install failed`

**解决方案**:
```bash
# 升级pip
pip install --upgrade pip

# 清除缓存后重新安装
pip install --no-cache-dir -r requirements.txt
```

### 问题3：Docker镜像构建失败

**错误信息**: `docker build failed`

**解决方案**:
```bash
# 清除缓存后重新构建
docker-compose build --no-cache

# 或者
docker build --no-cache -t vpp-master:latest .
```

### 问题4：数据库连接错误

**错误信息**: `database connection failed`

**解决方案**:
1. 检查PostgreSQL是否运行：`docker-compose ps`
2. 检查 `DATABASE_URL` 配置
3. 检查数据库凭证

---

## 📚 下一步

### 开发新功能

1. 创建新的路由文件 `routes/my_route.py`
2. 定义API端点
3. 在 `app.py` 中注册路由
4. 编写测试

### 查看完整文档

- [README.md](README.md) - 项目文档
- [../PRD-v2.0.md](../PRD-v2.0.md) - 需求文档
- [../DECISION_SUMMARY.md](../DECISION_SUMMARY.md) - 技术决策

---

## 💡 提示

- 使用 `docker-compose` 可以快速启动完整的开发环境
- 修改代码后，本地运行会自动重载（debug=true时）
- Docker运行需要手动重启容器才能加载代码变更
- 生产环境建议使用 `gunicorn` 或 `uWSGI`

---

**祝你开发愉快！** 🎉
