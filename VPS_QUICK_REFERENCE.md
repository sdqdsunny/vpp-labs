# VPS 快速参考卡

## 🚀 一键部署

```bash
ssh root@your-vps-ip
curl -fsSL https://raw.githubusercontent.com/your-org/vpp-phase2-simulation/main/deploy-vps.sh | sudo bash
```

---

## 📊 最低配置

| 项目 | 最低 | 推荐 | 生产 |
|------|------|------|------|
| CPU | 1核 | 2核 | 4核 |
| 内存 | 1GB | 2GB | 4-8GB |
| 存储 | 20GB | 50GB | 100GB |
| 成本 | $5/月 | $12/月 | $30/月 |

---

## 🌍 推荐云服务商

| 提供商 | 配置 | 价格 | 链接 |
|--------|------|------|------|
| Vultr | 1GB, 1核, 10GB | $2.5/月 | vultr.com |
| Hetzner | 2GB, 1核, 20GB | €3/月 | hetzner.com |
| Linode | 1GB, 1核, 25GB | $5/月 | linode.com |
| DigitalOcean | 1GB, 1核, 25GB | $6/月 | digitalocean.com |

---

## 📍 访问地址

```
健康检查:    http://your-vps-ip:8080/health
就绪检查:    http://your-vps-ip:8080/ready
指标:        http://your-vps-ip:8080/metrics
测试仪表板:  http://your-vps-ip:8080/test-dashboard
API 文档:    http://your-vps-ip:8080/api/docs
```

---

## 🔧 常用命令

```bash
# 查看日志
docker-compose logs -f

# 查看容器
docker-compose ps

# 重启服务
docker-compose restart

# 停止服务
docker-compose down

# 启动服务
docker-compose up -d

# 进入容器
docker-compose exec vpp-phase2-simulation bash

# 查看资源使用
docker stats
```

---

## 🔗 Phase 1 集成端点

```
GET  /api/phase1/health              检查连接
GET  /api/phase1/status              获取状态
POST /api/phase1/sync                同步数据
POST /api/phase1/sync/devices        同步设备
POST /api/phase1/sync/scenarios      同步场景
POST /api/phase1/sync/metrics        同步指标
GET  /api/phase1/sync/history        获取历史
```

---

## 📚 文档链接

- [VPS 部署指南](vpp-phase2-simulation/VPS_DEPLOYMENT_GUIDE.md)
- [VPS 配置要求](vpp-phase2-simulation/VPS_REQUIREMENTS.md)
- [API 文档](vpp-phase2-simulation/routes/)
- [故障排查](vpp-phase2-simulation/TROUBLESHOOTING_GUIDE.md)

---

## ⚡ 快速故障排查

| 问题 | 解决方案 |
|------|---------|
| 端口被占用 | `lsof -i :8080` 然后 `kill -9 <PID>` |
| 数据库连接失败 | `docker-compose restart postgres` |
| 内存不足 | `docker system prune -a` |
| 磁盘满 | `du -sh /*` 查看大文件 |
| 应用无法启动 | `docker-compose logs vpp-phase2-simulation` |

---

**最后更新**: 2026年2月17日
