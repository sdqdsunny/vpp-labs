# 最终诊断报告 - 为什么看不到 Wireshark 流量

## 🔴 根本原因

**vpp-phase2-simulation 容器启动失败！**

```
ModuleNotFoundError: No module named 'apscheduler'
```

### 问题链：
1. vpp-phase2-simulation 容器启动时缺少 `apscheduler` 模块
2. Phase1IntegrationService 无法初始化
3. 没有定时任务向 vpp-master 发送请求
4. 没有流量可以抓包

---

## 📊 当前状态

### vpp-phase2-simulation 日志
```
Traceback (most recent call last):
  File "/app/app.py", line 22, in <module>
    from routes.phase1_integration import create_phase1_integration_routes
  File "/app/routes/phase1_integration.py", line 14, in <module>
    from services.phase1_integration import Phase1IntegrationService
  File "/app/services/phase1_integration.py", line 17, in <module>
    from apscheduler.schedulers.background import BackgroundScheduler
ModuleNotFoundError: No module named 'apscheduler'
```

### 容器状态
```
vpp-phase2-simulation: 启动失败
vpp-master: 运行中（但有内部错误）
vpp-vcc: 运行中（但不健康）
vpp-upf: 运行中（但不健康）
vpp-gen: 运行中（但不健康）
vpp-analyzer: 运行中（健康）
```

---

## ✅ 解决方案

### 步骤 1：检查 vpp-phase2-simulation 的 requirements.txt

```bash
cat vpp-phase2-simulation/requirements.txt | grep -i apscheduler
```

### 步骤 2：确保 apscheduler 已安装

```bash
# 进入容器
docker exec -it vpp-phase2-simulation bash

# 安装缺失的模块
pip install apscheduler

# 或者重新构建镜像
docker build -t vpp-phase2-simulation:latest vpp-phase2-simulation/
```

### 步骤 3：重启容器

```bash
docker restart vpp-phase2-simulation
```

### 步骤 4：验证容器启动成功

```bash
docker logs vpp-phase2-simulation --tail 50
```

应该看到：
```
Phase 1 Integration Service initialized
master_url=http://vpp-master:8080
Scheduled sync started
```

### 步骤 5：现在可以抓包了

```bash
docker exec vpp-master tcpdump -i eth0 -w - 'tcp port 8080' > capture.pcap && open capture.pcap
```

---

## 🔍 为什么之前没有看到这个错误？

1. **容器启动失败但没有立即显示**
   - Docker 容器在启动失败后会退出
   - 但 `docker ps` 可能不会立即显示

2. **日志中有错误但被忽略了**
   - 需要查看完整的日志才能看到 ModuleNotFoundError

3. **没有流量意味着没有通信**
   - 即使网络连接正确，如果应用启动失败，也不会有流量

---

## 📋 完整的故障排查清单

- [ ] 检查 vpp-phase2-simulation 容器是否运行
- [ ] 查看容器日志中是否有错误
- [ ] 检查 requirements.txt 中是否有所有依赖
- [ ] 重新构建 Docker 镜像
- [ ] 重启容器
- [ ] 验证 Phase1IntegrationService 已初始化
- [ ] 检查是否有向 vpp-master 的请求
- [ ] 从容器内部抓包

---

## 🎯 下一步

1. **修复 vpp-phase2-simulation**
   - 安装缺失的 apscheduler 模块
   - 重新构建镜像
   - 重启容器

2. **修复 vpp-master**
   - 修复 request.user_agent 错误
   - 重启容器

3. **验证通信**
   - 检查日志中是否有 POST /api/v1/devices/sync 请求
   - 从容器内部抓包

4. **用 Wireshark 分析**
   - 抓包到 pcap 文件
   - 用 Wireshark 打开
   - 分析 HTTP 流量

---

## 💡 关键教训

1. **总是检查容器日志**
   ```bash
   docker logs <container> --tail 100
   ```

2. **检查依赖是否完整**
   ```bash
   docker exec <container> pip list | grep apscheduler
   ```

3. **验证应用启动成功**
   ```bash
   docker logs <container> | grep -i "initialized\|started\|error"
   ```

4. **从容器内部测试连接**
   ```bash
   docker exec <container> curl -v http://vpp-master:8080/health
   ```

---

## 📝 总结

**问题**: 看不到 Wireshark 流量

**根本原因**: vpp-phase2-simulation 容器启动失败（缺少 apscheduler 模块）

**解决方案**: 
1. 安装缺失的依赖
2. 重新构建镜像
3. 重启容器
4. 验证通信
5. 抓包分析

**预期结果**: 
- vpp-phase2-simulation 每 10 秒向 vpp-master 发送 POST 请求
- 每 30 秒发送 GET /health 请求
- 可以用 Wireshark 看到 HTTP 流量

