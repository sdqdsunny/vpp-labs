# 阿里云安全组配置指南

## 问题诊断

如果 `curl http://pte.ciscolab.cn:8080/test-dashboard` 超时，很可能是：
- ✅ 容器在 VPS 上正常运行
- ❌ 但阿里云安全组没有开放这些端口

## 需要映射的端口

VPP 五个容器需要以下端口：

| 容器 | 端口 | 协议 | 用途 |
|------|------|------|------|
| vpp-master | 8080 | TCP | Web 界面 + API |
| vpp-power-generation | 8081 | TCP | 电源侧 API |
| vpp-storage | 8082 | TCP | 储能侧 API |
| vpp-demand | 8083 | TCP | 需求侧 API |
| vpp-sniffer | - | - | 内部流量抓包 |

## 阿里云安全组配置步骤

### 方法 1：通过阿里云控制台（推荐）

1. **登录阿里云控制台**
   - 访问 https://console.aliyun.com
   - 进入 ECS 实例管理

2. **找到你的 VPS 实例**
   - 搜索 `pte.ciscolab.cn` 或实例 ID
   - 点击实例名称进入详情页

3. **进入安全组配置**
   - 在实例详情页，找到"安全组"标签
   - 点击关联的安全组名称

4. **添加入站规则**
   - 点击"入站规则"标签
   - 点击"添加规则"按钮
   - 为每个端口添加规则：

   **规则 1: vpp-master (8080)**
   - 协议类型: TCP
   - 端口范围: 8080/8080
   - 授权对象: 0.0.0.0/0 (允许所有 IP)
   - 优先级: 1
   - 描述: VPP Master Web Interface

   **规则 2: vpp-power-generation (8081)**
   - 协议类型: TCP
   - 端口范围: 8081/8081
   - 授权对象: 0.0.0.0/0
   - 优先级: 1
   - 描述: VPP Power Generation API

   **规则 3: vpp-storage (8082)**
   - 协议类型: TCP
   - 端口范围: 8082/8082
   - 授权对象: 0.0.0.0/0
   - 优先级: 1
   - 描述: VPP Storage API

   **规则 4: vpp-demand (8083)**
   - 协议类型: TCP
   - 端口范围: 8083/8083
   - 授权对象: 0.0.0.0/0
   - 优先级: 1
   - 描述: VPP Demand API

5. **保存规则**
   - 点击"确定"或"保存"按钮
   - 等待规则生效（通常 1-2 分钟）

### 方法 2：通过阿里云 CLI（如果已安装）

```bash
# 获取安全组 ID
aliyun ecs DescribeSecurityGroups --RegionId cn-beijing

# 添加入站规则（示例）
aliyun ecs AuthorizeSecurityGroup \
  --RegionId cn-beijing \
  --SecurityGroupId sg-xxxxx \
  --IpProtocol tcp \
  --PortRange 8080/8080 \
  --SourceCidrIp 0.0.0.0/0 \
  --Description "VPP Master"
```

### 方法 3：通过 VPS 上的 iptables（临时方案）

如果你无法访问阿里云控制台，可以在 VPS 上临时配置 iptables：

```bash
ssh root@pte.ciscolab.cn

# 查看当前规则
sudo iptables -L -n

# 添加规则
sudo iptables -A INPUT -p tcp --dport 8080 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 8081 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 8082 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 8083 -j ACCEPT

# 保存规则（CentOS/RHEL）
sudo service iptables save

# 或者保存规则（Ubuntu/Debian）
sudo iptables-save > /etc/iptables/rules.v4
```

## 验证配置

### 步骤 1：检查 VPS 上的端口监听

```bash
ssh root@pte.ciscolab.cn

# 检查端口是否在监听
netstat -tlnp | grep -E "8080|8081|8082|8083"

# 或者使用 ss 命令
ss -tlnp | grep -E "8080|8081|8082|8083"
```

**预期输出**：
```
tcp        0      0 0.0.0.0:8080            0.0.0.0:*               LISTEN
tcp        0      0 0.0.0.0:8081            0.0.0.0:*               LISTEN
tcp        0      0 0.0.0.0:8082            0.0.0.0:*               LISTEN
tcp        0      0 0.0.0.0:8083            0.0.0.0:*               LISTEN
```

### 步骤 2：从本地测试连接

```bash
# 测试 vpp-master
curl -v http://pte.ciscolab.cn:8080/health

# 测试 /test-dashboard
curl -v http://pte.ciscolab.cn:8080/test-dashboard

# 测试其他容器
curl -v http://pte.ciscolab.cn:8081/health
curl -v http://pte.ciscolab.cn:8082/health
curl -v http://pte.ciscolab.cn:8083/health
```

### 步骤 3：从 VPS 内部测试

```bash
ssh root@pte.ciscolab.cn

# 从容器内部测试
docker exec vpp-master curl -v http://localhost:8080/health
docker exec vpp-master curl -v http://localhost:8080/test-dashboard
```

## 常见问题

### Q: 为什么我添加了规则但仍然无法访问？

**A**: 可能的原因：
1. 规则还未生效（等待 1-2 分钟）
2. 容器没有正确绑定到 0.0.0.0（检查 docker-compose 配置）
3. 防火墙规则冲突（检查 iptables）
4. DNS 解析问题（尝试使用 IP 地址而不是域名）

### Q: 如何找到我的安全组 ID？

**A**: 
1. 登录阿里云控制台
2. 进入 ECS 实例管理
3. 找到你的实例
4. 在"安全组"标签中查看关联的安全组
5. 点击安全组名称查看详情

### Q: 我可以限制访问 IP 吗？

**A**: 可以。在"授权对象"字段中，不要使用 `0.0.0.0/0`，而是使用你的 IP 地址：
- 单个 IP: `1.2.3.4/32`
- IP 段: `1.2.3.0/24`

### Q: 规则生效需要多长时间？

**A**: 通常 1-2 分钟。如果超过 5 分钟仍未生效，尝试：
1. 刷新浏览器缓存
2. 重启 VPS 实例
3. 检查是否有其他防火墙规则冲突

## 快速检查清单

- [ ] 登录阿里云控制台
- [ ] 找到 VPS 实例
- [ ] 进入安全组配置
- [ ] 添加 4 个入站规则（8080, 8081, 8082, 8083）
- [ ] 等待规则生效（1-2 分钟）
- [ ] 测试 `curl http://pte.ciscolab.cn:8080/health`
- [ ] 测试 `curl http://pte.ciscolab.cn:8080/test-dashboard`
- [ ] 验证所有端口都可访问

## 下一步

配置完成后：

1. ✅ 验证所有端口都可访问
2. ✅ 检查 `/test-dashboard` 是否加载
3. ✅ 部署新的安全工具集成代码到 VPS
4. ✅ 测试所有功能

---

**需要帮助？** 完成配置后，运行以下命令验证：

```bash
./verify-vps-containers.sh
```

这个脚本会检查所有端口和端点是否可访问。
